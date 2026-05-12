"""JD Analyzer Web App"""
import streamlit as st
import pandas as pd
import sys
sys.path.append("src")

from jd import (
    fetch_jd_html,
    extract_text_from_html,
    extract_requirements,
    load_my_skills,
    skills_to_text,
    calculate_match,
)


def render_sidebar(skills):
    with st.sidebar:
        st.header("👤 내 프로필")
        st.write(f"**이름**: {skills['name']}")

        if skills.get('languages'):
            st.markdown("**언어:**")
            for lang in skills['languages']:
                st.markdown(f"- {lang['name']}: {lang['level']}")

        with st.expander("📚 전체 스킬셋"):
            st.json(skills)


def run_analysis(url, skills_text) -> dict:
    with st.spinner("📥 JD 텍스트 추출 중..."):
        html = fetch_jd_html(url)
        text = extract_text_from_html(html)
    st.success(f"추출 완료: {len(text):,}자")

    with st.spinner("🤖 LLM이 요구 역량 분석 중..."):
        requirements = extract_requirements(text)
    st.success(f"{requirements['company']} - {requirements['position']}")

    with st.spinner("📋 내 스킬셋 로드 중..."):
        skills = load_my_skills()
        skills_text = skills_to_text(skills)

    with st.spinner("⚖️ 매칭 점수 계산 중..."):
        match = calculate_match(skills_text, requirements)

    return {
        "url": url,
        "company": requirements['company'],
        "position": requirements['position'],
        "score": match['match_score'],
        "match": match,
        "requirements": requirements,
        "text": text,
    }


def render_analysis_result(result):
    match = result['match']
    requirements = result['requirements']
    text = result['text']

    st.divider()

    col_score, col_info = st.columns([1, 2])
    with col_score:
        score = match['match_score']
        if score >= 80:
            emoji, delta = "🎯", "강력 매칭"
        elif score >= 60:
            emoji, delta = "⚡", "양호"
        else:
            emoji, delta = "🤔", "보강 필요"

        st.metric(label="매칭 점수", value=f"{score}/100", delta=delta)

    with col_info:
        st.markdown(f"### {emoji} {requirements['company']}")
        st.markdown(f"**{requirements['position']}**")

    st.divider()

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

    st.divider()
    st.info(f"💡 **AI 조언**: {match['advice']}")

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


def render_input_form(skills_text):
    url = st.text_input(
        "채용공고 URL",
        placeholder="https://www.wanted.co.kr/wd/..."
    )
    analyze = st.button("🔍 분석 시작", type="primary")

    if analyze:
        if not url:
            st.error("URL을 입력해주세요.")
        else:
            try:
                result = run_analysis(url, skills_text)
                st.session_state.history.append(result)
                render_analysis_result(result)
            except Exception as e:
                st.error(f"분석 중 오류가 발생했습니다: {str(e)}")
                st.info("URL이 올바른지 확인하거나, 잠시 후 다시 시도해주세요.")


def render_comparison_tab():
    if not st.session_state.history:
        st.info("아직 분석한 JD가 없습니다.")
        return

    st.write(f"지금까지 분석한 JD: **{len(st.session_state.history)}개**")

    sorted_history = sorted(
        st.session_state.history,
        key=lambda x: x['score'],
        reverse=True
    )

    table_data = [
        {
            "점수": f"{r['score']}/100",
            "회사": r['company'],
            "포지션": r['position'],
            "URL": r['url'],
        }
        for r in sorted_history
    ]
    st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("🔬 상세 비교")

    if len(sorted_history) >= 2:
        options = [
            f"{i+1}. {r['company']} - {r['position']} ({r['score']}점)"
            for i, r in enumerate(sorted_history)
        ]
        selected = st.multiselect("비교할 JD 선택 (최대 3개)", options, max_selections=3)

        if selected:
            cols = st.columns(len(selected))
            for col, opt in zip(cols, selected):
                idx = int(opt.split(".")[0]) - 1
                record = sorted_history[idx]
                with col:
                    st.metric(record['company'], f"{record['score']}/100")
                    st.caption(record['position'])
                    with st.expander("매칭 역량"):
                        for s in record['match']['matched_skills']:
                            st.markdown(f"- {s}")
                    with st.expander("부족 역량"):
                        for s in record['match']['missing_must_have']:
                            st.markdown(f"- ❌ {s}")
                        for s in record['match']['missing_nice_to_have']:
                            st.markdown(f"- ⚠️ {s}")
    else:
        st.info("비교하려면 2개 이상의 JD를 분석해주세요.")

    if st.button("🗑️ 분석 기록 초기화", type="secondary"):
        st.session_state.history = []
        st.rerun()


def main():
    st.set_page_config(
        page_title="JD Analyzer",
        page_icon="🔍",
        layout="centered"
    )

    st.title("🔍 JD Analyzer")

    skills = load_my_skills()
    skills_text = skills_to_text(skills)

    render_sidebar(skills)

    st.caption("채용공고 URL을 넣으면 내 스킬과의 매칭 점수를 분석해줍니다.")

    if "history" not in st.session_state:
        st.session_state.history = []

    tab_current, tab_compare = st.tabs(["🔍 현재 분석", "📊 분석 비교"])

    with tab_current:
        render_input_form(skills_text)

    with tab_compare:
        render_comparison_tab()


if __name__ == "__main__":
    main()
