#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DART에서 화승R&A의 고유번호를 찾는 유틸리티 스크립트
"""

import requests
import json
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DART_API_KEY = "5523e4e6b24ce622cff0e56500dcccad55bcb26f"
DART_BASE_URL = "https://opendart.fss.or.kr/api"

def search_companies(keyword: str):
    """기업명으로 검색 시도"""
    # DART API는 직접적인 기업명 검색을 지원하지 않을 수 있음
    # 대신 공시 검색을 통해 기업 찾기 시도
    
    # 방법 1: 공시 검색
    url = f"{DART_BASE_URL}/list.json"
    params = {
        "crtfc_key": DART_API_KEY,
        "corp_name": keyword,
        "bgn_de": "20200101",
        "end_de": "20241231",
        "page_no": "1",
        "page_count": "10"
    }
    
    try:
        response = requests.get(url, params=params, timeout=30, verify=False)
        response.raise_for_status()
        data = response.json()
        print(f"공시 검색 결과: {json.dumps(data, ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"공시 검색 오류: {str(e)}")
    
    # 방법 2: 상장사 목록에서 찾기 (상장사인 경우)
    # 이 방법은 별도의 엔드포인트가 필요할 수 있음

if __name__ == "__main__":
    print("화승R&A 고유번호 찾기")
    print("=" * 60)
    search_companies("화승R&A")
    search_companies("화승 R&A")
    search_companies("화승")

