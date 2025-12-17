#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DART API를 사용한 기업 정보 조회 모듈
"""

import requests
import json
from datetime import datetime
from typing import Dict, List, Optional
import urllib3
import os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# SSL 경고 메시지 비활성화
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DART_API_KEY = "5523e4e6b24ce622cff0e56500dcccad55bcb26f"
DART_BASE_URL = "https://opendart.fss.or.kr/api"

class DartAPI:
    """DART API를 사용하여 기업 정보를 조회하는 클래스"""
    
    def __init__(self, api_key: str = DART_API_KEY, use_proxy: bool = False, proxy_url: str = None):
        self.api_key = api_key
        self.base_url = DART_BASE_URL
        
        # 세션 생성 및 설정
        self.session = requests.Session()
        
        # 재시도 전략 설정
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # User-Agent 설정 (일부 방화벽이 User-Agent를 확인함)
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        # 프록시 설정
        if use_proxy and proxy_url:
            self.session.proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
        elif use_proxy:
            # 환경변수에서 프록시 가져오기
            http_proxy = os.environ.get('HTTP_PROXY') or os.environ.get('http_proxy')
            https_proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')
            if http_proxy or https_proxy:
                self.session.proxies = {
                    'http': http_proxy,
                    'https': https_proxy or http_proxy
                }
    
    def search_company(self, company_name: str) -> Optional[Dict]:
        """기업명으로 기업 정보 검색"""
        # 여러 검색어 시도
        search_terms = [
            company_name,
            "화승알앤에이",
            "화승R&A",
            "화승 R&A",
            "화승"
        ]
        
        for search_term in search_terms:
            # 공시 검색을 통해 기업 찾기 (company.json은 타임아웃 발생)
            url = f"{self.base_url}/list.json"
            current_year = datetime.now().year
            params = {
                "crtfc_key": self.api_key,
                "corp_name": search_term,
                "bgn_de": f"{current_year-2}0101",
                "end_de": datetime.now().strftime("%Y%m%d"),
                "page_no": "1",
                "page_count": "10"
            }
            
            try:
                # 세션을 사용하여 요청 (연결 재사용)
                response = self.session.get(url, params=params, timeout=60, verify=False)
                response.raise_for_status()
                data = response.json()
                
                if data.get("status") == "000":
                    disclosures = data.get("list", [])
                    if disclosures:
                        # 첫 번째 공시에서 기업 정보 추출
                        first_disclosure = disclosures[0]
                        corp_code = first_disclosure.get("corp_code")
                        corp_name = first_disclosure.get("corp_name", "")
                        
                        if corp_code:
                            # 기업 상세 정보 조회
                            company_info = self.get_company_info(corp_code)
                            if company_info:
                                print(f"기업 찾음: {corp_name} (검색어: {search_term})")
                                return company_info
                            else:
                                # 상세 정보 조회 실패 시 공시 정보로부터 기본 정보 구성
                                print(f"기업 찾음: {corp_name} (검색어: {search_term}, 공시 정보 사용)")
                                return {
                                    "corp_code": corp_code,
                                    "corp_name": corp_name,
                                    "stock_code": first_disclosure.get("stock_code", ""),
                                    "modify_date": first_disclosure.get("rcept_dt", "")
                                }
                elif data.get("status") == "013":
                    # 검색 결과가 없는 경우, 다음 검색어 시도
                    continue
                else:
                    error_msg = data.get('message', '알 수 없는 오류')
                    print(f"DART 공시 검색 오류 ({search_term}): {error_msg}")
                    continue
            except requests.exceptions.Timeout:
                print(f"DART 공시 검색 타임아웃 ({search_term}, 30초 초과)")
                continue
            except Exception as e:
                print(f"DART 공시 검색 오류 ({search_term}): {str(e)}")
                continue
        
        print(f"모든 검색어로 기업 '{company_name}'을(를) 찾을 수 없습니다.")
        return None
    
    def get_company_info(self, corp_code: str) -> Optional[Dict]:
        """기업 고유번호로 상세 정보 조회"""
        url = f"{self.base_url}/company.json"
        params = {
            "crtfc_key": self.api_key,
            "corp_code": corp_code
        }
        
        # 재시도 로직 (최대 3회)
        for attempt in range(3):
            try:
                # 세션을 사용하여 요청 (연결 재사용)
                response = self.session.get(url, params=params, timeout=60, verify=False)
                response.raise_for_status()
                data = response.json()
                
                if data.get("status") == "000":
                    return data.get("list", [{}])[0] if data.get("list") else {}
                elif data.get("status") == "013":
                    print(f"DART: 기업 고유번호 {corp_code}를 찾을 수 없습니다.")
                    return None
                else:
                    error_msg = data.get('message', '알 수 없는 오류')
                    if attempt < 2:
                        print(f"DART API 오류, 재시도 중... ({attempt + 1}/3): {error_msg}")
                        continue
                    print(f"DART API 오류: {error_msg}")
                    return None
            except requests.exceptions.Timeout:
                if attempt < 2:
                    print(f"DART 기업 정보 조회 타임아웃, 재시도 중... ({attempt + 1}/3)")
                    continue
                print(f"DART 기업 정보 조회 타임아웃 (최대 재시도 횟수 초과)")
                return None
            except Exception as e:
                if attempt < 2:
                    print(f"DART 기업 정보 조회 오류, 재시도 중... ({attempt + 1}/3): {str(e)}")
                    continue
                print(f"DART 기업 정보 조회 오류: {str(e)}")
                return None
        return None
    
    def get_financial_data(self, corp_code: str, bsns_year: str, reprt_code: str = "11011") -> Optional[List[Dict]]:
        """재무정보 조회 (11011: 사업보고서, 11013: 분기보고서)"""
        url = f"{self.base_url}/fnlttSinglAcnt.json"
        params = {
            "crtfc_key": self.api_key,
            "corp_code": corp_code,
            "bsns_year": bsns_year,
            "reprt_code": reprt_code
        }
        
        try:
            # SSL 인증서 검증 우회 (회사 네트워크 환경 대응)
            response = requests.get(url, params=params, timeout=30, verify=False)
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") == "000":
                return data.get("list", [])
            return None
        except Exception as e:
            print(f"DART 재무정보 조회 오류: {str(e)}")
            return None
    
    def get_employee_info(self, corp_code: str, bsns_year: str) -> Optional[Dict]:
        """직원 수 정보 조회"""
        url = f"{self.base_url}/empSttus.json"
        params = {
            "crtfc_key": self.api_key,
            "corp_code": corp_code,
            "bsns_year": bsns_year
        }
        
        try:
            # SSL 인증서 검증 우회 (회사 네트워크 환경 대응)
            response = requests.get(url, params=params, timeout=60, verify=False)
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") == "000":
                emp_list = data.get("list", [])
                if emp_list:
                    # 최신 연도 데이터 반환
                    return emp_list[0]
            elif data.get("status") == "013":
                # 데이터 없음
                print(f"DART 직원 정보: {bsns_year}년 데이터가 없습니다.")
            else:
                print(f"DART 직원 정보 조회 오류: status={data.get('status')}, message={data.get('message', 'N/A')}")
            return None
        except Exception as e:
            print(f"DART 직원 정보 조회 오류: {str(e)}")
            return None
    
    def get_recent_disclosures(self, corp_code: str, bgn_de: str = None, end_de: str = None) -> List[Dict]:
        """최근 공시 정보 조회"""
        url = f"{self.base_url}/list.json"
        params = {
            "crtfc_key": self.api_key,
            "corp_code": corp_code,
            "bgn_de": bgn_de or (datetime.now().replace(month=1, day=1).strftime("%Y%m%d")),
            "end_de": end_de or datetime.now().strftime("%Y%m%d"),
            "page_no": "1",
            "page_count": "100"
        }
        
        try:
            # SSL 인증서 검증 우회 (회사 네트워크 환경 대응)
            response = requests.get(url, params=params, timeout=30, verify=False)
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") == "000":
                return data.get("list", [])
            return []
        except Exception as e:
            print(f"DART 공시 정보 조회 오류: {str(e)}")
            return []
    
    def get_company_all_data(self, company_name: str = "화승알앤에이", corp_code: str = "378850") -> Dict:
        """기업의 모든 정보를 종합하여 반환"""
        # corp_code가 직접 제공된 경우 사용
        if corp_code:
            company = self.get_company_info(corp_code)
            if not company:
                return {"error": f"고유번호 {corp_code}로 기업을 찾을 수 없습니다."}
        else:
            # 1. 기업 검색
            company = self.search_company(company_name)
            if not company:
                # 검색 실패 시, 화승R&A의 알려진 고유번호 시도
                # 주: 실제 고유번호는 DART에서 확인 필요
                known_codes = {
                    "화승R&A": None,  # 실제 고유번호로 교체 필요
                    "화승 R&A": None,
                    "화승": None
                }
                
                # 알려진 코드가 없으면 에러 반환
                return {"error": f"기업 '{company_name}'을(를) 찾을 수 없습니다. 고유번호를 직접 제공하거나 DART에서 확인하세요."}
        
        corp_code = company.get("corp_code") or corp_code
        if not corp_code:
            return {"error": "기업 고유번호를 확인할 수 없습니다."}
        
        current_year = datetime.now().year
        previous_year = current_year - 1
        
        # 2. 재무정보 조회 (최근 3년, 실패해도 계속 진행)
        financial_data = {}
        for year in [current_year, previous_year, current_year - 2]:
            year_str = str(year)
            try:
                fn_data = self.get_financial_data(corp_code, year_str)
                if fn_data:
                    financial_data[year_str] = fn_data
            except:
                pass  # 재무정보 조회 실패해도 계속 진행
        
        # 3. 직원 정보 조회 (여러 연도 시도)
        employee_info = None
        try:
            # 최근 3년 동안 시도 (사업보고서 우선, 없으면 분기보고서)
            for year in [current_year, previous_year, current_year - 2]:
                # 사업보고서(11011) 먼저 시도
                employee_info = self.get_employee_info(corp_code, str(year), "11011")
                if employee_info:
                    print(f"[DART] 직원 정보 수집 완료: {year}년 데이터 (사업보고서)")
                    break
                # 사업보고서에 없으면 분기보고서(11013) 시도
                employee_info = self.get_employee_info(corp_code, str(year), "11013")
                if employee_info:
                    print(f"[DART] 직원 정보 수집 완료: {year}년 데이터 (분기보고서)")
                    break
            if not employee_info:
                print("[DART] 직원 정보: 사용 가능한 데이터가 없습니다.")
        except Exception as e:
            print(f"[DART] 직원 정보 조회 중 오류: {str(e)}")
            pass  # 직원 정보 조회 실패해도 계속 진행
        
        # 4. 최근 공시 정보
        disclosures = []
        try:
            disclosures = self.get_recent_disclosures(corp_code)
        except:
            pass  # 공시 정보 조회 실패해도 계속 진행
        
        return {
            "company_info": company,
            "financial_data": financial_data,
            "employee_info": employee_info or {},
            "recent_disclosures": disclosures[:20],  # 최근 20개만
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

if __name__ == "__main__":
    # 테스트
    dart = DartAPI()
    data = dart.get_company_all_data("화승R&A")
    print(json.dumps(data, ensure_ascii=False, indent=2))

