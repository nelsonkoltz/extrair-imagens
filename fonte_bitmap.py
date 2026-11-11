"""Leitura exata de celulas 7x14 dos BMPs monocromaticos deste relatorio.

Nao usa aproximacao: apenas desenhos identicos aos modelos sao reconhecidos.
"""
import struct
import re


class LayoutIncompativel(ValueError):
    pass


def carregar(dados):
    if dados[:2] != b'BM' or len(dados) < 62:
        raise LayoutIncompativel('Nao e BMP monocromatico suportado.')
    offset = struct.unpack_from('<I', dados, 10)[0]
    tamanho = struct.unpack_from('<I', dados, 14)[0]
    largura, altura, planos, bits, compressao = struct.unpack_from('<iiHHI', dados, 18)
    if tamanho != 40 or largura != 640 or altura <= 0 or planos != 1 or bits != 1 or compressao:
        raise LayoutIncompativel('Esperado BMP 640px, 1 bit, sem compressao, cabecalho de 40 bytes.')
    stride = ((largura + 31) // 32) * 4
    if len(dados) < offset + stride * altura:
        raise LayoutIncompativel('BMP incompleto.')
    paleta = dados[54:62]
    escuro = 0 if sum(paleta[:3]) < sum(paleta[4:7]) else 1

    def pixel(x, y):
        if y >= altura:
            return 0
        byte = dados[offset + (altura - 1 - y) * stride + x // 8]
        return int(((byte >> (7 - x % 8)) & 1) == escuro)

    def celula(coluna, linha, indice):
        x = (320 if coluna == 2 else 0) + indice * 7
        return ''.join(str(pixel(x + dx, linha * 14 + dy)) for dy in range(14) for dx in range(7))

    return altura, celula


def extrair(dados, modelos):
    altura, celula = carregar(dados)
    registros = []
    desconhecidos = {}
    for coluna in (1, 2):
        for linha in range((altura + 13) // 14):
            letras = []
            pendencias = []
            ambiguos = []
            for indice in range(40):
                desenho = celula(coluna, linha, indice)
                if '1' not in desenho:
                    letras.append(' ')
                elif desenho in modelos and len(modelos[desenho]) == 1:
                    letras.append(modelos[desenho][0])
                elif desenho in modelos and set(modelos[desenho]) == {'0', 'O'}:
                    letras.append('\ufff0')
                    ambiguos.append(indice + 1)
                else:
                    letras.append('\u25a1')
                    pendencias.append(indice + 1)
                    desconhecidos[desenho] = desconhecidos.get(desenho, 0) + 1
            texto = ''.join(letras).rstrip()
            # A fonte desenha O e zero de forma identica. Contexto produz apenas
            # uma sugestao, registrada como ambigua e sempre sujeita a revisao.
            def resolver(match):
                palavra = match.group()
                numero = any(c.isdigit() for c in palavra) or not any(c.isalpha() for c in palavra)
                return palavra.replace('\ufff0', '0' if numero else 'O')
            texto = re.sub(r'\S+', resolver, texto)
            if texto.strip():
                registros.append({'coluna': coluna, 'linha': linha + 1, 'texto': texto,
                                  'status': 'NAO_REVISADO',
                                  'posicoes_desconhecidas': ','.join(map(str, pendencias)),
                                  'posicoes_ambiguas_0_O': ','.join(map(str, ambiguos)),
                                  'metodo': 'FONTE_EXATA'})
    return registros, desconhecidos
