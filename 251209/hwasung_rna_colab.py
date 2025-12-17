#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
화승알앤에이 실시간 분석 보고서 생성 (Google Colab용)
이 파일을 Colab에 업로드하고 실행하세요.
"""

# ============================================================================
# 1. 필요한 라이브러리 설치 (Colab에서 실행)
# ============================================================================
# !pip install requests -q

# ============================================================================
# 2. API 키 설정
# ============================================================================
DART_API_KEY = "5523e4e6b24ce622cff0e56500dcccad55bcb26f"
NAVER_CLIENT_ID = "00q938ugMTSfuzjWuLk4"
NAVER_CLIENT_SECRET = "MrIG7TWaGW"

COMPANY_NAME = "화승알앤에이"
CORP_CODE = "378850"  # 종목코드 (실제 고유번호는 공시 정보에서 추출)
# 참고: 실제 DART 고유번호는 "01532603" (공시 정보에서 확인됨)

# ============================================================================
# 3. 라이브러리 임포트
# ============================================================================
import requests
import json
from datetime import datetime
from typing import Dict, List, Optional
import hashlib
import re
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============================================================================
# 4. DART API 클래스
# ============================================================================
class DartAPI:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://opendart.fss.or.kr/api"
        self.session = requests.Session()
        retry_strategy = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        self.session.headers.update({'User-Agent': 'Mozilla/5.0'})
    
    def get_company_info(self, corp_code: str) -> Optional[Dict]:
        url = f"{self.base_url}/company.json"
        params = {"crtfc_key": self.api_key, "corp_code": corp_code}
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            if data.get("status") == "000":
                return data.get("list", [{}])[0] if data.get("list") else {}
            return None
        except Exception as e:
            print(f"DART 기업 정보 조회 오류: {str(e)}")
            return None
    
    def get_financial_data(self, corp_code: str, bsns_year: str, reprt_code: str = "11011") -> Optional[List[Dict]]:
        url = f"{self.base_url}/fnlttSinglAcnt.json"
        params = {"crtfc_key": self.api_key, "corp_code": corp_code, "bsns_year": bsns_year, "reprt_code": reprt_code}
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            if data.get("status") == "000":
                return data.get("list", [])
            return None
        except Exception as e:
            print(f"DART 재무정보 조회 오류: {str(e)}")
            return None
    
    def get_employee_info(self, corp_code: str, bsns_year: str, reprt_code: str = "11011") -> Optional[Dict]:
        """직원 수 정보 조회
        reprt_code: 11011(사업보고서), 11013(분기보고서)
        """
        url = f"{self.base_url}/empSttus.json"
        params = {
            "crtfc_key": self.api_key,
            "corp_code": corp_code,
            "bsns_year": bsns_year,
            "reprt_code": reprt_code
        }
        try:
            response = self.session.get(url, params=params, timeout=60)
            response.raise_for_status()
            data = response.json()
            if data.get("status") == "000":
                emp_list = data.get("list", [])
                if emp_list:
                    print(f"  - 직원 정보 수집 성공: {bsns_year}년 (보고서: {reprt_code})")
                    return emp_list[0]
            elif data.get("status") == "013":
                print(f"  - 직원 정보 없음: {bsns_year}년 (보고서: {reprt_code}, 데이터 미공시)")
            else:
                print(f"  - 직원 정보 조회 실패: status={data.get('status')}, message={data.get('message', 'N/A')}")
            return None
        except Exception as e:
            print(f"  - 직원 정보 조회 오류: {str(e)}")
            return None
    
    def get_recent_disclosures(self, corp_code: str) -> List[Dict]:
        url = f"{self.base_url}/list.json"
        params = {
            "crtfc_key": self.api_key,
            "corp_code": corp_code,
            "bgn_de": datetime.now().replace(month=1, day=1).strftime("%Y%m%d"),
            "end_de": datetime.now().strftime("%Y%m%d"),
            "page_no": "1",
            "page_count": "100"
        }
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            if data.get("status") == "000":
                return data.get("list", [])
            return []
        except Exception as e:
            print(f"DART 공시 정보 조회 오류: {str(e)}")
            return []
    
    def get_major_stockholders(self, corp_code: str, bsns_year: str, reprt_code: str = "11011") -> Optional[List[Dict]]:
        """주요주주 현황 조회"""
        url = f"{self.base_url}/majorstock.json"
        params = {
            "crtfc_key": self.api_key,
            "corp_code": corp_code,
            "bsns_year": bsns_year,
            "reprt_code": reprt_code
        }
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            if data.get("status") == "000":
                return data.get("list", [])
            return None
        except Exception as e:
            print(f"DART 주요주주 현황 조회 오류: {str(e)}")
            return None
    
    def get_executives(self, corp_code: str, bsns_year: str, reprt_code: str = "11011") -> Optional[List[Dict]]:
        """임원 현황 조회"""
        url = f"{self.base_url}/hyslrSttus.json"
        params = {
            "crtfc_key": self.api_key,
            "corp_code": corp_code,
            "bsns_year": bsns_year,
            "reprt_code": reprt_code
        }
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            if data.get("status") == "000":
                return data.get("list", [])
            return None
        except Exception as e:
            print(f"DART 임원 현황 조회 오류: {str(e)}")
            return None
    
    def get_dividend_info(self, corp_code: str, bsns_year: str, reprt_code: str = "11011") -> Optional[List[Dict]]:
        """배당 정보 조회"""
        url = f"{self.base_url}/alotMatter.json"
        params = {
            "crtfc_key": self.api_key,
            "corp_code": corp_code,
            "bsns_year": bsns_year,
            "reprt_code": reprt_code
        }
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            if data.get("status") == "000":
                return data.get("list", [])
            return None
        except Exception as e:
            print(f"DART 배당 정보 조회 오류: {str(e)}")
            return None
    
    def get_shareholders(self, corp_code: str, bsns_year: str, reprt_code: str = "11011") -> Optional[List[Dict]]:
        """주주 현황 조회"""
        url = f"{self.base_url}/stockTotqySttus.json"
        params = {
            "crtfc_key": self.api_key,
            "corp_code": corp_code,
            "bsns_year": bsns_year,
            "reprt_code": reprt_code
        }
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            if data.get("status") == "000":
                return data.get("list", [])
            return None
        except Exception as e:
            print(f"DART 주주 현황 조회 오류: {str(e)}")
            return None
    
    def get_cash_flow(self, corp_code: str, bsns_year: str, reprt_code: str = "11011") -> Optional[List[Dict]]:
        """현금흐름표 조회 (재무정보에서 별도 추출)"""
        # fnlttSinglAcnt.json에서 현금흐름표 항목만 필터링
        financial_data = self.get_financial_data(corp_code, bsns_year, reprt_code)
        if financial_data:
            # 현금흐름표 관련 계정명 필터링
            cash_flow_accounts = ["영업활동", "투자활동", "재무활동", "현금흐름", "현금및현금성자산"]
            cash_flow_data = [
                item for item in financial_data
                if any(account in item.get("account_nm", "") for account in cash_flow_accounts)
            ]
            return cash_flow_data if cash_flow_data else None
        return None
    
    def get_company_classification(self, corp_code: str) -> Optional[Dict]:
        """기업 분류 정보 조회"""
        url = f"{self.base_url}/crfcCorpCls.json"
        params = {
            "crtfc_key": self.api_key,
            "corp_code": corp_code
        }
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            if data.get("status") == "000":
                return data.get("list", [{}])[0] if data.get("list") else {}
            return None
        except Exception as e:
            print(f"DART 기업 분류 정보 조회 오류: {str(e)}")
            return None
    
    def get_company_all_data(self, corp_code: str) -> Dict:
        print(f"\n[DART] 기업 정보 수집 시작 (고유번호: {corp_code})...")
        print("=" * 60)
        
        # 먼저 공시 정보로부터 실제 고유번호 확인
        print("[1/10] 공시 정보로부터 고유번호 확인 중...")
        disclosures = self.get_recent_disclosures(corp_code)
        
        # 공시 정보에서 실제 고유번호 추출
        actual_corp_code = corp_code
        if disclosures and len(disclosures) > 0:
            actual_corp_code = disclosures[0].get("corp_code", corp_code)
            if actual_corp_code != corp_code:
                print(f"  → 실제 고유번호 확인: {actual_corp_code}")
        
        # 올바른 고유번호로 기업 정보 조회
        print("[2/10] 기업 기본 정보 수집 중...")
        company_info = self.get_company_info(actual_corp_code)
        if not company_info:
            print(f"  [경고] 기업 정보를 가져올 수 없습니다. 공시 정보에서 추출합니다.")
            # 공시 정보에서 기본 정보 추출
            if disclosures and len(disclosures) > 0:
                first_disc = disclosures[0]
                company_info = {
                    "corp_code": first_disc.get("corp_code", ""),
                    "corp_name": first_disc.get("corp_name", ""),
                    "stock_code": first_disc.get("stock_code", ""),
                    "corp_cls": first_disc.get("corp_cls", "")
                }
        if company_info:
            print(f"  → 기업명: {company_info.get('corp_name', 'N/A')}")
        
        # 기업 분류 정보
        print("[3/10] 기업 분류 정보 수집 중...")
        company_classification = self.get_company_classification(actual_corp_code)
        if company_classification:
            print(f"  → 기업 분류 정보 수집 완료")
        
        current_year = datetime.now().year
        
        # 재무정보 수집
        print("[4/10] 재무정보 수집 중...")
        financial_data = {}
        cash_flow_data = {}
        for year in [current_year, current_year - 1, current_year - 2]:
            fn_data = self.get_financial_data(actual_corp_code, str(year))
            if fn_data:
                financial_data[str(year)] = fn_data
                print(f"  → {year}년 재무정보 수집 완료")
            
            # 현금흐름표 별도 수집
            cf_data = self.get_cash_flow(actual_corp_code, str(year))
            if cf_data:
                cash_flow_data[str(year)] = cf_data
                print(f"  → {year}년 현금흐름표 수집 완료")
        
        # 직원 정보 수집
        print("[5/10] 직원 정보 수집 중...")
        employee_info = None
        for year in [current_year, current_year - 1, current_year - 2]:
            employee_info = self.get_employee_info(actual_corp_code, str(year), "11011")
            if employee_info:
                print(f"  → 직원 수: {employee_info.get('sm', employee_info.get('cnt', 'N/A'))}명 ({year}년 기준)")
                break
            employee_info = self.get_employee_info(actual_corp_code, str(year), "11013")
            if employee_info:
                print(f"  → 직원 수: {employee_info.get('sm', employee_info.get('cnt', 'N/A'))}명 ({year}년 기준, 분기보고서)")
                break
        if not employee_info:
            print("  → 직원 정보: 사용 가능한 데이터가 없습니다.")
        
        # 주요주주 현황 수집
        print("[6/10] 주요주주 현황 수집 중...")
        major_stockholders = {}
        for year in [current_year, current_year - 1, current_year - 2]:
            ms_data = self.get_major_stockholders(actual_corp_code, str(year))
            if ms_data:
                major_stockholders[str(year)] = ms_data
                print(f"  → {year}년 주요주주 현황 수집 완료 ({len(ms_data)}명)")
                break
        if not major_stockholders:
            print("  → 주요주주 현황: 사용 가능한 데이터가 없습니다.")
        
        # 임원 현황 수집
        print("[7/10] 임원 현황 수집 중...")
        executives = {}
        for year in [current_year, current_year - 1, current_year - 2]:
            exec_data = self.get_executives(actual_corp_code, str(year))
            if exec_data:
                executives[str(year)] = exec_data
                print(f"  → {year}년 임원 현황 수집 완료 ({len(exec_data)}명)")
                break
        if not executives:
            print("  → 임원 현황: 사용 가능한 데이터가 없습니다.")
        
        # 주주 현황 수집
        print("[8/10] 주주 현황 수집 중...")
        shareholders = {}
        for year in [current_year, current_year - 1, current_year - 2]:
            sh_data = self.get_shareholders(actual_corp_code, str(year))
            if sh_data:
                shareholders[str(year)] = sh_data
                print(f"  → {year}년 주주 현황 수집 완료")
                break
        if not shareholders:
            print("  → 주주 현황: 사용 가능한 데이터가 없습니다.")
        
        # 배당 정보 수집
        print("[9/10] 배당 정보 수집 중...")
        dividend_info = {}
        for year in [current_year, current_year - 1, current_year - 2]:
            div_data = self.get_dividend_info(actual_corp_code, str(year))
            if div_data:
                dividend_info[str(year)] = div_data
                print(f"  → {year}년 배당 정보 수집 완료")
                break
        if not dividend_info:
            print("  → 배당 정보: 사용 가능한 데이터가 없습니다.")
        
        # 공시 정보
        print("[10/10] 공시 정보 정리 중...")
        print(f"  → 공시 정보: {len(disclosures)}개")
        
        print("=" * 60)
        print("[DART] 모든 정보 수집 완료!")
        print("=" * 60)
        
        return {
            "company_info": company_info or {},
            "company_classification": company_classification or {},
            "financial_data": financial_data,
            "cash_flow_data": cash_flow_data,
            "employee_info": employee_info or {},
            "major_stockholders": major_stockholders,
            "executives": executives,
            "shareholders": shareholders,
            "dividend_info": dividend_info,
            "recent_disclosures": disclosures[:50],  # 최근 50개로 확장
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

# ============================================================================
# 5. 네이버 뉴스 API 클래스
# ============================================================================
class NaverNewsAPI:
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://openapi.naver.com/v1/search/news.json"
        self.headers = {"X-Naver-Client-Id": self.client_id, "X-Naver-Client-Secret": self.client_secret}
    
    def search_news(self, query: str, display: int = 100) -> List[Dict]:
        all_articles = []
        start = 1
        max_results = min(display, 1000)
        while start <= max_results:
            params = {"query": query, "display": min(100, max_results - start + 1), "start": start, "sort": "date"}
            try:
                response = requests.get(self.base_url, headers=self.headers, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                if "errorCode" in data:
                    print(f"네이버 API 오류: {data.get('errorMessage')}")
                    break
                items = data.get("items", [])
                if not items:
                    break
                for item in items:
                    article = {
                        "title": re.sub(r'<[^>]+>', '', item.get("title", "")).replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&"),
                        "link": item.get("link", ""),
                        "description": re.sub(r'<[^>]+>', '', item.get("description", "")).replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&"),
                        "pub_date": item.get("pubDate", ""),
                        "source": item.get("source", ""),
                        "article_id": hashlib.md5(item.get("link", "").encode()).hexdigest()
                    }
                    all_articles.append(article)
                start += len(items)
                if len(items) < params["display"]:
                    break
            except Exception as e:
                print(f"네이버 뉴스 검색 오류: {str(e)}")
                break
        return all_articles
    
    def get_company_news(self, company_name: str, keywords: List[str] = None) -> List[Dict]:
        if keywords is None:
            keywords = [company_name, "화승알앤에이", "화승 R&A", "화승R&A"]
        print(f"\n[네이버] 뉴스 기사 수집 시작...")
        all_articles = []
        seen_ids = set()
        for keyword in keywords:
            print(f"  - 검색어: {keyword}")
            articles = self.search_news(keyword, display=50)
            for article in articles:
                article_id = article["article_id"]
                if article_id not in seen_ids:
                    seen_ids.add(article_id)
                    article["search_keyword"] = keyword
                    all_articles.append(article)
            print(f"    → {len(articles)}개 기사 수집")
        all_articles.sort(key=lambda x: x.get("pub_date", ""), reverse=True)
        print(f"\n[네이버] 총 {len(all_articles)}개의 고유 기사 수집 완료")
        return all_articles

# ============================================================================
# 6. 메인 실행 코드
# ============================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("화승알앤에이 분석 보고서 데이터 수집 시작")
    print(f"시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # DART API 데이터 수집
    dart = DartAPI(DART_API_KEY)
    dart_data = dart.get_company_all_data(CORP_CODE)
    
    # 네이버 뉴스 API 데이터 수집
    naver = NaverNewsAPI(NAVER_CLIENT_ID, NAVER_CLIENT_SECRET)
    news_articles = naver.get_company_news(COMPANY_NAME)
    
    # 데이터 통합
    all_data = {
        "company_name": COMPANY_NAME,
        "company_info": dart_data.get("company_info", {}) if "error" not in dart_data else {},
        "company_classification": dart_data.get("company_classification", {}) if "error" not in dart_data else {},
        "financial_data": dart_data.get("financial_data", {}) if "error" not in dart_data else {},
        "cash_flow_data": dart_data.get("cash_flow_data", {}) if "error" not in dart_data else {},
        "employee_info": dart_data.get("employee_info", {}) if "error" not in dart_data else {},
        "major_stockholders": dart_data.get("major_stockholders", {}) if "error" not in dart_data else {},
        "executives": dart_data.get("executives", {}) if "error" not in dart_data else {},
        "shareholders": dart_data.get("shareholders", {}) if "error" not in dart_data else {},
        "dividend_info": dart_data.get("dividend_info", {}) if "error" not in dart_data else {},
        "recent_disclosures": dart_data.get("recent_disclosures", []) if "error" not in dart_data else [],
        "news_articles": news_articles,
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # DART 데이터 수집 결과 출력
    if "error" in dart_data:
        print(f"\n[경고] DART API 오류: {dart_data.get('error')}")
        print("네이버 뉴스 데이터만 저장됩니다.")
    else:
        print(f"\n[DART 데이터 수집 완료 - 상세 요약]")
        print(f"  ✓ 기업 정보: {'있음' if all_data.get('company_info') else '없음'}")
        print(f"  ✓ 기업 분류: {'있음' if all_data.get('company_classification') else '없음'}")
        print(f"  ✓ 재무 데이터: {len(all_data.get('financial_data', {}))}개 연도")
        print(f"  ✓ 현금흐름표: {len(all_data.get('cash_flow_data', {}))}개 연도")
        print(f"  ✓ 직원 정보: {'있음' if all_data.get('employee_info') else '없음'}")
        print(f"  ✓ 주요주주 현황: {len(all_data.get('major_stockholders', {}))}개 연도")
        print(f"  ✓ 임원 현황: {len(all_data.get('executives', {}))}개 연도")
        print(f"  ✓ 주주 현황: {len(all_data.get('shareholders', {}))}개 연도")
        print(f"  ✓ 배당 정보: {len(all_data.get('dividend_info', {}))}개 연도")
        print(f"  ✓ 공시 정보: {len(all_data.get('recent_disclosures', []))}개")
    
    # JSON 저장
    with open("hwasung_rna_data.json", "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    print("\n데이터 저장 완료: hwasung_rna_data.json")
    
    # 결과 출력
    print("\n" + "=" * 60)
    print("데이터 수집 완료")
    print("=" * 60)
    if "error" not in dart_data:
        print(f"\n[DART 데이터 상세]")
        print(f"  기업명: {dart_data.get('company_info', {}).get('corp_name', 'N/A')}")
        print(f"  재무 데이터: {len(dart_data.get('financial_data', {}))}개 연도")
        print(f"  현금흐름표: {len(dart_data.get('cash_flow_data', {}))}개 연도")
        print(f"  직원 정보: {'있음' if dart_data.get('employee_info') else '없음'}")
        print(f"  주요주주: {len(dart_data.get('major_stockholders', {}))}개 연도")
        print(f"  임원 현황: {len(dart_data.get('executives', {}))}개 연도")
        print(f"  주주 현황: {len(dart_data.get('shareholders', {}))}개 연도")
        print(f"  배당 정보: {len(dart_data.get('dividend_info', {}))}개 연도")
        print(f"  공시 정보: {len(dart_data.get('recent_disclosures', []))}개")
    print(f"\n[네이버 뉴스]")
    print(f"  수집된 기사 수: {len(news_articles)}개")
    print("\n" + "=" * 60)
    print("모든 데이터가 hwasung_rna_data.json 파일에 저장되었습니다.")
    print("=" * 60)

