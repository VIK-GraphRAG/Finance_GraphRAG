# Streamlit Cloud 설정 가이드

## 🔐 권한 문제 해결

### 문제: "You do not have access to this app or it does not exist"

이 오류는 Streamlit Cloud가 GitHub 저장소에 접근할 수 없을 때 발생합니다.

---

## ✅ 해결 방법

### 방법 1: GitHub 저장소 권한 확인

1. **저장소가 Public인지 확인**
   - https://github.com/gyutaetae/Financial-GraphRAG 접속
   - 저장소가 "Private"이면 "Settings" → "Change visibility" → "Make public" 클릭
   - 또는 Streamlit Cloud Pro 계정 사용 (Private 저장소 지원)

2. **GitHub 계정 권한 확인**
   - Streamlit Cloud에서 사용하는 GitHub 계정이 저장소 소유자이거나 Collaborator인지 확인
   - 현재 로그인: `github.com/gyutaetae`
   - 저장소 소유자: `gyutaetae` ✅ (일치함)

### 방법 2: Streamlit Cloud 재연결

1. **Streamlit Cloud에서 로그아웃**
   - https://share.streamlit.io/ 접속
   - 우측 상단 프로필 → "Sign out"

2. **GitHub로 다시 로그인**
   - "Sign in" 클릭
   - GitHub 계정 선택: `gyutaetae` 계정으로 로그인
   - Streamlit Cloud 권한 승인

3. **앱 다시 생성**
   - "New app" 클릭
   - Repository: `gyutaetae/Financial-GraphRAG` 선택
   - Branch: `main`
   - Main file path: `src/streamlit_app.py`
   - "Deploy!" 클릭

### 방법 3: 저장소 이름 확인

**올바른 저장소 이름:**
- ✅ `gyutaetae/Financial-GraphRAG` (대소문자 주의!)

**잘못된 예시:**
- ❌ `gyutaetae/financial-graphrag` (소문자)
- ❌ `gyutaetae/Finance_GraphRAG` (언더스코어)

### 방법 4: GitHub OAuth 권한 재설정

1. **GitHub Settings 접속**
   - https://github.com/settings/applications 접속
   - "Authorized OAuth Apps" 클릭

2. **Streamlit Cloud 권한 확인**
   - "Streamlit Cloud" 찾기
   - "Revoke" 클릭 후 다시 승인

3. **Streamlit Cloud에서 재연결**
   - Streamlit Cloud에서 "Connect to GitHub" 다시 클릭

---

## 🚀 새 앱 배포 단계

### 1단계: Streamlit Cloud 접속
```
https://share.streamlit.io/
```

### 2단계: GitHub 계정으로 로그인
- "Sign in with GitHub" 클릭
- `gyutaetae` 계정 선택
- 권한 승인

### 3단계: 앱 생성
1. "New app" 또는 "Create app" 클릭
2. **Repository 선택:**
   - 드롭다운에서 `gyutaetae/Financial-GraphRAG` 선택
   - 또는 직접 입력: `gyutaetae/Financial-GraphRAG`
3. **Branch:** `main`
4. **Main file path:** `src/streamlit_app.py`
5. "Deploy!" 클릭

### 4단계: Secrets 설정
1. 앱 페이지에서 "Settings" (⚙️) 클릭
2. "Secrets" 탭 클릭
3. 다음 내용 입력:
   ```toml
   OPENAI_API_KEY = "sk-your-actual-api-key-here"
   OPENAI_BASE_URL = "https://api.openai.com/v1"
   ```
4. "Save" 클릭

### 5단계: 배포 확인
- 앱이 자동으로 빌드 및 배포됨
- 완료되면 URL 생성: `https://your-app-name.streamlit.app`
- 이 URL을 공유하면 누구나 접속 가능!

---

## 🔍 문제 진단 체크리스트

- [ ] GitHub 저장소가 Public인가?
- [ ] Streamlit Cloud에 로그인한 GitHub 계정이 저장소 소유자인가?
- [ ] 저장소 이름이 정확한가? (`gyutaetae/Financial-GraphRAG`)
- [ ] Branch 이름이 정확한가? (`main`)
- [ ] Main file path가 정확한가? (`src/streamlit_app.py`)
- [ ] GitHub OAuth 권한이 올바르게 설정되었는가?

---

## 🆘 여전히 문제가 있다면?

### 대안 1: 저장소를 Fork해서 사용
1. 다른 GitHub 계정으로 저장소 Fork
2. Streamlit Cloud에서 Fork한 저장소 사용

### 대안 2: Streamlit Community Cloud 대신 자체 서버
- AWS EC2, GCP, Azure 등 클라우드 서버 사용
- [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) 참조

### 대안 3: Streamlit Cloud Support 문의
- https://discuss.streamlit.io/ 에서 도움 요청
- 또는 support@streamlit.io로 문의

---

## 📝 참고사항

**저장소 정보:**
- GitHub: https://github.com/gyutaetae/Financial-GraphRAG
- Branch: `main`
- Main file: `src/streamlit_app.py`

**필수 환경 변수:**
- `OPENAI_API_KEY`: OpenAI API 키
- `OPENAI_BASE_URL`: https://api.openai.com/v1
