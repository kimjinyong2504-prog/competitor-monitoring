#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
화승 R&A 분석 보고서 HTML 생성 모듈
"""

import json
from datetime import datetime
from typing import Dict, List
import re
from financial_analyzer import FinancialAnalyzer
from company_analyzer import CompanyAnalyzer

class ReportGenerator:
    """automotive.html 템플릿을 기반으로 HTML 보고서 생성"""
    
    def __init__(self, template_path: str = "automotive.html"):
        self.template_path = template_path
        self.template = self._load_template()
    
    def _load_template(self) -> str:
        """템플릿 파일 로드"""
        try:
            with open(self.template_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"템플릿 로드 오류: {str(e)}")
            return ""
    
    def _extract_financial_value(self, financial_data: List[Dict], account_nm: str, year: str = None) -> str:
        """재무 데이터에서 특정 계정 값 추출"""
        if not financial_data:
            return "N/A"
        
        # 연도별 데이터가 있는 경우
        if isinstance(financial_data, dict):
            if year and year in financial_data:
                data = financial_data[year]
            else:
                # 최신 연도 데이터 사용
                years = sorted(financial_data.keys(), reverse=True)
                data = financial_data[years[0]] if years else []
        else:
            data = financial_data
        
        for item in data:
            account_name = item.get("account_nm", "")
            # 정확한 매칭 또는 부분 매칭
            if account_nm in account_name or account_name == account_nm:
                amount = item.get("thstrm_amount", "0")
                if amount and amount != "0":
                    # 단위 변환 (원 -> 억원)
                    try:
                        amount_num = int(amount.replace(",", ""))
                        if abs(amount_num) >= 100000000:
                            return amount_num / 100000000  # 숫자로 반환 (차트용)
                        elif abs(amount_num) >= 10000:
                            return amount_num / 10000
                        else:
                            return amount_num
                    except:
                        return 0
        return 0
    
    def _extract_financial_value_str(self, financial_data: List[Dict], account_nm: str, year: str = None) -> str:
        """재무 데이터에서 특정 계정 값 추출 (문자열 형식)"""
        value = self._extract_financial_value(financial_data, account_nm, year)
        if isinstance(value, (int, float)):
            if abs(value) >= 1:
                return f"{value:.1f}억원"
            elif abs(value) >= 0.01:
                return f"{value * 100:.1f}만원"
            else:
                return f"{int(value * 10000)}원"
        return "N/A"
    
    def _format_number(self, value, unit: str = ""):
        """숫자 포맷팅"""
        if value == "N/A" or value is None:
            return "N/A"
        try:
            if isinstance(value, str):
                value = value.replace(",", "")
                value = int(value)
            if abs(value) >= 100000000:
                return f"{value / 100000000:.1f}억{unit}"
            elif abs(value) >= 10000:
                return f"{value / 10000:.1f}만{unit}"
            else:
                return f"{value:,}{unit}"
        except:
            return str(value) + unit
    
    def generate_report(self, data: Dict, output_path: str = "hwasung_rna_report.html") -> str:
        """HTML 보고서 생성"""
        if not self.template:
            print("템플릿을 로드할 수 없습니다.")
            return ""
        
        # 데이터 추출
        company_info = data.get("company_info", {})
        financial_data = data.get("financial_data", {})
        employee_info = data.get("employee_info", {})
        disclosures = data.get("recent_disclosures", [])
        news_articles = data.get("news_articles", [])
        finance_info = data.get("finance_info", {})
        
        # 기업 기본 정보
        corp_name = company_info.get("corp_name", "화승R&A")
        corp_code = company_info.get("corp_code", "")
        stock_code = company_info.get("stock_code", "")
        ceo = company_info.get("ceo_nm", "N/A")
        establish_date = company_info.get("est_dt", "N/A")
        address = company_info.get("adres", "N/A")
        
        # 주가 정보 (네이버 Finance에서 수집한 경우)
        stock_info = data.get("stock_info", {})
        
        # 재무 정보 추출
        years = sorted(financial_data.keys(), reverse=True)[:3] if financial_data else []
        
        # 매출, 영업이익 추출
        revenue_data = {}
        operating_profit_data = {}
        
        for year in years:
            year_data = financial_data[year]
            revenue = self._extract_financial_value_str(year_data, "매출액")
            operating_profit = self._extract_financial_value_str(year_data, "영업이익")
            revenue_data[year] = revenue
            operating_profit_data[year] = operating_profit
        
        # 직원 수 및 상세 정보 추출
        employee_count = "N/A"
        employee_details = {}
        
        if employee_info:
            # DART API 직원 정보 필드 확인
            # sm: 상시근로자수, cnt: 직원수, avrg_cnwk_sdytrn: 평균근속연수 등
            employee_count = employee_info.get("sm") or employee_info.get("cnt") or "N/A"
            
            # 숫자로 변환 시도
            if isinstance(employee_count, str) and employee_count.replace(",", "").isdigit():
                employee_count = f"{int(employee_count.replace(',', '')):,}명"
            elif isinstance(employee_count, (int, float)):
                employee_count = f"{int(employee_count):,}명"
            else:
                employee_count = str(employee_count) if employee_count != "N/A" else "N/A"
            
            # 상세 정보 추출 (DART API 필드명 매핑)
            # rgllbr_co: 정규직, cnttk_co: 계약직, fyer_salary_totamt: 연봉 총액, jan_salary_am: 1인당 연봉
            avg_tenure = employee_info.get("avrg_cnwk_sdytrn", "N/A")
            if avg_tenure != "N/A" and avg_tenure != "-":
                try:
                    avg_tenure = f"{float(avg_tenure):.2f}년"
                except:
                    pass
            
            # 기준일 추출 (stlm_dt 또는 rcept_dt)
            stlm_dt = employee_info.get("stlm_dt", employee_info.get("rcept_dt", "N/A"))
            if stlm_dt and stlm_dt != "N/A" and stlm_dt != "-":
                # 날짜 포맷팅 (YYYY-MM-DD -> YYYY년 MM월 DD일)
                try:
                    if len(stlm_dt) == 10:
                        parts = stlm_dt.split("-")
                        if len(parts) == 3:
                            stlm_dt = f"{parts[0]}년 {int(parts[1])}월 {int(parts[2])}일"
                except:
                    pass
            
            # 사업연도 추출 (rcept_no에서 추출하거나 직접)
            bsns_year = employee_info.get("bsns_year", "N/A")
            if bsns_year == "N/A" and employee_info.get("rcept_no"):
                # rcept_no에서 연도 추출 (예: 20250515001171 -> 2025)
                try:
                    bsns_year = employee_info.get("rcept_no", "")[:4]
                except:
                    pass
            
            employee_details = {
                "상시근로자수": employee_info.get("sm", "N/A"),
                "정규직": employee_info.get("rgllbr_co", "N/A"),
                "계약직": employee_info.get("cnttk_co", "N/A"),
                "평균근속연수": avg_tenure,
                "기준일": stlm_dt,
                "사업연도": bsns_year if bsns_year != "N/A" else "N/A"
            }
        
        # HTML 생성
        html = self.template
        
        # 제목 변경
        update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        html = html.replace("자동차 산업 시장 전망 보고서", f"{corp_name} 기업 분석 보고서")
        html = html.replace("2025-2030 Global & Korea Outlook", "")
        html = html.replace("전동화(EV)·소프트웨어 정의차량(SDV)·공급망 트렌드", "")
        
        # 홈 섹션 수정
        home_section = f"""        <div id="home" class="home-section">
    <h2>📋 보고서 목차</h2>
    <div class="button-grid">
        <div class="nav-button" onclick="showSection('company')">
            <h3>기업 개요</h3>
            <p>기업 기본 정보 및 개요</p>
        </div>
        <div class="nav-button" onclick="showSection('financial')">
            <h3>재무 정보</h3>
            <p>매출, 영업이익, 재무 현황</p>
        </div>
        <div class="nav-button" onclick="showSection('employee')">
            <h3>인력 현황</h3>
            <p>직원 수 및 조직 정보</p>
        </div>
        <div class="nav-button" onclick="showSection('disclosures')">
            <h3>공시 정보</h3>
            <p>최근 공시 내역</p>
        </div>
        <div class="nav-button" onclick="showSection('news')">
            <h3>관련 뉴스</h3>
            <p>최신 뉴스 및 기사</p>
        </div>
        <div class="nav-button" onclick="showSection('finance_info')">
            <h3>금융 정보</h3>
            <p>주가, 실적, 투자 정보</p>
        </div>
    </div>
</div>

"""
        
        # 기존 홈 섹션 교체 (더 정확한 패턴 - button-grid까지 포함)
        # 먼저 기존 home-section 전체를 찾아서 교체
        # 패턴: <div id="home" class="home-section"> ... </div> (button-grid 닫기) ... </div> (home-section 닫기)
        # 더 정확한 패턴: home-section 전체를 찾아서 교체
        # 여러 패턴 시도
        if re.search(r'<div id="home" class="home-section">.*?</div>\s*</div>\s*</div>', html, re.DOTALL):
            html = re.sub(
                r'<div id="home" class="home-section">.*?</div>\s*</div>\s*</div>',
                home_section.rstrip() + '\n',
                html,
                flags=re.DOTALL
            )
        elif re.search(r'<div id="home" class="home-section">.*?</div>\s*</div>', html, re.DOTALL):
            html = re.sub(
                r'<div id="home" class="home-section">.*?</div>\s*</div>',
                home_section.rstrip() + '\n',
                html,
                flags=re.DOTALL
            )
        else:
            # 패턴을 찾지 못한 경우 직접 교체 시도
            html = html.replace(
                '<div id="home" class="home-section">',
                home_section.split('<div id="home" class="home-section">')[1] if '<div id="home" class="home-section">' in home_section else home_section
            )
        
        # 기업 개요 섹션 (전문 분석 버전)
        company_analyzer = CompanyAnalyzer(
            company_info, 
            disclosures, 
            news_articles, 
            financial_data
        )
        
        company_overview = company_analyzer.generate_company_overview()
        business_description = company_analyzer.generate_business_description()
        financial_summary = company_analyzer.generate_financial_summary()
        
        # 주가 정보 표시
        stock_info_html = ""
        if stock_info and any(stock_info.values()):
            stock_info_html = f"""
    <h3>📈 주가 정보</h3>
    <div class="stat-card">
        <div class="stat-grid">
            {f'<div class="stat-item"><div class="stat-value">{stock_info.get("current_price", 0):,}원</div><div class="stat-label">현재가</div></div>' if stock_info.get("current_price") else ""}
            {f'<div class="stat-item"><div class="stat-value">{stock_info.get("market_cap", 0):.1f}억원</div><div class="stat-label">시가총액</div></div>' if stock_info.get("market_cap") else ""}
            {f'<div class="stat-item"><div class="stat-value">{stock_info.get("per", 0):.2f}</div><div class="stat-label">PER</div></div>' if stock_info.get("per") else ""}
            {f'<div class="stat-item"><div class="stat-value">{stock_info.get("pbr", 0):.2f}</div><div class="stat-label">PBR</div></div>' if stock_info.get("pbr") else ""}
            {f'<div class="stat-item"><div class="stat-value">{stock_info.get("dividend_yield", 0):.2f}%</div><div class="stat-label">배당수익률</div></div>' if stock_info.get("dividend_yield") else ""}
        </div>
        {f'<p style="margin-top: 15px; color: var(--muted); font-size: 0.9em;">종목코드: {stock_code}</p>' if stock_code else ""}
    </div>
            """
        
        company_section = f"""
<div id="company" class="content-section">
    <h2>기업 개요 및 사업 분석</h2>
    
    {company_overview}
    
    {business_description}
    
    {financial_summary}
    
    {stock_info_html}
    
    <h3>📰 최근 주요 공시</h3>
    <div class="stat-card">
        <p>최근 공시 정보는 하단의 "공시 정보" 섹션에서 상세히 확인할 수 있습니다.</p>
        <p>주요 공시: {len(disclosures)}건 (최근 20건 표시)</p>
    </div>
    
    <button class="back-button" onclick="showHome()">← 목차로 돌아가기</button>
</div>
"""
        
        # 재무 정보 섹션 (전문 분석 버전)
        financial_content = ""
        if years:
            # FinancialAnalyzer를 사용한 전문 분석
            analyzer = FinancialAnalyzer(financial_data)
            ratios = analyzer.analyze_financial_ratios()
            growth = analyzer.analyze_growth()
            structure = analyzer.analyze_financial_structure()
            insights = analyzer.generate_insights()
            
            # 주요 재무 지표 추출 (숫자와 문자열 모두)
            financial_metrics = {}
            chart_data = {'labels': years, 'revenue': [], 'operating_profit': [], 'net_income': []}
            
            for year in years:
                year_data = financial_data[year]
                metrics = {}
                # 숫자 값 추출 (차트용)
                metrics['매출액_num'] = self._extract_financial_value(year_data, "매출액")
                metrics['영업이익_num'] = self._extract_financial_value(year_data, "영업이익")
                metrics['당기순이익_num'] = self._extract_financial_value(year_data, "당기순이익")
                metrics['자산총계_num'] = self._extract_financial_value(year_data, "자산총계")
                metrics['부채총계_num'] = self._extract_financial_value(year_data, "부채총계")
                metrics['자본총계_num'] = self._extract_financial_value(year_data, "자본총계")
                
                # 문자열 값 추출 (표시용)
                metrics['매출액'] = self._extract_financial_value_str(year_data, "매출액")
                metrics['영업이익'] = self._extract_financial_value_str(year_data, "영업이익")
                metrics['당기순이익'] = self._extract_financial_value_str(year_data, "당기순이익")
                metrics['자산총계'] = self._extract_financial_value_str(year_data, "자산총계")
                metrics['부채총계'] = self._extract_financial_value_str(year_data, "부채총계")
                metrics['자본총계'] = self._extract_financial_value_str(year_data, "자본총계")
                
                financial_metrics[year] = metrics
                chart_data['revenue'].append(metrics['매출액_num'])
                chart_data['operating_profit'].append(metrics['영업이익_num'])
                chart_data['net_income'].append(metrics['당기순이익_num'])
            
            # 손익계산서 요약
            financial_table = "<h3>손익계산서 요약</h3><table><thead><tr><th>항목</th>"
            for year in years:
                financial_table += f"<th>{year}년</th>"
            financial_table += "</tr></thead><tbody>"
            
            for metric_name in ['매출액', '영업이익', '당기순이익']:
                financial_table += f"<tr><td><strong>{metric_name}</strong></td>"
                for year in years:
                    value = financial_metrics[year].get(metric_name, "N/A")
                    financial_table += f"<td>{value}</td>"
                financial_table += "</tr>"
            financial_table += "</tbody></table>"
            
            # 재무상태표 요약
            balance_table = "<h3>재무상태표 요약</h3><table><thead><tr><th>항목</th>"
            for year in years:
                balance_table += f"<th>{year}년</th>"
            balance_table += "</tr></thead><tbody>"
            
            for metric_name in ['자산총계', '부채총계', '자본총계']:
                balance_table += f"<tr><td><strong>{metric_name}</strong></td>"
                for year in years:
                    value = financial_metrics[year].get(metric_name, "N/A")
                    balance_table += f"<td>{value}</td>"
                balance_table += "</tr>"
            balance_table += "</tbody></table>"
            
            # 재무 비율 분석 (전문 분석)
            ratio_table = "<h3>재무 비율 분석</h3><table><thead><tr><th>비율</th>"
            for year in years:
                ratio_table += f"<th>{year}년</th>"
            ratio_table += "</tr></thead><tbody>"
            
            # 수익성 비율
            ratio_table += "<tr><td><strong>영업이익률</strong></td>"
            for year in years:
                ratio_table += f"<td>{ratios[year].get('영업이익률', 0):.2f}%</td>"
            ratio_table += "</tr>"
            
            ratio_table += "<tr><td><strong>순이익률</strong></td>"
            for year in years:
                ratio_table += f"<td>{ratios[year].get('순이익률', 0):.2f}%</td>"
            ratio_table += "</tr>"
            
            ratio_table += "<tr><td><strong>ROA (자산수익률)</strong></td>"
            for year in years:
                ratio_table += f"<td>{ratios[year].get('ROA', 0):.2f}%</td>"
            ratio_table += "</tr>"
            
            ratio_table += "<tr><td><strong>ROE (자기자본수익률)</strong></td>"
            for year in years:
                ratio_table += f"<td>{ratios[year].get('ROE', 0):.2f}%</td>"
            ratio_table += "</tr>"
            
            # 안정성 비율
            ratio_table += "<tr><td colspan=\"" + str(len(years) + 1) + "\"><strong>안정성 비율</strong></td></tr>"
            ratio_table += "<tr><td><strong>부채비율</strong></td>"
            for year in years:
                ratio_table += f"<td>{ratios[year].get('부채비율', 0):.2f}%</td>"
            ratio_table += "</tr>"
            
            ratio_table += "<tr><td><strong>자기자본비율</strong></td>"
            for year in years:
                ratio_table += f"<td>{ratios[year].get('자기자본비율', 0):.2f}%</td>"
            ratio_table += "</tr>"
            
            ratio_table += "<tr><td><strong>유동비율</strong></td>"
            for year in years:
                ratio_table += f"<td>{ratios[year].get('유동비율', 0):.1f}%</td>"
            ratio_table += "</tr>"
            
            # 활동성 비율
            ratio_table += "<tr><td colspan=\"" + str(len(years) + 1) + "\"><strong>활동성 비율</strong></td></tr>"
            ratio_table += "<tr><td><strong>총자산회전율</strong></td>"
            for year in years:
                ratio_table += f"<td>{ratios[year].get('총자산회전율', 0):.2f}회</td>"
            ratio_table += "</tr>"
            
            ratio_table += "</tbody></table>"
            
            # 성장률 분석
            growth_table = "<h3>성장률 분석</h3><table><thead><tr><th>항목</th>"
            for year in years:
                if year in growth and any(growth[year].values()):
                    growth_table += f"<th>{year}년</th>"
            growth_table += "</tr></thead><tbody>"
            
            if years and years[0] in growth:
                growth_table += "<tr><td><strong>매출 성장률</strong></td>"
                for year in years:
                    if year in growth:
                        gr = growth[year].get('매출성장률', 0)
                        growth_table += f"<td>{gr:+.1f}%</td>"
                growth_table += "</tr>"
                
                growth_table += "<tr><td><strong>영업이익 성장률</strong></td>"
                for year in years:
                    if year in growth:
                        gr = growth[year].get('영업이익성장률', 0)
                        growth_table += f"<td>{gr:+.1f}%</td>"
                growth_table += "</tr>"
                
                growth_table += "<tr><td><strong>순이익 성장률</strong></td>"
                for year in years:
                    if year in growth:
                        gr = growth[year].get('순이익성장률', 0)
                        growth_table += f"<td>{gr:+.1f}%</td>"
                growth_table += "</tr>"
            
            growth_table += "</tbody></table>"
            
            # 재무 인사이트
            insights_html = "<div class=\"highlight\"><h3>재무 분석 인사이트</h3><ul>"
            for insight in insights:
                insights_html += f"<li>{insight}</li>"
            insights_html += "</ul></div>"
            
            # 차트 생성
            chart_json = json.dumps(chart_data)
            
            financial_content = f"""
            <div class="highlight">
                <h3>📊 재무 분석 요약</h3>
                <p>DART API 데이터를 기반으로 한 전문적인 재무 분석 보고서입니다.</p>
            </div>
            
            {insights_html}
            
            {financial_table}
            {balance_table}
            {ratio_table}
            {growth_table}
            
            <div class="chart-container">
                <h3>재무 추이</h3>
                <canvas id="financial_chart"></canvas>
            </div>
            <script>
            (function() {{
                const ctx = document.getElementById('financial_chart');
                if (ctx && window.Chart) {{
                    const chartData = {chart_json};
                    new Chart(ctx, {{
                        type: 'bar',
                        data: {{
                            labels: chartData.labels,
                            datasets: [
                                {{
                                    label: '매출액 (억원)',
                                    data: chartData.revenue,
                                    backgroundColor: 'rgba(123, 100, 255, 0.6)',
                                    borderColor: 'rgba(123, 100, 255, 1)',
                                    borderWidth: 2
                                }},
                                {{
                                    label: '영업이익 (억원)',
                                    data: chartData.operating_profit,
                                    backgroundColor: 'rgba(18, 184, 134, 0.6)',
                                    borderColor: 'rgba(18, 184, 134, 1)',
                                    borderWidth: 2
                                }},
                                {{
                                    label: '당기순이익 (억원)',
                                    data: chartData.net_income,
                                    backgroundColor: 'rgba(255, 99, 132, 0.6)',
                                    borderColor: 'rgba(255, 99, 132, 1)',
                                    borderWidth: 2
                                }}
                            ]
                        }},
                        options: {{
                            responsive: true,
                            plugins: {{
                                legend: {{ display: true }},
                                title: {{ display: true, text: '재무 추이' }}
                            }},
                            scales: {{
                                y: {{
                                    beginAtZero: true,
                                    ticks: {{
                                        callback: function(value) {{
                                            return value.toFixed(1) + '억원';
                                        }}
                                    }}
                                }}
                            }}
                        }}
                    }});
                }}
            }})();
            </script>
            """
        
        financial_section = f"""
<div id="financial" class="content-section">
    <h2>재무 정보</h2>
    {financial_content if financial_content else "<p>재무 정보가 없습니다.</p>"}
    <button class="back-button" onclick="showHome()">← 목차로 돌아가기</button>
</div>
"""
        
        # 인력 현황 섹션 (상세 버전)
        employee_content = ""
        if employee_info and employee_details:
            employee_content = f"""
    <div class="stat-card">
        <h3>직원 현황</h3>
        <div class="stat-grid">
            <div class="stat-item">
                <div class="stat-value">{employee_count}</div>
                <div class="stat-label">직원 수</div>
            </div>
            {f'<div class="stat-item"><div class="stat-value">{employee_details.get("평균근속연수", "N/A")}</div><div class="stat-label">평균 근속연수</div></div>' if employee_details.get("평균근속연수") != "N/A" else ""}
            {f'<div class="stat-item"><div class="stat-value">{employee_details.get("기준일", "N/A")}</div><div class="stat-label">기준일</div></div>' if employee_details.get("기준일") != "N/A" else ""}
            {f'<div class="stat-item"><div class="stat-value">{employee_details.get("사업연도", "N/A")}년</div><div class="stat-label">사업연도</div></div>' if employee_details.get("사업연도") != "N/A" else ""}
        </div>
    </div>
    
    <div class="highlight">
        <h3>인력 정보 상세</h3>
        <table>
            <thead>
                <tr><th>항목</th><th>내용</th></tr>
            </thead>
            <tbody>
                <tr><td><strong>상시근로자수</strong></td><td>{employee_details.get("상시근로자수", "N/A")}명</td></tr>
                <tr><td><strong>정규직</strong></td><td>{employee_details.get("정규직", "N/A")}{"명" if employee_details.get("정규직", "N/A") != "N/A" and employee_details.get("정규직", "N/A") != "-" else ""}</td></tr>
                <tr><td><strong>계약직</strong></td><td>{employee_details.get("계약직", "N/A")}{"명" if employee_details.get("계약직", "N/A") != "N/A" and employee_details.get("계약직", "N/A") != "-" else ""}</td></tr>
                <tr><td><strong>평균근속연수</strong></td><td>{employee_details.get("평균근속연수", "N/A")}</td></tr>
                <tr><td><strong>기준일</strong></td><td>{employee_details.get("기준일", "N/A")}</td></tr>
                <tr><td><strong>사업연도</strong></td><td>{employee_details.get("사업연도", "N/A")}{"년" if employee_details.get("사업연도", "N/A") != "N/A" else ""}</td></tr>
            </tbody>
        </table>
    </div>
            """
        else:
            employee_content = f"""
    <div class="highlight">
        <h3>⚠️ 직원 정보 수집 안내</h3>
        <p>DART API를 통해 직원 정보를 조회했으나, 현재 사용 가능한 데이터가 없습니다.</p>
        <p>직원 정보는 기업이 사업보고서에 공시한 경우에만 제공됩니다.</p>
        <p>최신 사업보고서를 확인하시거나, DART 공시 정보에서 직접 확인하실 수 있습니다.</p>
    </div>
    
    <div class="stat-card">
        <h3>DART에서 직원 정보 확인 방법</h3>
        <ol>
            <li>DART 홈페이지 (dart.fss.or.kr) 접속</li>
            <li>기업명 "화승알앤에이" 검색</li>
            <li>최신 사업보고서 확인</li>
            <li>"직원 현황" 또는 "인력 현황" 섹션 확인</li>
        </ol>
    </div>
            """
        
        employee_section = f"""
<div id="employee" class="content-section">
    <h2>인력 현황</h2>
    {employee_content}
    <button class="back-button" onclick="showHome()">← 목차로 돌아가기</button>
</div>
"""
        
        # 공시 정보 섹션
        disclosure_list = ""
        if disclosures:
            disclosure_list = "<table><thead><tr><th>공시일</th><th>공시제목</th><th>링크</th></tr></thead><tbody>"
            for disc in disclosures[:20]:  # 최근 20개만
                rcept_dt = disc.get("rcept_dt", "")
                report_nm = disc.get("report_nm", "")
                rcept_no = disc.get("rcept_no", "")
                link = f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={rcept_no}" if rcept_no else "#"
                disclosure_list += f'<tr><td>{rcept_dt}</td><td>{report_nm}</td><td><a href="{link}" target="_blank">보기</a></td></tr>'
            disclosure_list += "</tbody></table>"
        
        disclosure_section = f"""
<div id="disclosures" class="content-section">
    <h2>공시 정보</h2>
    {disclosure_list if disclosure_list else "<p>공시 정보가 없습니다.</p>"}
    <button class="back-button" onclick="showHome()">← 목차로 돌아가기</button>
</div>
"""
        
        # 뉴스 섹션
        news_list = ""
        if news_articles:
            news_list = "<div style='display: grid; gap: 15px; margin: 20px 0;'>"
            for article in news_articles[:50]:  # 최근 50개만
                title = article.get("title", "")
                link = article.get("link", "")
                pub_date = article.get("pub_date", "")
                description = article.get("description", "")
                news_list += f"""
                <div class="nav-button" style="cursor: pointer;" onclick="window.open('{link}', '_blank')">
                    <h3>{title}</h3>
                    <p style="color: var(--muted); font-size: 0.9em; margin-top: 8px;">{description[:100]}...</p>
                    <p style="color: var(--muted); font-size: 0.85em; margin-top: 5px;">{pub_date}</p>
                </div>
                """
            news_list += "</div>"
        
        news_section = f"""
<div id="news" class="content-section">
    <h2>관련 뉴스</h2>
    <p class="muted">총 {len(news_articles)}개의 기사가 수집되었습니다. (최근 50개 표시)</p>
    {news_list if news_list else "<p>뉴스 기사가 없습니다.</p>"}
    <button class="back-button" onclick="showHome()">← 목차로 돌아가기</button>
</div>
"""
        
        # 금융 정보 섹션
        finance_content = ""
        if finance_info:
            finance_news = finance_info.get("finance_news", [])
            finance_analysis = finance_info.get("finance_analysis", [])
            
            # 금융 뉴스
            finance_news_list = ""
            if finance_news:
                finance_news_list = "<h3>📈 금융 뉴스</h3><div style='display: grid; gap: 15px; margin: 20px 0;'>"
                for article in finance_news[:20]:  # 최근 20개만
                    title = article.get("title", "")
                    link = article.get("link", "")
                    pub_date = article.get("pub_date", "")
                    description = article.get("description", "")
                    finance_news_list += f"""
                    <div class="nav-button" style="cursor: pointer;" onclick="window.open('{link}', '_blank')">
                        <h3>{title}</h3>
                        <p style="color: var(--muted); font-size: 0.9em; margin-top: 8px;">{description[:150]}...</p>
                        <p style="color: var(--muted); font-size: 0.85em; margin-top: 5px;">{pub_date}</p>
                    </div>
                    """
                finance_news_list += "</div>"
            
            # 금융 분석
            finance_analysis_list = ""
            if finance_analysis:
                finance_analysis_list = "<h3>📊 금융 분석</h3><div style='display: grid; gap: 15px; margin: 20px 0;'>"
                for article in finance_analysis[:20]:  # 최근 20개만
                    title = article.get("title", "")
                    link = article.get("link", "")
                    pub_date = article.get("pub_date", "")
                    description = article.get("description", "")
                    category = article.get("category", "")
                    finance_analysis_list += f"""
                    <div class="nav-button" style="cursor: pointer;" onclick="window.open('{link}', '_blank')">
                        <h3>{title}</h3>
                        <p style="color: var(--muted); font-size: 0.9em; margin-top: 8px;">{description[:150]}...</p>
                        <p style="color: var(--muted); font-size: 0.85em; margin-top: 5px;">{pub_date} | {category}</p>
                    </div>
                    """
                finance_analysis_list += "</div>"
            
            finance_content = f"""
            <div class="highlight">
                <h3>💰 금융 정보 요약</h3>
                <p>네이버 검색 API를 통해 수집한 화승알앤에이의 금융 관련 정보입니다.</p>
                <div class="stat-grid">
                    <div class="stat-item">
                        <div class="stat-value">{len(finance_news)}개</div>
                        <div class="stat-label">금융 뉴스</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{len(finance_analysis)}개</div>
                        <div class="stat-label">금융 분석</div>
                    </div>
                </div>
            </div>
            
            {finance_news_list if finance_news_list else "<p>금융 뉴스가 없습니다.</p>"}
            {finance_analysis_list if finance_analysis_list else ""}
            """
        else:
            finance_content = """
            <div class="highlight">
                <h3>⚠️ 금융 정보 수집 안내</h3>
                <p>네이버 검색 API를 통해 금융 정보를 수집했으나, 현재 사용 가능한 데이터가 없습니다.</p>
            </div>
            """
        
        finance_section = f"""
<div id="finance_info" class="content-section">
    <h2>금융 정보</h2>
    {finance_content}
    <button class="back-button" onclick="showHome()">← 목차로 돌아가기</button>
</div>
"""
        
        # 기존 섹션들 제거하고 새 섹션들 추가
        # 기존 content-section들을 모두 찾아서 제거
        # 더 정확한 패턴: 각 섹션이 <div id="..." class="content-section">로 시작하고 </div>로 끝남
        html = re.sub(
            r'<div id="[^"]*" class="content-section">.*?</button>\s*</div>\s*</div>',
            '',
            html,
            flags=re.DOTALL
        )
        
        # container의 마지막 부분 찾기 (</div> 태그들 전에 삽입)
        # automotive.html 구조 확인: </div> (content-section 닫기) -> </div> (container 닫기) -> </div> (최상위) -> <script>
        
        # home-section이 닫히는 위치 찾기 (</div> 태그들)
        # home-section 다음에 content-section들이 와야 함
        # 패턴: </div> (button-grid 닫기) -> </div> (home-section 닫기) -> 그 다음에 content-section 삽입
        
        # home-section 닫는 태그 다음에 content-section들 삽입
        # 가장 확실한 방법: home-section의 마지막 </div> 다음에 삽입
        # home-section 구조: <div id="home"> -> <div class="button-grid"> -> </div> (button-grid) -> </div> (home-section)
        
        # home-section이 닫히는 위치 찾기
        # home-section 구조: <div id="home"> -> <div class="button-grid"> -> </div> (button-grid) -> </div> (home-section)
        # 우리가 생성한 home_section은 마지막에 </div>\n</div>로 끝남
        
        # 가장 확실한 방법: <script> 태그가 시작되는 위치를 찾아서 그 전에 삽입
        script_start = html.find('    <script>')
        if script_start > 0:
            # <script> 태그 바로 전에 삽입
            html = html[:script_start] + f'\n{company_section}\n{financial_section}\n{employee_section}\n{disclosure_section}\n{news_section}\n{finance_section}\n' + html[script_start:]
        # 패턴 1: </div>\s*</div>\s*</div>\s*<script>
        elif re.search(r'</div>\s*</div>\s*</div>\s*<script>', html):
            html = re.sub(
                r'(</div>\s*</div>\s*</div>\s*<script>)',
                f'\\1\n{company_section}\n{financial_section}\n{employee_section}\n{disclosure_section}\n{news_section}\n{finance_section}',
                html,
                flags=re.DOTALL,
                count=1
            )
        # 패턴 2: </div>\n\n    </div> 패턴
        elif '</div>\n\n    </div>' in html:
            html = html.replace(
                '</div>\n\n    </div>',
                f'</div>\n\n    </div>\n\n{company_section}\n{financial_section}\n{employee_section}\n{disclosure_section}\n{news_section}\n{finance_section}',
                1
            )
        # 패턴 3: home-section이 닫히는 위치 (</div>\n</div>\n 다음)
        elif '</div>\n</div>\n' in html:
            html = html.replace(
                '</div>\n</div>\n',
                f'</div>\n</div>\n{company_section}\n{financial_section}\n{employee_section}\n{disclosure_section}\n{news_section}\n{finance_section}\n',
                1
            )
        # 최후의 수단: </body> 전에 삽입
        else:
            html = html.replace(
                '</body>',
                f'{company_section}\n{financial_section}\n{employee_section}\n{disclosure_section}\n{news_section}\n{finance_section}\n</body>',
                1
            )
        
        # 자동 업데이트 JavaScript 추가
        auto_update_script = """
        <script>
        // 자동 업데이트 기능
        (function() {
            const API_BASE = window.location.origin;
            let lastUpdateTime = null;
            let updateCheckInterval = null;
            
            // 업데이트 상태 표시 요소 생성
            function createUpdateIndicator() {
                const indicator = document.createElement('div');
                indicator.id = 'update-indicator';
                indicator.style.cssText = `
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background: var(--surface);
                    padding: 12px 20px;
                    border-radius: 8px;
                    box-shadow: var(--shadow);
                    border: 1px solid var(--border);
                    z-index: 10000;
                    font-size: 0.9em;
                    display: none;
                `;
                document.body.appendChild(indicator);
                return indicator;
            }
            
            function showUpdateIndicator(message, type = 'info') {
                const indicator = document.getElementById('update-indicator') || createUpdateIndicator();
                indicator.style.display = 'block';
                indicator.textContent = message;
                indicator.style.borderLeft = `4px solid ${type === 'success' ? '#12b886' : type === 'error' ? '#ff6b6b' : '#7b64ff'}`;
                
                if (type === 'success') {
                    setTimeout(() => {
                        indicator.style.display = 'none';
                    }, 3000);
                }
            }
            
            // 상태 확인
            async function checkStatus() {
                try {
                    const response = await fetch(API_BASE + '/api/status');
                    const status = await response.json();
                    
                    if (lastUpdateTime && status.last_updated && status.last_updated !== lastUpdateTime) {
                        // 업데이트 감지
                        showUpdateIndicator('새로운 데이터가 있습니다. 페이지를 새로고침합니다...', 'success');
                        setTimeout(() => {
                            window.location.reload();
                        }, 2000);
                    } else if (!lastUpdateTime && status.last_updated) {
                        lastUpdateTime = status.last_updated;
                    }
                } catch (error) {
                    // 로컬 서버가 실행 중이 아닐 때는 조용히 실패
                    console.log('로컬 서버에 연결할 수 없습니다. 자동 업데이트를 사용하려면 local_server.py를 실행하세요.');
                }
            }
            
            // 수동 업데이트 버튼
            function createUpdateButton() {
                const button = document.createElement('button');
                button.textContent = '🔄 업데이트';
                button.style.cssText = `
                    position: fixed;
                    bottom: 20px;
                    right: 20px;
                    background: var(--primary-500);
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 8px;
                    cursor: pointer;
                    font-size: 0.9em;
                    font-weight: 500;
                    box-shadow: var(--shadow);
                    z-index: 10000;
                    transition: all 0.3s;
                `;
                button.onmouseover = () => button.style.background = 'var(--primary-600)';
                button.onmouseout = () => button.style.background = 'var(--primary-500)';
                
                button.onclick = async () => {
                    button.disabled = true;
                    button.textContent = '업데이트 중...';
                    showUpdateIndicator('데이터를 업데이트하는 중...', 'info');
                    
                    try {
                        const response = await fetch(API_BASE + '/api/update', {
                            method: 'POST'
                        });
                        const result = await response.json();
                        
                        if (result.success) {
                            showUpdateIndicator('업데이트 완료! 페이지를 새로고침합니다...', 'success');
                            setTimeout(() => {
                                window.location.reload();
                            }, 2000);
                        } else {
                            showUpdateIndicator('업데이트 실패: ' + result.message, 'error');
                            button.disabled = false;
                            button.textContent = '🔄 업데이트';
                        }
                    } catch (error) {
                        showUpdateIndicator('서버에 연결할 수 없습니다.', 'error');
                        button.disabled = false;
                        button.textContent = '🔄 업데이트';
                    }
                };
                
                document.body.appendChild(button);
            }
            
            // 초기화
            if (window.location.protocol === 'http:' || window.location.protocol === 'https:') {
                // 웹 서버를 통해 접근하는 경우
                createUpdateButton();
                checkStatus(); // 초기 확인
                updateCheckInterval = setInterval(checkStatus, 60000); // 1분마다 확인
            }
        })();
        </script>
        """
        
        # </body> 전에 자동 업데이트 스크립트 추가
        if "</body>" in html:
            html = html.replace("</body>", auto_update_script + "\n</body>")
        else:
            html += auto_update_script
        
        # 파일 저장
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"HTML 보고서 생성 완료: {output_path}")
            return output_path
        except Exception as e:
            print(f"HTML 보고서 저장 오류: {str(e)}")
            return ""

if __name__ == "__main__":
    # 테스트
    from data_manager import DataManager
    manager = DataManager()
    data = manager.get_data()
    
    generator = ReportGenerator()
    generator.generate_report(data, "test_report.html")

