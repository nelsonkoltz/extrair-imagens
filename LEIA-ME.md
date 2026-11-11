# Extracao do relatorio BMP

O robô em Python está pronto. Veja [COMO_USAR_ROBO.md](COMO_USAR_ROBO.md) e abra `iniciar_robo.cmd` para monitorar a pasta `entrada`. As instruções abaixo se referem ao extrator PowerShell inicial, usado também como alternativa para formatos incompatíveis com o leitor da fonte.

Execute no PowerShell, nesta pasta:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\extrair.ps1
```

Para outra imagem com o mesmo layout de duas colunas:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\extrair.ps1 -Imagem '.\reports\outra.bmp'
```

Requer Windows com reconhecimento OCR do idioma instalado. Usa o OCR local do Windows, sem envio da imagem para servicos externos. As saidas automaticas ficam em `saida`, com sufixo `.ocr.txt` e `.ocr.csv`; uma nova execucao substitui as saidas da mesma imagem.

## Arquivos conferidos para a imagem 05_1111_0839_SG01__29_29_pent_malha_.bmp

- `dados_conferidos.csv`: campos de identificacao, turno, producao, analise, preparacao e alarmes.
- `depurador_conferido.csv`: contagens e taxas da tabela do depurador.
- `fora_padrao_conferido.csv`: tabela de posicoes fora do padrao. A linha REFERENCIA transcreve a linha logo abaixo do cabecalho; nao e uma posicao de trabalho. O asterisco original foi preservado.

Os CSVs usam ponto e virgula como separador e preservam o ponto decimal da imagem. Importe as colunas como texto no Excel para evitar conversao de datas, codigos e valores. Unidades em branco nao foram inferidas. Rotulos foram normalizados para leitura; os numeros foram transcritos da imagem. A imagem original continua sendo a referencia para auditoria. A verificacao visual nao constitui garantia de ausencia de erro.

Os arquivos conferidos sao especificos desta imagem e NAO sao recriados pelo script. Nao abrangem todos os textos decorativos ou identificadores tecnicos do cabecalho. Confira especialmente os codigos com I/l e os indicadores da tabela fora do padrao antes de usa-los em integracoes.

## Precisao

O OCR deste BMP apresentou trocas entre letras e numeros e omissoes. Por isso toda saida automatica e marcada NAO_REVISADO. Nao use a saida automatica como dado validado sem comparar com a imagem. Para outras imagens, execute o script e revise os campos antes de utiliza-los. O corte em duas colunas pressupoe o mesmo layout; outros layouts exigem ajuste.
