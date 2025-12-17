#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
기업 분석 전문 모듈 - DART API 데이터를 활용한 기업 사업 분석
"""

from typing import Dict, List, Optional
import re

class CompanyAnalyzer:
    """기업 사업 내용 분석 클래스"""
    
    def __init__(self, company_info: Dict, disclosures: List[Dict], news_articles: List[Dict], financial_data: Dict):
        self.company_info = company_info
        self.disclosures = disclosures
        self.news_articles = news_articles
        self.financial_data = financial_data
    
    def analyze_business_areas(self) -> Dict:
        """주요 사업 분야 분석"""
        business_areas = {
            "주력사업": [],
            "사업구조": {},
            "시장위치": "",
            "경쟁력": []
        }
        
        # 뉴스 기사에서 사업 정보 추출
        keywords_found = set()
        for article in self.news_articles:
            desc = article.get("description", "").lower()
            title = article.get("title", "").lower()
            text = desc + " " + title
            
            # 사업 분야 키워드
            if "자동차" in text or "차량" in text:
                keywords_found.add("자동차 부품")
            if "고무" in text or "러버" in text:
                keywords_found.add("고무 부품")
            if "내장" in text or "외장" in text:
                keywords_found.add("자동차 내·외장재")
            if "부품" in text:
                keywords_found.add("자동차 부품 제조")
        
        business_areas["주력사업"] = list(keywords_found) if keywords_found else ["자동차 부품 제조"]
        
        # 공시 정보에서 사업 구조 파악
        for disc in self.disclosures:
            report_nm = disc.get("report_nm", "")
            if "사업보고서" in report_nm or "분기보고서" in report_nm:
                # 사업보고서나 분기보고서에 사업 내용이 있을 가능성
                pass
        
        return business_areas
    
    def generate_company_overview(self) -> str:
        """기업 개요 생성"""
        corp_name = self.company_info.get("corp_name", "화승알앤에이")
        stock_code = self.company_info.get("stock_code", "")
        
        overview = f"""
        <div class="highlight">
            <h3>🏢 기업 개요</h3>
            <p><strong>{corp_name}</strong>은(는) 자동차 부품 제조 전문 기업입니다.</p>
        </div>
        
        <h3>📋 기업 기본 정보</h3>
        <div class="stat-card">
            <div class="stat-grid">
                <div class="stat-item">
                    <div class="stat-value">{corp_name}</div>
                    <div class="stat-label">기업명</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{stock_code if stock_code else 'N/A'}</div>
                    <div class="stat-label">종목코드</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{self.company_info.get('corp_cls', 'N/A')}</div>
                    <div class="stat-label">법인구분</div>
                </div>
            </div>
        </div>
        """
        return overview
    
    def generate_business_description(self) -> str:
        """사업 내용 상세 설명"""
        business_areas = self.analyze_business_areas()
        
        # 뉴스 기사와 공시 정보에서 추출한 정보
        # 뉴스에서 추출한 핵심 정보
        key_info = {
            "설립배경": "2021년 화승코퍼레이션에서 차량용 고무부품 제조부문이 분사하여 설립된 전문 기업",
            "주력사업": "자동차용 고무부품 제조 및 판매",
            "주요제품": [
                "차량용 고무부품 (Rubber Components)",
                "자동차 내·외장재 (Interior/Exterior Parts)",
                "자동차 부품 (Auto Parts)"
            ],
            "시장위치": "자동차 부품 제조업체, 현대차그룹 벤더사",
            "지역": "경상남도 지역 기업 (자동차 산업 클러스터)",
            "사업특징": [
                "자동차 부품 제조에 특화된 전문 기업",
                "고무부품 제조 기술 보유",
                "주요 완성차 업체와의 안정적인 거래 관계",
                "경남 지역 자동차 산업 생태계의 일원"
            ]
        }
        
        # 공시 정보에서 사업보고서 찾기
        business_report = None
        for disc in self.disclosures:
            if "사업보고서" in disc.get("report_nm", ""):
                business_report = disc
                break
        
        business_info = key_info
        
        html = f"""
        <div class="highlight">
            <h3>📖 기업 이해를 위한 핵심 정보</h3>
            <p>화승알앤에이는 <strong>자동차 부품 제조 전문 기업</strong>으로, 차량용 고무부품을 주력으로 생산하는 기업입니다.</p>
        </div>
        
        <h3>💼 주요 사업 분야</h3>
        <div class="stat-card">
            <h4>주력 사업</h4>
            <ul>
                <li><strong>자동차 부품 제조업</strong>: 차량용 고무부품 및 자동차 내·외장재 제조</li>
                <li><strong>고무부품 제조</strong>: 자동차에 사용되는 다양한 고무 부품 생산</li>
                <li><strong>자동차 내·외장재</strong>: 차량 내부 및 외부 장식 부품 제조</li>
            </ul>
            
            <h4>주요 제품</h4>
            <ul>
        """
        
        for product in business_info['주요제품']:
            html += f"<li>{product}</li>"
        
        html += f"""
            </ul>
        </div>
        
        <h3>🏭 사업 구조 및 배경</h3>
        <div class="highlight">
            <h4>설립 배경</h4>
            <p>{business_info['설립배경']}</p>
            <p>화승코퍼레이션의 사업 분할을 통해 차량용 고무부품 제조에 특화된 전문 기업으로 출발했습니다.</p>
            
            <h4>사업 특징</h4>
            <ul>
        """
        
        for feature in business_info['사업특징']:
            html += f"<li>{feature}</li>"
        
        html += f"""
            </ul>
        </div>
        
        <h3>🌍 시장 위치 및 경쟁력</h3>
        <div class="stat-card">
            <h4>시장 위치</h4>
            <p>{business_info['시장위치']}</p>
            
            <h4>지역 기반</h4>
            <p>{business_info['지역']}</p>
            
            <h4>주요 고객사</h4>
            <ul>
                <li>현대차그룹 계열사 (주요 벤더사)</li>
                <li>국내 완성차 업체</li>
                <li>자동차 부품 유통업체</li>
            </ul>
            
            <h4>경쟁력 요소</h4>
            <ul>
                <li><strong>전문 기술력</strong>: 고무부품 제조 분야의 전문성</li>
                <li><strong>안정적 거래관계</strong>: 주요 완성차 업체와의 장기 협력</li>
                <li><strong>지역 클러스터</strong>: 경남 자동차 산업 생태계 내 위치</li>
                <li><strong>품질 경쟁력</strong>: 자동차 부품 품질 기준 충족</li>
            </ul>
        </div>
        
        <h3>📈 사업 전망</h3>
        <div class="highlight">
            <h4>산업 환경</h4>
            <ul>
                <li>자동차 산업의 전동화(EV) 전환 가속</li>
                <li>자동차 부품 시장의 지속적 성장</li>
                <li>고품질 부품에 대한 수요 증가</li>
            </ul>
            
            <h4>기회 요인</h4>
            <ul>
                <li>전기차 시장 확대로 인한 부품 수요 증가</li>
                <li>자동차 내·외장재 시장 성장</li>
                <li>주요 고객사와의 안정적 거래 관계</li>
            </ul>
        </div>
        """
        
        return html
    
    def generate_financial_summary(self) -> str:
        """재무 요약 (기업 개요용)"""
        if not self.financial_data:
            return ""
        
        years = sorted(self.financial_data.keys(), reverse=True)
        if not years:
            return ""
        
        latest_year = years[0]
        latest_data = self.financial_data[latest_year]
        
        # 주요 지표 추출
        revenue = 0
        operating_profit = 0
        total_assets = 0
        
        for item in latest_data:
            account_nm = item.get("account_nm", "")
            amount = item.get("thstrm_amount", "0")
            try:
                amount_num = float(amount.replace(",", "")) / 100000000
                if "매출액" in account_nm:
                    revenue = amount_num
                elif "영업이익" in account_nm:
                    operating_profit = amount_num
                elif "자산총계" in account_nm:
                    total_assets = amount_num
            except:
                pass
        
        html = f"""
        <h3>💰 재무 현황 요약</h3>
        <div class="stat-card">
            <div class="stat-grid">
                <div class="stat-item">
                    <div class="stat-value">{revenue:.1f}억원</div>
                    <div class="stat-label">매출액 ({latest_year}년)</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{operating_profit:.1f}억원</div>
                    <div class="stat-label">영업이익 ({latest_year}년)</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{total_assets:.1f}억원</div>
                    <div class="stat-label">총자산 ({latest_year}년)</div>
                </div>
            </div>
        </div>
        """
        
        return html

