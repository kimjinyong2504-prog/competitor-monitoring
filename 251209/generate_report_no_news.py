#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Colab에서 다운로드한 JSON 파일로 HTML 보고서 생성 (뉴스 제외 버전)
"""

import json
import sys
from report_generator_no_news import ReportGeneratorNoNews

def main():
    json_file = "hwasung_rna_data.json"
    
    print("=" * 60)
    print("HTML 보고서 생성 (뉴스 제외)")
    print("=" * 60)
    
    # JSON 파일 로드
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"[OK] JSON 파일 로드 완료: {json_file}")
    except FileNotFoundError:
        print(f"[FAIL] 오류: {json_file} 파일을 찾을 수 없습니다.")
        return
    except Exception as e:
        print(f"[FAIL] JSON 파일 로드 오류: {str(e)}")
        return
    
    # 데이터 요약 출력
    print(f"\n[데이터 요약]")
    print(f"기업명: {data.get('company_name', 'N/A')}")
    print(f"재무 데이터: {len(data.get('financial_data', {}))}개 연도")
    print(f"공시 정보: {len(data.get('recent_disclosures', []))}개")
    
    # HTML 보고서 생성
    print(f"\n[HTML 보고서 생성 중...]")
    try:
        generator = ReportGeneratorNoNews()
        output_path = generator.generate_report(data, "hwasung_rna_report_no_news.html")
        
        if output_path:
            print(f"[OK] HTML 보고서 생성 완료: {output_path}")
            print(f"\n브라우저에서 열어서 확인하세요!")
        else:
            print("[FAIL] HTML 보고서 생성 실패")
    except Exception as e:
        print(f"[FAIL] HTML 보고서 생성 오류: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
