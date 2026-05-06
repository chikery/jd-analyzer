"""JD Analyzer Web App"""
import streamlit as st
import sys
sys.path.append("src")  # src 폴더의 모듈을 import 가능하게

from jd import (
    fetch_jd_html,
    extract_text_from_html,
    extract_requirements,
    load_my_skills,
    skills_to_text,
    calculate_match,
)
st.set_page_config(
    page_title="JD Analyzer",
    page_icon="🔍",
    layout="centered"
)

st.title("🔍 JD Analyzer")
st.caption("채용공고 URL을 넣으면 내 스킬과의 매칭 점수를 분석해줍니다.")

# 입력 영역
url = st.text_input(
    "채용공고 URL",
    placeholder="https://www.wanted.co.kr/wd/..."
)

analyze = st.button("🔍 분석 시작", type="primary")

# 분석 영역
if analyze:
    if not url:
        st.error("URL을 입력해주세요.")
    else:
        try:
            # 1. JD 텍스트 추출
            with st.spinner("📥 JD 텍스트 추출 중..."):
                html = fetch_jd_html(url)
                text = extract_text_from_html(html)
            st.success(f"추출 완료: {len(text):,}자")

            # 2. 요구 역량 추출
            with st.spinner("🤖 LLM이 요구 역량 분석 중..."):
                requirements = extract_requirements(text)
            st.success(f"{requirements['company']} - {requirements['position']}")

            # 3. 내 스킬셋 로드
            with st.spinner("📋 내 스킬셋 로드 중..."):
                skills = load_my_skills()
                skills_text = skills_to_text(skills)

            # 4. 매칭 분석
            with st.spinner("⚖️ 매칭 점수 계산 중..."):
                match = calculate_match(skills_text, requirements)

            # 결과 표시
            st.divider()
            st.header(f"📊 매칭 점수: {match['match_score']}/100")

            st.subheader("✅ 매칭되는 역량")
            for s in match['matched_skills']:
                st.write(f"- {s}")

            if match['missing_must_have']:
                st.subheader("❌ 부족한 필수 역량")
                for s in match['missing_must_have']:
                    st.write(f"- {s}")

            if match['missing_nice_to_have']:
                st.subheader("⚠️ 부족한 우대 역량")
                for s in match['missing_nice_to_have']:
                    st.write(f"- {s}")

            st.info(f"💡 **조언**: {match['advice']}")
        except Exception as e:
            st.error(f"분석 중 오류가 발생했습니다: {str(e)}")
            st.info("URL이 올바른지 확인하거나, 잠시 후 다시 시도해주세요.")