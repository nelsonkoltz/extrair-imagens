"""Monitora uma pasta e gera somente um CSV por imagem."""
import argparse
import csv
import io
import json
import logging
import os
from pathlib import Path
import subprocess
import tempfile
import time
import sys

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
from fonte_bitmap import extrair, LayoutIncompativel
from campos_selecionados import selecionar, CAMPOS
from tela_producao import interpretar_tela, CAMPOS_TELA
EXTENSOES = {'.bmp', '.png'}
PNG_TELA = {'.png'}


def deve_processar(imagem, modelo='auto'):
    if imagem.suffix.lower() in PNG_TELA:
        return imagem.name.lower().startswith('1.3.1_rt_')
    return modelo != 'tela' and imagem.suffix.lower() == '.bmp'


def processar(imagem, saida, modelo='auto'):
    if not deve_processar(imagem, modelo):
        return False
    if imagem.suffix.lower() in PNG_TELA:
        modelo = 'tela'
    destino = saida / (imagem.stem + '.csv')
    saida.mkdir(parents=True, exist_ok=True)
    # O OCR usa uma copia temporaria dos bytes lidos da imagem.
    with tempfile.TemporaryDirectory(prefix='extrair_') as tmp:
        copia = Path(tmp) / ('original' + imagem.suffix.lower())
        conteudo = imagem.read_bytes()
        copia.write_bytes(conteudo)
        modelos = json.loads((BASE / 'modelos_fonte.json').read_text(encoding='utf-8'))
        registros = None
        if modelo != 'tela':
            try:
                registros, _ = extrair(conteudo, modelos)
            except LayoutIncompativel:
                pass
        if registros is None and modelo != 'tela':
            processo = subprocess.run(
                ['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
                 str(BASE / 'extrair.ps1'), '-Imagem', str(copia), '-Destino', str(tmp)],
                capture_output=True, timeout=180,
            )
            if processo.returncode:
                raise RuntimeError(processo.stderr.decode('utf-8', errors='replace'))
            with (Path(tmp) / 'original.ocr.csv').open(encoding='utf-8-sig', newline='') as f:
                registros = list(csv.DictReader(f, delimiter=';'))
        textos = ' '.join(r['texto'] for r in (registros or []))
        eh_tela = modelo == 'tela' or ('artigo' in textos.lower() and 'pedido' in textos.lower())
        if eh_tela:
            arquivo_json = Path(tmp) / 'campos_tela.json'
            processo = subprocess.run(
                ['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
                 str(BASE / 'extrair_tela.ps1'), '-Imagem', str(copia), '-Destino', str(arquivo_json)],
                capture_output=True, timeout=180)
            if processo.returncode:
                raise RuntimeError(processo.stderr.decode('utf-8', errors='replace'))
            valores = interpretar_tela(json.loads(arquivo_json.read_text(encoding='utf-8-sig')))
            colunas = CAMPOS_TELA
            for chave, valor in valores.items():
                if not valor:
                    logging.warning('%s: confira o campo da tela %s.', imagem.name, chave)
            if sum(bool(v) for v in valores.values()) < 3:
                raise RuntimeError('Tela nao identificada nas regioes configuradas; confira o enquadramento.')
        elif not registros:
            raise RuntimeError('OCR nao identificou texto; nao foi gerado resultado valido.')
        else:
            registros = selecionar(registros)
            for campo in registros:
                if not campo['texto'] or '\u25a1' in campo['texto']:
                    logging.warning('%s: confira %s.', imagem.name, campo['rotulo'])
            valores = {r['campo']: r['texto'] for r in registros}
            colunas = [c[0] for c in CAMPOS]
        buffer = io.StringIO(newline='')
        escritor = csv.DictWriter(buffer, fieldnames=colunas, delimiter=';')
        escritor.writeheader()
        escritor.writerow(valores)
        dados = buffer.getvalue().encode('utf-8-sig')
        if destino.exists() and destino.read_bytes() == dados:
            return False
        temporario = None
        try:
            with tempfile.NamedTemporaryFile(dir=saida, suffix='.tmp', delete=False) as f:
                temporario = Path(f.name)
                f.write(dados)
            os.replace(temporario, destino)
        finally:
            if temporario and temporario.exists():
                temporario.unlink()
    logging.info('CSV gerado: %s', destino)
    return True



def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--entrada', type=Path, default=BASE / 'entrada')
    parser.add_argument('--saida', '--saida-conicaleiras', dest='saida', type=Path,
                        default=BASE / 'processadas' / 'conicaleiras')
    parser.add_argument('--saida-riater', type=Path, default=BASE / 'processadas' / 'riater')
    parser.add_argument('--uma-vez', action='store_true', help='Processa a pasta e encerra.')
    parser.add_argument('--modelo', choices=['auto', 'tela'], default='auto', help='Modelo automatico ou tela de producao.')
    args = parser.parse_args()
    args.entrada = args.entrada.resolve()
    args.saida = args.saida.resolve()
    args.saida_riater = args.saida_riater.resolve()
    if args.entrada in (args.saida, args.saida_riater):
        parser.error('Entrada e saida devem ser pastas diferentes.')
    args.entrada.mkdir(parents=True, exist_ok=True)
    args.saida.mkdir(parents=True, exist_ok=True)
    args.saida_riater.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s',
                        handlers=[logging.StreamHandler()])
    logging.info('Monitorando %s. Ctrl+C encerra.', args.entrada)
    anteriores = {}
    fontes = [BASE / nome for nome in ('robo.py', 'campos_selecionados.py', 'fonte_bitmap.py', 'modelos_fonte.json', 'tela_producao.py', 'regioes_tela.json', 'extrair_tela.ps1')]
    versoes_fontes = [p.stat().st_mtime_ns for p in fontes]
    falhas = False
    while True:
        if [p.stat().st_mtime_ns for p in fontes] != versoes_fontes:
            logging.info('Programa atualizado. Reiniciando o leitor automaticamente.')
            os.execv(sys.executable, [sys.executable, str(BASE / 'robo.py'), *sys.argv[1:]])
        for imagem in sorted(args.entrada.iterdir()):
            if not imagem.is_file() or not deve_processar(imagem, args.modelo):
                continue
            try:
                stat = imagem.stat()
                estado = (stat.st_size, stat.st_mtime_ns)
                if args.uma_vez:
                    time.sleep(0.3)
                    novo = imagem.stat()
                    if estado != (novo.st_size, novo.st_mtime_ns):
                        raise RuntimeError('Arquivo ainda esta sendo copiado; execute novamente.')
                elif anteriores.get(imagem) != estado:
                    anteriores[imagem] = estado
                    continue
                destino = args.saida_riater if imagem.suffix.lower() in PNG_TELA else args.saida
                processar(imagem, destino, args.modelo)
            except Exception:
                falhas = True
                logging.exception('Falha em %s. Nenhum resultado foi aprovado.', imagem.name)
        if args.uma_vez:
            return 1 if falhas else 0
        time.sleep(3)


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print('\nRobo encerrado.')
