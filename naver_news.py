#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
네이버 뉴스 API를 사용한 기사 크롤링 모듈
"""

import requests
import json
from datetime import datetime
from typing import List, Dict
import hashlib
import urllib3

# SSL 경고 메시지 비활성화 (verify=False 사용 시)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

NAVER_CLIENT_ID = "00q938ugMTSfuzjWuLk4"
NAVER_CLIENT_SECRET = "MrIG7TWaGW"

class NaverNewsAPI:
    """네이버 뉴스 검색 API를 사용하는 클래스"""
    
    def __init__(self, client_id: str = NAVER_CLIENT_ID, client_secret: str = NAVER_CLIENT_SECRET):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://openapi.naver.com/v1/search/news.json"
        self.headers = {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret
        }
    
    def search_finance(self, query: str, display: int = 100, sort: str = "date") -> List[Dict]:
        """금융 관련 정보 검색 (뉴스, 블로그, 웹문서 등 통합)"""
        all_results = []
        
        # 여러 카테고리에서 검색
        categories = [
            ("news", "https://openapi.naver.com/v1/search/news.json"),
            ("blog", "https://openapi.naver.com/v1/search/blog.json"),
            ("webkr", "https://openapi.naver.com/v1/search/webkr.json"),
            ("doc", "https://openapi.naver.com/v1/search/doc.json")
        ]
        
        for category_name, base_url in categories:
            results = self._search_category(base_url, query, display, sort, category_name)
            all_results.extend(results)
        
        # 중복 제거 (URL 기준)
        seen_urls = set()
        unique_results = []
        for result in all_results:
            url = result.get("link", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
        
        # 날짜순 정렬
        unique_results.sort(key=lambda x: x.get("pub_date", ""), reverse=True)
        
        return unique_results
    
    def _search_category(self, base_url: str, query: str, display: int, sort: str, category: str) -> List[Dict]:
        """특정 카테고리에서 검색"""
        results = []
        start = 1
        max_results = min(display, 100)  # 카테고리당 최대 100개
        
        while start <= max_results:
            params = {
                "query": query,
                "display": min(100, max_results - start + 1),
                "start": start,
                "sort": sort
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
                        "category": category,
                        "article_id": self._generate_id(item.get("link", ""))
                    }
                    results.append(result)
                
                start += len(items)
                if len(items) < params["display"]:
                    break
                    
            except Exception as e:
                print(f"네이버 {category} 검색 오류: {str(e)}")
                break
        
        return results
    
    def get_company_finance_info(self, company_name: str = "화승알앤에이", stock_code: str = None) -> Dict:
        """기업 금융 정보 수집"""
        finance_info = {
            "company_name": company_name,
            "stock_code": stock_code,
            "finance_news": [],
            "finance_analysis": [],
            "market_info": []
        }
        
        # 금융 관련 검색어 목록
        finance_keywords = [
            f"{company_name} 주가",
            f"{company_name} 재무",
            f"{company_name} 실적",
            f"{company_name} 투자",
            f"{company_name} 배당",
            f"{company_name} 시가총액",
            f"{company_name} PER",
            f"{company_name} PBR"
        ]
        
        if stock_code:
            finance_keywords.extend([
                f"{company_name} {stock_code}",
                f"종목코드 {stock_code}"
            ])
        
        # 각 검색어로 금융 정보 수집
        all_finance_results = []
        seen_ids = set()
        
        for keyword in finance_keywords:
            results = self.search_finance(keyword, display=30)
            for result in results:
                article_id = result.get("article_id", "")
                if article_id and article_id not in seen_ids:
                    seen_ids.add(article_id)
                    result["search_keyword"] = keyword
                    all_finance_results.append(result)
        
        # 카테고리별 분류
        for result in all_finance_results:
            category = result.get("category", "")
            if category == "news":
                finance_info["finance_news"].append(result)
            elif category in ["blog", "webkr", "doc"]:
                finance_info["finance_analysis"].append(result)
        
        # 날짜순 정렬
        finance_info["finance_news"].sort(key=lambda x: x.get("pub_date", ""), reverse=True)
        finance_info["finance_analysis"].sort(key=lambda x: x.get("pub_date", ""), reverse=True)
        
        return finance_info
    
    def search_news(self, query: str, display: int = 100, sort: str = "date") -> List[Dict]:
        """뉴스 검색"""
        all_articles = []
        start = 1
        
        # 최대 1000개까지 가져오기 (API 제한: 한 번에 최대 100개)
        max_results = min(display, 1000)
        
        while start <= max_results:
            params = {
                "query": query,
                "display": min(100, max_results - start + 1),
                "start": start,
                "sort": sort
            }
            
            try:
                # SSL 인증서 검증 우회 (회사 네트워크 환경 대응)
                response = requests.get(
                    self.base_url, 
                    headers=self.headers, 
                    params=params, 
                    timeout=30,
                    verify=False  # SSL 검증 우회 (보안 경고 무시)
                )
                response.raise_for_status()
                data = response.json()
                
                # 네이버 API 오류 확인
                if "errorCode" in data:
                    error_msg = data.get("errorMessage", "알 수 없는 오류")
                    print(f"네이버 API 오류 ({data.get('errorCode')}): {error_msg}")
                    break
                
                items = data.get("items", [])
                if not items:
                    break
                
                # HTML 태그 제거 및 데이터 정리
                for item in items:
                    article = {
                        "title": self._clean_html(item.get("title", "")),
                        "link": item.get("link", ""),
                        "description": self._clean_html(item.get("description", "")),
                        "pub_date": item.get("pubDate", ""),
                        "source": item.get("source", ""),
                        "article_id": self._generate_id(item.get("link", ""))
                    }
                    all_articles.append(article)
                
                start += len(items)
                
                # 더 이상 결과가 없으면 중단
                if len(items) < params["display"]:
                    break
                    
            except requests.exceptions.Timeout:
                print(f"네이버 뉴스 검색 타임아웃 (30초 초과)")
                break
            except requests.exceptions.RequestException as e:
                print(f"네이버 뉴스 검색 네트워크 오류: {str(e)}")
                break
            except Exception as e:
                print(f"네이버 뉴스 검색 오류: {str(e)}")
                break
        
        return all_articles
    
    def _clean_html(self, text: str) -> str:
        """HTML 태그 제거"""
        import re
        # HTML 태그 제거
        text = re.sub(r'<[^>]+>', '', text)
        # HTML 엔티티 디코딩
        text = text.replace("&lt;", "<").replace("&gt;", ">")
        text = text.replace("&amp;", "&").replace("&quot;", '"')
        text = text.replace("&#39;", "'")
        return text.strip()
    
    def _generate_id(self, url: str) -> str:
        """URL로부터 고유 ID 생성"""
        return hashlib.md5(url.encode()).hexdigest()
    
    def get_company_news(self, company_name: str = "화승알앤에이", keywords: List[str] = None) -> List[Dict]:
        """기업 관련 뉴스 수집"""
        if keywords is None:
            keywords = [company_name, "화승알앤에이", "화승 R&A", "화승R&A", "화승알앤에이"]
        
        all_articles = []
        seen_ids = set()
        
        for keyword in keywords:
            articles = self.search_news(keyword, display=50)
            for article in articles:
                article_id = article["article_id"]
                if article_id not in seen_ids:
                    seen_ids.add(article_id)
                    article["search_keyword"] = keyword
                    all_articles.append(article)
        
        # 날짜순 정렬 (최신순)
        all_articles.sort(key=lambda x: x.get("pub_date", ""), reverse=True)
        
        return all_articles

if __name__ == "__main__":
    # 테스트
    naver = NaverNewsAPI()
    articles = naver.get_company_news("화승R&A")
    print(f"총 {len(articles)}개의 기사를 찾았습니다.")
    for article in articles[:5]:
        print(f"- {article['title']}")
        print(f"  링크: {article['link']}")
        print()

