# Cloudflare Tunnel 자동 설정 스크립트
# 
# 이 스크립트는 Cloudflare Tunnel 설정을 도와줍니다.
# 단계별로 실행하며, 각 단계에서 필요한 정보를 입력받습니다.

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Cloudflare Tunnel 설정 도우미" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# cloudflared 설치 확인
$cloudflaredPath = Get-Command cloudflared -ErrorAction SilentlyContinue
if (-not $cloudflaredPath) {
    Write-Host "[경고] cloudflared가 설치되어 있지 않습니다." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "설치 방법:" -ForegroundColor Cyan
    Write-Host "1. https://github.com/cloudflare/cloudflared/releases 접속" -ForegroundColor White
    Write-Host "2. cloudflared-windows-amd64.exe 다운로드" -ForegroundColor White
    Write-Host "3. cloudflared.exe로 이름 변경 후 PATH에 추가" -ForegroundColor White
    Write-Host ""
    Write-Host "또는 Chocolatey 사용:" -ForegroundColor Cyan
    Write-Host "  choco install cloudflared" -ForegroundColor White
    Write-Host ""
    
    $continue = Read-Host "계속하시겠습니까? (Y/N)"
    if ($continue -ne "Y" -and $continue -ne "y") {
        exit
    }
}

Write-Host "[1단계] Cloudflare 로그인" -ForegroundColor Green
Write-Host "브라우저가 열리면 로그인하고 권한을 승인하세요." -ForegroundColor Yellow
Write-Host ""
Read-Host "준비되면 Enter를 누르세요"
cloudflared tunnel login
Write-Host ""

Write-Host "[2단계] 터널 생성" -ForegroundColor Green
$tunnelName = Read-Host "터널 이름을 입력하세요 (예: my-server)"
cloudflared tunnel create $tunnelName
Write-Host ""

Write-Host "[3단계] 도메인 라우팅" -ForegroundColor Green
Write-Host "터널을 도메인에 연결합니다." -ForegroundColor Yellow
$subdomain = Read-Host "서브도메인을 입력하세요 (예: api.my-server.tk)"

# 전체 도메인에서 서브도메인과 루트 도메인 추출
if ($subdomain -match "^(.+)\.(.+\..+)$") {
    $subdomainPart = $Matches[1]
    $rootDomain = $Matches[2]
    Write-Host "서브도메인: $subdomainPart" -ForegroundColor Cyan
    Write-Host "루트 도메인: $rootDomain" -ForegroundColor Cyan
} else {
    Write-Host "[오류] 도메인 형식이 올바르지 않습니다. (예: api.my-server.tk)" -ForegroundColor Red
    exit
}

cloudflared tunnel route dns $tunnelName $subdomain
Write-Host ""

Write-Host "[4단계] 설정 파일 생성" -ForegroundColor Green
$configDir = "$env:USERPROFILE\.cloudflared"
if (-not (Test-Path $configDir)) {
    New-Item -ItemType Directory -Path $configDir | Out-Null
}

$configFile = "$configDir\config.yml"
Write-Host "설정 파일 경로: $configFile" -ForegroundColor Cyan

# 터널 UUID 찾기 (터널 목록에서)
Write-Host "터널 목록을 확인합니다..." -ForegroundColor Yellow
$tunnelList = cloudflared tunnel list 2>&1 | Out-String
Write-Host $tunnelList

$uuid = Read-Host "터널 UUID를 입력하세요 (위 목록에서 확인)"

# 설정 파일 생성
$configContent = @"
tunnel: $uuid
credentials-file: `$HOME\.cloudflared\$uuid.json

ingress:
  - hostname: $subdomain
    service: http://localhost:8000
  - service: http_status:404
"@

Set-Content -Path $configFile -Value $configContent -Encoding UTF8
Write-Host "설정 파일이 생성되었습니다: $configFile" -ForegroundColor Green
Write-Host ""

Write-Host "[5단계] 설정 확인" -ForegroundColor Green
Write-Host "생성된 설정 파일 내용:" -ForegroundColor Cyan
Get-Content $configFile
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  설정 완료!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "다음 단계:" -ForegroundColor Yellow
Write-Host "1. DNS 설정이 완료될 때까지 최대 24시간 대기 (보통 몇 분 내)" -ForegroundColor White
Write-Host "2. 서버 실행: python unified_server.py" -ForegroundColor White
Write-Host "3. 터널 실행: cloudflared tunnel run $tunnelName" -ForegroundColor White
Write-Host "4. 접속: https://$subdomain" -ForegroundColor White
Write-Host ""
Write-Host "자동 실행 스크립트를 생성할까요? (Y/N)" -ForegroundColor Cyan
$createScript = Read-Host

if ($createScript -eq "Y" -or $createScript -eq "y") {
    $scriptContent = @"
@echo off
chcp 65001 > nul
echo ========================================
echo  서버 + Cloudflare Tunnel (고정 도메인)
echo ========================================
echo.

REM 서버 시작
echo [1/2] Python 서버 시작...
start "서버" cmd /k "python unified_server.py"
timeout /t 3 /nobreak > nul

REM Cloudflare Tunnel 시작
echo [2/2] Cloudflare Tunnel 시작...
echo 고정 도메인: https://$subdomain
echo.

cloudflared tunnel run $tunnelName
"@
    
    $scriptPath = "start_with_cloudflare_fixed.bat"
    Set-Content -Path $scriptPath -Value $scriptContent -Encoding UTF8
    Write-Host "자동 실행 스크립트가 생성되었습니다: $scriptPath" -ForegroundColor Green
}

