#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
자동 업데이트 스크립트 - 변경사항 감지 및 실시간 업데이트
"""

import json
import os
import time
from datetime import datetime
from main import update_report
from data_manager import DataManager
from report_generator import ReportGenerator

def check_for_changes(old_data: dict, new_data: dict) -> dict:
    """데이터 변경사항 감지"""
    changes = {
        "new_disclosures": [],
        "new_news": [],
        "updated_financial": False,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # 새로운 공시 확인
    old_disclosure_ids = {d.get("rcept_no") for d in old_data.get("recent_disclosures", [])}
    new_disclosures = [d for d in new_data.get("recent_disclosures", []) 
                      if d.get("rcept_no") not in old_disclosure_ids]
    if new_disclosures:
        changes["new_disclosures"] = new_disclosures
        changes["has_changes"] = True
    
    # 새로운 뉴스 확인
    old_news_ids = {a.get("article_id") for a in old_data.get("news_articles", [])}
    new_news = [a for a in new_data.get("news_articles", []) 
               if a.get("article_id") not in old_news_ids]
    if new_news:
        changes["new_news"] = new_news[:10]  # 최근 10개만
        changes["has_changes"] = True
    
    # 재무 데이터 업데이트 확인
    old_years = set(old_data.get("financial_data", {}).keys())
    new_years = set(new_data.get("financial_data", {}).keys())
    if new_years != old_years:
        changes["updated_financial"] = True
        changes["has_changes"] = True
    
    return changes

def auto_update_with_monitoring(interval: int = 3600, check_interval: int = 300):
    """자동 업데이트 및 변경사항 모니터링"""
    print("=" * 60)
    print("화승알앤에이 실시간 모니터링 시작")
    print(f"업데이트 간격: {interval}초 ({interval//60}분)")
    print(f"변경사항 확인 간격: {check_interval}초 ({check_interval//60}분)")
    print("=" * 60)
    
    data_manager = DataManager()
    last_update_time = None
    
    try:
        while True:
            current_time = datetime.now()
            
            # 주기적 업데이트 또는 변경사항 감지 시 업데이트
            should_update = False
            
            if last_update_time is None:
                should_update = True
                print(f"\n[{current_time.strftime('%Y-%m-%d %H:%M:%S')}] 초기 업데이트 실행")
            else:
                time_since_update = (current_time - last_update_time).total_seconds()
                if time_since_update >= interval:
                    should_update = True
                    print(f"\n[{current_time.strftime('%Y-%m-%d %H:%M:%S')}] 주기적 업데이트 실행")
            
            if should_update:
                # 기존 데이터 백업
                old_data = data_manager.get_data().copy()
                
                # 업데이트 실행
                update_report("화승알앤에이", "378850")
                
                # 새 데이터 로드
                new_data = data_manager.get_data()
                
                # 변경사항 확인
                changes = check_for_changes(old_data, new_data)
                
                if changes.get("has_changes"):
                    print(f"\n[변경사항 감지]")
                    if changes.get("new_disclosures"):
                        print(f"  - 새로운 공시: {len(changes['new_disclosures'])}개")
                        for disc in changes['new_disclosures'][:3]:
                            print(f"    • {disc.get('report_nm', 'N/A')} ({disc.get('rcept_dt', 'N/A')})")
                    
                    if changes.get("new_news"):
                        print(f"  - 새로운 뉴스: {len(changes['new_news'])}개")
                        for news in changes['new_news'][:3]:
                            print(f"    • {news.get('title', 'N/A')[:50]}...")
                    
                    if changes.get("updated_financial"):
                        print(f"  - 재무 데이터 업데이트됨")
                    
                    # HTML 보고서 재생성
                    print("\n[HTML 보고서 재생성 중...]")
                    generator = ReportGenerator()
                    generator.generate_report(new_data, "hwasung_rna_report.html")
                    print("[OK] HTML 보고서 업데이트 완료")
                else:
                    print("[정보] 변경사항 없음")
                
                last_update_time = current_time
            
            # 대기
            print(f"\n다음 확인까지 {check_interval}초 대기 중... (Ctrl+C로 종료)")
            time.sleep(check_interval)
            
    except KeyboardInterrupt:
        print("\n\n모니터링을 종료합니다.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="화승알앤에이 실시간 모니터링")
    parser.add_argument("--interval", "-i", type=int, default=3600, help="전체 업데이트 간격(초)")
    parser.add_argument("--check", "-c", type=int, default=300, help="변경사항 확인 간격(초)")
    args = parser.parse_args()
    
    auto_update_with_monitoring(args.interval, args.check)

