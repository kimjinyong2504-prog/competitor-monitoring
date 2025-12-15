#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
1시간 간격으로 자동 업데이트하는 스케줄러
"""

import time
import threading
from datetime import datetime
from crawler import HwasungNewsCrawler

class NewsScheduler:
    """뉴스 자동 업데이트 스케줄러"""
    
    def __init__(self, interval_seconds: int = 3600):
        self.interval = interval_seconds
        self.crawler = HwasungNewsCrawler()
        self.running = False
        self.thread = None
    
    def update_news(self):
        """뉴스 업데이트 실행"""
        try:
            print(f"\n{'='*60}")
            print(f"[자동 업데이트] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*60}")
            
            # 크롤링 실행
            new_crawled_articles = self.crawler.crawl_all_news()
            
            # 기존 데이터 로드
            existing_data = self.crawler.load_from_json("data.json")
            existing_articles = existing_data.get("articles", [])
            existing_ids = {article["article_id"] for article in existing_articles}
            
            # 새로운 기사만 추가
            new_articles = [article for article in new_crawled_articles if article["article_id"] not in existing_ids]
            
            # 기존 기사와 새 기사 병합
            all_articles = existing_articles + new_articles
            
            # 날짜순 정렬 (최신순 - pub_date가 큰 것이 위로)
            def parse_date(date_str):
                """날짜 문자열을 파싱하여 정렬 가능한 형식으로 변환"""
                if not date_str:
                    return "0000-00-00 00:00:00"
                # 네이버 뉴스 날짜 형식: "Mon, 01 Jan 2024 12:00:00 +0900" 또는 "2024-01-01 12:00:00"
                try:
                    # ISO 형식인 경우
                    if len(date_str) >= 19 and date_str[4] == '-':
                        return date_str[:19]
                    # RFC 형식인 경우
                    from datetime import datetime
                    dt = datetime.strptime(date_str[:25], "%a, %d %b %Y %H:%M:%S")
                    return dt.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    return date_str[:19] if len(date_str) >= 19 else date_str
            
            all_articles.sort(key=lambda x: parse_date(x.get("pub_date", "")), reverse=True)
            
            # 모든 기사 저장 (중복 제거)
            self.crawler.save_to_json(all_articles, "data.json")
            
            if new_articles:
                print(f"[새로운 기사] {len(new_articles)}개의 새로운 기사 발견")
            else:
                print(f"[새로운 기사] 새로운 기사 없음")
            
            print(f"[업데이트 완료] 총 {len(all_articles)}개의 기사")
            print(f"{'='*60}\n")
            
        except Exception as e:
            print(f"[오류] 업데이트 중 오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def start(self):
        """스케줄러 시작"""
        if self.running:
            print("스케줄러가 이미 실행 중입니다.")
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
        
        print(f"스케줄러가 시작되었습니다. 업데이트 간격: {self.interval}초 ({self.interval//60}분)")
        print("종료하려면 Ctrl+C를 누르세요.\n")
    
    def stop(self):
        """스케줄러 중지"""
        self.running = False
        print("\n스케줄러를 중지합니다...")

if __name__ == "__main__":
    # 1시간 = 3600초
    scheduler = NewsScheduler(interval_seconds=3600)
    
    try:
        scheduler.start()
        # 메인 스레드가 종료되지 않도록 대기
        while scheduler.running:
            time.sleep(1)
    except KeyboardInterrupt:
        scheduler.stop()
        print("프로그램을 종료합니다.")

