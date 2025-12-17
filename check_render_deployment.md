# Render 배포 상태 확인 가이드

## 1. GitHub 코드 확인

### 최신 커밋 확인
현재 로컬과 GitHub가 동기화되어 있는지 확인:
- 로컬: `git log --oneline -5`
- GitHub: https://github.com/kimjinyong2504-prog/competitor-monitoring/commits/main

### 주요 파일 확인
다음 파일들이 GitHub에 있는지 확인:
- ✅ `unified_server.py` - 백업/복원 로직 포함
- ✅ `data_backup.py` - GitHub 백업 모듈
- ✅ `README_BACKUP.md` - 백업 가이드

---

## 2. Render 환경 변수 설정 확인

Render 대시보드에서 다음 환경 변수가 설정되어 있는지 확인:

### 필수 환경 변수
1. **ENABLE_GITHUB_BACKUP**: `true`
   - GitHub 백업 기능 활성화

2. **GITHUB_TOKEN** (선택사항)
   - GitHub Personal Access Token
   - 백업 시 필요할 수 있음

3. **GITHUB_REPO** (선택사항)
   - 저장소 URL: `kimjinyong2504-prog/competitor-monitoring`

### 확인 방법
1. Render 대시보드 → 서비스 선택
2. "Environment" 탭 클릭
3. 환경 변수 목록 확인

---

## 3. Render 로그 확인

### 서버 시작 시 로그 확인
Render 대시보드 → "Logs" 탭에서 다음 메시지 확인:

#### 정상 작동 시 나타나는 메시지:
```
[초기화] GitHub 백업이 활성화되어 있습니다.
[복원] GitHub에서 데이터 복원 시작...
[복원] 데이터 복원 완료
```

또는

```
[초기화] GitHub 백업이 비활성화되어 있습니다. (ENABLE_GITHUB_BACKUP=false)
[초기화] 참고: 데이터 영구 저장을 위해 ENABLE_GITHUB_BACKUP=true를 설정하세요.
```

### 데이터 업데이트 시 로그 확인
새로고침 버튼을 눌렀을 때:
```
[백업] 화승 알엔에이 데이터 백업 시작...
[백업] 백업 완료
```

---

## 4. 기능 테스트

### 테스트 시나리오

1. **초기 상태 확인**
   - 서비스 접속: https://drb-auto.onrender.com/hwasung
   - 현재 기사 수 확인

2. **데이터 업데이트**
   - 새로고침 버튼 클릭
   - 새로운 기사가 추가되는지 확인

3. **서버 재시작 시뮬레이션**
   - Render 대시보드 → "Manual Deploy" → "Deploy latest commit"
   - 또는 서비스 재시작

4. **데이터 복원 확인**
   - 서비스 재시작 후
   - 이전에 추가한 기사가 여전히 있는지 확인
   - 기사 수가 유지되는지 확인

---

## 5. 문제 해결

### 문제: 백업이 작동하지 않음

**확인 사항:**
1. `ENABLE_GITHUB_BACKUP=true` 환경 변수 설정 확인
2. `data_backup.py` 파일이 GitHub에 있는지 확인
3. Render 로그에서 오류 메시지 확인

**해결 방법:**
- Render 환경 변수에 `ENABLE_GITHUB_BACKUP=true` 추가
- 서비스 재배포

### 문제: 데이터가 복원되지 않음

**확인 사항:**
1. GitHub 저장소에 `data.json` 파일이 있는지 확인
2. Render 로그에서 복원 메시지 확인
3. 파일 경로가 올바른지 확인

**해결 방법:**
- GitHub 저장소에서 데이터 파일 확인
- `data_backup.py`의 경로 설정 확인

### 문제: Git 관련 오류

**확인 사항:**
1. Render에서 Git 명령어 실행 가능한지 확인
2. Git 사용자 정보 설정 확인

**해결 방법:**
- `data_backup.py`에서 Git 설정 확인
- 환경 변수로 Git 사용자 정보 설정

---

## 6. 수동 확인 명령어

Render의 Shell에서 직접 확인 (가능한 경우):

```bash
# 환경 변수 확인
echo $ENABLE_GITHUB_BACKUP

# 데이터 파일 확인
ls -la 251215/data.json
ls -la 251215_yuil/data.json
ls -la 251215_aia/data.json

# Git 상태 확인
git status
git log --oneline -5
```

---

## 7. 예상 동작

### 정상 작동 시:
1. 서버 시작 → GitHub에서 데이터 복원
2. 새로고침 → 데이터 업데이트 → GitHub에 백업
3. 서버 재시작 → GitHub에서 데이터 복원 → 이전 데이터 유지

### 백업 비활성화 시:
1. 서버 시작 → 로컬 파일에서만 로드
2. 새로고침 → 로컬 파일에만 저장
3. 서버 재시작 → 데이터 초기화 (Render 무료 플랜)

---

## 확인 체크리스트

- [ ] GitHub에 최신 코드가 올라가 있음
- [ ] Render 환경 변수 `ENABLE_GITHUB_BACKUP=true` 설정
- [ ] Render 로그에서 백업/복원 메시지 확인
- [ ] 서버 재시작 후 데이터 유지 확인
- [ ] 새로고침 후 GitHub에 백업되는지 확인



