"""JD Analyzer Web App - Day 1 Hello World"""
import streamlit as st

# 페이지 설정
st.set_page_config(
    page_title="JD Analyzer",
    page_icon="🔍",
    layout="centered"
)

# 헤더
st.title("🔍 JD Analyzer")
st.caption("채용공고를 분석해 내 스킬과 매칭해주는 도구")

# 본문
st.write("Hello, World! Streamlit이 돌아가는 중!")

# 입력 테스트
name = st.text_input("이름을 입력하세요")
if name:
    st.success(f"안녕하세요, {name}님! 👋")

st.divider()  # 구분선

st.header("위젯 실험실")

# 슬라이더
age = st.slider("나이", 0, 100, 25)
st.write(f"나이: {age}")

# 셀렉트박스
job = st.selectbox(
    "직무 선택",
    ["AI 프로덕트 엔지니어", "AI 서비스 기획", "그로스 마케터"]
)
st.write(f"선택한 직무: {job}")

# 컬럼 (가로로 나누기)
col1, col2 = st.columns(2)
with col1:
    st.metric("매칭 점수", "72/100", "+5")
with col2:
    st.metric("부족 역량", "3개", "-2")

# 코드 블록
st.code("python src/jd.py 'URL'", language="bash")

# 정보 박스
st.info("이건 정보 메시지")
st.success("이건 성공 메시지")
st.warning("이건 경고 메시지")
st.error("이건 에러 메시지")