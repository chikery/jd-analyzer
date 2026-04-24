"""JD Analyzer v1 - Week 1"""
import requests
from bs4 import BeautifulSoup


def fetch_jd_html(url: str) -> str:
    """URL에서 HTML 가져오기"""
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; JDAnalyzer/0.1)"
    }
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    return response.text


if __name__ == "__main__":
    url = "https://www.wanted.co.kr/wd/340128"
    html = fetch_jd_html(url)
    print(f"받아온 HTML 길이: {len(html)} 글자")
    print(f"첫 500자: {html[:500]}")