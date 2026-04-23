"""
JD Analyzer - v1 진행 중
TODO:
- Week 1: URL → HTML → 텍스트 추출
- Week 2: Gemini로 요구 역량 추출
- Week 3: Streamlit UI
"""
from google import genai

def test_api_connection():
    """Gemini API 연결 테스트."""
    # API 키는 환경변수에서 자동으로 가져옵니다.
    client = genai.Client()
    response = client.models.generate_content(
        model="gemini-2.5-flash-lite", # 아까 성공했던 모델명으로 바꿨어요!
        contents="안녕! 한 문장으로 자기소개해줘."
    )
    return response.text

if __name__ == "__main__":
    result = test_api_connection()
    print(result)