# 해외 기업 분석을 위한 API 가이드

## 🎯 추천 조합 (무료)

### 1. **yfinance** (가장 추천 ⭐)
- **용도**: 주가, 재무제표, 기업 정보
- **무료**: 완전 무료, 제한 없음
- **설치**: `pip install yfinance`
- **지원 시장**: 전 세계 주요 증권거래소 (NYSE, NASDAQ, LSE, TSE 등)
- **데이터**:
  - 실시간/과거 주가
  - 재무제표 (손익계산서, 재무상태표, 현금흐름표)
  - 기업 정보 (직원 수, CEO, 섹터 등)
  - 배당 정보

### 2. **Alpha Vantage API**
- **용도**: 주가, 재무 데이터, 뉴스
- **무료 제한**: 5 calls/분, 500 calls/일
- **API 키**: https://www.alphavantage.co/support/#api-key
- **데이터**: 상세 재무제표, 기술적 지표, 뉴스

### 3. **NewsAPI**
- **용도**: 기업 뉴스 수집
- **무료 제한**: 100 requests/일
- **API 키**: https://newsapi.org/

## 📊 국가별 공식 API

### 미국 - SEC EDGAR API
- **용도**: 공시 정보, 재무제표
- **무료**: 완전 무료
- **데이터**: 10-K, 10-Q 등 공시 문서
- **API**: https://www.sec.gov/edgar/sec-api-documentation

### 영국 - Companies House API
- **용도**: 영국 기업 정보
- **무료**: 무료 플랜 있음
- **API**: https://developer.company-information.service.gov.uk/

## 💰 유료 API (더 많은 데이터)

### Financial Modeling Prep
- **무료**: 250 calls/일
- **유료**: 더 많은 데이터
- **특징**: 매우 상세한 재무 데이터

### IEX Cloud
- **무료**: 50,000 messages/월
- **특징**: 실시간 데이터, 상세 재무 정보

## 📝 사용 예시

```python
import yfinance as yf

# Apple 주식 정보
ticker = yf.Ticker("AAPL")
info = ticker.info  # 기업 정보
financials = ticker.financials  # 재무제표
balance_sheet = ticker.balance_sheet  # 재무상태표
history = ticker.history(period="1y")  # 주가 데이터
```

## 🔄 한국 vs 해외 비교

| 항목 | 한국 | 해외 (예: 미국) |
|------|------|----------------|
| 재무제표 | DART API | yfinance, SEC EDGAR |
| 공시 정보 | DART | SEC EDGAR |
| 주가 정보 | 네이버 Finance | yfinance, Alpha Vantage |
| 인력 정보 | DART (제한적) | SEC 10-K (일부) |
| 뉴스 | 네이버 검색 | NewsAPI, Alpha Vantage |





