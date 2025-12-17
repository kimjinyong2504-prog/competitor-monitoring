#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
재무 분석 전문 모듈 - DART API 데이터를 활용한 전문적인 재무 분석
"""

from typing import Dict, List, Optional
import json

class FinancialAnalyzer:
    """재무 데이터 전문 분석 클래스"""
    
    def __init__(self, financial_data: Dict):
        self.financial_data = financial_data
        self.years = sorted(financial_data.keys(), reverse=True) if financial_data else []
    
    def extract_value(self, year_data: List[Dict], account_name: str) -> float:
        """재무 데이터에서 특정 계정 값 추출 (숫자)"""
        for item in year_data:
            if account_name in item.get("account_nm", ""):
                amount = item.get("thstrm_amount", "0")
                try:
                    return float(amount.replace(",", "")) / 100000000  # 억원 단위
                except:
                    return 0.0
        return 0.0
    
    def calculate_growth_rate(self, current: float, previous: float) -> float:
        """성장률 계산"""
        if previous == 0:
            return 0.0
        return ((current - previous) / previous) * 100
    
    def analyze_financial_ratios(self) -> Dict:
        """재무 비율 분석"""
        ratios = {}
        
        for year in self.years:
            year_data = self.financial_data[year]
            year_ratios = {}
            
            # 기본 재무 지표
            revenue = self.extract_value(year_data, "매출액")
            operating_profit = self.extract_value(year_data, "영업이익")
            net_income = self.extract_value(year_data, "당기순이익")
            total_assets = self.extract_value(year_data, "자산총계")
            total_debt = self.extract_value(year_data, "부채총계")
            total_equity = self.extract_value(year_data, "자본총계")
            current_assets = self.extract_value(year_data, "유동자산")
            current_liabilities = self.extract_value(year_data, "유동부채")
            
            # 수익성 비율
            year_ratios['영업이익률'] = (operating_profit / revenue * 100) if revenue > 0 else 0
            year_ratios['순이익률'] = (net_income / revenue * 100) if revenue > 0 else 0
            year_ratios['ROA'] = (net_income / total_assets * 100) if total_assets > 0 else 0
            year_ratios['ROE'] = (net_income / total_equity * 100) if total_equity > 0 else 0
            
            # 안정성 비율
            year_ratios['부채비율'] = (total_debt / total_equity * 100) if total_equity > 0 else 0
            year_ratios['자기자본비율'] = (total_equity / total_assets * 100) if total_assets > 0 else 0
            year_ratios['유동비율'] = (current_assets / current_liabilities * 100) if current_liabilities > 0 else 0
            
            # 활동성 비율
            year_ratios['총자산회전율'] = (revenue / total_assets) if total_assets > 0 else 0
            
            ratios[year] = year_ratios
        
        return ratios
    
    def analyze_growth(self) -> Dict:
        """성장률 분석"""
        growth = {}
        
        for i, year in enumerate(self.years):
            year_data = self.financial_data[year]
            year_growth = {}
            
            revenue = self.extract_value(year_data, "매출액")
            operating_profit = self.extract_value(year_data, "영업이익")
            net_income = self.extract_value(year_data, "당기순이익")
            total_assets = self.extract_value(year_data, "자산총계")
            
            if i < len(self.years) - 1:
                prev_year = self.years[i + 1]
                prev_data = self.financial_data[prev_year]
                
                prev_revenue = self.extract_value(prev_data, "매출액")
                prev_op_profit = self.extract_value(prev_data, "영업이익")
                prev_net_income = self.extract_value(prev_data, "당기순이익")
                prev_assets = self.extract_value(prev_data, "자산총계")
                
                year_growth['매출성장률'] = self.calculate_growth_rate(revenue, prev_revenue)
                year_growth['영업이익성장률'] = self.calculate_growth_rate(operating_profit, prev_op_profit)
                year_growth['순이익성장률'] = self.calculate_growth_rate(net_income, prev_net_income)
                year_growth['자산성장률'] = self.calculate_growth_rate(total_assets, prev_assets)
            else:
                year_growth['매출성장률'] = 0
                year_growth['영업이익성장률'] = 0
                year_growth['순이익성장률'] = 0
                year_growth['자산성장률'] = 0
            
            growth[year] = year_growth
        
        return growth
    
    def analyze_financial_structure(self) -> Dict:
        """재무 구조 분석"""
        structure = {}
        
        for year in self.years:
            year_data = self.financial_data[year]
            year_structure = {}
            
            total_assets = self.extract_value(year_data, "자산총계")
            current_assets = self.extract_value(year_data, "유동자산")
            non_current_assets = self.extract_value(year_data, "비유동자산")
            total_debt = self.extract_value(year_data, "부채총계")
            current_debt = self.extract_value(year_data, "유동부채")
            non_current_debt = self.extract_value(year_data, "비유동부채")
            total_equity = self.extract_value(year_data, "자본총계")
            
            if total_assets > 0:
                year_structure['유동자산비율'] = (current_assets / total_assets * 100)
                year_structure['비유동자산비율'] = (non_current_assets / total_assets * 100)
                year_structure['부채비율'] = (total_debt / total_assets * 100)
                year_structure['자기자본비율'] = (total_equity / total_assets * 100)
                year_structure['유동부채비율'] = (current_debt / total_assets * 100)
                year_structure['비유동부채비율'] = (non_current_debt / total_assets * 100)
            
            structure[year] = year_structure
        
        return structure
    
    def generate_insights(self) -> List[str]:
        """재무 인사이트 생성"""
        insights = []
        
        if len(self.years) < 2:
            return ["분석을 위해서는 최소 2개 연도의 데이터가 필요합니다."]
        
        ratios = self.analyze_financial_ratios()
        growth = self.analyze_growth()
        
        latest_year = self.years[0]
        prev_year = self.years[1] if len(self.years) > 1 else None
        
        latest_ratios = ratios[latest_year]
        
        # 수익성 분석
        if latest_ratios['영업이익률'] > 5:
            insights.append(f"✅ 영업이익률 {latest_ratios['영업이익률']:.2f}%로 양호한 수익성을 보이고 있습니다.")
        elif latest_ratios['영업이익률'] > 0:
            insights.append(f"⚠️ 영업이익률 {latest_ratios['영업이익률']:.2f}%로 개선의 여지가 있습니다.")
        else:
            insights.append(f"❌ 영업이익률이 마이너스로 전환되어 주의가 필요합니다.")
        
        # 성장성 분석
        if prev_year and latest_year in growth:
            revenue_growth = growth[latest_year].get('매출성장률', 0)
            if revenue_growth > 10:
                insights.append(f"📈 매출 성장률 {revenue_growth:.1f}%로 강한 성장세를 보이고 있습니다.")
            elif revenue_growth > 0:
                insights.append(f"📊 매출 성장률 {revenue_growth:.1f}%로 안정적인 성장을 유지하고 있습니다.")
            else:
                insights.append(f"📉 매출 성장률 {revenue_growth:.1f}%로 성장 둔화가 관찰됩니다.")
        
        # 안정성 분석
        if latest_ratios['부채비율'] < 100:
            insights.append(f"✅ 부채비율 {latest_ratios['부채비율']:.1f}%로 재무 안정성이 우수합니다.")
        elif latest_ratios['부채비율'] < 200:
            insights.append(f"⚠️ 부채비율 {latest_ratios['부채비율']:.1f}%로 적정 수준입니다.")
        else:
            insights.append(f"❌ 부채비율 {latest_ratios['부채비율']:.1f}%로 부채 관리가 필요합니다.")
        
        # 유동성 분석
        if latest_ratios['유동비율'] > 150:
            insights.append(f"✅ 유동비율 {latest_ratios['유동비율']:.1f}%로 단기 유동성이 양호합니다.")
        elif latest_ratios['유동비율'] > 100:
            insights.append(f"⚠️ 유동비율 {latest_ratios['유동비율']:.1f}%로 단기 유동성에 주의가 필요합니다.")
        else:
            insights.append(f"❌ 유동비율 {latest_ratios['유동비율']:.1f}%로 단기 유동성 부족이 우려됩니다.")
        
        # ROE 분석
        if latest_ratios['ROE'] > 15:
            insights.append(f"✅ ROE {latest_ratios['ROE']:.2f}%로 자기자본 대비 수익성이 우수합니다.")
        elif latest_ratios['ROE'] > 5:
            insights.append(f"📊 ROE {latest_ratios['ROE']:.2f}%로 적정 수준의 자기자본 수익성을 보이고 있습니다.")
        else:
            insights.append(f"⚠️ ROE {latest_ratios['ROE']:.2f}%로 자기자본 수익성 개선이 필요합니다.")
        
        return insights










