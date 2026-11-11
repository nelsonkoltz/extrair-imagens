param([Parameter(Mandatory=$true)][string]$Imagem,
      [Parameter(Mandatory=$true)][string]$Destino,
      [string]$Configuracao = '')
$ErrorActionPreference = 'Stop'
if (!$Configuracao) { $Configuracao = Join-Path $PSScriptRoot 'regioes_tela.json' }
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
    $metodo.MakeGenericMethod($Tipo).Invoke($null, @($Operacao)).GetAwaiter().GetResult()
}
function ReconhecerArquivo([string]$Caminho, $Motor) {
    $arquivo = Aguardar ([Windows.Storage.StorageFile]::GetFileFromPathAsync($Caminho)) ([Windows.Storage.StorageFile])
    $fluxo = Aguardar ($arquivo.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
    try {
        $decoder = Aguardar ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($fluxo)) ([Windows.Graphics.Imaging.BitmapDecoder])
        $software = Aguardar ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
        try { Aguardar ($Motor.RecognizeAsync($software)) ([Windows.Media.Ocr.OcrResult]) }
        finally { $software.Dispose() }
    } finally { $fluxo.Dispose() }
}
$config = Get-Content -LiteralPath $Configuracao -Encoding UTF8 -Raw | ConvertFrom-Json
$bitmap = [Drawing.Bitmap]::FromFile((Resolve-Path -LiteralPath $Imagem).Path)
$motor = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
if (!$motor) { throw 'OCR do Windows indisponivel.' }
$dados = @{}
try {
    # O contexto da pagina inteira evita perder palavras isoladas nos recortes.
    $escala = 2
    $ampliada = [Drawing.Bitmap]::new($bitmap.Width * $escala, $bitmap.Height * $escala)
    $g = [Drawing.Graphics]::FromImage($ampliada)
    $g.InterpolationMode = [Drawing.Drawing2D.InterpolationMode]::NearestNeighbor
    $g.PixelOffsetMode = [Drawing.Drawing2D.PixelOffsetMode]::Half
    $atributos = [Drawing.Imaging.ImageAttributes]::new()
    $atributos.SetThreshold(0.5)
    $g.DrawImage($bitmap, [Drawing.Rectangle]::new(0,0,$ampliada.Width,$ampliada.Height),0,0,$bitmap.Width,$bitmap.Height,[Drawing.GraphicsUnit]::Pixel,$atributos)
    $atributos.Dispose()
    $g.Dispose()
    $temp = Join-Path ([IO.Path]::GetTempPath()) (([guid]::NewGuid().ToString()) + '.png')
    try {
        $ampliada.Save($temp,[Drawing.Imaging.ImageFormat]::Png)
        $arquivo = Aguardar ([Windows.Storage.StorageFile]::GetFileFromPathAsync($temp)) ([Windows.Storage.StorageFile])
        $fluxo = Aguardar ($arquivo.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
        try {
            $decoder = Aguardar ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($fluxo)) ([Windows.Graphics.Imaging.BitmapDecoder])
            $software = Aguardar ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
            try { $resultado = Aguardar ($motor.RecognizeAsync($software)) ([Windows.Media.Ocr.OcrResult]) }
            finally { $software.Dispose() }
            $palavras = @($resultado.Lines | ForEach-Object { $_.Words })
            foreach ($campo in $config.regioes.PSObject.Properties) {
                $r = $campo.Value
                $x = $r[0] * $bitmap.Width / $config.largura_referencia * $escala
                $y = $r[1] * $bitmap.Height / $config.altura_referencia * $escala
                $w = $r[2] * $bitmap.Width / $config.largura_referencia * $escala
                $h = $r[3] * $bitmap.Height / $config.altura_referencia * $escala
                $selecionadas = @($palavras | Where-Object {
                    $cx = $_.BoundingRect.X + $_.BoundingRect.Width / 2
                    $cy = $_.BoundingRect.Y + $_.BoundingRect.Height / 2
                    $cx -ge $x -and $cx -le ($x+$w) -and $cy -ge $y -and $cy -le ($y+$h)
                } | Sort-Object { [Math]::Floor(($_.BoundingRect.Y + $_.BoundingRect.Height / 2) / (10*$escala)) }, { $_.BoundingRect.X })
                $dados[$campo.Name] = ($selecionadas | ForEach-Object { $_.Text }) -join ' '
                $numerico = $campo.Name -in @('rendimento_percentual', 'producao_kg')
                if (!$dados[$campo.Name] -or ($numerico -and $dados[$campo.Name] -notmatch '\d+[.,]\d+')) {
                    # Um recorte ampliado recupera campos omitidos na pagina inteira.
                    $sx = [int][Math]::Round($x / $escala)
                    $sy = [int][Math]::Round($y / $escala)
                    $sw = [int][Math]::Round($w / $escala)
                    $sh = [int][Math]::Round($h / $escala)
                    $recorte = [Drawing.Bitmap]::new($sw*3+40,$sh*3+40)
                    $gc = [Drawing.Graphics]::FromImage($recorte)
                    $gc.Clear([Drawing.Color]::White)
                    $gc.InterpolationMode = [Drawing.Drawing2D.InterpolationMode]::NearestNeighbor
                    $gc.PixelOffsetMode = [Drawing.Drawing2D.PixelOffsetMode]::Half
                    $gc.DrawImage($bitmap,[Drawing.Rectangle]::new(20,20,$sw*3,$sh*3),[Drawing.Rectangle]::new($sx,$sy,$sw,$sh),[Drawing.GraphicsUnit]::Pixel)
                    $gc.Dispose()
                    $outro = Join-Path ([IO.Path]::GetTempPath()) (([guid]::NewGuid().ToString()) + '.png')
                    try {
                        $recorte.Save($outro,[Drawing.Imaging.ImageFormat]::Png)
                        $local = ReconhecerArquivo $outro $motor
                        $dados[$campo.Name] = ($local.Lines | ForEach-Object { $_.Text }) -join ' '
                    } finally {
                        $recorte.Dispose()
                        Remove-Item -LiteralPath $outro -Force -ErrorAction SilentlyContinue
                    }
                }
            }
        } finally { $fluxo.Dispose() }
    } finally {
        $ampliada.Dispose()
        Remove-Item -LiteralPath $temp -Force -ErrorAction SilentlyContinue
    }
} finally { $bitmap.Dispose() }
$dados | ConvertTo-Json | Set-Content -LiteralPath $Destino -Encoding UTF8
