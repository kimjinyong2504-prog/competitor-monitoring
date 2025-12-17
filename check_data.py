#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""JSON 데이터 확인 스크립트"""

import json

with open('hwasung_rna_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("=" * 60)
print("데이터 확인 결과")
print("=" * 60)
print(f"\n기업명: {data.get('company_name', 'N/A')}")
print(f"\n[DART 데이터]")
print(f"  기업 정보: {'있음' if data.get('company_info') and data.get('company_info') != {} else '없음 (비어있음)'}")
print(f"  재무 데이터: {len(data.get('financial_data', {}))}개 연도")
print(f"  직원 정보: {'있음' if data.get('employee_info') and data.get('employee_info') != {} else '없음 (비어있음)'}")
print(f"  공시 정보: {len(data.get('recent_disclosures', []))}개")
print(f"\n[네이버 뉴스]")
print(f"  뉴스 기사: {len(data.get('news_articles', []))}개")
print(f"\n최종 업데이트: {data.get('last_updated', 'N/A')}")

if not data.get('company_info') or data.get('company_info') == {}:
    print("\n" + "=" * 60)
    print("경고: DART API 데이터가 없습니다!")
    print("=" * 60)
    print("\nDART 데이터를 수집하려면:")
    print("1. Colab에서 다시 실행 (네트워크가 정상이면 자동 수집)")
    print("2. 또는 로컬에서 main.py 실행 (네트워크 문제 해결 후)")

