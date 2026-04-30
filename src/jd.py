"""JD Analyzer v1 - Week 2"""
import json
import sys
from google import genai
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

# 1단계: 페이지 가져오기
def fetch_jd_html(url: str) -> str:
    """헤드리스 브라우저로 JS 렌더링 후 HTML 가져오기."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
            locale="ko-KR"
        )
        page = context.new_page()
        
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        
        try:
            page.wait_for_selector("h1", timeout=10000)
        except Exception:
            print("[디버그] h1 못 찾음. 일단 진행.")
        
        page.wait_for_timeout(2000)
        
        # "더보기" 버튼 찾아서 클릭
        # 원티드는 보통 "상세 정보 더 보기" 또는 화살표 버튼
        more_button_selectors = [
            'button:has-text("상세 정보 더 보기")',
            'button:has-text("더 보기")',
            'button:has-text("더보기")',
            '[class*="more"]',  # class 이름에 "more" 들어가는 것
        ]
        
        for selector in more_button_selectors:
            try:
                button = page.locator(selector).first
                if button.is_visible(timeout=1000):
                    button.click()
                    print(f"[디버그] 더보기 버튼 클릭: {selector}")
                    page.wait_for_timeout(1000)  # 펼쳐질 시간
                    break
            except Exception:
                continue
        
        html = page.content()
        browser.close()
    return html

# 2단계: 텍스트만 뽑아내기
def extract_text_from_html(html: str) -> str:
    # 1. BeautifulSoup에 html
    soup = BeautifulSoup(html, "html.parser")

    # 2. 필요 없는 태그(광고, 메뉴바, 스타일 코드 등)는 잘라내기
    for tag in soup(["script", "style", "nav", "footer"]):
        tag.decompose()  # .decompose()는 아예 파괴해서 없애버린다는 뜻

    # 3. 태그들 싹 걷어내고 글자만 추출 (줄바꿈 단위로 구분)
    text = soup.get_text(separator="\n", strip=True)

    # 4. 빈 줄 정리
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)

def summarize_jd(jd_text: str) -> str:
    """JD 텍스트를 한 줄로 요약"""
    client = genai.Client()
    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=f"다음 채용공고를 한 줄로 요약해줘:\n\n{jd_text}"
    )
    return response.text

def extract_requirements(jd_text: str) -> dict:
    """JD에서 요구 역량을 구조화된 형식으로 추출"""
    client = genai.Client()

    prompt = f"""너는 채용공고 분석 전문가야.

다음 채용공고에서 정보를 추출해서 JSON 형식으로 답해줘.

채용공고:
{jd_text}

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
        model="gemini-2.5-flash-lite",
        contents=prompt
    )

    # JSON 파싱
    text = response.text.strip()
    # 가끔 ```json ... ``` 블록으로 감싸서 옴 — 제거
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()

    return json.loads(text)

# 3단계: 실행
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python src/jd.py [JD_URL] [저장파일명(선택)]")
        sys.exit(1)

    url = sys.argv[1]
    # 두 번째 인자가 있으면 파일명으로 저장, 없으면 None
    output_file = sys.argv[2] if len(sys.argv) >= 3 else None

    print(f"분석 대상: {url}\n")

    print("[1/2] JD 텍스트 추출 중...")
    html = fetch_jd_html(url)
    text = extract_text_from_html(html)
    print(f"추출 완료: {len(text)}자\n")

    # --- 여기서 파일 저장 로직 추가 ---
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"[알림] 원본 텍스트가 {output_file}에 저장되었습니다.\n")
    # ------------------------------

    print("[2/2] 요구 역량 추출 중...")
    result = extract_requirements(text)

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