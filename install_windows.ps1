# MikroTik Monitor - Windows Installation Script
# This script installs all requirements and sets up the MikroTik Monitor application on Windows

# Function definitions
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    else {
        $input | Write-Output
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

function Write-Info($message) {
    Write-ColorOutput Green "[INFO] $message"
}

function Write-Warning($message) {
    Write-ColorOutput Yellow "[WARN] $message"
}

function Write-Error($message) {
    Write-ColorOutput Red "[ERROR] $message"
}

function Print-Header($message) {
    Write-Output ""
    Write-Output "====== $message ======"
    Write-Output ""
}

function Generate-RandomString($length) {
    $chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789".ToCharArray()
    $password = ""
    for ($i = 0; $i -lt $length; $i++) {
        $password += $chars | Get-Random
    }
    return $password
}

function Install-PostgreSQL {
    Print-Header "Installing PostgreSQL"
    
    $pgVersion = "16"
    $pgInstallerUrl = "https://get.enterprisedb.com/postgresql/postgresql-$pgVersion.0-1-windows-x64.exe"
    $pgInstaller = "$env:TEMP\postgresql-$pgVersion.exe"
    $pgPassword = Generate-RandomString 12
    $pgInstallPath = "C:\Program Files\PostgreSQL\$pgVersion"
    
    # Check if PostgreSQL is already installed
    if (Test-Path $pgInstallPath) {
        Write-Warning "PostgreSQL seems to be already installed at $pgInstallPath"
        return $pgPassword
    }
    
    # Download PostgreSQL installer
    Write-Info "Downloading PostgreSQL installer..."
    try {
        Invoke-WebRequest -Uri $pgInstallerUrl -OutFile $pgInstaller
    }
    catch {
        Write-Error "Failed to download PostgreSQL installer: $_"
        Write-Info "Please download and install PostgreSQL manually from https://www.postgresql.org/download/windows/"
        exit 1
    }
    
    # Install PostgreSQL silently
    Write-Info "Installing PostgreSQL..."
    $installArgs = "--mode unattended --superpassword $pgPassword --servicename PostgreSQL --servicepassword $pgPassword --serverport 5432"
    Start-Process -FilePath $pgInstaller -ArgumentList $installArgs -Wait
    
    # Check if installation was successful
    if (Test-Path $pgInstallPath) {
        Write-Info "PostgreSQL installed successfully!"
    }
    else {
        Write-Error "PostgreSQL installation failed. Please install it manually."
        exit 1
    }
    
    # Add PostgreSQL bin directory to PATH
    $pgBinPath = "$pgInstallPath\bin"
    $currentPath = [Environment]::GetEnvironmentVariable("Path", "Machine")
    if (-not $currentPath.Contains($pgBinPath)) {
        [Environment]::SetEnvironmentVariable("Path", "$currentPath;$pgBinPath", "Machine")
        Write-Info "Added PostgreSQL bin directory to PATH"
    }
    
    return $pgPassword
}

function Install-Python {
    Print-Header "Installing Python"
    
    $pythonVersion = "3.11.6"
    $pythonInstallerUrl = "https://www.python.org/ftp/python/$pythonVersion/python-$pythonVersion-amd64.exe"
    $pythonInstaller = "$env:TEMP\python-$pythonVersion-amd64.exe"
    
    # Check if Python is already installed
    try {
        $pythonPath = (Get-Command python -ErrorAction SilentlyContinue).Source
        $installedVersion = & python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')"
        
        if ($installedVersion) {
            Write-Info "Python $installedVersion is already installed at $pythonPath"
            return
        }
    }
    catch {
        Write-Warning "Python is not installed or not in PATH"
    }
    
    # Download Python installer
    Write-Info "Downloading Python installer..."
    try {
        Invoke-WebRequest -Uri $pythonInstallerUrl -OutFile $pythonInstaller
    }
    catch {
        Write-Error "Failed to download Python installer: $_"
        Write-Info "Please download and install Python 3.11 manually from https://www.python.org/downloads/"
        exit 1
    }
    
    # Install Python silently
    Write-Info "Installing Python..."
    $installArgs = "/quiet InstallAllUsers=1 PrependPath=1 Include_test=0"
    Start-Process -FilePath $pythonInstaller -ArgumentList $installArgs -Wait
    
    # Refresh environment variables
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
    
    # Check if installation was successful
    try {
        $pythonVersion = & python --version
        Write-Info "Python installed successfully: $pythonVersion"
    }
    catch {
        Write-Error "Python installation failed. Please install it manually."
        exit 1
    }
}

function Create-PostgreSQLDatabase {
    param (
        [string]$PgPassword,
        [string]$DbName,
        [string]$DbUser,
        [string]$DbPassword
    )
    
    Print-Header "Setting up PostgreSQL Database"
    
    # Set environment variable for PostgreSQL password
    $env:PGPASSWORD = $PgPassword
    
    # Check if database user already exists
    $userExists = & psql -U postgres -h localhost -t -c "SELECT 1 FROM pg_roles WHERE rolname='$DbUser';" 2>$null
    
    if ($userExists) {
        Write-Warning "Database user $DbUser already exists"
    }
    else {
        Write-Info "Creating database user $DbUser..."
        & psql -U postgres -h localhost -c "CREATE USER $DbUser WITH PASSWORD '$DbPassword';" 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to create database user"
            exit 1
        }
    }
    
    # Check if database already exists
    $dbExists = & psql -U postgres -h localhost -t -c "SELECT 1 FROM pg_database WHERE datname='$DbName';" 2>$null
    
    if ($dbExists) {
        Write-Warning "Database $DbName already exists"
    }
    else {
        Write-Info "Creating database $DbName..."
        & psql -U postgres -h localhost -c "CREATE DATABASE $DbName OWNER $DbUser;" 2>$null
        & psql -U postgres -h localhost -c "GRANT ALL PRIVILEGES ON DATABASE $DbName TO $DbUser;" 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to create database"
            exit 1
        }
    }
    
    Write-Info "Database setup completed"
    
    # Clear PostgreSQL password environment variable
    $env:PGPASSWORD = ""
}

function Setup-Application {
    param (
        [string]$AppDir,
        [string]$DbUser,
        [string]$DbPassword,
        [string]$DbName
    )
    
    Print-Header "Setting up MikroTik Monitor application"
    
    # Create application directory if it doesn't exist
    if (-not (Test-Path $AppDir)) {
        Write-Info "Creating application directory..."
        New-Item -ItemType Directory -Path $AppDir -Force | Out-Null
    }
    
    # Download application source (replace with your actual URL)
    $repoZipUrl = "https://github.com/yourusername/mikrotik-monitor/archive/main.zip"
    $repoZip = "$env:TEMP\mikrotik-monitor.zip"
    $extractPath = "$env:TEMP\mikrotik-monitor-extract"
    
    Write-Info "Downloading application source..."
    try {
        # Comment out the next line if you're distributing the application files directly
        # Invoke-WebRequest -Uri $repoZipUrl -OutFile $repoZip
        
        # For now, we'll assume you're providing the files directly
        Write-Warning "This is a placeholder. In a real scenario, you would either:"
        Write-Warning "1. Download the application from a repository or"
        Write-Warning "2. Distribute the application files with this script"
    }
    catch {
        Write-Error "Failed to download application source: $_"
        exit 1
    }
    
    # Generate secrets
    $secretKey = Generate-RandomString 24
    $jwtSecretKey = Generate-RandomString 24
    $wtfCsrfSecretKey = Generate-RandomString 24
    
    # Create environment file
    $envFilePath = "$AppDir\.env"
    Write-Info "Creating environment configuration file..."
    $envContent = @"
# Flask Configuration
FLASK_APP=main.py
FLASK_ENV=production
FLASK_DEBUG=0

# Security Keys
SECRET_KEY=$secretKey
JWT_SECRET_KEY=$jwtSecretKey
WTF_CSRF_SECRET_KEY=$wtfCsrfSecretKey

# JWT Configuration
JWT_ACCESS_TOKEN_EXPIRES_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRES_DAYS=30
JWT_COOKIE_SECURE=1
JWT_COOKIE_CSRF_PROTECT=1

# Database Configuration
DATABASE_URL=postgresql://${DbUser}:${DbPassword}@localhost:5432/${DbName}

# MikroTik Connection Settings
MIKROTIK_CONNECTION_TIMEOUT=10
MIKROTIK_COMMAND_TIMEOUT=15
MIKROTIK_BACKUP_TIMEOUT=60
MIKROTIK_RESTORE_TIMEOUT=120
"@
    
    Set-Content -Path $envFilePath -Value $envContent
    
    # Set up Python virtual environment
    Write-Info "Creating Python virtual environment..."
    & python -m venv "$AppDir\venv"
    
    # Activate virtual environment and install dependencies
    Write-Info "Installing Python dependencies..."
    & "$AppDir\venv\Scripts\python.exe" -m pip install --upgrade pip
    & "$AppDir\venv\Scripts\pip.exe" install wheel
    
    # Create requirements.txt file
    $requirementsFilePath = "$AppDir\requirements.txt"
    Write-Info "Creating requirements.txt file..."
    $requirementsContent = @"
apscheduler>=3.11.0
cryptography==41.0.5
flask-socketio>=5.5.1
flask==3.0.0
flask-cors==4.0.0
flask-jwt-extended>=4.7.1
flask-login==0.6.3
flask-sqlalchemy==3.1.1
flask-wtf==1.2.1
gunicorn>=23.0.0
librouteros>=3.4.1
python-dotenv==1.0.0
sqlalchemy==2.0.23
werkzeug==3.0.1
wtforms>=3.2.1
netifaces>=0.11.0
psycopg2-binary>=2.9.10
requests>=2.32.3
pyjwt>=2.10.1
bcrypt>=4.3.0
sqlalchemy-utils>=0.41.2
flask-migrate>=4.1.0
"@
    
    Set-Content -Path $requirementsFilePath -Value $requirementsContent
    
    # Install dependencies
    & "$AppDir\venv\Scripts\pip.exe" install -r "$AppDir\requirements.txt"
    
    Write-Info "Application setup completed"
}

function Create-WindowsService {
    param (
        [string]$AppDir,
        [string]$ServiceName
    )
    
    Print-Header "Setting up Windows Service using NSSM"
    
    # Download NSSM (Non-Sucking Service Manager)
    $nssmUrl = "https://nssm.cc/release/nssm-2.24.zip"
    $nssmZip = "$env:TEMP\nssm.zip"
    $nssmDir = "$env:TEMP\nssm"
    
    Write-Info "Downloading NSSM..."
    try {
        Invoke-WebRequest -Uri $nssmUrl -OutFile $nssmZip
    }
    catch {
        Write-Error "Failed to download NSSM: $_"
        Write-Warning "You will need to set up the Windows service manually."
        return
    }
    
    # Extract NSSM
    Write-Info "Extracting NSSM..."
    if (Test-Path $nssmDir) {
        Remove-Item -Path $nssmDir -Recurse -Force
    }
    Expand-Archive -Path $nssmZip -DestinationPath $nssmDir
    
    # Find NSSM executable
    $nssmExe = Get-ChildItem -Path $nssmDir -Recurse -Filter "nssm.exe" | Where-Object { $_.FullName -like "*win64*" } | Select-Object -First 1 -ExpandProperty FullName
    
    if (-not $nssmExe) {
        Write-Error "Could not find NSSM executable"
        Write-Warning "You will need to set up the Windows service manually."
        return
    }
    
    # Check if service already exists
    $serviceExists = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    
    if ($serviceExists) {
        Write-Warning "Service $ServiceName already exists"
        return
    }
    
    # Create a startup script
    $startupScriptPath = "$AppDir\start_server.bat"
    $startupScriptContent = @"
@echo off
cd $AppDir
call venv\Scripts\activate.bat
python app.py
"@
    
    Set-Content -Path $startupScriptPath -Value $startupScriptContent
    
    # Create the service
    Write-Info "Creating Windows service..."
    & $nssmExe install $ServiceName $startupScriptPath
    & $nssmExe set $ServiceName DisplayName "MikroTik Monitor"
    & $nssmExe set $ServiceName Description "MikroTik Monitor Web Application"
    & $nssmExe set $ServiceName AppDirectory $AppDir
    & $nssmExe set $ServiceName AppStdout "$AppDir\logs\service_stdout.log"
    & $nssmExe set $ServiceName AppStderr "$AppDir\logs\service_stderr.log"
    & $nssmExe set $ServiceName Start SERVICE_AUTO_START
    
    # Create logs directory
    if (-not (Test-Path "$AppDir\logs")) {
        New-Item -ItemType Directory -Path "$AppDir\logs" -Force | Out-Null
    }
    
    # Start the service
    Write-Info "Starting service..."
    Start-Service -Name $ServiceName
    
    Write-Info "Windows service setup completed"
}

function Create-AdminUser {
    param (
        [string]$AppDir
    )
    
    Print-Header "Creating admin user"
    
    # Copy create_admin.py to the application directory if it doesn't exist
    $adminScriptPath = "$AppDir\create_admin.py"
    if (-not (Test-Path $adminScriptPath)) {
        $adminScriptContent = @"
from app import app, db, User
from datetime import datetime

def create_admin():
    """Create an administrator user if none exists"""
    with app.app_context():
        # Check if admin user already exists
        admin = User.query.filter_by(username='admin').first()
        if admin:
            print("Administrator user already exists")
            return
        
        # Create new admin user
        admin = User(
            username='admin',
            email='admin@example.com',
            role='admin',
            created_at=datetime.utcnow()
        )
        admin.set_password('admin123')  # Default password, should be changed immediately
        
        # Add to database
        db.session.add(admin)
        db.session.commit()
        print("Administrator user created successfully")

if __name__ == '__main__':
    create_admin()
"@
        Set-Content -Path $adminScriptPath -Value $adminScriptContent
    }
    
    # Run the admin creation script
    Write-Info "Creating initial admin user..."
    & "$AppDir\venv\Scripts\python.exe" $adminScriptPath
    
    Write-Info "Admin user created successfully"
}

function Show-CompletionMessage {
    param (
        [string]$DbName,
        [string]$DbUser,
        [string]$DbPassword,
        [string]$AppDir,
        [string]$ServiceName
    )
    
    Print-Header "Installation Completed!"
    
    Write-ColorOutput Green "MikroTik Monitor has been successfully installed!"
    Write-Output ""
    Write-Output "Database Information:"
    Write-Output "  Database: $DbName"
    Write-Output "  Username: $DbUser"
    Write-Output "  Password: $DbPassword"
    Write-Output ""
    Write-Output "Admin User Details:"
    Write-Output "  Username: admin"
    Write-Output "  Password: admin123 (PLEASE CHANGE IMMEDIATELY AFTER LOGIN)"
    Write-Output ""
    Write-Output "Application Details:"
    Write-Output "  Installation Directory: $AppDir"
    Write-Output "  Service Name: $ServiceName"
    Write-Output ""
    Write-Output "Access the application at: http://localhost:5000"
    Write-Output ""
    Write-ColorOutput Yellow "Please save these credentials in a secure location."
    Write-Output ""
    Write-Output "For any issues, please check the logs in:"
    Write-Output "  $AppDir\logs"
    Write-Output ""
}

# Main script execution starts here

# Verify PowerShell is running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Error "This script must be run as Administrator. Please restart PowerShell as Administrator."
    exit 1
}

# Variables
$appName = "MikroTik Monitor"
$appDir = "C:\MikroTikMonitor"
$serviceName = "MikroTikMonitor"
$dbName = "mikmon"
$dbUser = "mikmon"
$dbPassword = Generate-RandomString 12

Print-Header "Starting $appName installation on Windows"

# Execute installation steps
Install-Python
$pgPassword = Install-PostgreSQL
Create-PostgreSQLDatabase -PgPassword $pgPassword -DbName $dbName -DbUser $dbUser -DbPassword $dbPassword
Setup-Application -AppDir $appDir -DbUser $dbUser -DbPassword $dbPassword -DbName $dbName
Create-WindowsService -AppDir $appDir -ServiceName $serviceName
Create-AdminUser -AppDir $appDir

Show-CompletionMessage -DbName $dbName -DbUser $dbUser -DbPassword $dbPassword -AppDir $appDir -ServiceName $serviceName