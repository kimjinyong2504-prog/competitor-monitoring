#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
해외 기업 분석을 위한 API 통합 모듈
yfinance, Alpha Vantage 등을 활용
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import urllib3

# SSL 경고 비활성화
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    print("⚠️ yfinance가 설치되지 않았습니다. 'pip install yfinance'로 설치하세요.")

try:
    from alpha_vantage.timeseries import TimeSeries
    from alpha_vantage.fundamentaldata import FundamentalData
    ALPHA_VANTAGE_AVAILABLE = True
except ImportError:
    ALPHA_VANTAGE_AVAILABLE = False
    print("⚠️ alpha_vantage가 설치되지 않았습니다. 'pip install alpha-vantage'로 설치하세요.")


class InternationalFinanceAPI:
    """해외 기업 정보 수집을 위한 통합 API 클래스"""
    
    def __init__(self, alpha_vantage_key: str = None, newsapi_key: str = None):
        """
        Args:
            alpha_vantage_key: Alpha Vantage API 키 (선택)
            newsapi_key: NewsAPI 키 (선택)
        """
        self.alpha_vantage_key = alpha_vantage_key
        self.newsapi_key = newsapi_key
        
        if ALPHA_VANTAGE_AVAILABLE and alpha_vantage_key:
            self.ts = TimeSeries(key=alpha_vantage_key, output_format='pandas')
            self.fd = FundamentalData(key=alpha_vantage_key, output_format='pandas')
        else:
            self.ts = None
            self.fd = None
    
    def get_company_info_yfinance(self, ticker_symbol: str) -> Dict:
        """yfinance를 사용하여 기업 정보 수집"""
        if not YFINANCE_AVAILABLE:
            return {"error": "yfinance가 설치되지 않았습니다."}
        
        try:
            ticker = yf.Ticker(ticker_symbol)
            info = ticker.info
            
            company_info = {
                "symbol": ticker_symbol,
                "company_name": info.get("longName", info.get("shortName", "")),
                "sector": info.get("sector", ""),
                "industry": info.get("industry", ""),
                "country": info.get("country", ""),
                "website": info.get("website", ""),
                "employees": info.get("fullTimeEmployees", 0),
                "ceo": info.get("companyOfficers", [{}])[0].get("name", "") if info.get("companyOfficers") else "",
                "market_cap": info.get("marketCap", 0),
                "currency": info.get("currency", "USD")
            }
            
            return company_info
        except Exception as e:
            return {"error": f"yfinance 오류: {str(e)}"}
    
    def get_financial_data_yfinance(self, ticker_symbol: str) -> Dict:
        """yfinance를 사용하여 재무 데이터 수집"""
        if not YFINANCE_AVAILABLE:
            return {}
        
        try:
            ticker = yf.Ticker(ticker_symbol)
            
            # 재무제표 가져오기
            financials = ticker.financials  # 손익계산서
            balance_sheet = ticker.balance_sheet  # 재무상태표
            cashflow = ticker.cashflow  # 현금흐름표
            
            financial_data = {}
            
            # 연도별 데이터 추출
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
                    
                    # 영업이익 (Operating Income)
                    if "Operating Income" in financials.index:
                        op_income = financials.loc["Operating Income", year]
                        if not pd.isna(op_income):
                            financial_data[year_str].append({
                                "account_nm": "영업이익",
                                "thstrm_amount": str(int(op_income))
                            })
                    
                    # 당기순이익 (Net Income)
                    if "Net Income" in financials.index:
                        net_income = financials.loc["Net Income", year]
                        if not pd.isna(net_income):
                            financial_data[year_str].append({
                                "account_nm": "당기순이익",
                                "thstrm_amount": str(int(net_income))
                            })
            
            return financial_data
        except Exception as e:
            print(f"yfinance 재무 데이터 오류: {str(e)}")
            return {}
    
    def get_stock_data_yfinance(self, ticker_symbol: str, period: str = "1y") -> Dict:
        """yfinance를 사용하여 주가 데이터 수집"""
        if not YFINANCE_AVAILABLE:
            return {}
        
        try:
            ticker = yf.Ticker(ticker_symbol)
            info = ticker.info
            
            # 최근 주가 데이터
            history = ticker.history(period=period)
            
            stock_info = {
                "symbol": ticker_symbol,
                "current_price": info.get("currentPrice", 0),
                "market_cap": info.get("marketCap", 0),
                "pe_ratio": info.get("trailingPE", 0),
                "pb_ratio": info.get("priceToBook", 0),
                "dividend_yield": info.get("dividendYield", 0) * 100 if info.get("dividendYield") else 0,
                "52_week_high": info.get("fiftyTwoWeekHigh", 0),
                "52_week_low": info.get("fiftyTwoWeekLow", 0),
                "currency": info.get("currency", "USD")
            }
            
            return stock_info
        except Exception as e:
            print(f"yfinance 주가 데이터 오류: {str(e)}")
            return {}
    
    def get_company_all_data(self, ticker_symbol: str, use_alpha_vantage: bool = False) -> Dict:
        """기업 전체 정보 수집"""
        print(f"  - 해외 기업 정보 수집 중: {ticker_symbol}")
        
        # yfinance로 기본 정보 수집
        company_info = self.get_company_info_yfinance(ticker_symbol)
        financial_data = self.get_financial_data_yfinance(ticker_symbol)
        stock_info = self.get_stock_data_yfinance(ticker_symbol)
        
        # Alpha Vantage로 보완 (선택)
        if use_alpha_vantage and self.fd:
            try:
                # 재무제표 보완
                balance_sheet, _ = self.fd.get_balance_sheet_annual(symbol=ticker_symbol)
                income_statement, _ = self.fd.get_income_statement_annual(symbol=ticker_symbol)
                # 데이터 병합 로직 추가 가능
            except Exception as e:
                print(f"Alpha Vantage 오류: {str(e)}")
        
        return {
            "company_info": company_info,
            "financial_data": financial_data,
            "stock_info": stock_info,
            "employee_info": {
                "employees": company_info.get("employees", 0)
            } if company_info.get("employees") else {},
            "recent_disclosures": []  # 해외는 SEC EDGAR 등 별도 필요
        }
    
    def get_company_news(self, company_name: str, ticker_symbol: str = None) -> List[Dict]:
        """기업 뉴스 수집"""
        articles = []
        
        # NewsAPI 사용 (API 키가 있는 경우)
        if self.newsapi_key:
            try:
                url = "https://newsapi.org/v2/everything"
                query = company_name
                if ticker_symbol:
                    query += f" OR {ticker_symbol}"
                
                params = {
                    "q": query,
                    "apiKey": self.newsapi_key,
                    "language": "en",
                    "sortBy": "publishedAt",
                    "pageSize": 50
                }
                
                response = requests.get(url, params=params, timeout=30, verify=False)
                if response.status_code == 200:
                    data = response.json()
                    for article in data.get("articles", []):
                        articles.append({
                            "title": article.get("title", ""),
                            "link": article.get("url", ""),
                            "description": article.get("description", ""),
                            "pub_date": article.get("publishedAt", ""),
                            "source": article.get("source", {}).get("name", "")
                        })
            except Exception as e:
                print(f"NewsAPI 오류: {str(e)}")
        
        return articles


if __name__ == "__main__":
    # 테스트
    api = InternationalFinanceAPI()
    
    # Apple 주식 정보 수집
    data = api.get_company_all_data("AAPL")
    print(json.dumps(data, ensure_ascii=False, indent=2))





