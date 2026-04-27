"""JD Analyzer v1 - Week 2"""
from google import genai
import sys
import requests
from bs4 import BeautifulSoup

# 1단계: 페이지 가져오기
def fetch_jd_html(url: str) -> str:
    headers = {"User-Agent": "Mozilla/5.0 (compatible; JDAnalyzer/0.1)"}
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    return response.text

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

# 3단계: 실행
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python src/jd.py [JD_URL]")
        sys.exit(1)

    url = sys.argv[1]
    print(f"분석 대상: {url}")

    # 1. JD 텍스트 가져오기
    print("\n[1/2] JD 텍스트 추출 중...")
    html = fetch_jd_html(url)
    text = extract_text_from_html(html)
    print(f"추출 완료: {len(text)}자")

    # 2. LLM 요약
    print("\n[2/2] AI 요약 중...")
    summary = summarize_jd(text)
    print(f"\n=== 요약 ===")
    print(summary)