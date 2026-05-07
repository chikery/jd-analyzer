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
# 페이지 상단에서 한 번 로드
skills = load_my_skills()
skills_text = skills_to_text(skills)

# 사이드바 (왼쪽)
with st.sidebar:
    st.header("👤 내 프로필")
    st.write(f"**이름**: {skills['name']}")

    if skills.get('languages'):
        st.markdown("**언어:**")
        for lang in skills['languages']:
            st.markdown(f"- {lang['name']}: {lang['level']}")

    with st.expander("📚 전체 스킬셋"):
        st.json(skills)
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

            # 매칭 점수 + 회사 정보 (상단)
            col_score, col_info = st.columns([1, 2])

            with col_score:
                score = match['match_score']
                # 점수에 따라 다른 이모지
                if score >= 80:
                    emoji = "🎯"
                    delta = "강력 매칭"
                elif score >= 60:
                    emoji = "⚡"
                    delta = "양호"
                else:
                    emoji = "🤔"
                    delta = "보강 필요"

                st.metric(
                    label="매칭 점수",
                    value=f"{score}/100",
                    delta=delta
                )

            with col_info:
                st.markdown(f"### {emoji} {requirements['company']}")
                st.markdown(f"**{requirements['position']}**")

            st.divider()

            # 매칭/부족 역량 (좌우로)
            col_match, col_missing = st.columns(2)

            with col_match:
                st.subheader("✅ 매칭되는 역량")
                if match['matched_skills']:
                    for s in match['matched_skills']:
                        st.markdown(f"- {s}")
                else:
                    st.write("(없음)")

            with col_missing:
                st.subheader("❌ 부족한 역량")
                if match['missing_must_have']:
                    st.markdown("**[필수]**")
                    for s in match['missing_must_have']:
                        st.markdown(f"- {s}")
                if match['missing_nice_to_have']:
                    st.markdown("**[우대]**")
                    for s in match['missing_nice_to_have']:
                        st.markdown(f"- {s}")
                if not match['missing_must_have'] and not match['missing_nice_to_have']:
                    st.write("(부족한 역량 없음 — 강력 매칭!)")

            # 조언 (하단 전체 폭)
            st.divider()
            st.info(f"💡 **AI 조언**: {match['advice']}")

            # 추가 정보 (접혀있음)
            with st.expander("📋 추출된 JD 요구사항 보기"):
                st.markdown("**필수 역량:**")
                for s in requirements['must_have']:
                    st.markdown(f"- {s}")
                st.markdown("**우대 역량:**")
                for s in requirements['nice_to_have']:
                    st.markdown(f"- {s}")
                st.markdown("**기술 스택:**")
                st.markdown(", ".join(requirements['tech_stack']))

            with st.expander("📄 JD 원문 보기"):
                st.text(text[:2000] + ("..." if len(text) > 2000 else ""))

        except Exception as e:
            st.error(f"분석 중 오류가 발생했습니다: {str(e)}")
            st.info("URL이 올바른지 확인하거나, 잠시 후 다시 시도해주세요.")