#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DART API 직원 정보 테스트 스크립트
"""

from dart_api import DartAPI
from datetime import datetime

def test_employee_info():
    """직원 정보 조회 테스트"""
    print("=" * 60)
    print("DART API 직원 정보 조회 테스트")
    print("=" * 60)
    
    dart = DartAPI()
    corp_code = "01532603"  # 화승알앤에이 고유번호
    
    current_year = datetime.now().year
    
    # 최근 3년 동안 시도
    for year in [current_year, current_year - 1, current_year - 2]:
        print(f"\n[{year}년 직원 정보 조회 시도]")
        try:
            employee_info = dart.get_employee_info(corp_code, str(year))
            if employee_info:
                print(f"[OK] {year}년 직원 정보 수집 성공!")
                print(f"  데이터: {employee_info}")
                return employee_info
            else:
                print(f"[INFO] {year}년 직원 정보 없음")
        except Exception as e:
            print(f"[FAIL] {year}년 조회 오류: {str(e)}")
    
    print("\n[결과] 사용 가능한 직원 정보가 없습니다.")
    print("\n[참고]")
    print("1. DART API의 직원 정보는 기업이 사업보고서에 공시한 경우에만 제공됩니다.")
    print("2. 일부 기업은 직원 정보를 공시하지 않을 수 있습니다.")
    print("3. 네트워크 문제로 인해 조회가 실패할 수 있습니다.")
    print("4. DART 홈페이지에서 직접 확인하시기 바랍니다: https://dart.fss.or.kr")
    
    return None

if __name__ == "__main__":
    test_employee_info()










