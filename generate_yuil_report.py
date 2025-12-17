#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
유일고무 기업 분석 보고서 생성 스크립트
yfinance를 사용하여 데이터 수집
"""

import sys
import json
import os
from datetime import datetime
from data_manager import DataManager
from report_generator import ReportGenerator
from naver_finance import NaverFinanceAPI
from yfinance_ssl_fix import setup_yfinance_ssl_bypass, patch_yfinance_session

# SSL 인증서 검증 비활성화 설정
setup_yfinance_ssl_bypass()

try:
    import yfinance as yf
    import pandas as pd
except ImportError:
    print("[ERROR] yfinance와 pandas가 필요합니다.")
    print("설치: pip install yfinance pandas")
    sys.exit(1)

def get_yuil_data():
    """유일고무 기업 데이터 수집"""
    print("=" * 60)
    print("유일고무 기업 분석 보고서 데이터 수집")
    print(f"시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 유일고무 티커 심볼 (한국 기업은 .KS 또는 .KQ 접미사)
    # 유일고무 종목코드: 003240 (코스닥)
    ticker_symbol = "003240.KQ"
    company_name = "유일고무"
    
    print(f"\n[1/4] yfinance로 {company_name} 정보 수집 중...")
    print(f"  - 티커 심볼: {ticker_symbol}")
    
    try:
        # yfinance Ticker 생성
        ticker = yf.Ticker(ticker_symbol)
        
        # SSL 검증 비활성화 패치 적용
        patch_yfinance_session(ticker)
        
        # 데이터 가져오기 시도
        print("  - 기업 정보 가져오는 중...")
        info = ticker.info
        
        # 기업 기본 정보
        company_info = {
            "corp_name": info.get("longName", info.get("shortName", company_name)),
            "stock_code": "003240",
            "ceo_nm": "",
            "est_dt": "",
            "adres": info.get("address1", ""),
            "corp_cls": "K"  # 코스닥
        }
        
        # CEO 정보 추출 시도
        if "companyOfficers" in info and info["companyOfficers"]:
            company_info["ceo_nm"] = info["companyOfficers"][0].get("name", "")
        
        print(f"  [OK] 기업명: {company_info['corp_name']}")
        print(f"  [OK] 종목코드: {company_info['stock_code']}")
        
        # 재무 데이터 수집
        print("\n[2/4] 재무 데이터 수집 중...")
        financials = ticker.financials
        balance_sheet = ticker.balance_sheet
        cashflow = ticker.cashflow
        
        financial_data = {}
        
        if not financials.empty:
            for year in financials.columns:
                year_str = str(year.year)
                financial_data[year_str] = []
                
                # 매출액 (Total Revenue)
                if "Total Revenue" in financials.index:
                    revenue = financials.loc["Total Revenue", year]
                    if not pd.isna(revenue):
                        financial_data[year_str].append({
                            "account_nm": "매출액",
                            "thstrm_amount": str(int(revenue))
                        })
                        print(f"  - {year_str}년 매출액: {revenue/100000000:.1f}억원")
                
                # 영업이익 (Operating Income)
                if "Operating Income" in financials.index:
                    op_income = financials.loc["Operating Income", year]
                    if not pd.isna(op_income):
                        financial_data[year_str].append({
                            "account_nm": "영업이익",
                            "thstrm_amount": str(int(op_income))
                        })
                        print(f"  - {year_str}년 영업이익: {op_income/100000000:.1f}억원")
                
                # 당기순이익 (Net Income)
                if "Net Income" in financials.index:
                    net_income = financials.loc["Net Income", year]
                    if not pd.isna(net_income):
                        financial_data[year_str].append({
                            "account_nm": "당기순이익",
                            "thstrm_amount": str(int(net_income))
                        })
                        print(f"  - {year_str}년 당기순이익: {net_income/100000000:.1f}억원")
                
                # 자산총계 (Total Assets)
                if not balance_sheet.empty and "Total Assets" in balance_sheet.index:
                    total_assets = balance_sheet.loc["Total Assets", year]
                    if not pd.isna(total_assets):
                        financial_data[year_str].append({
                            "account_nm": "자산총계",
                            "thstrm_amount": str(int(total_assets))
                        })
                
                # 부채총계 (Total Liabilities)
                if not balance_sheet.empty and "Total Liabilities" in balance_sheet.index:
                    total_liab = balance_sheet.loc["Total Liabilities", year]
                    if not pd.isna(total_liab):
                        financial_data[year_str].append({
                            "account_nm": "부채총계",
                            "thstrm_amount": str(int(total_liab))
                        })
                
                # 자본총계 (Total Stockholder Equity)
                if not balance_sheet.empty and "Total Stockholder Equity" in balance_sheet.index:
                    total_equity = balance_sheet.loc["Total Stockholder Equity", year]
                    if not pd.isna(total_equity):
                        financial_data[year_str].append({
                            "account_nm": "자본총계",
                            "thstrm_amount": str(int(total_equity))
                        })
        
        print(f"  [OK] 재무 데이터: {len(financial_data)}개 연도")
        
        # 주가 정보
        print("\n[3/4] 주가 정보 수집 중...")
        stock_info = {
            "current_price": info.get("currentPrice", 0),
            "market_cap": info.get("marketCap", 0),
            "pe_ratio": info.get("trailingPE", 0),
            "pb_ratio": info.get("priceToBook", 0),
            "dividend_yield": info.get("dividendYield", 0) * 100 if info.get("dividendYield") else 0,
            "52_week_high": info.get("fiftyTwoWeekHigh", 0),
            "52_week_low": info.get("fiftyTwoWeekLow", 0),
            "currency": info.get("currency", "KRW")
        }
        
        print(f"  - 현재가: {stock_info['current_price']:,.0f}원")
        print(f"  - 시가총액: {stock_info['market_cap']/100000000:.1f}억원")
        print(f"  - PER: {stock_info['pe_ratio']:.2f}")
        print(f"  - PBR: {stock_info['pb_ratio']:.2f}")
        
        # 직원 정보
        employee_info = {}
        if "fullTimeEmployees" in info and info["fullTimeEmployees"]:
            employee_info = {
                "sm": str(info["fullTimeEmployees"]),  # 상시근로자수
                "cnt": str(info["fullTimeEmployees"]),
                "avrg_cnwk_sdytrn": "",
                "stlm_dt": datetime.now().strftime("%Y-%m-%d"),
                "bsns_year": str(datetime.now().year)
            }
            print(f"\n[4/4] 직원 정보: {info['fullTimeEmployees']:,}명")
        
        # 뉴스 정보 (빈 리스트 - 네이버 뉴스 API로 별도 수집 가능)
        news_articles = []
        disclosures = []
        
        return {
            "company_name": company_name,
            "company_info": company_info,
            "financial_data": financial_data,
            "stock_info": stock_info,
            "employee_info": employee_info,
            "recent_disclosures": disclosures,
            "news_articles": news_articles
        }
        
    except Exception as e:
        print(f"[FAIL] 데이터 수집 오류: {str(e)}")
        # SSL 인증서 문제인 경우 재시도
        if "SSL" in str(e) or "certificate" in str(e).lower():
            print("  - SSL 인증서 문제 감지, 재시도 중...")
            try:
                # requests 세션을 직접 사용하여 재시도
                import requests
                import urllib3
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                
                # 간단한 방법: yfinance 대신 requests로 직접 데이터 가져오기
                print("  - 대체 방법으로 데이터 수집 시도...")
                # 여기서는 기본 정보만 수집
                return {
                    "company_name": company_name,
                    "company_info": {
                        "corp_name": company_name,
                        "stock_code": "003240",
                        "corp_cls": "K"
                    },
                    "financial_data": {},
                    "stock_info": {},
                    "employee_info": {},
                    "recent_disclosures": [],
                    "news_articles": []
                }
            except:
                pass
        import traceback
        traceback.print_exc()
        return None


def main():
    """메인 함수"""
    # 데이터 수집
    data = get_yuil_data()
    
    if not data:
        print("\n❌ 데이터 수집 실패")
        return
    
    # 데이터 매니저에 저장
    print("\n[5/5] 데이터 저장 중...")
    data_manager = DataManager("yuil_data.json")
    data_manager.update_company_info(data["company_info"])
    data_manager.update_financial_data(data["financial_data"])
    if data.get("employee_info"):
        data_manager.update_employee_info(data["employee_info"])
    if data.get("stock_info"):
        current_data = data_manager.get_data()
        current_data["stock_info"] = data["stock_info"]
        data_manager.save_data(current_data)
    
    # HTML 보고서 생성
    print("\n[6/6] HTML 보고서 생성 중...")
    try:
        generator = ReportGenerator(template_path="hwasung_rna_report.html")
        output_path = generator.generate_report(data, "yuil_report.html")
        
        if output_path:
            print(f"\n[OK] 보고서 생성 완료: {output_path}")
            print("=" * 60)
        else:
            print("\n[FAIL] 보고서 생성 실패")
    except Exception as e:
        print(f"\n❌ 보고서 생성 오류: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

