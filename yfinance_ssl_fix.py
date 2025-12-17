#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
yfinance SSL 인증서 문제 해결을 위한 유틸리티
"""

import os
import ssl

def setup_yfinance_ssl_bypass():
    """yfinance SSL 검증 우회 설정"""
    
    # 1. Python SSL 컨텍스트 설정
    ssl._create_default_https_context = ssl._create_unverified_context
    
    # 2. 환경변수 설정
    os.environ['CURL_CA_BUNDLE'] = ''
    os.environ['REQUESTS_CA_BUNDLE'] = ''
    os.environ['CURL_SSL_NO_VERIFY'] = '1'
    os.environ['PYTHONHTTPSVERIFY'] = '0'
    
    # 3. curl_cffi SSL 검증 비활성화
    try:
        from curl_cffi import requests as curl_requests
        # curl_cffi의 기본 옵션 설정
        if hasattr(curl_requests, 'DEFAULT_OPTIONS'):
            curl_requests.DEFAULT_OPTIONS['verify'] = False
    except ImportError:
        pass
    
    # 4. urllib3 경고 비활성화
    try:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    except:
        pass

def patch_yfinance_session(ticker):
    """yfinance Ticker 객체의 세션에 SSL 검증 비활성화 적용"""
    try:
        # yfinance의 내부 데이터 객체 접근
        if hasattr(ticker, '_data'):
            data_obj = ticker._data
            if hasattr(data_obj, '_session'):
                session = data_obj._session
                
                # requests 세션인 경우
                if hasattr(session, 'verify'):
                    session.verify = False
                
                # curl_cffi 세션인 경우
                if hasattr(session, 'setopt'):
                    try:
                        session.setopt('SSL_VERIFYPEER', False)
                        session.setopt('SSL_VERIFYHOST', False)
                    except:
                        pass
                
                # curl_cffi의 requests 모듈인 경우
                if hasattr(session, 'get'):
                    # 세션의 verify 속성 설정 시도
                    try:
                        session.verify = False
                    except:
                        pass
    except Exception as e:
        print(f"[INFO] 세션 패치 중 오류 (무시 가능): {e}")





