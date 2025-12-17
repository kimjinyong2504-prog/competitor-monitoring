#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
데이터 저장 및 관리 모듈
"""

import json
import os
from datetime import datetime
from typing import Dict, List

DATA_FILE = "hwasung_rna_data.json"

class DataManager:
    """기업 데이터를 저장하고 관리하는 클래스"""
    
    def __init__(self, data_file: str = DATA_FILE):
        self.data_file = data_file
        self.data = self.load_data()
    
    def load_data(self) -> Dict:
        """저장된 데이터 로드"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"데이터 로드 오류: {str(e)}")
                return self._init_data()
        return self._init_data()
    
    def _init_data(self) -> Dict:
        """초기 데이터 구조 생성"""
        return {
            "company_name": "화승알앤에이",
            "company_info": {},
            "financial_data": {},
            "employee_info": {},
            "recent_disclosures": [],
            "news_articles": [],
            "finance_info": {},
            "update_history": [],
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "last_updated": None
        }
    
    def save_data(self, data: Dict = None):
        """데이터 저장"""
        if data:
            self.data.update(data)
        
        # 초기 데이터 구조 확인
        if "update_history" not in self.data:
            self.data["update_history"] = []
        
        self.data["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 업데이트 히스토리 추가
        update_record = {
            "timestamp": self.data["last_updated"],
            "type": "full_update" if data else "manual_update"
        }
        self.data["update_history"].append(update_record)
        
        # 최근 100개만 유지
        if len(self.data["update_history"]) > 100:
            self.data["update_history"] = self.data["update_history"][-100:]
        
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            print(f"데이터 저장 완료: {self.data_file}")
        except Exception as e:
            print(f"데이터 저장 오류: {str(e)}")
    
    def update_company_info(self, company_info: Dict):
        """기업 정보 업데이트"""
        self.data["company_info"] = company_info
        self.save_data()
    
    def update_financial_data(self, financial_data: Dict):
        """재무 데이터 업데이트"""
        # 기존 데이터와 병합
        if "financial_data" not in self.data:
            self.data["financial_data"] = {}
        
        for year, data in financial_data.items():
            self.data["financial_data"][year] = data
        
        self.save_data()
    
    def update_employee_info(self, employee_info: Dict):
        """직원 정보 업데이트"""
        self.data["employee_info"] = employee_info
        self.save_data()
    
    def update_disclosures(self, disclosures: List[Dict]):
        """공시 정보 업데이트 (중복 제거)"""
        if "recent_disclosures" not in self.data:
            self.data["recent_disclosures"] = []
        
        existing_ids = {d.get("rcept_no") for d in self.data["recent_disclosures"]}
        
        for disclosure in disclosures:
            if disclosure.get("rcept_no") not in existing_ids:
                self.data["recent_disclosures"].append(disclosure)
        
        # 날짜순 정렬 (최신순)
        self.data["recent_disclosures"].sort(
            key=lambda x: x.get("rcept_dt", ""), 
            reverse=True
        )
        
        # 최근 50개만 유지
        self.data["recent_disclosures"] = self.data["recent_disclosures"][:50]
        
        self.save_data()
    
    def update_news_articles(self, articles: List[Dict]):
        """뉴스 기사 업데이트 (중복 제거)"""
        if "news_articles" not in self.data:
            self.data["news_articles"] = []
        
        existing_ids = {a.get("article_id") for a in self.data["news_articles"]}
        
        for article in articles:
            if article.get("article_id") not in existing_ids:
                self.data["news_articles"].append(article)
        
        # 날짜순 정렬 (최신순)
        self.data["news_articles"].sort(
            key=lambda x: x.get("pub_date", ""), 
            reverse=True
        )
        
        # 최근 100개만 유지
        self.data["news_articles"] = self.data["news_articles"][:100]
        
        self.save_data()
    
    def get_data(self) -> Dict:
        """전체 데이터 반환"""
        return self.data
    
    def update_finance_info(self, finance_info: Dict):
        """금융 정보 업데이트"""
        self.data["finance_info"] = finance_info
        self.save_data()
    
    def merge_dart_data(self, dart_data: Dict):
        """DART 데이터 병합"""
        if "company_info" in dart_data:
            self.update_company_info(dart_data["company_info"])
        
        if "financial_data" in dart_data:
            self.update_financial_data(dart_data["financial_data"])
        
        if "employee_info" in dart_data:
            self.update_employee_info(dart_data["employee_info"])
        
        if "recent_disclosures" in dart_data:
            self.update_disclosures(dart_data["recent_disclosures"])

if __name__ == "__main__":
    # 테스트
    manager = DataManager()
    test_data = {
        "company_info": {"corp_name": "화승R&A", "test": True}
    }
    manager.merge_dart_data(test_data)
    print("테스트 데이터 저장 완료")

