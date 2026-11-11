"""Separa tabelas por posicoes fixas sem converter ou arredondar numeros."""
import re


def tabelas(registros):
    depurador, fora_padrao = [], []
    secao = None
    modo = False
    for r in registros:
        texto = r['texto']
        if 'Dados do depurador' in texto:
            secao = 'depurador'
        if secao:
            if 'Cortes especiais do depurador' in texto:
                secao = 'cortes_especiais'
            elif 'Alarme do depurador' in texto:
                secao = 'alarmes'
            m = re.fullmatch(r'\(([^)]+)\)\s+([0-9]+)\s+([0-9]+\.[0-9]+)', texto.strip())
            if m:
                codigo, quantidade, taxa = m.groups()
                depurador.append(dict(secao=secao, codigo=codigo, quantidade=quantidade,
                                      por_100_km=taxa, coluna=r['coluna'], linha=r['linha'], status='NAO_REVISADO'))
        if 'Partida fora do padrão' in texto:
            modo = True
        elif 'Análise de produção' in texto:
            modo = False
        elif modo:
            # Cada coluna conserva seus limites: asteriscos nao mudam de campo.
            partes = [texto[a:b].strip() for a, b in [(0,3),(3,10),(10,17),(17,25),(25,33),(33,40)]]
            if partes[0].isdigit():
                fora_padrao.append(dict(numero=partes[0], MA=partes[1], nCCl=partes[2], nTB=partes[3],
                                        RL=partes[4], nOS=partes[5], coluna=r['coluna'], linha=r['linha'], status='NAO_REVISADO'))
    return {'depurador.csv': depurador, 'fora_padrao.csv': fora_padrao}
