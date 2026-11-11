"""Somente os campos destacados pelo usuario, identificados pelo rotulo."""
import re
from datetime import datetime

CAMPOS = [
    ('maquina', 'Máquina', ''),
    ('nome_partida', 'Nome da partida', ''),
    ('fim_turno', 'Fim do turno', ''),
    ('rendimento_percentual', 'Rendimento da máquina', '%'),
    ('producao_kg', 'Quantidade de produção', 'kg'),
]


def selecionar(registros):
    esquerda = [r for r in registros if int(r['coluna']) == 1]
    encontrados = {}

    def guardar(chave, r, valor):
        encontrados[chave] = dict(r, campo=chave, texto=valor)

    for i, r in enumerate(esquerda):
        texto = r['texto'].strip()
        m = re.fullmatch(r'(\d+)\s+(\d+-\d+)', texto)
        if m:
            guardar('maquina', r, m[1])
        for chave, padrao in (
            ('nome_partida', r'Nome partida\s+(.+)'),
            ('fim_turno', r'Fim do turno\s+(\d{1,2}\.\d{1,2}\.(?:\d{4}|\d{2})\s+\d{1,2}:\d{2})'),
            ('producao_kg', r'Quantidade de produção\s+\[kg\]\s+(\d+\.\d+)'),
        ):
            m = re.fullmatch(padrao, texto)
            if m:
                valor = re.sub(r'\s+', ' ', m[1])
                if chave == 'fim_turno':
                    ano = valor.split()[0].split('.')[-1]
                    try:
                        datetime.strptime(valor, '%d.%m.' + ('%Y' if len(ano) == 4 else '%y') + ' %H:%M')
                    except ValueError:
                        continue
                guardar(chave, r, valor)
        if texto == 'Efeito de rendimento da' and i + 1 < len(esquerda):
            seguinte = esquerda[i + 1]
            m = re.fullmatch(r'máquina\s+\[%\]\s+(\d+\.\d+)', seguinte['texto'].strip())
            if m and int(seguinte['linha']) == int(r['linha']) + 1:
                guardar('rendimento_percentual', seguinte, m[1])
    resultado = []
    for chave, rotulo, unidade in CAMPOS:
        r = encontrados.get(chave, dict(coluna=1, linha=0, texto='', metodo='', campo=chave,
                                       status='CAMPO_NAO_ENCONTRADO'))
        resultado.append(dict(r, rotulo=rotulo, unidade=unidade))
    return resultado
