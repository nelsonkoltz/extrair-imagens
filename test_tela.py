import sys
from pathlib import Path
import unittest
import tempfile
import csv
sys.path.insert(0, str(Path(__file__).resolve().parent))
from tela_producao import interpretar_tela
from robo import processar, deve_processar
import subprocess


class TelaTest(unittest.TestCase):
    def test_filtro_por_nome_e_extensao(self):
        self.assertTrue(deve_processar(Path('1.3.1_RT_09-11-2026-turno-1.png')))
        self.assertTrue(deve_processar(Path('1.3.1_RT_teste.PNG')))
        self.assertFalse(deve_processar(Path('09-11-2026-turno-2.png')))
        self.assertFalse(deve_processar(Path('x1.3.1_RT_teste.png')))
        self.assertFalse(deve_processar(Path('1.3.1_RT_teste.jpeg')))
        self.assertFalse(deve_processar(Path('1.3.1_RT_teste.jpg')))
        self.assertFalse(deve_processar(Path('1.3.2_RT_teste.png')))
        self.assertTrue(deve_processar(Path('01_relatorio.bmp')))
        self.assertTrue(deve_processar(Path('01_relatorio.BMP')))
        self.assertTrue(deve_processar(Path('05_relatorio.bmp')))
        self.assertTrue(deve_processar(Path('relatorio.bmp')))
        self.assertFalse(deve_processar(Path('01_relatorio.png')))
        self.assertFalse(deve_processar(Path('01_relatorio.bmp'), 'tela'))

    def test_png_original_de_ponta_a_ponta(self):
        imagem = Path(__file__).resolve().parent / 'entrada' / '1.3.1_RT_2026-11-11_05h31m15s_MC.png'
        if not imagem.exists():
            self.skipTest('PNG de referencia indisponivel.')
        with tempfile.TemporaryDirectory() as pasta:
            saida = Path(pasta)
            self.assertTrue(processar(imagem, saida))
            arquivo = saida / (imagem.stem + '.csv')
            self.assertEqual(list(saida.iterdir()), [arquivo])
            with arquivo.open(encoding='utf-8-sig', newline='') as f:
                registros = list(csv.DictReader(f, delimiter=';'))
            self.assertEqual(registros, [dict(artigo='NE 30/1', pedido='Maq 6', data_inicio='10.11.26',
                turno='1',
                rendimento_percentual='56.2', producao_kg='596.0')])

    def test_lote_ignora_outros_prefixos_e_grava_em_riater(self):
        base = Path(__file__).resolve().parent
        origem = base / 'entrada' / '1.3.1_RT_2026-11-11_05h31m15s_MC.png'
        if not origem.exists():
            self.skipTest('PNG de referencia indisponivel.')
        with tempfile.TemporaryDirectory() as tmp:
            entrada = Path(tmp) / 'entrada'
            entrada.mkdir()
            (entrada / origem.name).write_bytes(origem.read_bytes())
            (entrada / '09-11-2026-turno-2.jpeg').write_bytes(b'nao deve ser lido')
            (entrada / '1.3.1_RT_ignorar.jpeg').write_bytes(b'nao deve ser lido')
            (entrada / '1.3.2_RT_ignorar.png').write_bytes(b'nao deve ser lido')
            (entrada / '1.3.3_RT_ignorar.png').write_bytes(b'nao deve ser lido')
            bmp = next((base / 'entrada').glob('01_*.bmp'), None)
            if bmp is not None:
                (entrada / bmp.name).write_bytes(bmp.read_bytes())
            (entrada / '05_ignorar.txt').write_bytes(b'nao deve ser lido')
            riater = Path(tmp) / 'processadas' / 'riater'
            conicaleiras = Path(tmp) / 'processadas' / 'conicaleiras'
            resultado = subprocess.run([sys.executable, str(base/'robo.py'), '--entrada', str(entrada),
                '--saida-conicaleiras', str(conicaleiras), '--saida-riater', str(riater), '--uma-vez'], capture_output=True)
            self.assertEqual(resultado.returncode, 0, resultado.stderr)
            self.assertEqual([p.name for p in riater.iterdir()], [origem.stem+'.csv'])
            if bmp is not None:
                self.assertEqual([p.name for p in conicaleiras.iterdir()], [bmp.stem+'.csv'])
                with next(conicaleiras.iterdir()).open(encoding='utf-8-sig', newline='') as f:
                    registros = list(csv.DictReader(f, delimiter=';'))
                self.assertTrue(registros[0]['fim_turno'])
                self.assertNotIn('artigo', registros[0])
            else:
                self.assertEqual(list(conicaleiras.iterdir()), [])

    def test_valores_mostrados_na_captura(self):
        resultado = interpretar_tela(dict(artigo='NE 30/1', pedido='Maq 6',
            periodo='09.11.26 - 09.11.26 05:00 - 13:30', turno='1',
            rendimento_percentual='61.7', producao_kg='654.5'))
        self.assertEqual(resultado, dict(artigo='NE 30/1', pedido='Maq 6', data_inicio='09.11.26',
            turno='1',
            rendimento_percentual='61.7', producao_kg='654.5'))

    def test_nao_corrige_digitos_por_adivinhacao(self):
        r = interpretar_tela(dict(periodo='31.02.26 - 31.02.26 05:00 - 13:30',
            turno='I', rendimento_percentual='6I.7', producao_kg='65A.5'))
        for c in ('data_inicio', 'turno', 'rendimento_percentual', 'producao_kg'):
            self.assertEqual(r[c], '')


if __name__ == '__main__':
    unittest.main()
