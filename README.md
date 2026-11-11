# Extrair dados de imagens

Robô local para Windows que monitora `entrada` e gera somente CSVs:

- Qualquer `.bmp`: `processadas/conicaleiras`.
- `1.3.1_RT_*.png`: `processadas/riater`.

## Executar

Use Python 3.10 ou superior e o reconhecimento de texto do Windows instalado. Não há dependências pip. Abra `iniciar_robo.cmd` ou execute:

```powershell
python robo.py
```

Para processar uma única vez:

```powershell
python robo.py --uma-vez
```

As pastas de entrada e saída são criadas automaticamente. O Python portátil de `.runtime` não é distribuído neste repositório; o inicializador usa `python` do sistema quando ele não está presente.

Consulte [COMO_USAR_ROBO.md](COMO_USAR_ROBO.md) para campos, filtros e limites de precisão. A calibração depende do formato dos relatórios e do enquadramento da tela; confira os CSVs com as imagens originais.

## Testes

```powershell
python test_tela.py
```

Testes com imagens de referência são ignorados quando as imagens não estão disponíveis. Imagens de produção, saídas CSV e arquivos temporários não são versionados.
