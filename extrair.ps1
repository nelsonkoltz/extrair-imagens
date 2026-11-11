param(
    [string]$Imagem = "$PSScriptRoot\reports\05_1111_0839_SG01__29_29_pent_malha_.bmp",
    [string]$Destino = "$PSScriptRoot\saida"
)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Runtime.WindowsRuntime
Add-Type -AssemblyName System.Drawing
$null = [Windows.Storage.StorageFile,Windows.Storage,ContentType=WindowsRuntime]
$null = [Windows.Storage.FileAccessMode,Windows.Storage,ContentType=WindowsRuntime]
$null = [Windows.Storage.Streams.IRandomAccessStream,Windows.Storage.Streams,ContentType=WindowsRuntime]
$null = [Windows.Graphics.Imaging.BitmapDecoder,Windows.Graphics.Imaging,ContentType=WindowsRuntime]
$null = [Windows.Graphics.Imaging.SoftwareBitmap,Windows.Graphics.Imaging,ContentType=WindowsRuntime]
$null = [Windows.Media.Ocr.OcrEngine,Windows.Foundation,ContentType=WindowsRuntime]
$null = [Windows.Media.Ocr.OcrResult,Windows.Foundation,ContentType=WindowsRuntime]
function Aguardar($Operacao, [Type]$Tipo) {
    $metodo = [System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
        $_.Name -eq 'AsTask' -and $_.IsGenericMethod -and $_.GetParameters().Count -eq 1 -and
        $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'
    } | Select-Object -First 1
    $tarefa = $metodo.MakeGenericMethod($Tipo).Invoke($null, @($Operacao))
    $tarefa.GetAwaiter().GetResult()
}
$origem = (Resolve-Path -LiteralPath $Imagem).Path
$null = New-Item -ItemType Directory -Force -Path $Destino
$Destino = (Resolve-Path -LiteralPath $Destino).Path
$nome = [IO.Path]::GetFileNameWithoutExtension($origem)
$motor = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
if (!$motor) { throw 'Instale o reconhecimento de texto do idioma Portugues nas configuracoes do Windows.' }
$bitmap = [Drawing.Bitmap]::FromFile($origem)
$linhas = @()
$texto = @('OCR AUTOMATICO - NAO REVISADO. Confira os valores na imagem original.', "Origem: $origem")
try {
    # Este layout usa duas colunas iguais; o corte impede a mistura das linhas.
    foreach ($coluna in 1..2) {
        $x = if ($coluna -eq 1) { 0 } else { [int][Math]::Floor($bitmap.Width / 2) }
        $largura = if ($coluna -eq 1) { [int][Math]::Floor($bitmap.Width / 2) } else { $bitmap.Width - $x }
        $ampliada = New-Object Drawing.Bitmap ($largura * 3), ($bitmap.Height * 3)
        $g = [Drawing.Graphics]::FromImage($ampliada)
        $g.InterpolationMode = [Drawing.Drawing2D.InterpolationMode]::NearestNeighbor
        $g.PixelOffsetMode = [Drawing.Drawing2D.PixelOffsetMode]::Half
        $g.DrawImage($bitmap, [Drawing.Rectangle]::new(0,0,$ampliada.Width,$ampliada.Height), [Drawing.Rectangle]::new($x,0,$largura,$bitmap.Height), [Drawing.GraphicsUnit]::Pixel)
        $g.Dispose()
        $temporario = Join-Path ([IO.Path]::GetTempPath()) (([guid]::NewGuid().ToString()) + '.png')
        try {
            $ampliada.Save($temporario, [Drawing.Imaging.ImageFormat]::Png)
            $arquivo = Aguardar ([Windows.Storage.StorageFile]::GetFileFromPathAsync($temporario)) ([Windows.Storage.StorageFile])
            $fluxo = Aguardar ($arquivo.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
            try {
                $decoder = Aguardar ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($fluxo)) ([Windows.Graphics.Imaging.BitmapDecoder])
                $software = Aguardar ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
                try { $resultado = Aguardar ($motor.RecognizeAsync($software)) ([Windows.Media.Ocr.OcrResult]) } finally { $software.Dispose() }
                $texto += "`r`nCOLUNA $coluna"
                $numero = 0
                $palavras = @($resultado.Lines | ForEach-Object { $_.Words } | Sort-Object { $_.BoundingRect.Y + $_.BoundingRect.Height / 2 })
                $grupos = @()
                foreach ($palavra in $palavras) {
                    $centro = $palavra.BoundingRect.Y + $palavra.BoundingRect.Height / 2
                    if (!$grupos.Count -or [Math]::Abs($centro - $grupos[-1].y) -gt 15) {
                        $grupos += [pscustomobject]@{ y=$centro; palavras=[Collections.Generic.List[object]]::new() }
                    }
                    $grupos[-1].palavras.Add($palavra)
                }
                foreach ($grupo in $grupos) {
                    $conteudo = ($grupo.palavras | Sort-Object { $_.BoundingRect.X } | ForEach-Object { $_.Text }) -join ' '
                    $numero++
                    $texto += $conteudo
                    $linhas += [pscustomobject]@{coluna=$coluna;linha=$numero;texto=$conteudo;status='NAO_REVISADO'}
                }
            } finally { $fluxo.Dispose() }
        } finally {
            $ampliada.Dispose()
            Remove-Item -LiteralPath $temporario -Force -ErrorAction SilentlyContinue
        }
    }
} finally { $bitmap.Dispose() }
$texto | Set-Content -LiteralPath (Join-Path $Destino "$nome.ocr.txt") -Encoding UTF8
$linhas | Export-Csv -LiteralPath (Join-Path $Destino "$nome.ocr.csv") -Delimiter ';' -NoTypeInformation -Encoding UTF8
Write-Host "Extraidos $($linhas.Count) registros OCR em $Destino. Os registros precisam de revisao."
