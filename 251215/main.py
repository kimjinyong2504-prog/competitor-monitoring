#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
화승R&A 뉴스 크롤링 및 자동 업데이트 메인 스크립트
"""

import os
import sys
import time
import json
import http.server
import socketserver
import threading
from pathlib import Path
from urllib.parse import urlparse
from scheduler import NewsScheduler
from crawler import HwasungNewsCrawler

# 현재 디렉토리를 기준으로 작업
BASE_DIR = Path(__file__).parent
os.chdir(BASE_DIR)

# 크롤러 인스턴스 (전역 변수)
crawler_instance = None

def update_news_now():
    """즉시 뉴스 업데이트 실행"""
    global crawler_instance
    if crawler_instance is None:
        crawler_instance = HwasungNewsCrawler()
    
    try:
        print(f"\n[수동 업데이트 요청] {time.strftime('%Y-%m-%d %H:%M:%S')}")
        new_crawled_articles = crawler_instance.crawl_all_news()
        
        # 기존 데이터 로드
        existing_data = crawler_instance.load_from_json("data.json")
        existing_articles = existing_data.get("articles", [])
        existing_ids = {article["article_id"] for article in existing_articles}
        
        # 새로운 기사만 확인
        new_articles = [article for article in new_crawled_articles if article["article_id"] not in existing_ids]
        
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
        crawler_instance.save_to_json(all_articles, "data.json")
        
        result = {
            "success": True,
            "total_count": len(all_articles),
            "new_count": len(new_articles),
            "last_updated": time.strftime('%Y-%m-%d %H:%M:%S')
        }
        print(f"[수동 업데이트 완료] 총 {len(all_articles)}개, 신규 {len(new_articles)}개")
        return result
    except Exception as e:
        print(f"[수동 업데이트 오류] {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e)
        }

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """CORS를 지원하는 커스텀 HTTP 핸들러"""
    
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
        
        if parsed_path.path == '/api/update':
            # 뉴스 업데이트 API
            result = update_news_now()
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            
            response_json = json.dumps(result, ensure_ascii=False)
            self.wfile.write(response_json.encode('utf-8'))
        elif parsed_path.path == '/api/article':
            # 기사 전체 내용 가져오기 API
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                url = data.get('url', '')
                
                if url:
                    global crawler_instance
                    if crawler_instance is None:
                        crawler_instance = HwasungNewsCrawler()
                    
                    article_content = crawler_instance.get_full_article(url)
                    
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json; charset=utf-8')
                    self.end_headers()
                    
                    response_json = json.dumps(article_content, ensure_ascii=False)
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
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_GET(self):
        """GET 요청 처리 (정적 파일 서빙)"""
        super().do_GET()

def start_web_server(port=8000):
    """웹 서버 시작"""
    handler = CustomHTTPRequestHandler
    
    # 포트가 사용 중이면 다른 포트 시도
    for attempt in range(10):
        try:
            httpd = socketserver.TCPServer(("", port), handler)
            print(f"웹 서버가 시작되었습니다: http://localhost:{port}")
            print(f"브라우저에서 http://localhost:{port}/index.html 을 열어주세요.\n")
            
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("\n웹 서버를 종료합니다...")
                httpd.shutdown()
            break
        except OSError as e:
            if e.winerror == 10048:  # 포트가 이미 사용 중
                print(f"포트 {port}가 사용 중입니다. 포트 {port + 1}을 시도합니다...")
                port += 1
            else:
                raise
    else:
        print(f"사용 가능한 포트를 찾을 수 없습니다. (8000-8009 시도)")

def main():
    """메인 함수"""
    global crawler_instance
    
    print("="*60)
    print("화승R&A 뉴스 크롤링 및 모니터링 시스템")
    print("="*60)
    print()
    
    # 크롤러 인스턴스 초기화
    crawler_instance = HwasungNewsCrawler()
    
    # 초기 데이터 파일이 없으면 생성
    if not os.path.exists("data.json"):
        print("[초기화] 데이터 파일이 없습니다. 초기 크롤링을 시작합니다...")
        articles = crawler_instance.crawl_all_news()
        crawler_instance.save_to_json(articles, "data.json")
        print("[초기화] 초기 크롤링 완료\n")
    
    # 스케줄러 시작 (1시간 = 3600초)
    scheduler = NewsScheduler(interval_seconds=3600)
    scheduler.start()
    
    # 웹 서버 시작 (별도 스레드)
    server_thread = threading.Thread(target=start_web_server, daemon=True)
    server_thread.start()
    
    try:
        # 메인 스레드가 종료되지 않도록 대기
        while scheduler.running:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n프로그램을 종료합니다...")
        scheduler.stop()
        sys.exit(0)

if __name__ == "__main__":
    main()

