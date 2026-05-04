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
GEMINI_MODEL_EXTRACT = "gemini-2.5-flash-lite"  # JD 추출용 (가벼운 작업)
GEMINI_MODEL_MATCH = "gemini-2.5-flash"          # 매칭 분석용 (정밀 작업)

MY_SKILLS_FILE = "my_skills.json"
SEPARATOR = "=" * 50

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/121.0.0.0 Safari/537.36"
)

# 사이트마다 "더보기" 버튼 텍스트/클래스가 달라서 여러 개 시도
EXPAND_BUTTON_SELECTORS = [
    'button:has-text("상세 정보 더 보기")',
    'button:has-text("더 보기")',
    'button:has-text("더보기")',
    '[class*="more"]',
]

# Playwright 타임아웃 (ms)
PAGE_LOAD_TIMEOUT = 30_000
H1_WAIT_TIMEOUT = 10_000
EXPAND_BUTTON_TIMEOUT = 1_000
EXPAND_WAIT_MS = 500
LAZY_LOAD_WAIT_MS = 1_000


# ===== Low-level 헬퍼 =====

def _click_expand_button_if_exists(page) -> None:
    """더보기 버튼이 있으면 첫 번째로 발견된 것을 클릭.

    EXPAND_BUTTON_SELECTORS를 순서대로 시도하고,
    visible한 버튼을 찾으면 클릭 후 펼쳐질 시간을 준다.
    """
    for selector in EXPAND_BUTTON_SELECTORS:
        try:
            button = page.locator(selector).first
            if button.is_visible(timeout=EXPAND_BUTTON_TIMEOUT):
                button.click()
                print(f"[디버그] 더보기 버튼 클릭: {selector}")
                page.wait_for_timeout(EXPAND_WAIT_MS)
                return
        except Exception:
            continue


def _parse_json_response(text: str) -> dict:
    """LLM 응답에서 JSON 파싱.

    LLM이 응답을 ```json ... ``` 마크다운 블록으로 감싸는 경우를 처리한다.
    """
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    return json.loads(text)


# ===== 1단계: 페이지 가져오기 =====

def fetch_jd_html(url: str) -> str:
    """헤드리스 브라우저로 JS 렌더링 후 HTML 가져오기.

    JS로 동적 렌더링되는 사이트(원티드 등)는 requests로는 빈 페이지만 받아온다.
    Playwright로 실제 브라우저를 띄워 JS 실행 후의 최종 HTML을 가져온다.
    더보기 버튼이 있으면 클릭해서 가려진 콘텐츠도 펼친 후 추출한다.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=USER_AGENT,
            viewport={"width": 1280, "height": 800},
            locale="ko-KR"
        )
        # 텍스트만 필요하므로 이미지·폰트·미디어 요청 차단
        context.route(
            "**/*.{png,jpg,jpeg,gif,svg,webp,woff,woff2,ttf,mp4}",
            lambda route: route.abort()
        )
        page = context.new_page()

        page.goto(url, wait_until="domcontentloaded", timeout=PAGE_LOAD_TIMEOUT)

        try:
            page.wait_for_selector("h1", timeout=H1_WAIT_TIMEOUT)
        except Exception:
            print("[디버그] h1 못 찾음. 일단 진행.")

        page.wait_for_timeout(LAZY_LOAD_WAIT_MS)
        _click_expand_button_if_exists(page)

        html = page.content()
        browser.close()
    return html


# ===== 2단계: 텍스트 추출 =====

def extract_text_from_html(html: str) -> str:
    """HTML에서 본문 텍스트만 추출.

    광고·메뉴바·스타일 코드 등 노이즈 태그를 제거한 뒤
    줄바꿈 단위로 텍스트를 합친다.
    """
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "nav", "footer"]):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)


# ===== 3단계: LLM 분석 =====

def extract_requirements(jd_text: str) -> dict:
    """JD 텍스트에서 요구 역량을 구조화된 dict로 추출.

    Returns:
        {"company": str, "position": str,
         "must_have": list[str], "nice_to_have": list[str], "tech_stack": list[str]}
    """
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
        model=GEMINI_MODEL_EXTRACT,
        contents=prompt
    )
    return _parse_json_response(response.text)


def calculate_match(skills_text: str, jd_requirements: dict) -> dict:
    """내 스킬 vs JD 요구역량 비교 분석.

    Args:
        skills_text: skills_to_text()로 변환된 자연어 스킬 설명
        jd_requirements: extract_requirements()가 반환한 dict

    Returns:
        {"match_score": int, "matched_skills": list[str],
         "missing_must_have": list[str], "missing_nice_to_have": list[str], "advice": str}
    """
    client = genai.Client()

    requirements_text = (
        f"필수 역량: {', '.join(jd_requirements['must_have'])}\n"
        f"우대 역량: {', '.join(jd_requirements['nice_to_have'])}\n"
        f"기술 스택: {', '.join(jd_requirements['tech_stack'])}"
    )

    prompt = f"""너는 채용 매칭 전문가야.

지원자 정보:
{skills_text}

채용공고 요구사항:
{requirements_text}

다음을 JSON으로 답해줘. JSON 외 다른 말은 절대 쓰지 마:
{{
  "match_score": 0-100 사이 정수,
  "matched_skills": ["내가 가진 역량 중 매칭되는 것들"],
  "missing_must_have": ["내가 부족한 필수 역량들"],
  "missing_nice_to_have": ["내가 부족한 우대 역량들"],
  "advice": "이 공고에 지원할 때 보완하면 좋을 점 1-2문장"
}}
"""

    response = client.models.generate_content(
        model=GEMINI_MODEL_MATCH,
        contents=prompt
    )
    return _parse_json_response(response.text)


# ===== 4단계: 스킬셋 =====

def load_my_skills(filepath: str = MY_SKILLS_FILE) -> dict:
    """내 스킬셋 JSON 파일 로드."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def skills_to_text(skills: dict) -> str:
    """스킬셋 dict를 LLM이 읽기 좋은 자연어로 변환."""
    parts = [f"이름: {skills['name']}"]

    parts.append("\n[기술 스킬]")
    tech = skills['tech_skills']
    if tech.get('languages'):
        parts.append(f"- 언어: {', '.join(tech['languages'])}")
    if tech.get('ai_ml'):
        parts.append(f"- AI/ML: {', '.join(tech['ai_ml'])}")
    if tech.get('tools'):
        parts.append(f"- 도구: {', '.join(tech['tools'])}")

    if skills.get('soft_skills'):
        parts.append("\n[소프트 스킬]")
        for s in skills['soft_skills']:
            parts.append(f"- {s}")

    if skills.get('experiences'):
        parts.append("\n[경험]")
        for exp in skills['experiences']:
            parts.append(f"- {exp['title']} ({exp['role']}, {exp['duration']})")
            parts.append(f"  사용 스킬: {', '.join(exp['skills_used'])}")

    return "\n".join(parts)


# ===== 5단계: 결과 출력 =====

def print_requirements(result: dict) -> None:
    """요구 역량 결과를 보기 좋게 출력."""
    print(SEPARATOR)
    print(f"회사: {result['company']}")
    print(f"포지션: {result['position']}")

    print("\n[필수 역량]")
    for skill in result['must_have']:
        print(f"  - {skill}")

    print("\n[우대 역량]")
    for skill in result['nice_to_have']:
        print(f"  - {skill}")

    print("\n[기술 스택]")
    for tech in result['tech_stack']:
        print(f"  - {tech}")


def print_match_result(match: dict, requirements: dict) -> None:
    """매칭 결과를 보기 좋게 출력."""
    print(f"\n{SEPARATOR}")
    print(f"📊 매칭 점수: {match['match_score']}/100")
    print(SEPARATOR)

    print(f"\n🏢 {requirements['company']} - {requirements['position']}")

    print("\n✅ 매칭되는 역량:")
    for s in match['matched_skills']:
        print(f"  - {s}")

    if match['missing_must_have']:
        print("\n❌ 부족한 필수 역량:")
        for s in match['missing_must_have']:
            print(f"  - {s}")

    if match['missing_nice_to_have']:
        print("\n⚠️  부족한 우대 역량:")
        for s in match['missing_nice_to_have']:
            print(f"  - {s}")

    print(f"\n💡 조언: {match['advice']}")


# ===== 메인 실행 =====

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python src/jd.py [JD_URL]")
        sys.exit(1)

    url = sys.argv[1]
    print(f"분석 대상: {url}\n")

    print("[1/4] JD 텍스트 추출 중...")
    html = fetch_jd_html(url)
    text = extract_text_from_html(html)
    print(f"  └ 추출 완료: {len(text)}자")

    print("\n[2/4] 요구 역량 추출 중...")
    requirements = extract_requirements(text)
    print(f"  └ {requirements['company']} - {requirements['position']}")

    print("\n[3/4] 내 스킬셋 로드 중...")
    skills = load_my_skills()
    skills_text = skills_to_text(skills)
    print(f"  └ {skills['name']}님의 스킬셋 로드 완료")

    print("\n[4/4] 매칭 분석 중...")
    match = calculate_match(skills_text, requirements)

    print_match_result(match, requirements)
