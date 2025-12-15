# 데이터 백업 설정 가이드

Render의 무료 플랜에서는 서버가 재시작되면 데이터가 초기화됩니다. 이를 방지하기 위해 GitHub 자동 백업 기능을 사용할 수 있습니다.

## GitHub 자동 백업 설정 방법

### 1. GitHub Personal Access Token 생성

1. GitHub에 로그인
2. Settings → Developer settings → Personal access tokens → Tokens (classic)
3. "Generate new token (classic)" 클릭
4. 다음 권한 선택:
   - `repo` (전체 저장소 접근 권한)
5. 토큰 생성 후 복사 (한 번만 표시됨)

### 2. Render 환경 변수 설정

Render 대시보드에서 다음 환경 변수를 추가:

- `ENABLE_GITHUB_BACKUP`: `true` (백업 기능 활성화)
- `GITHUB_TOKEN`: 생성한 Personal Access Token

### 3. Git 사용자 정보 설정

Render의 빌드 명령에 다음을 추가하거나, 환경 변수로 설정:

```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

또는 환경 변수로:
- `GIT_USER_NAME`: Git 사용자 이름
- `GIT_USER_EMAIL`: Git 사용자 이메일

## 동작 방식

1. **서버 시작 시**: GitHub에서 최신 데이터를 자동으로 복원합니다.
2. **데이터 업데이트 시**: 변경된 데이터 파일을 자동으로 GitHub에 커밋/푸시합니다.
3. **백업 파일**: `data.json`과 `deleted_articles.json` 파일만 백업됩니다.

## 주의사항

- GitHub API 제한에 주의하세요 (시간당 5,000 요청)
- 백업은 데이터 업데이트 시마다 실행되므로, 너무 자주 업데이트하면 제한에 걸릴 수 있습니다.
- Personal Access Token은 안전하게 보관하세요.

## 대안 방법

GitHub 백업이 복잡하다면 다음 방법을 고려할 수 있습니다:

1. **Render Disk 스토리지** (유료 플랜): 영구 저장소 제공
2. **외부 데이터베이스**: PostgreSQL, MongoDB 등
3. **클라우드 스토리지**: AWS S3, Google Cloud Storage 등

