"""Constroi modelos somente das celulas explicitamente transcritas da amostra."""
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fonte_bitmap import carregar

BASE = Path(__file__).resolve().parent


def calibrar():
    arquivo = BASE / 'reports' / '05_1111_0839_SG01__29_29_pent_malha_.bmp'
    _, celula = carregar(arquivo.read_bytes())
    # coluna, linha (base zero), posicao horizontal (base zero), transcricao.
    amostras = [
        (1, 0, 0, '*'),
        (1, 12, 0, '*'),
        (1, 12, 10, 'Ó'),
        (1, 21, 28, '[Ne]'),
        (1, 34, 29, '[%]'),
        (1, 35, 28, '[kg]'),
        (1, 52, 32, '<'),
        (1, 78, 6, 'y'),
        (1, 5, 36, 'x'),
        (2, 5, 0, 'K'),
        (2, 9, 29, 'W'),
        (2, 28, 35, '='),
        (1, 1, 12, 'Informator AC X5'),
        (1, 3, 0, 'S1.30.01'),
        (1, 4, 0, 'S:1.30.00'),
        (1, 5, 0, 'Costa Rica'),
        (1, 6, 0, '05'),
        (1, 7, 0, 'LOEPFE YarnMaster'),
        (1, 9, 0, 'Ligação à rede de'),
        (1, 10, 0, 'comunicação'),
        (1, 14, 0, 'Grupo'),
        (1, 15, 0, 'Nome partida'),
        (1, 16, 0, 'Número da partida'),
        (1, 17, 0, 'Area de trabalho'),
        (1, 18, 0, 'Condução'),
        (1, 19, 0, 'Fim do turno'),
        (1, 20, 0, 'No. de fios'),
        (1, 21, 0, 'Titulo do fio'),
        (1, 22, 0, 'Velocidade'),
        (1, 23, 0, 'Comprimento teórico'),
        (1, 24, 0, 'Pressostato : pressão de'),
        (1, 25, 0, 'comutação'),
        (1, 26, 0, 'Opções'),
        (1, 30, 0, 'Tempo de produção'),
        (1, 31, 0, 'Tempo de observação'),
        (1, 32, 0, 'Duração do turno'),
        (1, 33, 0, 'Efeito de rendimento da'),
        (1, 34, 0, 'máquina'),
        (1, 35, 0, 'Quantidade de produção'),
        (1, 36, 0, 'Bobinas cruzadas trocadas'),
        (1, 37, 0, 'Junções de fio'),
        (1, 38, 0, 'Rupturas de fio'),
        (1, 39, 0, '(nYBE/)'),
        (1, 40, 0, 'Cortes do depurador'),
        (1, 41, 0, '(nCX/)'),
        (1, 42, 0, 'Cortes do depurador/espula'),
        (1, 44, 0, 'Luzes vermelhas'),
        (1, 45, 0, 'Duração/luz vermelha'),
        (1, 46, 0, 'LUZ VERMELHA-AMARELA'),
        (1, 47, 0, 'PERMANENTE'),
        (1, 48, 0, 'Intervenções adicionais'),
        (1, 21, 35, '29.00'),
        (1, 35, 34, '175.01'),
        (1, 38, 36, '48.7'),
        (1, 36, 38, '62'),
    ]
    modelos = {}
    for coluna, linha, inicio, texto in amostras:
        for indice, letra in enumerate(texto):
            if letra == ' ':
                continue
            desenho = celula(coluna, linha, inicio + indice)
            if '1' not in desenho:
                raise ValueError(f'Amostra vazia em {linha}/{inicio + indice}: {letra!r}')
            modelos.setdefault(desenho, [])
            if letra not in modelos[desenho]:
                if modelos[desenho] and set(modelos[desenho] + [letra]) not in ({'0', 'O'}, {'1', 'l'}):
                    raise ValueError(f'Conflito na linha {linha}, indice {inicio + indice}: {modelos[desenho]!r} e {letra!r}')
                modelos[desenho].append(letra)
    (BASE / 'modelos_fonte.json').write_text(json.dumps(modelos, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'{len(modelos)} desenhos cadastrados.')


if __name__ == '__main__':
    calibrar()
