"""JD Analyzer v1 - Week 1"""
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

# 3단계: 실행
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python src/jd.py [JD_URL] [출력파일(선택)]")
        sys.exit(1)

    url = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) >= 3 else None

    print(f"분석 대상: {url}")

    html = fetch_jd_html(url)
    text = extract_text_from_html(html)

    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"저장 완료: {output_file} ({len(text)}자)")
    else:
        print(f"\n=== 추출된 JD 텍스트 ({len(text)}자) ===\n")
        print(text)