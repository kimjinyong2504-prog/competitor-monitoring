# Google Colab 빠른 시작 가이드

## 방법 1: Python 스크립트 파일 사용 (추천)

### 1단계: Colab 열기
- https://colab.research.google.com 접속
- 새 노트북 생성

### 2단계: 파일 업로드
1. 왼쪽 파일 탐색기(폴더 아이콘) 클릭
2. `hwasung_rna_colab.py` 파일 업로드

### 3단계: 실행
새 셀에 다음 코드 입력:

```python
# 라이브러리 설치
!pip install requests -q

# 스크립트 실행
exec(open('hwasung_rna_colab.py').read())
```

Shift + Enter로 실행

---

## 방법 2: 노트북 셀에 직접 코드 입력

### 셀 1: 라이브러리 설치
```python
!pip install requests -q
```

### 셀 2: 전체 코드 실행
`hwasung_rna_colab.py` 파일의 내용을 복사하여 셀에 붙여넣고 실행

---

## 결과 확인

실행 후 다음 파일이 생성됩니다:
- `hwasung_rna_data.json`: 수집된 모든 데이터
- (선택) HTML 보고서 생성 코드 추가 가능

### 파일 다운로드
1. 왼쪽 파일 탐색기에서 파일 우클릭
2. "다운로드" 선택

---

## 주의사항

- Colab에서는 네트워크 제한이 없으므로 DART API가 정상 작동합니다
- API 호출 제한에 주의하세요
- 세션이 종료되면 파일이 삭제될 수 있으므로 다운로드하세요

