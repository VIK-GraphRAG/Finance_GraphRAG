# Baseline Knowledge Base

기술 기업 분석을 위한 산업 공통 지식 베이스입니다.

## 데이터 구조

### 1. 공급망 매핑 (Supply Chain Mapping)

**파일:**
- `supply_chain_mapping.json` - 기업 간 관계, 티커 정보 (정량 데이터)
- `supply_chain_mapping.pdf` - 공급망 분석 리포트 (정성 데이터)

**내용:**
- ASML → TSMC → Nvidia → CSP 공급망 체인
- 기업 간 의존도 (dependency_level)
- 중요도 (criticality: critical/high/medium/low)
- 파트너십 정보

### 2. 산업 리스크 팩터 (Industry Risk Factors)

**파일:**
- `industry_risk_factors.pdf`

**내용:**
- 지정학적 위기 (Geopolitical Risks)
  - 미중 갈등, 대만 해협 긴장
  - 수출 통제, 제재
- 전력 수급 문제 (Power Supply Issues)
  - 데이터센터 전력 소비 증가
  - 재생에너지 전환 압력
- 금리 민감도 (Interest Rate Sensitivity)
  - CAPEX 투자 영향
  - 기업 가치 평가 변동

### 3. 규제 가이드라인 (Regulation Guidelines)

**파일:**
- `regulation_guidelines.pdf`

**내용:**
- **CHIPS Act (미국)**
  - 보조금 규모: $52B
  - 수혜 기업: Intel, TSMC (Arizona), Samsung
  - 조건: 중국 투자 제한 (Guardrails)
- **EU AI Act**
  - High-risk AI 시스템 규제
  - 반도체 기업 영향: Nvidia, AMD GPU 사용처 제한 가능
- **중국 수출 통제**
  - Advanced chip 수출 금지 (7nm 이하)
  - GPU 수출 제한 (A100/H100)

### 4. 기술 로드맵 (Technology Roadmap)

**파일:**
- `tech_roadmap.pdf`

**내용:**
- **공정 기술 (Process Technology)**
  - 2nm: TSMC (2025 양산), Samsung (2025 양산), Intel 20A (2024)
  - 1.4nm: TSMC (2027 예정)
  - GAA (Gate-All-Around): 2nm 이하 핵심 기술
- **메모리 기술 (Memory Technology)**
  - HBM3: 현재 양산 중 (SK Hynix, Samsung)
  - HBM3E: 2024 양산 (대역폭 1.15TB/s)
  - HBM4: 2026 예정 (2TB/s 목표)
- **패키징 기술 (Packaging Technology)**
  - CoWoS (Chip-on-Wafer-on-Substrate): TSMC 독점
  - Foveros: Intel 3D 패키징
  - X-Cube: Samsung 3D 패키징

## 사용 방법

### 1. Baseline 그래프 구축

```bash
python seed_baseline_graph.py
```

이 스크립트는:
1. JSON 데이터를 읽어 기업 노드 생성
2. 공급망 관계를 그래프로 구축
3. PDF 내용을 파싱하여 리스크/규제/기술 노드 추가

### 2. 사용자 PDF와 병합

사용자가 새로운 PDF를 업로드하면:
1. 티커 기반 엔티티 매칭 (예: 'NVDA' → 'Nvidia' 노드)
2. 기존 Baseline 지식과 결합
3. 새로운 관계만 추가 (증분 업데이트)

### 3. 쿼리 예시

**Q1: "대만 지진이 반도체 산업에 미치는 영향은?"**
- Baseline 그래프에서 Taiwan → TSMC → Nvidia/AMD 경로 탐색
- Perplexity로 최신 뉴스 검색
- 공급망 차질 분석 리포트 생성

**Q2: "CHIPS Act가 Intel에 어떤 영향을 주나?"**
- Regulation 노드에서 CHIPS Act → Intel 관계 찾기
- 보조금 규모, 조건 정보 제공
- 경쟁사 (TSMC, Samsung) 비교

**Q3: "HBM4 도입이 늦어지면 누가 영향받나?"**
- 기술 로드맵 노드에서 HBM4 정보 찾기
- SK Hynix/Samsung → Nvidia/AMD 의존 관계 추적
- 대체 공급사 분석 (Micron)

## 데이터 업데이트

Baseline 데이터는 분기별로 업데이트:
- 공급망 변화 (신규 파트너십, 의존도 변화)
- 규제 업데이트 (새로운 법안, 제재)
- 기술 마일스톤 달성 (양산 시점 확정)

업데이트 시:
```bash
python seed_baseline_graph.py --update
```

## 데이터 소스

- 기업 IR 자료
- 산업 리포트 (Gartner, IDC, TrendForce)
- 정부 발표 (CHIPS Act, EU AI Act)
- 기술 로드맵 (TSMC, Samsung, Intel 공개 자료)
