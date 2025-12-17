#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
화승 R&A 실시간 분석 보고서 생성 메인 스크립트
"""

import sys
import time
import os
from datetime import datetime
from naver_finance import NaverFinanceAPI
from naver_news import NaverNewsAPI
from data_manager import DataManager
from report_generator import ReportGenerator

def update_report(company_name: str = "화승알앤에이", corp_code: str = None):
    """보고서 업데이트"""
    print("=" * 60)
    print(f"화승 R&A 분석 보고서 업데이트 시작")
    print(f"시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 데이터 매니저 초기화
    data_manager = DataManager()
    
    # 1. 네이버 Finance API로 기업 정보 수집 (DART API 대체)
    print("\n[1/5] 네이버 Finance API에서 기업 정보 수집 중...")
    try:
        # 종목코드 확인
        stock_code = None
        if corp_code and len(corp_code) == 6:
            # corp_code가 6자리면 종목코드로 간주
            stock_code = corp_code
        else:
            # 기존 파일에서 종목코드 확인
            try:
                import json
                if os.path.exists("hwasung_rna_data.json"):
                    with open("hwasung_rna_data.json", 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                        existing_stock_code = existing_data.get('company_info', {}).get('stock_code')
                        if existing_stock_code:
                            print(f"  - 기존 파일의 종목코드 사용: {existing_stock_code}")
                            stock_code = existing_stock_code
            except:
                pass
        
        # 기본값으로 알려진 종목코드 사용
        if not stock_code:
            if "화승" in company_name and "알앤에이" in company_name:
                stock_code = "378850"  # 화승알앤에이 종목코드
                print(f"  - 알려진 종목코드 사용: {stock_code}")
        
        naver_finance = NaverFinanceAPI()
        finance_data = naver_finance.get_company_all_data(company_name, stock_code)
        
        # 데이터 매니저에 저장 (DART 형식과 호환되도록)
        if finance_data:
            # company_info 업데이트
            if "company_info" in finance_data:
                data_manager.update_company_info(finance_data["company_info"])
            
            # financial_data 업데이트
            if "financial_data" in finance_data:
                data_manager.update_financial_data(finance_data["financial_data"])
            
            # stock_info 저장
            if "stock_info" in finance_data:
                current_data = data_manager.get_data()
                current_data["stock_info"] = finance_data["stock_info"]
                data_manager.save_data(current_data)
            
            print("[OK] 네이버 Finance 데이터 수집 완료")
            print(f"  - 기업명: {finance_data.get('company_info', {}).get('corp_name', 'N/A')}")
            print(f"  - 종목코드: {finance_data.get('company_info', {}).get('stock_code', 'N/A')}")
            print(f"  - 재무 데이터: {len(finance_data.get('financial_data', {}))}개 연도")
            if finance_data.get('stock_info'):
                stock_info = finance_data['stock_info']
                print(f"  - 현재가: {stock_info.get('current_price', 0):,}원")
                print(f"  - PER: {stock_info.get('per', 0):.2f}, PBR: {stock_info.get('pbr', 0):.2f}")
        else:
            print("[FAIL] 네이버 Finance 데이터 수집 실패")
    except Exception as e:
        print(f"[FAIL] 네이버 Finance API 오류: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # 2. 네이버 뉴스 API로 관련 기사 수집
    print("\n[2/5] 네이버 뉴스 API에서 관련 기사 수집 중...")
    try:
        naver = NaverNewsAPI()
        articles = naver.get_company_news(company_name)
        data_manager.update_news_articles(articles)
        print(f"[OK] 뉴스 기사 수집 완료: {len(articles)}개")
    except Exception as e:
        print(f"[FAIL] 네이버 뉴스 API 오류: {str(e)}")
    
    # 3. 네이버 검색 API로 금융 정보 수집
    print("\n[3/5] 네이버 검색 API에서 금융 정보 수집 중...")
    try:
        naver = NaverNewsAPI()
        # 기업 정보에서 종목코드 가져오기
        stock_code = data_manager.get_data().get("company_info", {}).get("stock_code", "")
        finance_info = naver.get_company_finance_info(company_name, stock_code)
        data_manager.update_finance_info(finance_info)
        finance_news_count = len(finance_info.get("finance_news", []))
        finance_analysis_count = len(finance_info.get("finance_analysis", []))
        print(f"[OK] 금융 정보 수집 완료: 뉴스 {finance_news_count}개, 분석 {finance_analysis_count}개")
    except Exception as e:
        print(f"[FAIL] 네이버 금융 정보 수집 오류: {str(e)}")
    
    # 4. HTML 보고서 생성
    print("\n[4/5] HTML 보고서 생성 중...")
    try:
        generator = ReportGenerator()
        output_path = generator.generate_report(data_manager.get_data(), "hwasung_rna_report.html")
        if output_path:
            print(f"[OK] HTML 보고서 생성 완료: {output_path}")
        else:
            print("[FAIL] HTML 보고서 생성 실패")
    except Exception as e:
        print(f"[FAIL] HTML 보고서 생성 오류: {str(e)}")
    
    # 5. 완료
    print("\n[5/5] 업데이트 완료!")
    print("=" * 60)
    print(f"최종 업데이트 시간: {data_manager.get_data().get('last_updated', 'N/A')}")
    print("=" * 60)

def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description="화승 R&A 실시간 분석 보고서 생성")
    parser.add_argument("--company", "-c", default="화승알앤에이", help="기업명 (기본값: 화승알앤에이)")
    parser.add_argument("--stock-code", "-s", default="378850", help="종목코드 (기본값: 378850)")
    parser.add_argument("--corp-code", "-cc", help="종목코드 (deprecated, --stock-code 사용 권장)")
    parser.add_argument("--watch", "-w", action="store_true", help="자동 업데이트 모드 (1시간마다)")
    parser.add_argument("--interval", "-i", type=int, default=3600, help="자동 업데이트 간격(초) (기본값: 3600)")
    
    args = parser.parse_args()
    
    if args.watch:
        print(f"자동 업데이트 모드 시작 (간격: {args.interval}초)")
        print("종료하려면 Ctrl+C를 누르세요.\n")
        
        try:
            while True:
                stock_code = args.stock_code or args.corp_code
                update_report(args.company, corp_code=stock_code)
                print(f"\n다음 업데이트까지 {args.interval}초 대기 중...\n")
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\n\n자동 업데이트 모드를 종료합니다.")
    else:
        stock_code = args.stock_code or args.corp_code
        update_report(args.company, corp_code=stock_code)

if __name__ == "__main__":
    main()

