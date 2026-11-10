<#
Trae de CESGA (FinisTerrae III) los ZIP de Drama 3 y los coloca con la misma
estructura que el resto de modelos:

  audios\CASTELLANO\DRAMA3\VOZ INFANTIL\p01_es.wav ... + resultados.csv
  audios\GALLEGO\DRAMA3\VOZ PERSONA MAYOR\p01_gl.wav ...

Correspondencia de perfiles:
  infantil -> VOZ INFANTIL | joven -> VOZ JOVEN | mediana -> VOZ ADULTA | mayor -> VOZ PERSONA MAYOR

Uso (doble clic en traer_resultados_drama3.bat, o desde PowerShell):
  .\traer_resultados_drama3.ps1 -Usuario tu_usuario
  .\traer_resultados_drama3.ps1 -Usuario tu_usuario -RutaRemota '/mnt/lustre/.../drama3_cesga_paquete'
  .\traer_resultados_drama3.ps1 -ZipLocales C:\ruta\con\los\zip     (si ya los descargaste a mano)

Requisitos: cliente OpenSSH de Windows (ssh/scp) y, fuera de la red universitaria,
la VPN CheckPoint de CESGA conectada.
#>
param(
  [string]$Usuario = "",
  [string]$Servidor = "ft3.cesga.es",
  # Entre comillas simples: $STORE lo expande el servidor, no Windows.
  [string]$RutaRemota = '$STORE/drama3_cesga_paquete',
  [string]$ZipLocales = "",
  [string]$Modelo = "DRAMA3",
  [switch]$SinMacs   # quita la opción MACs=hmac-sha2-512 que recomienda CESGA para Windows
)
$ErrorActionPreference = "Stop"
$Audios = $PSScriptRoot

$Idiomas = [ordered]@{ "es" = "CASTELLANO"; "gl" = "GALLEGO" }
$Edades  = [ordered]@{ "infantil" = "VOZ INFANTIL"; "joven" = "VOZ JOVEN"; "mediana" = "VOZ ADULTA"; "mayor" = "VOZ PERSONA MAYOR" }

if ($ZipLocales -eq "") {
  foreach ($cmd in "ssh", "scp") {
    if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
      throw "No se encuentra '$cmd'. Instala 'Cliente OpenSSH' en Configuración > Aplicaciones > Características opcionales."
    }
  }
  if ($Usuario -eq "") { $Usuario = Read-Host "Usuario de CESGA (sin @ft3.cesga.es)" }
  $opts = @()
  if (-not $SinMacs) { $opts += @("-o", "MACs=hmac-sha2-512") }
  $destino = "$Usuario@$Servidor"
  Write-Host "Si estás fuera de la universidad, conecta antes la VPN CheckPoint de CESGA."
  Write-Host "[1/2] Localizando resultados en $Servidor (pedirá la contraseña)..."
  $rutaAbs = (& ssh @opts $destino "cd $RutaRemota/resultados_drama3 && pwd" | Select-Object -Last 1)
  if ($LASTEXITCODE -ne 0 -or -not $rutaAbs) { throw "No existe $RutaRemota/resultados_drama3 en CESGA (¿terminó el trabajo? ¿ruta correcta?)." }
  $rutaAbs = $rutaAbs.Trim()
  $ZipLocales = Join-Path $env:TEMP ("drama3_zip_" + (Get-Date -Format "yyyyMMdd-HHmmss"))
  New-Item -ItemType Directory -Path $ZipLocales | Out-Null
  Write-Host "[2/2] Descargando ZIP desde $rutaAbs (pedirá la contraseña otra vez)..."
  & scp @opts "${destino}:$rutaAbs/drama3_*.zip" $ZipLocales
  if ($LASTEXITCODE -ne 0) { throw "Falló la descarga con scp." }
}

$resumen = @()
foreach ($i in $Idiomas.Keys) {
  foreach ($e in $Edades.Keys) {
    $zip = Join-Path $ZipLocales "drama3_${i}_${e}.zip"
    if (-not (Test-Path -LiteralPath $zip)) { Write-Warning "Falta $zip"; continue }
    $dest = Join-Path $Audios (Join-Path $Idiomas[$i] (Join-Path $Modelo $Edades[$e]))
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
    Expand-Archive -LiteralPath $zip -DestinationPath $dest -Force
    $wavs = @(Get-ChildItem -LiteralPath $dest -Filter *.wav).Count
    $errores = 0
    $csv = Join-Path $dest "resultados.csv"
    if (Test-Path -LiteralPath $csv) {
      $errores = @(Import-Csv -LiteralPath $csv -Encoding UTF8 | Where-Object { $_.estado -ne "OK" }).Count
    }
    $resumen += [pscustomobject]@{ Carpeta = "$($Idiomas[$i])\$Modelo\$($Edades[$e])"; WAV = $wavs; Errores = $errores }
  }
}
$resumen | Format-Table -AutoSize
Write-Host "ZIP originales en: $ZipLocales"
Write-Host "Escucha los audios antes de usarlos: la edad indicada por texto en Drama 3 es experimental."
