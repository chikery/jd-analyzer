from google import genai

# 환경변수에서 자동으로 API 키 가져옴
client = genai.Client()

response = client.models.generate_content(
    model="gemini-2.5-flash-lite",
    contents="안녕! 한 문장으로 자기소개해줘."
)

print(response.text)