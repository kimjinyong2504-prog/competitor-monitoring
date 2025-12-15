#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
네이버 뉴스 API를 사용한 화승R&A 관련 기사 크롤러
"""

import requests
import json
import hashlib
import re
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import urlparse, quote, urlencode, quote, urlencode
import urllib3
from bs4 import BeautifulSoup
import feedparser

# SSL 경고 메시지 비활성화
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

NAVER_CLIENT_ID = "00q938ugMTSfuzjWuLk4"
NAVER_CLIENT_SECRET = "MrIG7TWaGW"

class HwasungNewsCrawler:
    """화승R&A 관련 뉴스 크롤러"""
    
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
            "화승",
            "화승R&A",
            "화승 RnA",
            "화승알엔에이",
            "화승알앤에이",
            "화승 R&A"
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
                    # 제목에 키워드가 포함되어 있는지 확인
                    if any(keyword.lower() in title.lower() for keyword in self.keywords):
                        # 출처 정보 추출
                        source = self._extract_source(item)
                        
                        # 디버깅: 출처가 "출처 없음"인 경우 로그 출력
                        if source == "출처 없음":
                            link = item.get("originallink", "") or item.get("link", "")
                            print(f"  [경고] 출처를 찾을 수 없음 - 링크: {link[:80]}")
                        
                        article = {
                            "title": title,
                            "link": item.get("link", ""),
                            "description": self._clean_html(item.get("description", "")),
                            "pub_date": item.get("pubDate", ""),
                            "source": source,
                            "article_id": self._generate_id(item.get("link", "")),
                            "search_keyword": query,
                            "source_type": "naver",
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
            # 구글 뉴스 RSS 피드 URL
            encoded_query = quote(query)
            rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=ko&gl=KR&ceid=KR:ko"
            
            print(f"    [구글 뉴스] 검색 URL: {rss_url}")
            
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
                return all_articles
            
            print(f"    [구글 뉴스] 피드 엔트리 수: {len(feed.entries)}")
            
            if len(feed.entries) == 0:
                print(f"    [구글 뉴스] 경고: 피드에 엔트리가 없습니다.")
                return all_articles
            
            matched_count = 0
            for entry in feed.entries[:max_results]:
                try:
                    title = self._clean_html(entry.get("title", ""))
                    link = entry.get("link", "")
                    
                    if not title:
                        continue
                    
                    # 제목에 키워드가 포함되어 있는지 확인
                    title_lower = title.lower()
                    if any(keyword.lower() in title_lower for keyword in self.keywords):
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
                        description = ""
                        if hasattr(entry, "summary"):
                            description = self._clean_html(entry.summary)
                        elif hasattr(entry, "description"):
                            description = self._clean_html(entry.description)
                        
                        article = {
                            "title": title,
                            "link": link,
                            "description": description,
                            "pub_date": pub_date,
                            "source": source,
                            "article_id": self._generate_id(link),
                            "search_keyword": query,
                            "source_type": "google"
                        }
                        all_articles.append(article)
                except Exception as e:
                    print(f"    [구글 뉴스 기사 파싱 오류] {str(e)}")
                    import traceback
                    traceback.print_exc()
                    continue
            
            print(f"    [구글 뉴스] 키워드 매칭된 기사 수: {matched_count}/{len(feed.entries[:max_results])}")
                    
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
        
        print(f"[크롤링 시작] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
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
            google_articles = self.search_google_news(keyword, max_results=50)
            
            for article in google_articles:
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
            "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
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
    crawler = HwasungNewsCrawler()
    articles = crawler.crawl_all_news()
    crawler.save_to_json(articles, "data.json")
    
    print(f"\n=== 크롤링 결과 ===")
    print(f"총 {len(articles)}개의 기사")
    for i, article in enumerate(articles[:5], 1):
        print(f"\n{i}. {article['title']}")
        print(f"   링크: {article['link']}")
        print(f"   날짜: {article['pub_date']}")

