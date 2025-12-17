#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
네이버 뉴스 API를 사용한 SaarGummi 관련 기사 크롤러
"""

import os
import requests
import json
import hashlib
import re
import time
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional
from pathlib import Path

# 한국 시간대 (KST, UTC+9)
KST = timezone(timedelta(hours=9))

def get_kst_now():
    """한국 시간 현재 시각 반환"""
    return datetime.now(KST)
from urllib.parse import urlparse, quote, urlencode, quote, urlencode
import urllib3
from bs4 import BeautifulSoup
import feedparser

# SSL 경고 메시지 비활성화
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 번역 라이브러리 (선택적 사용)
try:
    from googletrans import Translator
    TRANSLATOR_AVAILABLE = True
    translator = Translator()
except ImportError:
    TRANSLATOR_AVAILABLE = False
    translator = None

NAVER_CLIENT_ID = "00q938ugMTSfuzjWuLk4"
NAVER_CLIENT_SECRET = "MrIG7TWaGW"

class SaarGummiNewsCrawler:
    """SaarGummi 관련 뉴스 크롤러"""
    
    def __init__(self, client_id: str = NAVER_CLIENT_ID, client_secret: str = NAVER_CLIENT_SECRET):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://openapi.naver.com/v1/search/news.json"
        self.headers = {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret
        }
        # 검색 키워드 목록
        self.keywords = [
            "SaarGummi",
            "자르구미",
            "SaarGummi 고무",
            "SaarGummi 자동차",
            "SaarGummi sealing",
            "Saar Gummi",
            "사르구미",
            "SaarGummi rubber",
            "SaarGummi automotive",
            "SaarGummi auto parts",
            "SaarGummi sealing systems"
        ]
    
    def _clean_html(self, text: str) -> str:
        """HTML 태그 제거"""
        if not text:
            return ""
        # HTML 태그 제거
        text = re.sub(r'<[^>]+>', '', text)
        # HTML 엔티티 디코딩
        text = text.replace("&lt;", "<").replace("&gt;", ">")
        text = text.replace("&amp;", "&").replace("&quot;", '"')
        text = text.replace("&#39;", "'")
        text = text.replace("&nbsp;", " ")
        return text.strip()
    
    def _is_mostly_english(self, text: str) -> bool:
        """텍스트가 주로 영어인지 판단"""
        if not text:
            return False
        # 한글이 포함되어 있으면 영어가 아님
        if re.search(r'[가-힣]', text):
            return False
        # 영문자, 숫자, 공백, 기본 구두점이 주를 이루는지 확인
        english_chars = len(re.findall(r'[a-zA-Z0-9\s.,!?;:\-()\[\]{}"\']', text))
        total_chars = len(re.sub(r'\s', '', text))
        if total_chars == 0:
            return False
        return (english_chars / total_chars) > 0.7
    
    def _translate_to_korean(self, text: str) -> Optional[str]:
        """영어 텍스트를 한국어로 번역"""
        if not text or not TRANSLATOR_AVAILABLE or not translator:
            return None
        
        try:
            # 텍스트가 너무 길면 잘라서 번역
            max_length = 5000
            if len(text) > max_length:
                text = text[:max_length]
            
            result = translator.translate(text, src='en', dest='ko')
            if result and result.text:
                return result.text
        except Exception as e:
            print(f"    [번역 오류] {str(e)}")
            return None
        
        return None
    
    def _extract_source(self, item: Dict) -> str:
        """출처 정보 추출"""
        # 1. API에서 제공하는 source 필드 확인 (네이버 뉴스 API에는 source 필드가 없을 수 있음)
        source = item.get("source", "")
        if source:
            # HTML 태그 제거
            source = self._clean_html(source)
            if source and source.strip():
                return source.strip()
        
        # 2. 링크에서 도메인 추출
        # originallink가 있으면 우선 사용, 없으면 link 사용
        link = item.get("originallink", "") or item.get("link", "")
        if link:
            try:
                parsed_url = urlparse(link)
                domain = parsed_url.netloc
                
                # 네이버 뉴스인 경우
                if "news.naver.com" in domain or "n.news.naver.com" in domain:
                    # 네이버 뉴스 링크에서 언론사 코드 추출
                    # 형식 1: https://n.news.naver.com/mnews/article/001/0011234567
                    # 형식 2: https://news.naver.com/main/read.naver?oid=001&aid=0001234567
                    press_code = None
                    
                    # URL 경로에서 추출 (형식 1)
                    path_match = re.search(r'/article/(\d{3})/', link)
                    if path_match:
                        press_code = path_match.group(1)
                    
                    # URL 파라미터에서 추출 (형식 2)
                    if not press_code:
                        param_match = re.search(r'[?&]oid=(\d{3})', link)
                        if param_match:
                            press_code = param_match.group(1)
                    
                    # 언론사 코드 매핑
                    if press_code:
                        press_codes = {
                            "001": "연합뉴스", "002": "연합뉴스", "003": "뉴시스",
                            "005": "국민일보", "008": "머니투데이", "009": "한국경제",
                            "011": "서울경제", "014": "파이낸셜뉴스", "015": "한국경제TV",
                            "016": "아시아경제", "018": "이데일리", "020": "동아일보",
                            "021": "문화일보", "022": "세계일보", "023": "조선일보",
                            "024": "중앙일보", "025": "한겨레", "028": "매일경제",
                            "029": "디지털타임스", "030": "전자신문", "031": "아이뉴스24",
                            "032": "헤럴드경제", "033": "조선비즈", "034": "비즈워치",
                            "036": "서울신문", "037": "KBS", "038": "MBC",
                            "044": "SBS", "052": "JTBC", "055": "YTN",
                            "056": "채널A", "057": "TV조선", "079": "노컷뉴스",
                            "081": "오마이뉴스", "082": "프레시안", "277": "아시아투데이",
                            "421": "뉴스1", "422": "뉴스1", "437": "이투데이",
                            "584": "스포츠조선", "586": "스포츠한국", "629": "스포츠동아"
                        }
                        press_name = press_codes.get(press_code)
                        if press_name:
                            return press_name
                    
                    # 언론사 코드를 찾지 못한 경우
                    return "네이버 뉴스"
                
                # 도메인에서 www 제거
                domain = domain.replace("www.", "")
                
                # 일반적인 언론사 도메인 매핑
                domain_mapping = {
                    "chosun.com": "조선일보",
                    "joongang.co.kr": "중앙일보",
                    "donga.com": "동아일보",
                    "hani.co.kr": "한겨레",
                    "khan.co.kr": "경향신문",
                    "mk.co.kr": "매일경제",
                    "hankyung.com": "한국경제",
                    "etoday.co.kr": "이데일리",
                    "yna.co.kr": "연합뉴스",
                    "yna.kr": "연합뉴스",
                    "news1.kr": "뉴스1",
                    "newsis.com": "뉴시스",
                    "ytn.co.kr": "YTN",
                    "sbs.co.kr": "SBS",
                    "kbs.co.kr": "KBS",
                    "mbc.co.kr": "MBC",
                    "jtbc.co.kr": "JTBC",
                    "chosunbiz.com": "조선비즈",
                    "bizwatch.co.kr": "비즈워치",
                    "edaily.co.kr": "이데일리",
                    "fnnews.com": "파이낸셜뉴스",
                    "asiae.co.kr": "아시아경제",
                    "seoul.co.kr": "서울신문",
                    "munhwa.com": "문화일보",
                    "segye.com": "세계일보",
                    "kukinews.com": "국민일보",
                    "heraldcorp.com": "헤럴드경제",
                    "inews24.com": "아이뉴스24",
                    "news.mt.co.kr": "머니투데이",
                    "mt.co.kr": "머니투데이",
                    "zdnet.co.kr": "ZDNet Korea",
                    "it.chosun.com": "IT조선",
                    "it.donga.com": "IT동아",
                }
                
                # 도메인 매핑 확인
                for key, value in domain_mapping.items():
                    if key in domain:
                        return value
                
                # 매핑이 없으면 도메인 이름 반환
                domain = domain.replace('www.', '')
                domain_parts = domain.split(".")
                
                if len(domain_parts) >= 2:
                    # 최상위 도메인 제거 (.com, .kr, .co.kr 등)
                    if domain_parts[-1] in ['kr', 'com', 'net', 'org']:
                        if len(domain_parts) >= 2:
                            domain_name = domain_parts[-2]
                        else:
                            domain_name = domain_parts[0]
                    elif domain_parts[-1] in ['co', 'go', 'ac'] and len(domain_parts) >= 3:
                        # .co.kr, .go.kr, .ac.kr 등
                        domain_name = domain_parts[-3]
                    else:
                        domain_name = domain_parts[0] if domain_parts[0] != 'www' else domain_parts[1] if len(domain_parts) > 1 else domain
                    
                    if domain_name:
                        # 첫 글자 대문자로 변환
                        return domain_name.capitalize()
                
                return domain
                
            except Exception as e:
                print(f"출처 추출 오류 ({link}): {str(e)}")
                import traceback
                traceback.print_exc()
        
        return "출처 없음"
    
    def _generate_id(self, url: str) -> str:
        """URL로부터 고유 ID 생성"""
        return hashlib.md5(url.encode()).hexdigest()
    
    def search_news(self, query: str, display: int = 100) -> List[Dict]:
        """뉴스 검색"""
        all_articles = []
        start = 1
        max_results = min(display, 1000)  # 최대 1000개
        
        while start <= max_results:
            params = {
                "query": query,
                "display": min(100, max_results - start + 1),
                "start": start,
                "sort": "date"  # 날짜순 정렬
            }
            
            try:
                response = requests.get(
                    self.base_url,
                    headers=self.headers,
                    params=params,
                    timeout=30,
                    verify=False
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
                    title = self._clean_html(item.get("title", ""))
                    description = self._clean_html(item.get("description", ""))
                    # 제목에만 키워드가 포함되어 있는지 확인 (필터링 강화)
                    title_lower = title.lower()
                    desc_lower = description.lower()
                    text_combined = title_lower + " " + desc_lower
                    
                    # 제목 또는 설명에 회사 이름이 포함되어야 함 (영문 기사 지원)
                    has_company = any(keyword.lower() in title_lower or keyword.lower() in desc_lower for keyword in self.keywords)
                    if not has_company:
                        continue
                    
                    # 고무/자동차 부품 관련 키워드가 포함되어야 함
                    rubber_keywords = [
                        "고무", "rubber", "타이어", "tire", "tyre",
                        "씰링", "sealing", "자동차 부품", "automotive parts", "auto parts",
                        "방진", "vibration", "NVH", "부품", "parts",
                        "오토모티브", "automotive", "자동차", "automobile", "vehicle"
                    ]
                    has_rubber = any(rubber_kw.lower() in text_combined for rubber_kw in rubber_keywords)
                    if not has_rubber:
                        continue
                    
                    if True:  # 위 조건을 모두 통과한 경우
                        # 출처 정보 추출
                        source = self._extract_source(item)
                        
                        # 디버깅: 출처가 "출처 없음"인 경우 로그 출력
                        if source == "출처 없음":
                            link = item.get("originallink", "") or item.get("link", "")
                            print(f"  [경고] 출처를 찾을 수 없음 - 링크: {link[:80]}")
                        
                        # 번역 추가 (영어인 경우)
                        title_translated = None
                        description_translated = None
                        if self._is_mostly_english(title):
                            title_translated = self._translate_to_korean(title)
                        if description and self._is_mostly_english(description):
                            description_translated = self._translate_to_korean(description)
                        
                        article = {
                            "title": title,
                            "title_translated": title_translated,
                            "link": item.get("link", ""),
                            "description": description,
                            "description_translated": description_translated,
                            "pub_date": item.get("pubDate", ""),
                            "source": source,
                            "article_id": self._generate_id(item.get("link", "")),
                            "search_keyword": query,
                            "source_type": "naver"
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
    
    
    def search_google_news(self, query: str, max_results: int = 50) -> List[Dict]:
        """구글 뉴스 검색 (RSS 피드 사용)"""
        all_articles = []
        
        try:
            # 구글 뉴스 RSS 피드 URL (여러 언어/지역 시도)
            encoded_query = quote(query)
            
            # 한국어 및 영어 뉴스 검색 (모두 시도)
            rss_urls = [
                (f"https://news.google.com/rss/search?q={encoded_query}&hl=ko&gl=KR&ceid=KR:ko", "ko"),
                (f"https://news.google.com/rss/search?q={encoded_query}&hl=en&gl=US&ceid=US:en", "en"),
                (f"https://news.google.com/rss/search?q={encoded_query}&hl=en&gl=GB&ceid=GB:en", "en"),
                (f"https://news.google.com/rss/search?q={encoded_query}&hl=ko&gl=KR&ceid=KR:ko&when=7d", "ko")  # 최근 7일
            ]
            
            all_feeds = []
            for rss_url, lang in rss_urls:
                try:
                    print(f"    [구글 뉴스] 검색 URL ({lang}): {rss_url}")
                    
                    # requests를 사용하여 RSS 피드 가져오기 (SSL 검증 비활성화)
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                    }
                    response = requests.get(rss_url, headers=headers, timeout=30, verify=False)
                    response.raise_for_status()
                    
                    print(f"    [구글 뉴스] HTTP 상태 코드: {response.status_code}")
                    print(f"    [구글 뉴스] 응답 크기: {len(response.content)} bytes")
                    
                    # RSS 피드 파싱
                    feed = feedparser.parse(response.content)
                    
                    if feed.bozo and feed.bozo_exception:
                        print(f"    [구글 뉴스 RSS 오류] {str(feed.bozo_exception)}")
                        continue
                    
                    print(f"    [구글 뉴스] 피드 엔트리 수: {len(feed.entries)}")
                    
                    if len(feed.entries) > 0:
                        all_feeds.append((feed, lang))
                except Exception as e:
                    print(f"    [구글 뉴스 URL 시도 실패] {str(e)}")
                    continue
            
            # 모든 피드에서 기사 수집
            if not all_feeds:
                return all_articles
            
            matched_count = 0
            seen_entry_ids = set()  # 중복 제거용
            
            # 모든 피드의 엔트리를 순회
            for feed, lang in all_feeds:
                for entry in feed.entries[:max_results]:
                    try:
                        title = self._clean_html(entry.get("title", ""))
                        link = entry.get("link", "")
                        description = self._clean_html(entry.get("description", ""))
                        
                        if not title:
                            continue
                        
                        # 제목에만 키워드가 포함되어 있는지 확인 (필터링 강화)
                        title_lower = title.lower()
                        desc_lower = description.lower()
                        text_combined = title_lower + " " + desc_lower
                        
                        # 제목 또는 설명에 회사 이름이 포함되어야 함 (영문 기사 지원)
                        has_company = any(keyword.lower() in title_lower or keyword.lower() in desc_lower for keyword in self.keywords)
                        if not has_company:
                            continue
                        
                        # 고무/자동차 부품 관련 키워드가 포함되어야 함
                        rubber_keywords = [
                            "고무", "rubber", "타이어", "tire", "tyre",
                            "씰링", "sealing", "자동차 부품", "automotive parts", "auto parts",
                            "방진", "vibration", "NVH", "부품", "parts",
                            "오토모티브", "automotive", "자동차", "automobile", "vehicle"
                        ]
                        has_rubber = any(rubber_kw.lower() in text_combined for rubber_kw in rubber_keywords)
                        if not has_rubber:
                            continue
                        
                        if True:  # 위 조건을 모두 통과한 경우
                            # 중복 체크
                            article_id = self._generate_id(link)
                            if article_id in seen_entry_ids:
                                continue
                            seen_entry_ids.add(article_id)
                            
                            matched_count += 1
                            # 출처 정보 추출
                            source = entry.get("source", {}).get("title", "") if hasattr(entry, "source") else ""
                            if not source:
                                # 링크에서 도메인 추출
                                source = self._extract_source_from_url(link)
                            
                            # 날짜 파싱
                            pub_date = ""
                            if hasattr(entry, "published_parsed") and entry.published_parsed:
                                pub_date = datetime(*entry.published_parsed[:6]).strftime('%Y-%m-%d %H:%M:%S')
                            elif hasattr(entry, "published"):
                                pub_date = entry.published
                            
                            # 설명 추출
                            if not description:
                                if hasattr(entry, "summary"):
                                    description = self._clean_html(entry.summary)
                                elif hasattr(entry, "description"):
                                    description = self._clean_html(entry.description)
                            
                            # 번역 추가 (영어인 경우)
                            title_translated = None
                            description_translated = None
                            if self._is_mostly_english(title):
                                title_translated = self._translate_to_korean(title)
                            if description and self._is_mostly_english(description):
                                description_translated = self._translate_to_korean(description)
                            
                            article = {
                                "title": title,
                                "title_translated": title_translated,
                                "link": link,
                                "description": description,
                                "description_translated": description_translated,
                                "pub_date": pub_date,
                                "source": source,
                                "article_id": article_id,
                                "search_keyword": query,
                                "source_type": "google"
                            }
                            all_articles.append(article)
                    except Exception as e:
                        print(f"    [구글 뉴스 기사 파싱 오류] {str(e)}")
                        import traceback
                        traceback.print_exc()
                        continue
            
            total_entries = sum(len(feed.entries) for feed, _ in all_feeds)
            print(f"    [구글 뉴스] 키워드 매칭된 기사 수: {matched_count}/{total_entries}")
                    
        except requests.exceptions.Timeout:
            print(f"    [구글 뉴스 검색 타임아웃] 30초 초과")
        except requests.exceptions.RequestException as e:
            print(f"    [구글 뉴스 검색 네트워크 오류] {str(e)}")
            import traceback
            traceback.print_exc()
        except Exception as e:
            print(f"    [구글 뉴스 검색 오류] {str(e)}")
            import traceback
            traceback.print_exc()
        
        return all_articles
    
    def _get_google_api_quota_file(self) -> Path:
        """구글 API 쿼리 사용량 파일 경로 반환"""
        return Path(__file__).parent.parent / "google_api_quota.json"
    
    def _load_google_api_quota(self) -> Dict:
        """구글 API 쿼리 사용량 로드"""
        quota_file = self._get_google_api_quota_file()
        if quota_file.exists():
            try:
                with open(quota_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {"date": get_kst_now().strftime('%Y-%m-%d'), "count": 0}
    
    def _save_google_api_quota(self, quota_data: Dict):
        """구글 API 쿼리 사용량 저장"""
        quota_file = self._get_google_api_quota_file()
        with open(quota_file, 'w', encoding='utf-8') as f:
            json.dump(quota_data, f, ensure_ascii=False, indent=2)
    
    def _check_google_api_quota(self) -> bool:
        """구글 API 무료 한도 체크 (하루 100개)"""
        quota_data = self._load_google_api_quota()
        today = get_kst_now().strftime('%Y-%m-%d')
        
        # 날짜가 바뀌면 카운트 리셋
        if quota_data.get("date") != today:
            quota_data = {"date": today, "count": 0}
            self._save_google_api_quota(quota_data)
        
        # 하루 100개 제한
        if quota_data.get("count", 0) >= 100:
            print(f"    [구글 일반 검색] 무료 한도 초과 (하루 100개 제한)")
            return False
        
        return True
    
    def _increment_google_api_quota(self):
        """구글 API 쿼리 사용량 증가"""
        quota_data = self._load_google_api_quota()
        quota_data["count"] = quota_data.get("count", 0) + 1
        self._save_google_api_quota(quota_data)
        print(f"    [구글 API 쿼리 사용량] {quota_data['count']}/100")
    
    def search_google_web(self, query: str, max_results: int = 50) -> List[Dict]:
        """구글 일반 웹 검색 (Custom Search JSON API 사용, 무료 한도 내에서만)"""
        all_articles = []
        
        # 무료 한도 체크
        if not self._check_google_api_quota():
            return all_articles
        
        # 구글 Custom Search API 설정
        GOOGLE_API_KEY = "AIzaSyCkGs04ZxXkyufmr1AGQKHxcyRcEql3S7o"
        GOOGLE_CSE_ID = "b4ecadd96e4154846"
        
        try:
            print(f"    [구글 일반 검색] 검색어: {query}")
            
            search_url = "https://www.googleapis.com/customsearch/v1"
            
            params = {
                'key': GOOGLE_API_KEY,
                'cx': GOOGLE_CSE_ID,
                'q': query,
                'num': min(max_results, 10),
                'lr': 'lang_en|lang_ko',
                'safe': 'active'
            }
            
            matched_count = 0
            seen_entry_ids = set()
            start_index = 1
            total_fetched = 0
            
            while total_fetched < max_results:
                if not self._check_google_api_quota():
                    print(f"    [구글 일반 검색] 무료 한도 도달, 검색 중단")
                    break
                
                params['start'] = start_index
                
                response = requests.get(search_url, params=params, timeout=30, verify=False)
                response.raise_for_status()
                
                self._increment_google_api_quota()
                
                data = response.json()
                
                items = data.get('items', [])
                if not items:
                    break
                
                for item in items:
                    try:
                        title = self._clean_html(item.get('title', ''))
                        link = item.get('link', '')
                        description = self._clean_html(item.get('snippet', ''))
                        
                        if not title or not link:
                            continue
                        
                        title_lower = title.lower()
                        desc_lower = description.lower()
                        text_combined = title_lower + " " + desc_lower
                        
                        has_company = any(keyword.lower() in title_lower or keyword.lower() in desc_lower for keyword in self.keywords)
                        if not has_company:
                            continue
                        
                        rubber_keywords = [
                            "고무", "rubber", "타이어", "tire", "tyre",
                            "씰링", "sealing", "자동차 부품", "automotive parts", "auto parts",
                            "방진", "vibration", "NVH", "부품", "parts",
                            "오토모티브", "automotive", "자동차", "automobile", "vehicle",
                            "component", "supplier", "manufacturing", "production", "factory"
                        ]
                        has_rubber = any(rubber_kw.lower() in text_combined for rubber_kw in rubber_keywords)
                        
                        # 고무 키워드가 필수로 포함되어야 함
                        if not has_rubber:
                            continue
                        
                        article_id = self._generate_id(link)
                        if article_id in seen_entry_ids:
                            continue
                        seen_entry_ids.add(article_id)
                        
                        matched_count += 1
                        total_fetched += 1
                        
                        source = self._extract_source_from_url(link)
                        
                        pub_date = get_kst_now().strftime('%Y-%m-%d %H:%M:%S')
                        if 'pagemap' in item and 'metatags' in item['pagemap']:
                            for meta in item['pagemap']['metatags']:
                                if 'article:published_time' in meta:
                                    pub_date = meta['article:published_time']
                                    break
                        
                        # 번역 추가 (영어인 경우)
                        title_translated = None
                        description_translated = None
                        if self._is_mostly_english(title):
                            title_translated = self._translate_to_korean(title)
                        if description and self._is_mostly_english(description):
                            description_translated = self._translate_to_korean(description)
                        
                        article = {
                            "title": title,
                            "title_translated": title_translated,
                            "link": link,
                            "description": description,
                            "description_translated": description_translated,
                            "pub_date": pub_date,
                            "source": source,
                            "article_id": article_id,
                            "search_keyword": query,
                            "source_type": "google_web"
                        }
                        all_articles.append(article)
                        
                        if total_fetched >= max_results:
                            break
                            
                    except Exception as e:
                        print(f"    [구글 일반 검색 기사 파싱 오류] {str(e)}")
                        continue
                
                if 'queries' in data and 'nextPage' in data['queries']:
                    start_index += 10
                else:
                    break
                
                time.sleep(1)
            
            print(f"    [구글 일반 검색] 키워드 매칭된 기사 수: {matched_count}/{total_fetched}")
                    
        except requests.exceptions.Timeout:
            print(f"    [구글 일반 검색 타임아웃] 30초 초과")
        except requests.exceptions.RequestException as e:
            print(f"    [구글 일반 검색 네트워크 오류] {str(e)}")
        except Exception as e:
            print(f"    [구글 일반 검색 오류] {str(e)}")
            import traceback
            traceback.print_exc()
        
        return all_articles
    
    def _extract_source_from_url(self, url: str) -> str:
        """URL에서 출처 정보 추출 (구글 뉴스용)"""
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
            
            # 구글 뉴스 리다이렉트 URL 처리
            if "news.google.com" in domain:
                # URL 파라미터에서 실제 링크 추출
                if "url=" in url:
                    import urllib.parse
                    params = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
                    if "url" in params:
                        actual_url = params["url"][0]
                        parsed_actual = urlparse(actual_url)
                        domain = parsed_actual.netloc
            
            # 도메인에서 www 제거
            domain = domain.replace("www.", "")
            
            # 일반적인 언론사 도메인 매핑
            domain_mapping = {
                "chosun.com": "조선일보",
                "joongang.co.kr": "중앙일보",
                "donga.com": "동아일보",
                "hani.co.kr": "한겨레",
                "khan.co.kr": "경향신문",
                "mk.co.kr": "매일경제",
                "hankyung.com": "한국경제",
                "etoday.co.kr": "이데일리",
                "yna.co.kr": "연합뉴스",
                "yna.kr": "연합뉴스",
                "news1.kr": "뉴스1",
                "newsis.com": "뉴시스",
                "ytn.co.kr": "YTN",
                "sbs.co.kr": "SBS",
                "kbs.co.kr": "KBS",
                "mbc.co.kr": "MBC",
                "jtbc.co.kr": "JTBC",
            }
            
            for key, value in domain_mapping.items():
                if key in domain:
                    return value
            
            # 매핑이 없으면 도메인 이름 반환
            domain_parts = domain.split(".")
            if len(domain_parts) >= 2:
                domain_name = domain_parts[-2] if domain_parts[-1] in ['kr', 'com', 'net', 'org'] else domain_parts[0]
                return domain_name.capitalize() if domain_name else domain
            
            return domain
        except:
            return "출처 없음"
    

    def crawl_all_news(self) -> List[Dict]:
        """모든 키워드로 뉴스 크롤링 (네이버 + 구글)"""
        all_articles = []
        seen_ids = set()
        
        print(f"[크롤링 시작] {get_kst_now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        for keyword in self.keywords:
            print(f"  - 네이버 뉴스 검색 중: {keyword}")
            articles = self.search_news(keyword, display=100)
            
            for article in articles:
                article_id = article["article_id"]
                if article_id not in seen_ids:
                    seen_ids.add(article_id)
                    article["source_type"] = "naver"
                    all_articles.append(article)
            
            print(f"  - 구글 뉴스 검색 중: {keyword}")
            google_articles = self.search_google_news(keyword, max_results=100)  # max_results 증가
            
            for article in google_articles:
                article_id = article["article_id"]
                if article_id not in seen_ids:
                    seen_ids.add(article_id)
                    all_articles.append(article)
        
        # 구글 일반 검색은 기본 기업 이름(첫 번째 키워드)만 사용
        if self.keywords:
            base_keyword = self.keywords[0]
            print(f"  - 구글 일반 검색 중: {base_keyword}")
            google_web_articles = self.search_google_web(base_keyword, max_results=50)
            
            for article in google_web_articles:
                article_id = article["article_id"]
                if article_id not in seen_ids:
                    seen_ids.add(article_id)
                    all_articles.append(article)
        
        # 날짜순 정렬 (최신순)
        all_articles.sort(key=lambda x: x.get("pub_date", ""), reverse=True)
        
        print(f"[크롤링 완료] 총 {len(all_articles)}개의 기사 발견 (네이버 + 구글)")
        
        return all_articles
    
    def save_to_json(self, articles: List[Dict], filepath: str = "data.json"):
        """크롤링된 데이터를 JSON 파일로 저장"""
        data = {
            "last_updated": get_kst_now().strftime('%Y-%m-%d %H:%M:%S'),
            "total_count": len(articles),
            "articles": articles
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"[저장 완료] {filepath}에 {len(articles)}개의 기사 저장")
    
    def load_from_json(self, filepath: str = "data.json") -> Dict:
        """JSON 파일에서 데이터 로드"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {"last_updated": "", "total_count": 0, "articles": []}
        except Exception as e:
            print(f"데이터 로드 오류: {str(e)}")
            return {"last_updated": "", "total_count": 0, "articles": []}
    
    def get_full_article(self, url: str) -> Optional[Dict]:
        """기사 URL에서 전체 내용 가져오기"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30, verify=False)
            response.raise_for_status()
            
            # 인코딩 확인
            if response.encoding is None or response.encoding == 'ISO-8859-1':
                response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 네이버 뉴스 기사 본문 추출
            article_content = None
            source_name = None
            
            # 네이버 뉴스인 경우 언론사 정보 추출
            if "news.naver.com" in url or "n.news.naver.com" in url:
                # 네이버 뉴스 언론사 정보 추출
                press_selectors = [
                    '.press_logo img[alt]',
                    '.press_logo a',
                    '.media_end_head_top a',
                    '.media_end_head_top .press_logo',
                    '._press_logo',
                    '.media_end_head_top_logo img[alt]'
                ]
                
                for selector in press_selectors:
                    press_elem = soup.select_one(selector)
                    if press_elem:
                        source_name = press_elem.get('alt', '') or press_elem.get_text(strip=True)
                        if source_name:
                            break
                
                # 언론사 이름이 없으면 다른 방법 시도
                if not source_name:
                    # 링크에서 언론사 코드 추출 시도
                    match = re.search(r'sid=(\d+)', url)
                    if match:
                        # 언론사 코드 매핑 (주요 언론사)
                        press_codes = {
                            "001": "연합뉴스", "002": "연합뉴스", "003": "뉴시스",
                            "005": "국민일보", "008": "머니투데이", "009": "한국경제",
                            "011": "서울경제", "014": "파이낸셜뉴스", "015": "한국경제TV",
                            "016": "아시아경제", "018": "이데일리", "020": "동아일보",
                            "021": "문화일보", "022": "세계일보", "023": "조선일보",
                            "024": "중앙일보", "025": "한겨레", "028": "매일경제",
                            "029": "디지털타임스", "030": "전자신문", "031": "아이뉴스24",
                            "032": "헤럴드경제", "033": "조선비즈", "034": "비즈워치",
                            "036": "서울신문", "037": "KBS", "038": "MBC",
                            "044": "SBS", "052": "JTBC", "055": "YTN",
                            "056": "채널A", "057": "TV조선", "079": "노컷뉴스",
                            "081": "오마이뉴스", "082": "프레시안", "277": "아시아투데이",
                            "421": "뉴스1", "422": "뉴스1", "437": "이투데이",
                            "584": "스포츠조선", "586": "스포츠한국", "629": "스포츠동아"
                        }
                        press_code = match.group(1)
                        source_name = press_codes.get(press_code, None)
            
            # 네이버 뉴스 본문 선택자들
            selectors = [
                '#articleBodyContents',
                '.article_body',
                '#articleBody',
                '.article_view',
                '.news_end_body',
                '#newsEndContents'
            ]
            
            for selector in selectors:
                article_content = soup.select_one(selector)
                if article_content:
                    break
            
            # 일반 뉴스 사이트용
            if not article_content:
                article_content = soup.find('article') or soup.find('main') or soup.find('div', class_=re.compile('content|body|article', re.I))
            
            if article_content:
                # 스크립트 태그 제거
                for script in article_content.find_all(['script', 'style', 'iframe']):
                    script.decompose()
                
                # 텍스트 추출 및 정리
                text = article_content.get_text(separator='\n', strip=True)
                text = re.sub(r'\n{3,}', '\n\n', text)  # 연속된 줄바꿈 정리
                text = text.strip()
                
                result = {
                    "success": True,
                    "content": text,
                    "url": url
                }
                
                # 언론사 정보가 있으면 추가
                if source_name:
                    result["source"] = source_name
                
                return result
            else:
                # 본문을 찾지 못한 경우 description 반환
                return {
                    "success": False,
                    "content": "기사 본문을 가져올 수 없습니다. 원본 링크를 확인해주세요.",
                    "url": url
                }
                
        except Exception as e:
            print(f"기사 내용 가져오기 오류 ({url}): {str(e)}")
            return {
                "success": False,
                "content": f"기사 내용을 가져오는 중 오류가 발생했습니다: {str(e)}",
                "url": url
            }

if __name__ == "__main__":
    # 테스트
    crawler = SaarGummiNewsCrawler()
    articles = crawler.crawl_all_news()
    crawler.save_to_json(articles, "data.json")
    
    print(f"\n=== 크롤링 결과 ===")
    print(f"총 {len(articles)}개의 기사")
    for i, article in enumerate(articles[:5], 1):
        print(f"\n{i}. {article['title']}")
        print(f"   링크: {article['link']}")
        print(f"   날짜: {article['pub_date']}")

