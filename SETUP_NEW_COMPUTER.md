# 다른 컴퓨터에서 실행하기 🖥️

## 1단계: 저장소 클론

```bash
# GitHub 저장소 클론
git clone https://github.com/gyutaetae/Financial-GraphRAG.git
cd Financial-GraphRAG

# 또는 특정 브랜치 클론
git clone -b fix/reliability-precision-enhancement https://github.com/gyutaetae/Financial-GraphRAG.git
cd Financial-GraphRAG
```

## 2단계: 환경 변수 설정

```bash
# .env 파일 생성
cp env.docker.example .env

# .env 파일 편집
nano .env  # Mac/Linux
# 또는
notepad .env  # Windows
```

**필수 입력 항목:**

```bash
# OpenAI API 키 (필수)
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx

# Neo4j 비밀번호 (필수, 강력한 비밀번호 사용)
NEO4J_PASSWORD=YourSecurePassword123!

# Tavily API 키 (선택사항, 웹 검색 기능 사용 시)
TAVILY_API_KEY=tvly-xxxxxxxxxxxxx
```

## 3단계: Docker 실행

### 방법 A: 자동 배포 스크립트 사용 (권장)

```bash
# 실행 권한 부여 (Mac/Linux)
chmod +x deploy.sh

# 배포 실행
./deploy.sh
```

### 방법 B: 수동 실행

```bash
# 모든 서비스 빌드 및 실행
docker-compose up -d --build

# 로그 확인
docker-compose logs -f
```

## 4단계: 서비스 확인

### 컨테이너 상태 확인

```bash
docker-compose ps
```

모든 컨테이너가 `Up` 상태여야 합니다:
- `finance-graphrag-neo4j` (포트 7474, 7687)
- `finance-graphrag-ollama` (포트 11434)
- `finance-graphrag-backend` (포트 8000)
- `finance-graphrag-frontend` (포트 8501)

### 접속 URL

- **Streamlit UI**: http://localhost:8501
- **FastAPI API**: http://localhost:8000/docs
- **Neo4j Browser**: http://localhost:7474

## 5단계: 모델 다운로드 확인

Ollama 모델이 자동으로 다운로드됩니다:
- `qwen2.5-coder:3b` (약 1.9GB)
- `nomic-embed-text` (약 274MB)

다운로드 진행상황 확인:

```bash
docker logs finance-graphrag-ollama-loader -f
```

## 문제 해결

### 포트가 이미 사용 중인 경우

```bash
# 사용 중인 포트 확인
lsof -i :8000   # Mac/Linux
netstat -ano | findstr :8000  # Windows

# docker-compose.yml에서 포트 변경
# 예: "8000:8000" → "8001:8000"
```

### Docker가 설치되지 않은 경우

**Mac:**
```bash
# Homebrew로 설치
brew install --cask docker
```

**Windows:**
- Docker Desktop 다운로드: https://www.docker.com/products/docker-desktop

**Linux:**
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

### 컨테이너가 시작되지 않는 경우

```bash
# 로그 확인
docker-compose logs backend
docker-compose logs frontend
docker-compose logs neo4j

# 컨테이너 재시작
docker-compose restart

# 전체 재시작 (데이터 유지)
docker-compose down
docker-compose up -d
```

### GPU 에러가 발생하는 경우

GPU가 없는 컴퓨터에서는 `docker-compose.yml`의 GPU 설정이 주석 처리되어 있어야 합니다.
이미 주석 처리되어 있으므로 문제없이 실행됩니다.

## 네트워크 공유 (팀원 접속)

### 같은 네트워크에서 접속

```bash
# 본인 IP 확인
ifconfig | grep "inet " | grep -v 127.0.0.1  # Mac/Linux
ipconfig  # Windows

# 팀원 접속 URL
http://YOUR_IP:8501  # Streamlit
http://YOUR_IP:8000  # API
```

### 방화벽 설정

**Mac:**
```bash
# 방화벽에서 포트 허용
sudo pfctl -f /etc/pf.conf
```

**Windows:**
- Windows Defender 방화벽 → 고급 설정 → 인바운드 규칙 → 새 규칙
- 포트: 8000, 8501, 7474, 7687 허용

## 빠른 참조

```bash
# 서비스 시작
docker-compose up -d

# 서비스 중지
docker-compose down

# 서비스 재시작
docker-compose restart

# 로그 확인
docker-compose logs -f [서비스명]

# 컨테이너 상태 확인
docker-compose ps

# 전체 초기화 (데이터 삭제)
docker-compose down -v
```

## 다음 단계

1. **데이터 인덱싱**: Streamlit UI → "Data Ingestion" 탭에서 PDF 업로드
2. **질문하기**: "Query Interface" 탭에서 질문 입력
3. **도메인 분석**: "Domain Analysis" 탭에서 Event/Actor/Asset 관계 탐색

---

**문의**: GitHub Issues 또는 팀 채널로 연락 주세요!
