# Instalador automático de MosaicoPDF 2.0 para Windows (sin conocimientos técnicos)
$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Instalador MosaicoPDF 2.0 (Windows)" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $ScriptDir "..")

function Find-Python310 {
    $candidates = @(
        @{ Cmd = "py"; Args = @("-3") },
        @{ Cmd = "python"; Args = @() },
        @{ Cmd = "python3"; Args = @() }
    )
    foreach ($cand in $candidates) {
        $found = Get-Command $cand.Cmd -ErrorAction SilentlyContinue
        if ($null -ne $found) {
            try {
                & $cand.Cmd @($cand.Args + @("-c", "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)")) 2>$null
                if ($LASTEXITCODE -eq 0) {
                    return $cand
                }
            } catch {}
        }
    }
    return $null
}

$py = Find-Python310
if ($null -eq $py) {
    Write-Host "[INFO] Python 3.10+ no detectado. Intentando instalar Python con winget..." -ForegroundColor Yellow
    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if ($null -ne $winget) {
        winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
        $py = Find-Python310
    }
}

if ($null -eq $py) {
    Write-Host "[ERR] No se pudo localizar Python 3.10 o superior." -ForegroundColor Red
    Write-Host "      Descargalo desde https://www.python.org/downloads/windows/ (marca 'Add python.exe to PATH') y vuelve a ejecutar este instalador."
    exit 1
}

$AppDir = Join-Path $env:LOCALAPPDATA "MosaicoPDF"
$VenvDir = Join-Path $AppDir "venv"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
$VenvMosaic = Join-Path $VenvDir "Scripts\mosaicopdf.exe"

Write-Host "[INFO] Creando entorno interno en: $VenvDir"
New-Item -ItemType Directory -Force -Path $AppDir | Out-Null
& $py.Cmd @($py.Args + @("-m", "venv", $VenvDir))

Write-Host "[INFO] Instalando MosaicoPDF 2.0 y PyMuPDF..."
& $VenvPython -m pip install --disable-pip-version-check --upgrade pip | Out-Null
& $VenvPython -m pip install --disable-pip-version-check --upgrade "$RepoRoot"

# Agregar Scripts del entorno gestionado al PATH del usuario
$ScriptsDir = Join-Path $VenvDir "Scripts"
$UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($UserPath -notlike "*$ScriptsDir*") {
    $NewPath = if ([string]::IsNullOrWhiteSpace($UserPath)) { $ScriptsDir } else { "$UserPath;$ScriptsDir" }
    [Environment]::SetEnvironmentVariable("Path", $NewPath, "User")
    Write-Host "[ OK ] Agregado al PATH del usuario: $ScriptsDir" -ForegroundColor Green
}

# Instalar extension de Inkscape
& $VenvMosaic integrar --inkscape

# Registrar menu contextual 'Abrir con MosaicoPDF 2.0' para archivos .pdf (sin requerir admin)
$RegBase = "HKCU:\Software\Classes\SystemFileAssociations\.pdf\shell\MosaicoPDF"
New-Item -Path "$RegBase\command" -Force | Out-Null
Set-ItemProperty -Path $RegBase -Name "(Default)" -Value "Dividir/Escalar con MosaicoPDF 2.0"
Set-ItemProperty -Path "$RegBase\command" -Name "(Default)" -Value "`"$VenvMosaic`" `"%1`" --interactivo"
Write-Host "[ OK ] Menu clic derecho registrado para archivos .pdf en el Explorador de Windows." -ForegroundColor Green

# Crear acceso directo en el Escritorio
$Desktop = [Environment]::GetFolderPath("Desktop")
if (Test-Path $Desktop) {
    $WshShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut((Join-Path $Desktop "MosaicoPDF 2.0.lnk"))
    $Shortcut.TargetPath = $VenvMosaic
    $Shortcut.Arguments = "--interactivo"
    $Shortcut.WorkingDirectory = $Desktop
    $Shortcut.Description = "MosaicoPDF 2.0 - Asistente vectorial de mosaicos PDF"
    $Shortcut.Save()
    Write-Host "[ OK ] Acceso directo creado en el Escritorio." -ForegroundColor Green
}

Write-Host ""
Write-Host "[ OK ] MosaicoPDF 2.0 instalado correctamente." -ForegroundColor Green
Write-Host "       Puedes abrirlo desde el Escritorio, haciendo clic derecho en cualquier PDF, o desde Inkscape."
