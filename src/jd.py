"""JD Analyzer v1 - Week 2

채용공고 URL을 받아 요구 역량을 구조화된 형식으로 추출한다.

사용법:
    python src/jd.py [JD_URL]
    python src/jd.py [JD_URL] [저장파일명]
"""
import json
import sys

from bs4 import BeautifulSoup
from google import genai
from playwright.sync_api import sync_playwright


# ===== 설정 =====
GEMINI_MODEL = "gemini-2.5-flash-lite"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/121.0.0.0 Safari/537.36"
)

# "더보기" 버튼 후보 셀렉터들
# 사이트마다 버튼 텍스트나 클래스가 다르므로 여러 개 시도
EXPAND_BUTTON_SELECTORS = [
    'button:has-text("상세 정보 더 보기")',
    'button:has-text("더 보기")',
    'button:has-text("더보기")',
    '[class*="more"]',
]


# ===== 1단계: 페이지 가져오기 =====
def fetch_jd_html(url: str) -> str:
    """헤드리스 브라우저로 JS 렌더링 후 HTML 가져오기.
    
    JS로 동적 렌더링되는 사이트(원티드 등)는 requests로는
    빈 페이지만 받아온다. Playwright로 실제 브라우저를 띄워
    JS 실행 후의 최종 HTML을 가져온다.
    
    더보기 버튼이 있으면 클릭해서 가려진 콘텐츠도 펼친 후 추출한다.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=USER_AGENT,
            viewport={"width": 1280, "height": 800},
            locale="ko-KR"
        )
        # 이미지/폰트/미디어 차단 (텍스트만 필요하므로)
        context.route(
            "**/*.{png,jpg,jpeg,gif,svg,webp,woff,woff2,ttf,mp4}",
            lambda route: route.abort()
        )
        page = context.new_page()
        
        # 1. 페이지 로드 (HTML 파싱 완료까지만 대기)
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        
        # 2. 제목 영역 나타날 때까지 대기 (JD 콘텐츠 렌더링 신호)
        try:
            page.wait_for_selector("h1", timeout=10000)
        except Exception:
            print("[디버그] h1 못 찾음. 일단 진행.")
        
        # 3. lazy loading 대비 추가 대기
        page.wait_for_timeout(1000)
        
        # 4. 더보기 버튼이 있으면 클릭해서 숨겨진 내용 펼치기
        _click_expand_button_if_exists(page)
        
        html = page.content()
        browser.close()
    return html


def _click_expand_button_if_exists(page) -> None:
    """더보기 버튼이 있으면 첫 번째로 발견된 것을 클릭."""
    for selector in EXPAND_BUTTON_SELECTORS:
        try:
            button = page.locator(selector).first
            if button.is_visible(timeout=1000):
                button.click()
                print(f"[디버그] 더보기 버튼 클릭: {selector}")
                page.wait_for_timeout(500)  # 펼쳐질 시간
                return
        except Exception:
            continue


# ===== 2단계: 텍스트 추출 =====
def extract_text_from_html(html: str) -> str:
    """HTML에서 본문 텍스트만 추출."""
    soup = BeautifulSoup(html, "html.parser")
    
    # 광고, 메뉴바, 스타일 코드 등 본문이 아닌 태그 제거
    for tag in soup(["script", "style", "nav", "footer"]):
        tag.decompose()
    
    # 줄바꿈 단위로 텍스트 추출
    text = soup.get_text(separator="\n", strip=True)
    
    # 빈 줄 정리
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)


# ===== 3단계: LLM으로 요구 역량 추출 =====
def extract_requirements(jd_text: str) -> dict:
    """JD 텍스트에서 요구 역량을 구조화된 dict로 추출."""
    client = genai.Client()
    
    prompt = f"""너는 채용공고 분석 전문가야.

다음 채용공고에서 정보를 추출해서 JSON 형식으로 답해줘.

채용공고:
{jd_text}

추출 가이드:
- must_have: '필수', '필요', '~이상의 경험' 등으로 표현된 것
- nice_to_have: '우대', '선호', 'Plus', '+α', '있으면 좋음' 등으로 표현된 것

다음 형식으로 답변해. JSON 외 다른 말은 절대 쓰지 마:
{{
  "company": "회사명",
  "position": "포지션명",
  "must_have": ["필수 역량1", "필수 역량2"],
  "nice_to_have": ["우대 역량1", "우대 역량2"],
  "tech_stack": ["사용 기술1", "사용 기술2"]
}}
"""
    
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt
    )
    
    return _parse_json_response(response.text)


def _parse_json_response(text: str) -> dict:
    """LLM 응답에서 JSON 파싱. ```json ... ``` 블록 처리."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    return json.loads(text)


# ===== 4단계: 결과 출력 =====
def print_requirements(result: dict) -> None:
    """요구 역량 결과를 보기 좋게 출력."""
    print("=" * 50)
    print(f"회사: {result['company']}")
    print(f"포지션: {result['position']}")
    
    print(f"\n[필수 역량]")
    for skill in result['must_have']:
        print(f"  - {skill}")
    
    print(f"\n[우대 역량]")
    for skill in result['nice_to_have']:
        print(f"  - {skill}")
    
    print(f"\n[기술 스택]")
    for tech in result['tech_stack']:
        print(f"  - {tech}")


# ===== 메인 실행 =====
import time

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python src/jd.py [JD_URL] [저장파일명(선택)]")
        sys.exit(1)
    
    url = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) >= 3 else None
    
    print(f"분석 대상: {url}\n")
    
    # === 시간 측정 시작 ===
    t0 = time.time()
    
    print("[1/2] JD 텍스트 추출 중...")
    html = fetch_jd_html(url)
    t1 = time.time()
    print(f"  └ HTML 가져오기: {t1-t0:.1f}초")
    
    text = extract_text_from_html(html)
    t2 = time.time()
    print(f"  └ 텍스트 추출: {t2-t1:.1f}초")
    print(f"  └ 추출 완료: {len(text)}자\n")
    
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"[알림] {output_file}에 저장됨\n")
    
    print("[2/2] 요구 역량 추출 중...")
    result = extract_requirements(text)
    t3 = time.time()
    print(f"  └ LLM 호출: {t3-t2:.1f}초")
    
    print_requirements(result)
    print(f"\n총 시간: {t3-t0:.1f}초")