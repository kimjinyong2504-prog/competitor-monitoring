#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
기존 data.json 파일에 번역 추가 스크립트
"""

import json
import sys
import os
import importlib.util
from pathlib import Path

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def load_crawler_class(folder_name, class_name):
    """크롤러 클래스를 동적으로 로드"""
    module_path = Path(folder_name) / "crawler.py"
    spec = importlib.util.spec_from_file_location(f"{folder_name}.crawler", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, class_name)

def add_translations_to_data(folder: str, crawler_class):
    """기존 data.json에 번역 추가"""
    data_file = Path(folder) / "data.json"
    
    if not data_file.exists():
        print(f"[건너뛰기] {folder}/data.json 파일이 없습니다.")
        return
    
    print(f"\n[처리 중] {folder}/data.json")
    
    # 데이터 로드
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    articles = data.get("articles", [])
    if not articles:
        print(f"[건너뛰기] {folder}에 기사가 없습니다.")
        return
    
    # 크롤러 인스턴스 생성
    crawler = crawler_class()
    
    updated_count = 0
    for i, article in enumerate(articles):
        title = article.get("title", "")
        description = article.get("description", "")
        
        # 번역이 이미 있으면 건너뛰기
        if article.get("title_translated") or article.get("description_translated"):
            continue
        
        # 제목 번역
        if title and crawler._is_mostly_english(title):
            translated_title = crawler._translate_to_korean(title)
            if translated_title:
                article["title_translated"] = translated_title
                updated_count += 1
                print(f"  [{i+1}/{len(articles)}] 제목 번역 추가: {title[:50]}...")
        
        # 설명 번역
        if description and crawler._is_mostly_english(description):
            translated_desc = crawler._translate_to_korean(description)
            if translated_desc:
                article["description_translated"] = translated_desc
                updated_count += 1
                print(f"  [{i+1}/{len(articles)}] 설명 번역 추가")
        
        # 진행 상황 표시
        if (i + 1) % 10 == 0:
            print(f"  진행: {i+1}/{len(articles)}")
    
    # 데이터 저장
    if updated_count > 0:
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[완료] {folder}: {updated_count}개의 번역 추가됨")
    else:
        print(f"[완료] {folder}: 번역할 항목이 없거나 이미 번역이 있습니다.")

def main():
    """메인 함수"""
    print("="*60)
    print("기존 데이터에 번역 추가")
    print("="*60)
    
    # 각 업체별 처리
    companies = [
        ("251215_cooper", "CooperStandardNewsCrawler"),
        ("251215_saargummi", "SaarGummiNewsCrawler"),
        ("251215_hutchinson", "HutchinsonNewsCrawler")
    ]
    
    for folder, class_name in companies:
        try:
            crawler_class = load_crawler_class(folder, class_name)
            add_translations_to_data(folder, crawler_class)
        except Exception as e:
            print(f"[오류] {folder} 처리 중 오류: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print("\n[완료] 모든 작업이 완료되었습니다.")

if __name__ == "__main__":
    main()
