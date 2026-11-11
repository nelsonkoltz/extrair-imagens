import json
from pathlib import Path
import sys
import unittest

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
from fonte_bitmap import extrair, carregar, LayoutIncompativel
from validar_dados import validar
from robo import processar
from tabelas_relatorio import tabelas
from campos_selecionados import selecionar
import csv
import tempfile
import subprocess
import time


class ExtracaoTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.modelos = json.loads((BASE / 'modelos_fonte.json').read_text(encoding='utf-8'))

    def ler(self, nome):
        imagem = BASE / 'reports' / nome
        if not imagem.exists():
            self.skipTest('Imagem de teste original removida: ' + nome)
        return extrair(imagem.read_bytes(), self.modelos)

    def test_valores_amostra_calibrada(self):
        linhas, desconhecidos = self.ler('05_1111_0839_SG01__29_29_pent_malha_.bmp')
        self.assertFalse(desconhecidos)
        texto = '\n'.join(r['texto'] for r in linhas)
        for esperado in ('175.01', '74.9', '48.7', '-397.4', '6445', '3889', '3928'):
            self.assertIn(esperado, texto)
        self.assertTrue(all(v['resultado'] == 'CONSISTENTE' for v in validar(linhas)))

    def test_somente_campos_destacados(self):
        linhas, _ = self.ler('05_1111_0839_SG01__29_29_pent_malha_.bmp')
        resultado = selecionar(linhas)
        self.assertEqual({r['campo']: r['texto'] for r in resultado}, {
            'maquina': '05', 'nome_partida': '29pent malha',
            'fim_turno': '11.11.26 5:00', 'rendimento_percentual': '55.0', 'producao_kg': '175.01'})

    def test_fim_turno_dia_com_um_digito(self):
        for hora in ('5:00', '13:30', '22:00'):
            linhas = [dict(coluna=1, linha=20, texto='Fim do turno               9.11.26  ' + hora)]
            campo = next(r for r in selecionar(linhas) if r['campo'] == 'fim_turno')
            self.assertEqual(campo['texto'], '9.11.26 ' + hora)

    def test_fim_turno_data_ou_hora_invalida_fica_pendente(self):
        for valor in ('31.02.26 5:00', '9.11.26 25:00', '9.11.26 5:99'):
            campo = next(r for r in selecionar([dict(coluna=1, linha=20, texto='Fim do turno  ' + valor)]) if r['campo'] == 'fim_turno')
            self.assertEqual(campo['texto'], '')

    def test_fim_turno_imagens_novas(self):
        for sufixo, esperado in [('0808', '9.11.26 5:00'), ('1330', '9.11.26 13:30'), ('2200', '9.11.26 22:00')]:
            caminhos = list((BASE / 'entrada').glob('01_1109_' + sufixo + '*.bmp'))
            if not caminhos:
                continue
            linhas, _ = extrair(caminhos[0].read_bytes(), self.modelos)
            valores = {r['campo']: r['texto'] for r in selecionar(linhas)}
            self.assertEqual(valores['fim_turno'], esperado)
            self.assertNotIn('codigo_maquina', valores)

    def test_campo_ausente_nao_inventa_valor(self):
        linhas, _ = self.ler('05_1111_0839_SG01__29_29_pent_malha_.bmp')
        resultado = selecionar([r for r in linhas if not r['texto'].startswith('Quantidade de produção')])
        producao = next(r for r in resultado if r['campo'] == 'producao_kg')
        self.assertEqual(producao['texto'], '')
        self.assertEqual(producao['status'], 'CAMPO_NAO_ENCONTRADO')

    def test_frases_relatadas_pelo_usuario(self):
        for imagem in (BASE / 'reports').glob('*.bmp'):
            with self.subTest(imagem=imagem.name):
                linhas, _ = self.ler(imagem.name)
                texto = '\n'.join(r['texto'] for r in linhas)
                for frase in ('Rupturas por tensão', 'Cortes motivados por splice /', 'Defeito do fio superior'):
                    self.assertIn(frase, texto)
                for erro in ('tensaa', 'Cartes', 'da fia superior'):
                    self.assertNotIn(erro, texto)

    def test_tabelas_preservam_codigos_e_colunas(self):
        linhas, _ = self.ler('05_1111_0839_SG01__29_29_pent_malha_.bmp')
        resultado = tabelas(linhas)
        ncb = next(r for r in resultado['depurador.csv'] if r['codigo'] == 'nCB')
        self.assertEqual((ncb['quantidade'], ncb['por_100_km']), ('54', '0.6'))
        linha = next(r for r in resultado['fora_padrao.csv'] if r['numero'] == '7')
        self.assertEqual([linha[c] for c in ('MA','nCCl','nTB','RL','nOS')], ['31.9*','61.04','1.34','8.5','6'])

    def test_linha_zerada_ausente_nao_passa_na_validacao(self):
        linhas, _ = self.ler('05_1111_0839_SG01__29_29_pent_malha_.bmp')
        linhas = [r for r in linhas if not r['texto'].startswith('(nCFF)')]
        self.assertEqual(validar(linhas)[0]['resultado'], 'NAO_VERIFICAVEL')

    def test_amostra_nao_usada_na_calibracao(self):
        linhas, desconhecidos = self.ler('07_1111_1105_SG01__29_29_1ent_mlha_1.bmp')
        self.assertFalse(desconhecidos)
        for prefixo, valor in [('Quantidade de produção', '209.12'), ('Tempo de produção', '286'),
                               ('Rupturas de fio', '38.9'), ('Dispositivo de anti-imagem', '-366.4')]:
            linha = next(r['texto'] for r in linhas if r['texto'].startswith(prefixo))
            self.assertEqual(linha.split()[-1], valor)
        self.assertTrue(all(v['resultado'] == 'CONSISTENTE' for v in validar(linhas)))

    def test_bmp_truncado_rejeitado(self):
        arquivo = next((BASE / 'entrada').glob('*.bmp'), None)
        if arquivo is None:
            self.skipTest('Nenhuma imagem de teste disponivel.')
        with self.assertRaises(LayoutIncompativel):
            carregar(arquivo.read_bytes()[:100])

    def test_desenho_nao_cadastrado_nao_e_adivinhado(self):
        arquivo = next((BASE / 'entrada').glob('*.bmp'), None)
        if arquivo is None:
            self.skipTest('Nenhuma imagem de teste disponivel.')
        linhas, desconhecidos = extrair(arquivo.read_bytes(), {})
        self.assertTrue(desconhecidos)
        self.assertTrue(any('□' in r['texto'] for r in linhas))

    def test_divergencia_detectada(self):
        linhas, _ = self.ler('05_1111_0839_SG01__29_29_pent_malha_.bmp')
        for linha in linhas:
            if '(nCCl)      3889' in linha['texto']:
                linha['texto'] = linha['texto'].replace('3889', '3888')
        self.assertTrue(any(v['resultado'] == 'DIVERGENCIA' for v in validar(linhas)))

    def test_nao_reprocessa_conteudo_ja_extraido(self):
        with tempfile.TemporaryDirectory() as pasta:
            imagem = next((BASE / 'entrada').glob('*.bmp'), None)
            if imagem is None:
                self.skipTest('Nenhuma imagem de teste disponivel.')
            self.assertTrue(processar(imagem, Path(pasta)))
            self.assertFalse(processar(imagem, Path(pasta)))
            dados = Path(pasta) / (imagem.stem + '.csv')
            with dados.open(encoding='utf-8-sig', newline='') as f:
                saida = list(csv.DictReader(f, delimiter=';'))
            self.assertEqual(len(saida), 1)
            self.assertEqual(len(saida[0]), 5)
            linhas, _ = extrair(imagem.read_bytes(), self.modelos)
            self.assertEqual(saida[0], {r['campo']: r['texto'] for r in selecionar(linhas)})
            self.assertEqual(list(Path(pasta).iterdir()), [dados])

    def test_monitora_imagem_adicionada_depois_de_iniciar(self):
        with tempfile.TemporaryDirectory() as pasta:
            entrada, saida = Path(pasta) / 'entrada', Path(pasta) / 'saida'
            entrada.mkdir()
            processo = subprocess.Popen([sys.executable, str(BASE / 'robo.py'), '--entrada', str(entrada), '--saida', str(saida)],
                                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            try:
                time.sleep(1)
                imagem = next((BASE / 'entrada').glob('*.bmp'), None)
                if imagem is None:
                    self.skipTest('Nenhuma imagem de teste disponivel.')
                (entrada / imagem.name).write_bytes(imagem.read_bytes())
                limite = time.monotonic() + 20
                while time.monotonic() < limite and not list(saida.glob('*.csv')):
                    time.sleep(0.5)
                self.assertEqual(len(list(saida.glob('*.csv'))), 1)
                self.assertEqual(len(list(saida.iterdir())), 1)
            finally:
                processo.terminate()
                processo.wait(timeout=5)


if __name__ == '__main__':
    unittest.main()
