#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF 분석 및 HTML 보고서 생성 사용 예제
"""

from pdf_to_html_report import PDFAnalyzer, LLMAnalyzer, HTMLReportGenerator
import os

def example_usage():
    """사용 예제"""
    
    # 1. PDF 파일 경로 설정
    pdf_path = input("PDF 파일 경로를 입력하세요: ").strip()
    
    if not os.path.exists(pdf_path):
        print(f"오류: 파일을 찾을 수 없습니다: {pdf_path}")
        return
    
    # 2. PDF 읽기
    print("\n[1/4] PDF 파일 읽는 중...")
    pdf_analyzer = PDFAnalyzer(pdf_path)
    pdf_text = pdf_analyzer.extract_text()
    metadata = pdf_analyzer.metadata
    
    print(f"✓ 텍스트 추출 완료 ({len(pdf_text)} 문자, {metadata.get('pages', 0)} 페이지)")
    
    # 3. 분석 모드 선택
    print("\n[2/4] 분석 모드 선택")
    use_local = input("로컬 모드 사용? (y/n, 기본값: n): ").strip().lower() == 'y'
    
    if not use_local:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("경고: OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
            print("로컬 모드로 전환합니다.")
            use_local = True
    
    # 4. PDF 내용 분석
    print("\n[3/4] PDF 내용 분석 중...")
    llm_analyzer = LLMAnalyzer(use_local=use_local)
    analysis_data = llm_analyzer.analyze_pdf_content(pdf_text, metadata)
    
    print("✓ 분석 완료")
    print(f"  - 제목: {analysis_data.get('title', 'N/A')}")
    print(f"  - 주요 발견사항: {len(analysis_data.get('key_findings', []))}개")
    
    # 5. HTML 보고서 생성
    print("\n[4/4] HTML 보고서 생성 중...")
    output_path = input("출력 파일명 (기본값: report.html): ").strip() or "report.html"
    
    html_generator = HTMLReportGenerator(template_path="automotive.html")
    result_path = html_generator.generate_report(analysis_data, output_path=output_path)
    
    print(f"\n✓ 완료! 보고서가 생성되었습니다: {result_path}")
    print(f"브라우저에서 열어서 확인하세요.")

if __name__ == "__main__":
    example_usage()











