#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
네이버 Finance API를 사용한 기업 정보 수집 모듈
DART API 대체용
"""

import requests
import json
import re
from datetime import datetime
from typing import List, Dict, Optional
import hashlib
import urllib3
from bs4 import BeautifulSoup

# SSL 경고 메시지 비활성화
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

NAVER_CLIENT_ID = "00q938ugMTSfuzjWuLk4"
NAVER_CLIENT_SECRET = "MrIG7TWaGW"

class NaverFinanceAPI:
    """네이버 검색 API를 사용하여 기업 금융 정보를 수집하는 클래스"""
    
    def __init__(self, client_id: str = NAVER_CLIENT_ID, client_secret: str = NAVER_CLIENT_SECRET):
        self.client_id = client_id
        self.client_secret = client_secret
        self.headers = {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret
        }
    
    def _clean_html(self, text: str) -> str:
        """HTML 태그 제거"""
        if not text:
            return ""
        text = re.sub(r'<[^>]+>', '', text)
        text = text.replace("&lt;", "<").replace("&gt;", ">")
        text = text.replace("&amp;", "&").replace("&quot;", '"')
        text = text.replace("&#39;", "'")
        return text.strip()
    
    def _search_naver(self, query: str, category: str = "news", display: int = 100) -> List[Dict]:
        """네이버 검색 API로 검색"""
        base_urls = {
            "news": "https://openapi.naver.com/v1/search/news.json",
            "blog": "https://openapi.naver.com/v1/search/blog.json",
            "webkr": "https://openapi.naver.com/v1/search/webkr.json",
            "doc": "https://openapi.naver.com/v1/search/doc.json"
        }
        
        base_url = base_urls.get(category, base_urls["news"])
        results = []
        start = 1
        max_results = min(display, 100)
        
        while start <= max_results:
            params = {
                "query": query,
                "display": min(100, max_results - start + 1),
                "start": start,
                "sort": "date"
            }
            
            try:
                response = requests.get(
                    base_url,
                    headers=self.headers,
                    params=params,
                    timeout=30,
                    verify=False
                )
                response.raise_for_status()
                data = response.json()
                
                if "errorCode" in data:
                    break
                
                items = data.get("items", [])
                if not items:
                    break
                
                for item in items:
                    result = {
                        "title": self._clean_html(item.get("title", "")),
                        "link": item.get("link", ""),
                        "description": self._clean_html(item.get("description", "")),
                        "pub_date": item.get("pubDate", item.get("postdate", "")),
                        "source": item.get("source", ""),
                        "category": category
                    }
                    results.append(result)
                
                start += len(items)
                if len(items) < params["display"]:
                    break
                    
            except Exception as e:
                print(f"네이버 {category} 검색 오류: {str(e)}")
                break
        
        return results
    
    def get_company_info(self, company_name: str, stock_code: str = None) -> Dict:
        """기업 기본 정보 수집"""
        company_info = {
            "corp_name": company_name,
            "stock_code": stock_code or "",
            "ceo_nm": "",
            "est_dt": "",
            "adres": "",
            "corp_cls": "Y"  # 법인구분 (Y: 유가증권, K: 코스닥)
        }
        
        # 종목코드가 있으면 네이버 금융 페이지에서 정보 수집 시도
        if stock_code:
            try:
                finance_url = f"https://finance.naver.com/item/main.naver?code={stock_code}"
                response = requests.get(finance_url, timeout=30, verify=False)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # 기업명 추출
                    title_elem = soup.find('h2', class_='wrap_company')
                    if title_elem:
                        company_info["corp_name"] = title_elem.get_text(strip=True)
                    
                    # 기업 정보 추출
                    info_table = soup.find('table', class_='tb_type1')
                    if info_table:
                        rows = info_table.find_all('tr')
                        for row in rows:
                            th = row.find('th')
                            td = row.find('td')
                            if th and td:
                                key = th.get_text(strip=True)
                                value = td.get_text(strip=True)
                                if '대표자' in key:
                                    company_info["ceo_nm"] = value
                                elif '설립일' in key or '설립' in key:
                                    company_info["est_dt"] = value
                                elif '주소' in key or '본사' in key:
                                    company_info["adres"] = value
            except Exception as e:
                print(f"네이버 금융 페이지 크롤링 오류: {str(e)}")
        
        # 검색 API로 추가 정보 수집
        search_query = f"{company_name} 기업정보"
        search_results = self._search_naver(search_query, "webkr", 10)
        
        # 검색 결과에서 정보 추출 시도
        for result in search_results:
            description = result.get("description", "")
            if "대표자" in description or "CEO" in description:
                # 대표자 정보 추출 시도
                match = re.search(r'대표자[:\s]+([가-힣\s]+)', description)
                if match and not company_info["ceo_nm"]:
                    company_info["ceo_nm"] = match.group(1).strip()
        
        return company_info
    
    def get_financial_info(self, company_name: str, stock_code: str = None) -> Dict:
        """재무 정보 수집 (검색 API 기반)"""
        financial_info = {
            "revenue": {},
            "operating_profit": {},
            "net_income": {},
            "total_assets": {},
            "total_liabilities": {},
            "total_equity": {}
        }
        
        # 재무 관련 검색어
        finance_keywords = [
            f"{company_name} 매출",
            f"{company_name} 영업이익",
            f"{company_name} 순이익",
            f"{company_name} 재무제표",
            f"{company_name} 실적"
        ]
        
        if stock_code:
            finance_keywords.append(f"{company_name} {stock_code} 실적")
        
        all_results = []
        for keyword in finance_keywords:
            results = self._search_naver(keyword, "news", 20)
            all_results.extend(results)
            results = self._search_naver(keyword, "blog", 20)
            all_results.extend(results)
        
        # 중복 제거
        seen_links = set()
        unique_results = []
        for result in all_results:
            link = result.get("link", "")
            if link and link not in seen_links:
                seen_links.add(link)
                unique_results.append(result)
        
        # 재무 정보 추출 시도 (간단한 패턴 매칭)
        current_year = datetime.now().year
        for year in range(current_year - 2, current_year + 1):
            year_str = str(year)
            for result in unique_results:
                text = result.get("title", "") + " " + result.get("description", "")
                
                # 매출액 추출 (억원 단위)
                revenue_match = re.search(rf'{year_str}.*?매출[액]*[:\s]*([0-9,]+)\s*억', text)
                if revenue_match:
                    try:
                        revenue = float(revenue_match.group(1).replace(",", ""))
                        if year_str not in financial_info["revenue"]:
                            financial_info["revenue"][year_str] = revenue
                    except:
                        pass
                
                # 영업이익 추출
                op_match = re.search(rf'{year_str}.*?영업이익[:\s]*([0-9,]+)\s*억', text)
                if op_match:
                    try:
                        op = float(op_match.group(1).replace(",", ""))
                        if year_str not in financial_info["operating_profit"]:
                            financial_info["operating_profit"][year_str] = op
                    except:
                        pass
        
        return financial_info
    
    def get_stock_info(self, stock_code: str) -> Dict:
        """주가 정보 수집"""
        stock_info = {
            "current_price": 0,
            "market_cap": 0,
            "per": 0,
            "pbr": 0,
            "dividend_yield": 0
        }
        
        if not stock_code:
            return stock_info
        
        try:
            finance_url = f"https://finance.naver.com/item/main.naver?code={stock_code}"
            response = requests.get(finance_url, timeout=30, verify=False)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 현재가 추출
                price_elem = soup.find('p', class_='no_today')
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    price_match = re.search(r'([0-9,]+)', price_text)
                    if price_match:
                        try:
                            stock_info["current_price"] = int(price_match.group(1).replace(",", ""))
                        except:
                            pass
                
                # 시가총액, PER, PBR 등 추출
                summary_table = soup.find('table', class_='tb_type1')
                if summary_table:
                    rows = summary_table.find_all('tr')
                    for row in rows:
                        th = row.find('th')
                        td = row.find('td')
                        if th and td:
                            key = th.get_text(strip=True)
                            value = td.get_text(strip=True)
                            
                            if '시가총액' in key:
                                cap_match = re.search(r'([0-9,]+)', value)
                                if cap_match:
                                    try:
                                        cap = cap_match.group(1).replace(",", "")
                                        if '조' in value:
                                            stock_info["market_cap"] = float(cap) * 10000  # 조 -> 억원
                                        elif '억' in value:
                                            stock_info["market_cap"] = float(cap)
                                    except:
                                        pass
                            elif 'PER' in key:
                                per_match = re.search(r'([0-9.]+)', value)
                                if per_match:
                                    try:
                                        stock_info["per"] = float(per_match.group(1))
                                    except:
                                        pass
                            elif 'PBR' in key:
                                pbr_match = re.search(r'([0-9.]+)', value)
                                if pbr_match:
                                    try:
                                        stock_info["pbr"] = float(pbr_match.group(1))
                                    except:
                                        pass
                            elif '배당수익률' in key or '배당률' in key:
                                div_match = re.search(r'([0-9.]+)', value)
                                if div_match:
                                    try:
                                        stock_info["dividend_yield"] = float(div_match.group(1))
                                    except:
                                        pass
        except Exception as e:
            print(f"주가 정보 수집 오류: {str(e)}")
        
        return stock_info
    
    def get_company_all_data(self, company_name: str, stock_code: str = None) -> Dict:
        """기업 전체 정보 수집 (DART API 대체)"""
        print(f"  - 네이버 Finance API로 {company_name} 정보 수집 중...")
        
        # 종목코드가 없으면 검색으로 찾기
        if not stock_code:
            # 화승알앤에이의 알려진 종목코드
            if "화승" in company_name and "알앤에이" in company_name:
                stock_code = "378850"
            else:
                # 검색으로 종목코드 찾기 시도
                search_query = f"{company_name} 종목코드"
                results = self._search_naver(search_query, "webkr", 5)
                for result in results:
                    text = result.get("description", "")
                    code_match = re.search(r'(\d{6})', text)
                    if code_match:
                        stock_code = code_match.group(1)
                        break
        
        # 기업 정보 수집
        company_info = self.get_company_info(company_name, stock_code)
        if stock_code:
            company_info["stock_code"] = stock_code
        
        # 재무 정보 수집
        financial_info = self.get_financial_info(company_name, stock_code)
        
        # 주가 정보 수집
        stock_info = {}
        if stock_code:
            stock_info = self.get_stock_info(stock_code)
        
        # 재무 데이터를 DART 형식으로 변환
        financial_data = {}
        for year in financial_info.get("revenue", {}).keys():
            financial_data[year] = []
            
            # 매출액
            if year in financial_info.get("revenue", {}):
                financial_data[year].append({
                    "account_nm": "매출액",
                    "thstrm_amount": str(int(financial_info["revenue"][year] * 100000000))  # 억원 -> 원
                })
            
            # 영업이익
            if year in financial_info.get("operating_profit", {}):
                financial_data[year].append({
                    "account_nm": "영업이익",
                    "thstrm_amount": str(int(financial_info["operating_profit"][year] * 100000000))
                })
            
            # 당기순이익
            if year in financial_info.get("net_income", {}):
                financial_data[year].append({
                    "account_nm": "당기순이익",
                    "thstrm_amount": str(int(financial_info["net_income"][year] * 100000000))
                })
        
        return {
            "company_info": company_info,
            "financial_data": financial_data,
            "stock_info": stock_info,
            "employee_info": {},  # 네이버 Finance에서는 직원 정보 제공 안 함
            "recent_disclosures": []  # 네이버 Finance에서는 공시 정보 제공 안 함
        }

if __name__ == "__main__":
    # 테스트
    api = NaverFinanceAPI()
    data = api.get_company_all_data("화승알앤에이", "378850")
    print(json.dumps(data, ensure_ascii=False, indent=2))





