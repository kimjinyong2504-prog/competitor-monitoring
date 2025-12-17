#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF 파일을 분석하여 HTML 보고서를 생성하는 모델
automotive.html 템플릿을 기반으로 보고서 생성
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Optional
import argparse

try:
    import pdfplumber
except ImportError:
    print("pdfplumber가 설치되지 않았습니다. 'pip install pdfplumber'를 실행하세요.")
    sys.exit(1)

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("OpenAI 라이브러리가 설치되지 않았습니다. 로컬 LLM 모드를 사용하거나 'pip install openai'를 실행하세요.")


class PDFAnalyzer:
    """PDF 파일을 읽고 분석하는 클래스"""
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.text_content = ""
        self.metadata = {}
        
    def extract_text(self) -> str:
        """PDF에서 텍스트 추출 (개선된 버전)"""
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                text_parts = []
                self.metadata = {
                    'pages': len(pdf.pages),
                    'title': pdf.metadata.get('Title', ''),
                    'author': pdf.metadata.get('Author', ''),
                    'subject': pdf.metadata.get('Subject', '')
                }
                
                for page_num, page in enumerate(pdf.pages, 1):
                    # 텍스트 추출
                    text = page.extract_text()
                    if text:
                        # 페이지 번호 추가
                        text_parts.append(f"[페이지 {page_num}]\n{text}")
                    
                    # 표 추출 시도
                    tables = page.extract_tables()
                    if tables:
                        for table in tables:
                            table_text = self._table_to_text(table)
                            if table_text:
                                text_parts.append(f"\n[표 - 페이지 {page_num}]\n{table_text}\n")
                
                self.text_content = '\n\n'.join(text_parts)
                # 불필요한 공백 정리
                self.text_content = re.sub(r'\n{3,}', '\n\n', self.text_content)
                return self.text_content
        except Exception as e:
            raise Exception(f"PDF 읽기 오류: {str(e)}")
    
    def _table_to_text(self, table) -> str:
        """표를 텍스트로 변환"""
        if not table:
            return ""
        
        lines = []
        for row in table:
            if row:
                # None 값을 빈 문자열로 변환
                row_text = [str(cell) if cell else '' for cell in row]
                lines.append(' | '.join(row_text))
        return '\n'.join(lines)
    
    def get_summary(self, max_length: int = 10000) -> str:
        """텍스트 요약 (너무 길면 잘라냄)"""
        if len(self.text_content) > max_length:
            return self.text_content[:max_length] + "\n\n[... 내용이 길어 일부만 표시됨 ...]"
        return self.text_content


class LLMAnalyzer:
    """LLM을 사용하여 PDF 내용을 분석하는 클래스"""
    
    def __init__(self, use_local: bool = False, model_name: str = "gpt-4o-mini"):
        self.use_local = use_local
        self.model_name = model_name
        self.client = None
        
        if not use_local and OPENAI_AVAILABLE:
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                self.client = OpenAI(api_key=api_key)
            else:
                print("경고: OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
                print("로컬 LLM 모드로 전환하거나 API 키를 설정하세요.")
    
    def analyze_pdf_content(self, pdf_text: str, metadata: Dict) -> Dict:
        """PDF 내용을 분석하여 구조화된 데이터 반환"""
        
        if self.use_local or not self.client:
            # 로컬 LLM 모드: 간단한 키워드 추출 및 구조화
            return self._simple_analysis(pdf_text, metadata)
        else:
            # OpenAI API 사용
            return self._openai_analysis(pdf_text, metadata)
    
    def _simple_analysis(self, pdf_text: str, metadata: Dict) -> Dict:
        """간단한 로컬 분석 (키워드 기반)"""
        # 기본 구조화된 데이터 생성
        lines = pdf_text.split('\n')[:50]  # 처음 50줄만 사용
        
        # 숫자 패턴 찾기
        numbers = re.findall(r'\d+[.,]\d+%?|\d+%?', pdf_text[:5000])
        
        # 주요 섹션 찾기
        sections = []
        for line in lines:
            if len(line.strip()) > 10 and any(keyword in line for keyword in ['시장', '전망', '분석', '전략', '요약']):
                sections.append(line.strip())
        
        return {
            'title': metadata.get('title', 'PDF 분석 보고서'),
            'summary': pdf_text[:500] + '...' if len(pdf_text) > 500 else pdf_text,
            'key_numbers': numbers[:10],
            'sections': sections[:5],
            'full_text': pdf_text[:10000]  # 처음 10000자만
        }
    
    def _openai_analysis(self, pdf_text: str, metadata: Dict) -> Dict:
        """OpenAI API를 사용한 분석"""
        prompt = f"""다음 PDF 문서 내용을 분석하여 구조화된 JSON 형식으로 정리해주세요.

PDF 메타데이터:
- 제목: {metadata.get('title', 'N/A')}
- 작성자: {metadata.get('author', 'N/A')}
- 페이지 수: {metadata.get('pages', 'N/A')}

PDF 내용 (일부):
{pdf_text[:8000]}

다음 형식으로 JSON을 반환해주세요:
{{
    "title": "보고서 제목",
    "summary": "핵심 요약 (3-5문장)",
    "key_findings": ["주요 발견사항 1", "주요 발견사항 2", "주요 발견사항 3"],
    "key_numbers": ["숫자/통계 1", "숫자/통계 2"],
    "sections": [
        {{"title": "섹션 제목", "content": "섹션 내용"}},
        ...
    ],
    "recommendations": ["권장사항 1", "권장사항 2"]
}}

JSON만 반환하고 다른 설명은 하지 마세요."""

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "당신은 전문 문서 분석가입니다. PDF 문서를 분석하여 구조화된 정보를 제공합니다."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # JSON 추출
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # JSON 파싱 실패 시 기본 구조 반환
                return {
                    'title': metadata.get('title', 'PDF 분석 보고서'),
                    'summary': result_text[:500],
                    'key_findings': [],
                    'key_numbers': [],
                    'sections': [],
                    'recommendations': []
                }
        except Exception as e:
            print(f"OpenAI API 오류: {str(e)}")
            return self._simple_analysis(pdf_text, metadata)


class HTMLReportGenerator:
    """automotive.html 템플릿을 기반으로 HTML 보고서 생성"""
    
    def __init__(self, template_path: str = "automotive.html"):
        self.template_path = template_path
        self.template_content = ""
        
    def load_template(self) -> str:
        """템플릿 파일 로드"""
        try:
            with open(self.template_path, 'r', encoding='utf-8') as f:
                self.template_content = f.read()
            return self.template_content
        except FileNotFoundError:
            raise FileNotFoundError(f"템플릿 파일을 찾을 수 없습니다: {self.template_path}")
    
    def generate_report(self, analysis_data: Dict, output_path: str = "report.html"):
        """분석 데이터를 기반으로 HTML 보고서 생성"""
        if not self.template_content:
            self.load_template()
        
        # 템플릿의 제목과 부제목 교체
        html = self.template_content
        
        # 제목 교체
        title = analysis_data.get('title', 'PDF 분석 보고서')
        html = re.sub(
            r'<h1>.*?</h1>',
            f'<h1>{title}</h1>',
            html,
            flags=re.DOTALL
        )
        
        # 부제목 교체 (첫 번째 subtitle만)
        subtitle = analysis_data.get('summary', 'PDF 문서 분석 결과')[:150]
        subtitle_lines = html.split('\n')
        subtitle_replaced = False
        for i, line in enumerate(subtitle_lines):
            if 'class="subtitle"' in line and not subtitle_replaced:
                subtitle_lines[i] = f'    <p class="subtitle">{subtitle}</p>'
                subtitle_replaced = True
        html = '\n'.join(subtitle_lines)
        
        # Executive Summary 섹션 업데이트
        exec_summary = self._generate_executive_summary(analysis_data)
        html = self._replace_section(html, 'exec', exec_summary)
        
        # 주요 섹션들 생성
        if analysis_data.get('sections'):
            segments_html = self._generate_sections_content(analysis_data)
            html = self._replace_section(html, 'segments', segments_html)
        
        # 권장사항 섹션 생성
        if analysis_data.get('recommendations'):
            actions_html = self._generate_recommendations(analysis_data)
            html = self._replace_section(html, 'actions', actions_html)
        
        # 파일 저장
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"HTML 보고서가 생성되었습니다: {output_path}")
        return output_path
    
    def _generate_executive_summary(self, data: Dict) -> str:
        """Executive Summary 섹션 HTML 생성"""
        summary = data.get('summary', '')
        key_findings = data.get('key_findings', [])
        key_numbers = data.get('key_numbers', [])
        
        html = f"""
    <h2>요약 (Executive Summary)</h2>
    <div class="stat-card">
        <h3>핵심 요약</h3>
        <p>{summary}</p>
    </div>
"""
        
        if key_numbers:
            html += """
    <div class="stat-card">
        <h3>핵심 지표</h3>
        <div class="stat-grid">
"""
            for i, num in enumerate(key_numbers[:4]):
                html += f'            <div class="stat-item"><div class="stat-value">{num}</div><div class="stat-label">주요 지표 {i+1}</div></div>\n'
            html += """        </div>
    </div>
"""
        
        if key_findings:
            html += """
    <div class="highlight">
        <h4>핵심 인사이트</h4>
        <ul>
"""
            for finding in key_findings[:5]:
                html += f'            <li><strong>{finding}</strong></li>\n'
            html += """        </ul>
    </div>
"""
        
        html += '    <button class="back-button" onclick="showHome()">← 목차로 돌아가기</button>'
        return html
    
    def _generate_sections_content(self, data: Dict) -> str:
        """주요 섹션 내용 생성"""
        sections = data.get('sections', [])
        
        html = '<h2>주요 내용 분석</h2>\n'
        
        if isinstance(sections, list) and len(sections) > 0:
            for i, section in enumerate(sections[:10], 1):  # 최대 10개 섹션
                if isinstance(section, dict):
                    section_title = section.get('title', f'섹션 {i}')
                    section_content = section.get('content', '')
                else:
                    section_title = f'섹션 {i}'
                    section_content = str(section)
                
                html += f"""
    <div class="stat-card">
        <h3>{section_title}</h3>
        <p>{section_content[:500]}</p>
    </div>
"""
        else:
            html += '<p>주요 섹션 정보가 없습니다.</p>\n'
        
        html += '    <button class="back-button" onclick="showHome()">← 목차로 돌아가기</button>'
        return html
    
    def _generate_recommendations(self, data: Dict) -> str:
        """권장사항 섹션 생성"""
        recommendations = data.get('recommendations', [])
        
        html = '<h2>실행 과제 및 권장사항</h2>\n'
        
        if recommendations:
            html += '<table>\n  <thead><tr><th>우선순위</th><th>과제</th><th>설명</th></tr></thead>\n  <tbody>\n'
            for i, rec in enumerate(recommendations[:10], 1):
                priority = "높음" if i <= 3 else "중간" if i <= 6 else "낮음"
                html += f'    <tr><td>{priority}</td><td>권장사항 {i}</td><td>{rec}</td></tr>\n'
            html += '  </tbody>\n</table>\n'
        else:
            html += '<p>권장사항 정보가 없습니다.</p>\n'
        
        html += '    <button class="back-button" onclick="showHome()">← 목차로 돌아가기</button>'
        return html
    
    def _replace_section(self, html: str, section_id: str, new_content: str) -> str:
        """특정 섹션의 내용을 교체"""
        # 섹션 시작과 끝을 찾기
        start_pattern = f'<div id="{section_id}" class="content-section">'
        end_pattern = '</div>'
        
        start_idx = html.find(start_pattern)
        if start_idx == -1:
            # 섹션이 없으면 추가하지 않음 (기존 템플릿 구조 유지)
            return html
        
        # 해당 섹션의 끝 찾기 (중첩된 div 고려)
        depth = 0
        pos = start_idx + len(start_pattern)
        end_idx = -1
        
        for i in range(pos, len(html)):
            if html[i:i+5] == '<div ':
                depth += 1
            elif html[i:i+6] == '</div>':
                if depth == 0:
                    end_idx = i + 6
                    break
                depth -= 1
        
        if end_idx != -1:
            # 섹션 내용 교체
            html = html[:start_idx + len(start_pattern)] + '\n' + new_content + '\n' + html[end_idx:]
        else:
            # 끝을 찾지 못한 경우 간단히 교체
            pattern = f'<div id="{section_id}" class="content-section">.*?</div>'
            replacement = f'<div id="{section_id}" class="content-section">\n{new_content}\n</div>'
            html = re.sub(pattern, replacement, html, flags=re.DOTALL)
        
        return html


def main():
    parser = argparse.ArgumentParser(description='PDF 파일을 분석하여 HTML 보고서 생성')
    parser.add_argument('pdf_path', help='분석할 PDF 파일 경로')
    parser.add_argument('-o', '--output', default='report.html', help='출력 HTML 파일 경로 (기본값: report.html)')
    parser.add_argument('--local', action='store_true', help='로컬 LLM 모드 사용 (OpenAI API 미사용)')
    parser.add_argument('--model', default='gpt-4o-mini', help='사용할 LLM 모델 (기본값: gpt-4o-mini)')
    parser.add_argument('--template', default='automotive.html', help='HTML 템플릿 파일 경로 (기본값: automotive.html)')
    
    args = parser.parse_args()
    
    # PDF 파일 확인
    if not os.path.exists(args.pdf_path):
        print(f"오류: PDF 파일을 찾을 수 없습니다: {args.pdf_path}")
        sys.exit(1)
    
    # 템플릿 파일 확인
    if not os.path.exists(args.template):
        print(f"오류: 템플릿 파일을 찾을 수 없습니다: {args.template}")
        sys.exit(1)
    
    print(f"PDF 파일 읽는 중: {args.pdf_path}")
    
    # PDF 읽기
    pdf_analyzer = PDFAnalyzer(args.pdf_path)
    pdf_text = pdf_analyzer.extract_text()
    metadata = pdf_analyzer.metadata
    
    print(f"텍스트 추출 완료 ({len(pdf_text)} 문자, {metadata.get('pages', 0)} 페이지)")
    
    # LLM 분석
    print("PDF 내용 분석 중...")
    llm_analyzer = LLMAnalyzer(use_local=args.local, model_name=args.model)
    analysis_data = llm_analyzer.analyze_pdf_content(pdf_text, metadata)
    
    print("분석 완료")
    
    # HTML 보고서 생성
    print("HTML 보고서 생성 중...")
    html_generator = HTMLReportGenerator(template_path=args.template)
    output_path = html_generator.generate_report(analysis_data, output_path=args.output)
    
    print(f"\n완료! 보고서가 생성되었습니다: {output_path}")
    print(f"브라우저에서 열어서 확인하세요.")


if __name__ == "__main__":
    main()

