# DuckDNS IP 자동 업데이트 스크립트
# 
# 사용 방법:
# 1. DuckDNS 사이트에서 토큰 확인: https://www.duckdns.org/
# 2. 아래 $token과 $domain 변수 수정
# 3. 이 스크립트를 실행하거나 작업 스케줄러에 등록

# ============================================
# 설정 (수정 필요!)
# ============================================
$token = "YOUR_DUCKDNS_TOKEN"  # DuckDNS 사이트에서 확인
$domain = "my-server"  # 서브도메인 이름 (예: my-server -> my-server.duckdns.org)

# ============================================
# IP 업데이트 실행
# ============================================
try {
    $url = "https://www.duckdns.org/update?domains=$domain&token=$token&ip="
    $response = Invoke-WebRequest -Uri $url -UseBasicParsing
    
    if ($response.Content -eq "OK") {
        $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
        Write-Host "[$timestamp] DuckDNS IP 업데이트 성공: $domain.duckdns.org" -ForegroundColor Green
        
        # 현재 공인 IP 확인
        try {
            $currentIp = (Invoke-WebRequest -Uri "https://api.ipify.org" -UseBasicParsing).Content
            Write-Host "[$timestamp] 현재 공인 IP: $currentIp" -ForegroundColor Cyan
        } catch {
            Write-Host "[$timestamp] 공인 IP 확인 실패" -ForegroundColor Yellow
        }
    } else {
        $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
        Write-Host "[$timestamp] DuckDNS 업데이트 실패: $($response.Content)" -ForegroundColor Red
    }
} catch {
    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    Write-Host "[$timestamp] DuckDNS 업데이트 오류: $_" -ForegroundColor Red
}

