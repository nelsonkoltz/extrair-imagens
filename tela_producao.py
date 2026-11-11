"""Valida os valores de regioes da tela de producao; nao completa numeros."""
from datetime import datetime
import re

CAMPOS_TELA = ['artigo', 'pedido', 'data_inicio',
               'turno', 'rendimento_percentual', 'producao_kg']


def interpretar_tela(bruto):
    dados = dict.fromkeys(CAMPOS_TELA, '')
    for chave in ('artigo', 'pedido'):
        texto = ' '.join(bruto.get(chave, '').split())
        dados[chave] = re.sub(r'^' + chave + r'\s*', '', texto, flags=re.IGNORECASE)
    periodo = bruto.get('periodo', '')
    datas = re.findall(r'\b\d{1,2}\.\d{1,2}\.(?:\d{4}|\d{2})\b', periodo)
    horas = re.findall(r'\b\d{1,2}:\d{2}\b', periodo)
    if len(datas) == 2 and len(horas) == 2:
        try:
            for data, hora in zip(datas, horas):
                formato = '%d.%m.' + ('%Y' if len(data.split('.')[-1]) == 4 else '%y') + ' %H:%M'
                datetime.strptime(data + ' ' + hora, formato)
            dados['data_inicio'] = datas[0]
        except ValueError:
            pass
    turno = bruto.get('turno', '').strip()
    turno = re.sub(r'\b\d{1,2}\.\d{1,2}\.(?:\d{4}|\d{2})\b', '', turno)
    turno = re.sub(r'\b\d{1,2}:\d{2}\b', '', turno).replace('-', '').strip()
    if re.fullmatch(r'[1-9]', turno):
        dados['turno'] = turno
    for chave in ('rendimento_percentual', 'producao_kg'):
        valor = bruto.get(chave, '').strip().replace(',', '.')
        if chave == 'rendimento_percentual':
            valor = re.sub(r'^Rendimento da produção\s*', '', valor, flags=re.IGNORECASE)
        if re.fullmatch(r'\d+(?:\.\d+)?', valor):
            if chave != 'rendimento_percentual' or 0 <= float(valor) <= 100:
                dados[chave] = valor
    return dados
