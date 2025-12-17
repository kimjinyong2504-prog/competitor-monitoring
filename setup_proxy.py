#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
프록시 설정 도우미 스크립트
회사 네트워크에서 DART API 접근이 차단될 때 사용
"""

import os

def setup_proxy():
    """프록시 설정 안내"""
    print("=" * 60)
    print("DART API 프록시 설정")
    print("=" * 60)
    print("\n회사 네트워크에서 DART API 접근이 차단되는 경우 프록시를 설정할 수 있습니다.\n")
    
    print("방법 1: 환경변수로 프록시 설정")
    print("-" * 60)
    print("Windows PowerShell:")
    print('  $env:HTTP_PROXY="http://프록시주소:포트"')
    print('  $env:HTTPS_PROXY="http://프록시주소:포트"')
    print('  $env:USE_PROXY="true"')
    print("\nWindows CMD:")
    print('  set HTTP_PROXY=http://프록시주소:포트')
    print('  set HTTPS_PROXY=http://프록시주소:포트')
    print('  set USE_PROXY=true')
    print("\nLinux/Mac:")
    print('  export HTTP_PROXY=http://프록시주소:포트')
    print('  export HTTPS_PROXY=http://프록시주소:포트')
    print('  export USE_PROXY=true')
    
    print("\n방법 2: 프록시 정보 직접 입력")
    print("-" * 60)
    proxy_url = input("프록시 주소를 입력하세요 (예: http://proxy.company.com:8080, 없으면 Enter): ").strip()
    
    if proxy_url:
        print(f"\n프록시가 설정되었습니다: {proxy_url}")
        print("\n다음 명령어로 환경변수를 설정하세요:")
        print(f'  $env:HTTP_PROXY="{proxy_url}"')
        print(f'  $env:HTTPS_PROXY="{proxy_url}"')
        print(f'  $env:USE_PROXY="true"')
        print("\n그 다음 main.py를 실행하세요:")
        print("  python main.py")
    else:
        print("\n프록시 없이 실행합니다.")
        print("네트워크 문제가 계속되면 IT 부서에 문의하세요.")
    
    print("\n" + "=" * 60)
    print("추가 팁:")
    print("- 회사 프록시 주소는 IT 부서에 문의하세요")
    print("- 프록시 인증이 필요한 경우: http://사용자명:비밀번호@프록시주소:포트")
    print("- 방화벽 예외 목록에 opendart.fss.or.kr 추가 요청")
    print("=" * 60)

if __name__ == "__main__":
    setup_proxy()

