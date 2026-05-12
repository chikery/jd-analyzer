# JD Analyzer 🔍

채용공고를 자동 분석해서 내 스킬과의 매칭도를 알려주는 AI 도구.

[데모 GIF 또는 스크린샷]

## ✨ 주요 기능

- 🌐 채용공고 URL 입력 → 자동 스크래핑 (JS 렌더링 사이트 지원)
- 🤖 LLM 기반 요구역량 추출 (필수/우대/기술스택 자동 분류)
- 📊 본인 스킬셋과 매칭 점수 계산 (0-100)
- 💡 부족 역량 + 보완 조언
- 📋 여러 JD 비교 기능 (점수 순 정렬)

## 🛠️ 기술 스택

- **Frontend**: Streamlit
- **Backend**: Python 3.10+
- **AI/ML**: Google Gemini API (gemini-2.5-flash-lite)
- **Web Scraping**: Playwright (JS 렌더링 대응) + BeautifulSoup4
- **Data**: pandas

## 🚀 사용법

### 설치
\`\`\`bash
git clone https://github.com/chikery/jd-analyzer.git
cd jd-analyzer
python -m venv venv
source venv/bin/activate  # Windows: venv\\Scripts\\activate
pip install -r requirements.txt
playwright install chromium
\`\`\`

### 환경변수 설정
\`\`\`bash
export GEMINI_API_KEY="your-api-key-here"
\`\`\`

### 내 프로필 설정
\`my_skills.json\`에 본인 정보 작성

### 실행
\`\`\`bash
# 웹 UI
streamlit run app.py

# CLI (선택)
python src/jd.py "https://example.com/jd/123"
\`\`\`

## 🧗 개발 과정에서 마주친 문제와 해결

### 1. JS 렌더링 페이지 처리
- 문제: 원티드 등 SPA 사이트에서 BeautifulSoup이 빈 페이지만 받아옴
- 해결: Playwright로 헤드리스 브라우저 사용, JS 실행 후 HTML 추출

### 2. 'networkidle' 타임아웃
- 문제: 대형 사이트는 트래커 트래픽이 계속 발생, networkidle 무한 대기
- 해결: domcontentloaded + 특정 selector 대기 방식으로 변경

### 3. 동적 콘텐츠 (더보기 버튼)
- 문제: Chrome에서는 우대사항이 더보기 버튼 뒤에 숨김 (Safari는 안 그럼)
- 해결: Playwright로 더보기 버튼 클릭 시뮬레이션

### 4. 성능 최적화
- 측정: HTML 가져오기 4.9s + LLM 호출 2.1s = 7.0s
- 개선: 이미지/폰트 차단 + 대기 시간 조정으로 5.5s (-30%)

## 📈 다음 버전 (v2 계획)

- 벡터 DB 기반 RAG로 본인 경험 자동 매칭
- 자소서 초안 자동 생성
- AWS 배포

## 🗓️ 개발 일지

- v1.0 (2026.05): 기본 분석 파이프라인 + Streamlit UI 완성
- v1.1 (예정): UI 개선
- v2.0 (예정): RAG 기반 자소서 생성

## 🧑 Author

Jay (chikery)