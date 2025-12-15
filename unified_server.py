#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
통합 뉴스 모니터링 서버 - 모든 경쟁사 통합 관리
"""

import os
import sys
import time
import json
import http.server
import socketserver
import threading
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from datetime import datetime

# 각 업체별 크롤러 import (독립적으로 로드)
import importlib.util

# 화승 알엔에이
spec_hwasung_crawler = importlib.util.spec_from_file_location(
    "crawler_hwasung", 
    Path(__file__).parent / "251215" / "crawler.py"
)
crawler_hwasung_module = importlib.util.module_from_spec(spec_hwasung_crawler)
spec_hwasung_crawler.loader.exec_module(crawler_hwasung_module)
HwasungNewsCrawler = crawler_hwasung_module.HwasungNewsCrawler

# 유일고무
spec_yuil_crawler = importlib.util.spec_from_file_location(
    "crawler_yuil", 
    Path(__file__).parent / "251215_yuil" / "crawler.py"
)
crawler_yuil_module = importlib.util.module_from_spec(spec_yuil_crawler)
spec_yuil_crawler.loader.exec_module(crawler_yuil_module)
YuilNewsCrawler = crawler_yuil_module.YuilNewsCrawler

# AIA
spec_aia_crawler = importlib.util.spec_from_file_location(
    "crawler_aia", 
    Path(__file__).parent / "251215_aia" / "crawler.py"
)
crawler_aia_module = importlib.util.module_from_spec(spec_aia_crawler)
spec_aia_crawler.loader.exec_module(crawler_aia_module)
AIANewsCrawler = crawler_aia_module.AIANewsCrawler

# 스케줄러는 직접 구현 (import 충돌 방지)
class UnifiedNewsScheduler:
    """통합 뉴스 스케줄러"""
    
    def __init__(self, crawler, interval_seconds: int = 3600, company_name: str = ""):
        self.interval = interval_seconds
        self.crawler = crawler
        self.running = False
        self.thread = None
        self.company_name = company_name
    
    def update_news(self):
        """뉴스 업데이트 실행"""
        try:
            print(f"\n{'='*60}")
            print(f"[{self.company_name} 자동 업데이트] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*60}")
            
            # 크롤링 실행
            new_crawled_articles = self.crawler.crawl_all_news()
            
            # 삭제된 기사 ID 목록 로드
            deleted_ids = load_deleted_articles(self.company_name)
            if deleted_ids:
                print(f"[{self.company_name} 삭제된 기사 필터링] {len(deleted_ids)}개의 삭제된 기사 ID 제외")
            
            # 기존 데이터 로드
            data_file = get_data_file_path(self.company_name)
            existing_data = self.crawler.load_from_json(data_file)
            existing_articles = existing_data.get("articles", [])
            existing_ids = {article["article_id"] for article in existing_articles}
            
            # 새로운 기사만 추가 (기존에 없고, 삭제된 목록에도 없는 기사만)
            new_articles = [
                article for article in new_crawled_articles 
                if article["article_id"] not in existing_ids and article["article_id"] not in deleted_ids
            ]
            
            # 기존 기사와 새 기사 병합
            all_articles = existing_articles + new_articles
            
            # 날짜순 정렬 (최신순)
            def parse_date(date_str):
                """날짜 문자열을 파싱하여 정렬 가능한 형식으로 변환"""
                if not date_str:
                    return "0000-00-00 00:00:00"
                try:
                    if len(date_str) >= 19 and date_str[4] == '-':
                        return date_str[:19]
                    dt = datetime.strptime(date_str[:25], "%a, %d %b %Y %H:%M:%S")
                    return dt.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    return date_str[:19] if len(date_str) >= 19 else date_str
            
            all_articles.sort(key=lambda x: parse_date(x.get("pub_date", "")), reverse=True)
            
            # 모든 기사 저장
            self.crawler.save_to_json(all_articles, data_file)
            
            if new_articles:
                print(f"[새로운 기사] {len(new_articles)}개의 새로운 기사 발견")
            else:
                print(f"[새로운 기사] 새로운 기사 없음")
            
            print(f"[업데이트 완료] 총 {len(all_articles)}개의 기사")
            print(f"{'='*60}\n")
            
        except Exception as e:
            print(f"[오류] {self.company_name} 업데이트 중 오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def start(self):
        """스케줄러 시작"""
        if self.running:
            print(f"{self.company_name} 스케줄러가 이미 실행 중입니다.")
            return
        
        self.running = True
        
        # 즉시 한 번 실행
        self.update_news()
        
        # 백그라운드 스레드에서 주기적으로 실행
        def run_scheduler():
            while self.running:
                time.sleep(self.interval)
                if self.running:
                    self.update_news()
        
        self.thread = threading.Thread(target=run_scheduler, daemon=True)
        self.thread.start()
        
        print(f"{self.company_name} 스케줄러가 시작되었습니다. 업데이트 간격: {self.interval}초 ({self.interval//60}분)")
    
    def stop(self):
        """스케줄러 중지"""
        self.running = False
        print(f"\n{self.company_name} 스케줄러를 중지합니다...")

# 현재 디렉토리를 기준으로 작업
BASE_DIR = Path(__file__).parent
os.chdir(BASE_DIR)

# 각 업체별 크롤러 인스턴스
crawlers = {
    "hwasung": None,
    "yuil": None,
    "aia": None
}

# 각 업체별 스케줄러 인스턴스
schedulers = {
    "hwasung": None,
    "yuil": None,
    "aia": None
}

def get_crawler(company: str):
    """업체별 크롤러 인스턴스 가져오기"""
    if company == "hwasung":
        if crawlers["hwasung"] is None:
            crawlers["hwasung"] = HwasungNewsCrawler()
        return crawlers["hwasung"]
    elif company == "yuil":
        if crawlers["yuil"] is None:
            crawlers["yuil"] = YuilNewsCrawler()
        return crawlers["yuil"]
    elif company == "aia":
        if crawlers["aia"] is None:
            crawlers["aia"] = AIANewsCrawler()
        return crawlers["aia"]
    return None

def update_news_now(company: str):
    """즉시 뉴스 업데이트 실행"""
    crawler = get_crawler(company)
    if crawler is None:
        return {
            "success": False,
            "error": f"알 수 없는 업체: {company}"
        }
    
    try:
        print(f"\n[{company} 수동 업데이트 요청] {time.strftime('%Y-%m-%d %H:%M:%S')}")
        new_crawled_articles = crawler.crawl_all_news()
        
        # 삭제된 기사 ID 목록 로드
        deleted_ids = load_deleted_articles(company)
        print(f"[{company} 삭제된 기사 필터링] {len(deleted_ids)}개의 삭제된 기사 ID 제외")
        
        # 기존 데이터 로드
        data_file = f"{get_data_file_path(company)}"
        existing_data = crawler.load_from_json(data_file)
        existing_articles = existing_data.get("articles", [])
        existing_ids = {article["article_id"] for article in existing_articles}
        
        # 새로운 기사만 확인 (기존에 없고, 삭제된 목록에도 없는 기사만)
        new_articles = [
            article for article in new_crawled_articles 
            if article["article_id"] not in existing_ids and article["article_id"] not in deleted_ids
        ]
        
        # 기존 기사와 새 기사 병합
        all_articles = existing_articles + new_articles
        
        # 날짜순 정렬 (최신순)
        def parse_date(date_str):
            """날짜 문자열을 파싱하여 정렬 가능한 형식으로 변환"""
            if not date_str:
                return "0000-00-00 00:00:00"
            try:
                if len(date_str) >= 19 and date_str[4] == '-':
                    return date_str[:19]
                from datetime import datetime
                dt = datetime.strptime(date_str[:25], "%a, %d %b %Y %H:%M:%S")
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                return date_str[:19] if len(date_str) >= 19 else date_str
        
        all_articles.sort(key=lambda x: parse_date(x.get("pub_date", "")), reverse=True)
        
        # 모든 기사 저장
        crawler.save_to_json(all_articles, data_file)
        
        result = {
            "success": True,
            "total_count": len(all_articles),
            "new_count": len(new_articles),
            "last_updated": time.strftime('%Y-%m-%d %H:%M:%S')
        }
        print(f"[{company} 수동 업데이트 완료] 총 {len(all_articles)}개, 신규 {len(new_articles)}개")
        return result
    except Exception as e:
        print(f"[{company} 수동 업데이트 오류] {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e)
        }

def get_data_file_path(company: str) -> str:
    """업체별 데이터 파일 경로 반환"""
    if company == "hwasung":
        return "251215/data.json"
    elif company == "yuil":
        return "251215_yuil/data.json"
    elif company == "aia":
        return "251215_aia/data.json"
    return "data.json"

def get_deleted_articles_file_path(company: str) -> str:
    """업체별 삭제된 기사 파일 경로 반환"""
    if company == "hwasung":
        return "251215/deleted_articles.json"
    elif company == "yuil":
        return "251215_yuil/deleted_articles.json"
    elif company == "aia":
        return "251215_aia/deleted_articles.json"
    return "deleted_articles.json"

def load_deleted_articles(company: str) -> set:
    """삭제된 기사 ID 목록 로드"""
    deleted_file = get_deleted_articles_file_path(company)
    try:
        with open(deleted_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return set(data.get("deleted_ids", []))
    except FileNotFoundError:
        return set()
    except Exception as e:
        print(f"[{company} 삭제된 기사 로드 오류] {str(e)}")
        return set()

def save_deleted_article(company: str, article_id: str):
    """삭제된 기사 ID 저장"""
    deleted_file = get_deleted_articles_file_path(company)
    deleted_ids = load_deleted_articles(company)
    deleted_ids.add(article_id)
    
    data = {
        "deleted_ids": list(deleted_ids),
        "last_updated": time.strftime('%Y-%m-%d %H:%M:%S')
    }
    
    try:
        with open(deleted_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[{company} 삭제된 기사 저장] article_id: {article_id} (총 {len(deleted_ids)}개)")
    except Exception as e:
        print(f"[{company} 삭제된 기사 저장 오류] {str(e)}")

def delete_article(company: str, article_id: str):
    """기사 삭제"""
    try:
        crawler = get_crawler(company)
        if crawler is None:
            return {
                "success": False,
                "error": f"알 수 없는 업체: {company}"
            }
        
        data_file = get_data_file_path(company)
        existing_data = crawler.load_from_json(data_file)
        existing_articles = existing_data.get("articles", [])
        
        # 삭제할 기사 제외
        filtered_articles = [article for article in existing_articles if article.get("article_id") != article_id]
        
        if len(filtered_articles) == len(existing_articles):
            return {
                "success": False,
                "error": "기사를 찾을 수 없습니다."
            }
        
        # 삭제된 기사 저장
        crawler.save_to_json(filtered_articles, data_file)
        
        # 삭제된 기사 ID를 별도 파일에 저장 (재크롤링 방지)
        save_deleted_article(company, article_id)
        
        print(f"[{company} 기사 삭제] article_id: {article_id}")
        
        return {
            "success": True,
            "message": "기사가 삭제되었습니다.",
            "remaining_count": len(filtered_articles)
        }
    except Exception as e:
        print(f"[{company} 기사 삭제 오류] {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e)
        }

class UnifiedHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """통합 HTTP 핸들러"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.getcwd(), **kwargs)
    
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()
    
    def do_POST(self):
        """POST 요청 처리 (API 엔드포인트)"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path.startswith('/api/update/'):
            # 뉴스 업데이트 API: /api/update/{company}
            company = path.split('/')[-1]
            result = update_news_now(company)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            
            response_json = json.dumps(result, ensure_ascii=False)
            self.wfile.write(response_json.encode('utf-8'))
        elif path.startswith('/api/delete/'):
            # 기사 삭제 API: /api/delete/{company}
            company = path.split('/')[-1]
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                article_id = data.get('article_id', '')
                
                if article_id:
                    result = delete_article(company, article_id)
                    
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json; charset=utf-8')
                    self.end_headers()
                    
                    response_json = json.dumps(result, ensure_ascii=False)
                    self.wfile.write(response_json.encode('utf-8'))
                else:
                    self.send_response(400)
                    self.end_headers()
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                error_response = json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)
                self.wfile.write(error_response.encode('utf-8'))
            
        elif path.startswith('/api/article/'):
            # 기사 전체 내용 가져오기 API: /api/article/{company}
            company = path.split('/')[-1]
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                url = data.get('url', '')
                
                if url:
                    crawler = get_crawler(company)
                    if crawler:
                        article_content = crawler.get_full_article(url)
                        
                        self.send_response(200)
                        self.send_header('Content-Type', 'application/json; charset=utf-8')
                        self.end_headers()
                        
                        response_json = json.dumps(article_content, ensure_ascii=False)
                        self.wfile.write(response_json.encode('utf-8'))
                    else:
                        self.send_response(400)
                        self.end_headers()
                else:
                    self.send_response(400)
                    self.end_headers()
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                error_response = json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)
                self.wfile.write(error_response.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_GET(self):
        """GET 요청 처리 (정적 파일 서빙)"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        # 루트 경로를 메인 대시보드로 리다이렉트
        if path == '/' or path == '':
            self.path = '/competitor-monitoring.html'
        
        # 각 업체별 index.html 경로 매핑
        elif path == '/hwasung' or path == '/hwasung/':
            self.path = '/251215/index.html'
        elif path == '/yuil' or path == '/yuil/':
            self.path = '/251215_yuil/index.html'
        elif path == '/aia' or path == '/aia/':
            self.path = '/251215_aia/index.html'
        
        # 정적 파일 서빙
        try:
            super().do_GET()
        except Exception as e:
            print(f"파일 서빙 오류: {str(e)}")
            self.send_error(404, "File not found")

def start_web_server(port=None):
    """웹 서버 시작"""
    handler = UnifiedHTTPRequestHandler
    
    # Render나 다른 클라우드 플랫폼에서 PORT 환경 변수 사용
    if port is None:
        port = int(os.environ.get('PORT', 8000))
    
    # 포트가 사용 중이면 다른 포트 시도 (로컬 환경에서만)
    for attempt in range(10):
        try:
            httpd = socketserver.TCPServer(("", port), handler)
            print(f"통합 웹 서버가 시작되었습니다: http://localhost:{port}")
            print(f"메인 페이지: http://localhost:{port}/competitor-monitoring.html")
            print(f"화승 R&A: http://localhost:{port}/hwasung")
            print(f"유일고무: http://localhost:{port}/yuil")
            print(f"AIA(아이아): http://localhost:{port}/aia")
            print()
            
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("\n웹 서버를 종료합니다...")
                httpd.shutdown()
            break
        except OSError as e:
            # Windows 환경에서만 winerror 체크
            if hasattr(e, 'winerror') and e.winerror == 10048:  # 포트가 이미 사용 중
                print(f"포트 {port}가 사용 중입니다. 포트 {port + 1}을 시도합니다...")
                port += 1
            elif 'Address already in use' in str(e) or 'already in use' in str(e).lower():
                print(f"포트 {port}가 사용 중입니다. 포트 {port + 1}을 시도합니다...")
                port += 1
            else:
                raise
    else:
        print(f"사용 가능한 포트를 찾을 수 없습니다. (시도한 포트: {port-10}-{port-1})")

def main():
    """메인 함수"""
    print("="*60)
    print("통합 경쟁사 뉴스 모니터링 시스템")
    print("="*60)
    print()
    
    # 각 업체별 크롤러 초기화
    print("[초기화] 각 업체별 크롤러 초기화 중...")
    crawlers["hwasung"] = HwasungNewsCrawler()
    crawlers["yuil"] = YuilNewsCrawler()
    crawlers["aia"] = AIANewsCrawler()
    print("[초기화] 완료\n")
    
    # 각 업체별 초기 데이터 파일 확인 및 생성
    companies = {
        "hwasung": ("251215", HwasungNewsCrawler),
        "yuil": ("251215_yuil", YuilNewsCrawler),
        "aia": ("251215_aia", AIANewsCrawler)
    }
    
    for company_name, (folder, CrawlerClass) in companies.items():
        data_file = f"{folder}/data.json"
        if not os.path.exists(data_file):
            print(f"[초기화] {company_name} 데이터 파일이 없습니다. 초기 크롤링을 시작합니다...")
            crawler = get_crawler(company_name)
            articles = crawler.crawl_all_news()
            crawler.save_to_json(articles, data_file)
            print(f"[초기화] {company_name} 초기 크롤링 완료\n")
    
    # 각 업체별 스케줄러 시작 (1시간 = 3600초)
    print("[스케줄러 시작] 각 업체별 자동 업데이트 스케줄러를 시작합니다...")
    
    # 화승 알엔에이 스케줄러
    schedulers["hwasung"] = UnifiedNewsScheduler(crawlers["hwasung"], interval_seconds=3600, company_name="화승 알엔에이")
    schedulers["hwasung"].start()
    
    # 유일고무 스케줄러
    schedulers["yuil"] = UnifiedNewsScheduler(crawlers["yuil"], interval_seconds=3600, company_name="유일고무")
    schedulers["yuil"].start()
    
    # AIA 스케줄러
    schedulers["aia"] = UnifiedNewsScheduler(crawlers["aia"], interval_seconds=3600, company_name="AIA(아이아)")
    schedulers["aia"].start()
    
    print()
    
    print()
    
    # 웹 서버 시작 (별도 스레드)
    server_thread = threading.Thread(target=start_web_server, daemon=True)
    server_thread.start()
    
    try:
        # 메인 스레드가 종료되지 않도록 대기
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n프로그램을 종료합니다...")
        for scheduler in schedulers.values():
            if scheduler:
                scheduler.stop()
        sys.exit(0)

if __name__ == "__main__":
    main()

