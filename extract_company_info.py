#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
공시 정보에서 기업 정보 추출 및 JSON 파일 업데이트
"""

import json

# JSON 파일 로드
with open('hwasung_rna_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("=" * 60)
print("공시 정보에서 기업 정보 추출")
print("=" * 60)

# 공시 정보가 있는지 확인
disclosures = data.get('recent_disclosures', [])
if disclosures:
    # 첫 번째 공시에서 기업 정보 추출
    first_disclosure = disclosures[0]
    
    # 기업 정보가 비어있으면 공시 정보로부터 채우기
    if not data.get('company_info') or data.get('company_info') == {}:
        data['company_info'] = {
            "corp_code": first_disclosure.get("corp_code", ""),
            "corp_name": first_disclosure.get("corp_name", ""),
            "stock_code": first_disclosure.get("stock_code", ""),
            "corp_cls": first_disclosure.get("corp_cls", ""),
            "flr_nm": first_disclosure.get("flr_nm", "")
        }
        print(f"[OK] 기업 정보 추출 완료")
        print(f"  - 기업명: {data['company_info'].get('corp_name')}")
        print(f"  - 종목코드: {data['company_info'].get('stock_code')}")
        print(f"  - 고유번호: {data['company_info'].get('corp_code')}")
    else:
        print("[SKIP] 기업 정보가 이미 있습니다.")
    
    print(f"\n[공시 정보]")
    print(f"  - 공시 개수: {len(disclosures)}개")
    print(f"  - 최신 공시: {disclosures[0].get('report_nm', 'N/A')} ({disclosures[0].get('rcept_dt', 'N/A')})")
else:
    print("[FAIL] 공시 정보가 없습니다.")

# 업데이트된 데이터 저장
with open('hwasung_rna_data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("\n[OK] JSON 파일 업데이트 완료")

