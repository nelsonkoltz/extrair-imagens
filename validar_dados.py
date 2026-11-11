"""Verificacoes de consistencia; nao substituem comparacao com a imagem."""
import re


def validar(registros):
    resultados = []
    bloco = None
    valores = []
    codigos = []
    padrao = re.compile(r'^\(([^)]+)\)\s+([0-9]+)\s+([0-9]+\.[0-9]+)\s*$')
    for registro in registros:
        texto = registro['texto'].strip()
        if texto == '(nCCl) Cortes do depurador':
            bloco, valores, codigos = 'Cortes do depurador', [], []
        elif texto == '(nCSp) Cortes especiais do depurador':
            bloco, valores, codigos = 'Cortes especiais do depurador', [], []
        match = padrao.fullmatch(texto)
        if not match or not bloco:
            continue
        codigo, n, _ = match.groups()
        n = int(n)
        if codigo in ('nCCl', 'nCSp'):
            soma = sum(valores)
            esperados = ({'nCN','nCS','nCL','nCT','nCFF','nCPp'} if codigo == 'nCCl' else
                         {'nCSy','nCB','nCSK','nCU','nCMo','nCYC','nCYFC','nCFFC','nCSfI'})
            completo = set(codigos) == esperados and len(codigos) == len(esperados)
            resultados.append({'teste': bloco, 'total_lido': n, 'soma_das_linhas': soma,
                               'resultado': ('NAO_VERIFICAVEL' if not completo else 'CONSISTENTE' if soma == n else 'DIVERGENCIA'),
                               'codigos_ausentes': sorted(esperados - set(codigos)),
                               'codigos_inesperados': sorted(set(codigos) - esperados)})
            bloco = None
        else:
            valores.append(n)
            codigos.append(codigo)
    for teste in ('Cortes do depurador', 'Cortes especiais do depurador'):
        if not any(r['teste'] == teste for r in resultados):
            resultados.append({'teste': teste, 'resultado': 'NAO_VERIFICAVEL'})
    return resultados
