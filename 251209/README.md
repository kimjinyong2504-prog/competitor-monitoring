# 화승알앤에이 기업 분석 보고서 생성 프로젝트

## 📁 파일 구조

### 핵심 파일
- **hwasung_rna_colab.py**: Google Colab에서 실행하는 데이터 수집 스크립트
  - DART API를 통한 기업 정보 수집
  - 네이버 뉴스 API를 통한 뉴스 기사 수집
  - 모든 데이터를 JSON 파일로 저장

- **generate_report_no_news.py**: HTML 보고서 생성 스크립트
  - JSON 데이터를 읽어서 HTML 보고서 생성

- **report_generator_no_news.py**: 보고서 생성 모듈
  - HTML 템플릿 기반 보고서 생성
  - 재무 분석, 기업 분석 통합

- **financial_analyzer.py**: 재무 분석 모듈
  - 재무 비율 계산
  - 성장률 분석
  - 재무 구조 분석

- **company_analyzer.py**: 기업 분석 모듈
  - 기업 개요 생성
  - 사업 설명 생성
  - 시장 위치 분석

- **automotive.html**: HTML 보고서 템플릿

- **hwasung_rna_data.json**: 수집된 기업 데이터 (Colab에서 생성)

- **requirements.txt**: Python 패키지 의존성

## 🚀 사용 방법

### 1. Google Colab에서 데이터 수집

1. Google Colab에 `hwasung_rna_colab.py` 파일 업로드
2. 필요한 라이브러리 설치:
   ```python
   !pip install requests -q
   ```
3. 스크립트 실행하여 `hwasung_rna_data.json` 파일 생성
4. 생성된 JSON 파일 다운로드

### 2. 로컬에서 HTML 보고서 생성

1. JSON 파일을 프로젝트 폴더에 배치
2. 필요한 패키지 설치:
   ```bash
   pip install -r requirements.txt
   ```
3. 보고서 생성:
   ```bash
   python generate_report_no_news.py
   ```
4. 생성된 `hwasung_rna_report_no_news.html` 파일을 브라우저에서 열기

## 📊 보고서 내용

- **기업 개요**: 기업 기본 정보 및 사업 분석
- **재무 정보**: 손익계산서, 재무상태표, 재무비율, 성장률 분석
- **인력 현황**: 직원 수, 정규직/계약직, 평균근속연수
- **지배구조**: 주요주주, 임원, 주주 현황
- **배당 정보**: 배당금 및 배당 정책
- **공시 정보**: 최근 공시 내역

## 📝 참고사항

- DART API 키와 네이버 API 키는 `hwasung_rna_colab.py` 파일에 설정되어 있습니다.
- 보고서는 뉴스 섹션을 제외한 버전입니다.
- 모든 데이터는 DART API와 네이버 뉴스 API에서 실시간으로 수집됩니다.









