# Robô de extração para CSV

1. Abra `iniciar_robo.cmd` e mantenha a janela aberta.
2. Coloque as imagens em `entrada`.
3. Os CSVs são salvos de acordo com o nome e o formato:

| Imagens aceitas | Pasta dos CSVs |
| --- | --- |
| Qualquer arquivo `.bmp` | `processadas/conicaleiras` |
| `1.3.1_RT_*.png` | `processadas/riater` |

JPEGs, arquivos `1.3.2_RT_*.png`, arquivos `1.3.3_RT_*.png` e outros nomes são ignorados. As extensões podem estar em maiúsculas. Cada imagem gera somente um CSV com o mesmo nome, diretamente na pasta correspondente; a imagem original não é movida nem alterada.

Para encerrar, pressione Ctrl+C ou feche a janela. `parar_robo.cmd` encerra outras instâncias deste robô. O modo `iniciar_tela.cmd` lê somente os PNGs aceitos para riater.

## Campos

Conicaleiras: `maquina`, `nome_partida`, `fim_turno`, `rendimento_percentual` e `producao_kg`.

Riater: `artigo`, `pedido`, `data_inicio`, `turno`, `rendimento_percentual` e `producao_kg`. Não são exportadas data final nem horas de início e fim.

## Leitura e precisão

Os BMPs usam a fonte calibrada. Para a tela PNG, as regiões de `regioes_tela.json` usam uma referência de 1024 × 799 pixels. O OCR do Windows lê a página com contraste ampliado e seleciona palavras pela posição; campos omitidos recebem uma tentativa adicional por recorte. A imagem precisa manter o mesmo enquadramento. Margens ou recortes diferentes exigem nova calibração.

Campos não encontrados ficam vazios e geram aviso na janela. A leitura automática precisa de conferência; não há garantia de 100% de precisão. `test_tela.py` compara todos os campos de uma amostra PNG com os valores conferidos visualmente, além de testar os filtros e os destinos.

## Arquivos e comandos

O separador do CSV é `;`, com codificação UTF-8 com BOM. Para preservar zeros à esquerda e pontos decimais no Excel, importe as colunas como texto. Feche o CSV no Excel para permitir sua atualização.

Não são gerados TXT, HTML, JSON ou log nas pastas de saída. Intermediários do OCR são temporários e removidos ao terminar. Saídas antigas das pastas `processados` e `resultados` são históricas.

Processar uma vez:

```powershell
.\.runtime\python\python.exe .\robo.py --uma-vez
```

As opções `--entrada`, `--saida-conicaleiras` e `--saida-riater` permitem alterar as pastas. `--saida` é um apelido de `--saida-conicaleiras`.

Executar os testes da tela e dos filtros:

```powershell
.\.runtime\python\python.exe .\test_tela.py
```
