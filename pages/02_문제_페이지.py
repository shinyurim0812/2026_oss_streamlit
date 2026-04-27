from __future__ import annotations

import time
import streamlit as st
import streamlit.components.v1 as components

from utils import (
    APP_TITLE,
    TYPE_META,
    apply_global_styles,
    build_answer_breakdown,
    get_option_contribution_label,
    build_meta_label,
    calculate_result,
    ensure_initialized,
    ensure_result_saved,
    format_complexity_label,
    format_players_label,
    format_time_label,
    get_ordered_questions,
    get_type_icon_uri,
    preprocess_boardgame_data_cached,
    reset_quiz_state,
    sidebar_status_box,
)


st.set_page_config(page_title=f"{APP_TITLE}", page_icon="🧩", layout="wide")


ensure_initialized()
apply_global_styles()
sidebar_status_box()

st.title("🏹 보드게임 성향 정밀 진단 테스트")
st.caption("던전 중심부까지 이동하며 선택을 저장하고, 모험이 끝날 때 내 직업(성향)과 그에 최적화된 보드게임(매칭 결과)을 확인합니다.")

if not st.session_state["logged_in"]:
    st.warning("이 페이지는 로그인 후 사용할 수 있습니다. 왼쪽 사이드바에서 개인페이지로 이동해 로그인해 주세요.")
    st.stop()


def render_quiz() -> None:
    ordered_questions = get_ordered_questions()

    if "intro_played" not in st.session_state:
        st.session_state["intro_played"] = False

    if not st.session_state["intro_played"] and st.session_state["current_question_index"] == 0:
        intro_text = "...오래된 던전의 문이 무겁게 열리며, 당신 앞에 모험의 제단이 나타납니다..."
        placeholder = st.empty()
        displayed_text = ""
        for char in intro_text:
            displayed_text += char
            placeholder.markdown(
                f"<h4 style='color:#7A5B44; text-align:center; padding:2rem 0; font-weight:700;'>{displayed_text}</h4>", 
                unsafe_allow_html=True
            )
            time.sleep(0.08)
        time.sleep(0.8)
        placeholder.empty()
        st.session_state["intro_played"] = True

    question_index = st.session_state["current_question_index"]
    question = ordered_questions[question_index]
    options = question["options"]
    labels = [label for label, _ in options]
    value_by_label = {label: value for label, value in options}
    answer_key = question["key"]
    current_value = st.session_state["answers"].get(answer_key)

    selected_index = None
    if current_value is not None:
        for idx, (_, value) in enumerate(options):
            if value == current_value:
                selected_index = idx
                break

    st.progress(len(st.session_state["answers"]) / len(ordered_questions))
    st.markdown(
        f"""
        <div class="question-card">
            <div class="question-step">{question_index + 1} / {len(ordered_questions)} 문항</div>
            <h3 style="margin:0 0 0.5rem 0;">{question['display_title']}</h3>
            <p style="margin:0; color:#75604f;">{question['caption']}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    selected_label = None
    st.write("가장 끌리는 옵션을 클릭하세요:")
    
    cols = st.columns(1)
    for idx, lbl in enumerate(labels):
        is_active = (selected_index == idx)
        btn_type = "primary" if is_active else "secondary"
        if cols[0].button(f"{'✅' if is_active else '⬜'} {lbl}", use_container_width=True, type=btn_type, key=f"btn_{answer_key}_{idx}_{question_index}"):
            st.session_state["answers"][answer_key] = value_by_label[lbl]
            st.rerun()
            
    if selected_index is not None:
        selected_label = labels[selected_index]

    st.write("")
    col1, col2 = st.columns([1, 1.2])
    with col1:
        if st.button("⬅ 이전", use_container_width=True, disabled=question_index == 0):
            st.session_state["current_question_index"] -= 1
            st.rerun()
    with col2:
        if st.button("다음 ➡", use_container_width=True, disabled=question_index == len(ordered_questions) - 1):
            if selected_index is None:
                st.error("옵션을 클릭해 답변을 선택해 주세요.")
            else:
                st.session_state["current_question_index"] += 1
                st.rerun()

    st.caption(f"현재 {len(st.session_state['answers'])} / {len(ordered_questions)} 걸음 이동 완료")

    if st.button("🎯 운명의 결과 열어보기", use_container_width=True, type="primary", disabled=len(st.session_state["answers"]) != len(ordered_questions)):
        st.session_state["quiz_submitted"] = True
        st.session_state["result_scroll_pending"] = True
        st.rerun()


def render_result() -> None:
    if st.session_state.get("result_scroll_pending"):
        components.html(
            """
            <script>
                window.parent.scrollTo({ top: 0, behavior: "smooth" });
            </script>
            """,
            height=0,
        )
        st.session_state["result_scroll_pending"] = False

    df = preprocess_boardgame_data_cached()

    if st.session_state["current_result"] is None:
        st.session_state["current_result"] = calculate_result(df, st.session_state["answers"])

    result = st.session_state["current_result"]
    ensure_result_saved(result)

    type_key = result["resolved_type"]
    type_meta = TYPE_META[type_key]
    profile = result["profile"]
    type_icon = get_type_icon_uri(type_key)

    # ── 최종 유형 카드 (진단 결과 요약) ──
    st.markdown(
        f"""
        <div class="panel-card">
            <div class="section-label">최종 진단 성향</div>
            <div class="type-hero">
                <img class="type-icon" src="{type_icon}" alt="{type_meta['label']}"/>
                <div>
                    <div class="metric-value" style="font-size:1.6rem;">{type_meta['emoji']} {type_meta['label']}</div>
                    <p class="quiet-text" style="margin-top:0.55rem;">{type_meta['summary']}</p>
                    <p class="quiet-text" style="margin-top:0.6rem;">{type_meta['detail']}</p>
                    <div class="meta-list">
                        <span class="mini-pill">👥 선호 인원: {format_players_label(profile['players_preference'])}</span>
                        <span class="mini-pill">⏱ 집중 시간: {format_time_label(profile['time_preference'])}</span>
                        <span class="mini-pill">🧠 수용 난이도: {format_complexity_label(profile['complexity_preference'])}</span>
                        <span class="mini-pill">🕐 진단 완료: {result['timestamp']}</span>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── 탭 시스템 도입 (분석 / 매칭 분리) ──
    tab_report, tab_matching = st.tabs(["🧬 1. 진단 분석 리포트", "🎮 2. 맞춤 매칭 보드게임"])

    with tab_report:
        # 1) 상세 계산 로직
        st.markdown("##### 🧬 결과 산출 과정")
        st.markdown(
            """
            <div style="background:#fdfcfb; padding:1.2rem 1.25rem; border-radius:12px; border:1px solid #eee; margin-bottom:1rem;">
                <p style="margin:0; font-size:1.18rem; font-weight:800; color:#4b3a2d;">
                    유형별 성향 진단(1~4번) + 보드게임 top3 제시(5~8번)
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        st.markdown("**📊 문항별 응답 분석**")
        st.caption("선택지에 숨겨진 성향 기여도를 확인하세요. 내가 선택한 항목은 진하게 표시됩니다.")

        for q in get_ordered_questions():
            q_key = q["key"]
            user_choice = st.session_state["answers"].get(q_key)

            st.markdown(f"**{q['display_title']}**")
            st.caption(q["caption"])
            for label, val in q["options"]:
                is_selected = (val == user_choice)
                contribution = get_option_contribution_label(q_key, val)

                if is_selected:
                    st.markdown(
                        f"&nbsp;&nbsp; <span style='font-size:1.1rem; font-weight:800; color:#4b3a2d;'> (●) {label} <small>({contribution})</small></span>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f"&nbsp;&nbsp; <span style='color:rgba(75,58,45,0.6);'> ( ) {label} <small>({contribution})</small></span>",
                        unsafe_allow_html=True,
                    )
            st.write("")

        st.divider()
        st.markdown("##### 📊 문항별 요약 데이터")
        breakdown = build_answer_breakdown(st.session_state["answers"])
        summary_data = [
            {"질문": item["question_title"], "내 선택": item["selected_label"], "진단 기여": item["contribution"]}
            for item in breakdown
        ]
        st.table(summary_data)

        st.divider()
        st.markdown("##### 📊 최종 능력치 합산 결과")
        st.caption("진단 알고리즘에 의해 합산된 당신의 영역별 성향 수치입니다.")

        score_cols = st.columns(4)
        for col, key in zip(score_cols, ("strategy", "party", "coop", "theme")):
            meta = TYPE_META[key]
            score = result["type_scores"][key]
            suffix = " 🏆" if key == type_key else ""
            col.metric(f"{meta['emoji']} {meta['label'].split(' ')[1]}", f"{score}점{suffix}")

        st.divider()
        st.markdown("##### 🎯 top3 보드게임 진단 필터링 과정")
        st.markdown(
            f"""
            **1️⃣ 성향 필터링**  
            전처리에서 미리 계산해둔 (dominant_type) 열 기준으로,  
            내 진단 유형인 {type_meta['label']} 와 일치하는 게임만 먼저 남김

            **2️⃣ 인원수 필터링**  
            남은 게임 중에서 (Min Players), (Max Players) 열을 기준으로  
            내가 응답한 인원 조건 {format_players_label(profile['players_preference'])} 에 맞는 게임만 추림

            **3️⃣ 플레이 시간 필터링**  
            (Play Time) 열을 바탕으로 만든 (time_bucket) 값을 기준으로  
            내가 선택한 {format_time_label(profile['time_preference'])} 조건에 맞는 게임만 다시 남김

            **4️⃣ 난이도 필터링**  
            (Complexity Average) 열을 바탕으로 만든 (complexity_bucket) 값을 기준으로  
            내가 선택한 {format_complexity_label(profile['complexity_preference'])} 조건까지 맞는 게임만 최종 후보로 남김

            **5️⃣ 결과 산출**  
            이렇게 남은 최종 후보 {result['stats']['filtered_count']:,}개 중에서  
            (BGG Rank) 열은 오름차순, (Rating Average) 열은 내림차순으로 정렬함  
            그중 상위 3개를 최종 결과로 제시함
            """
        )

    with tab_matching:
        st.markdown("##### 🎮 진단 기반 맞춤 매칭 보드게임 TOP 3")
        st.caption("당신의 진단 수치와 가장 높은 적합성을 보이는 보드게임 리스트입니다.")
        if not result["recommendations"]:
            st.warning("현재 조건을 모두 통과한 게임이 없어 TOP 3를 만들지 못했습니다. 인원, 시간, 난이도 조건을 조금 완화하면 결과가 나올 수 있습니다.")
        else:
            for item in result["recommendations"]:
                st.markdown(
                    f"""
                    <div class="result-card" style="margin-bottom:0.9rem;">
                        <div class="rank-badge">매칭 {item['rank_index']}순위</div>
                        <h3 style="margin:0 0 0.45rem 0;">{item['name']}</h3>
                        <div class="badge-row">
                            <span class="mini-pill">👥 {item['players_text']}</span>
                            <span class="mini-pill">⏱ {item['play_time_text']}</span>
                            <span class="mini-pill">{item['rating_display']}</span>
                            <span class="mini-pill">🏷 {item['domain']}</span>
                        </div>
                        <div style="margin:0.6rem 0 0.4rem;">
                            <div class="section-label">🧠 난이도</div>
                            {item['complexity_gauge']}
                        </div>
                        <div style="margin:0.6rem 0 0.4rem;">
                            <div class="section-label">🧐 매칭 분석</div>
                            <p class="quiet-text">{item['reason']}</p>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    st.markdown("##### 🃏 다른 유형도 함께 보기")
    type_keys = ("strategy", "party", "coop", "theme")
    col_left, col_right = st.columns(2)
    for i, key in enumerate(type_keys):
        meta = TYPE_META[key]
        active_class = " active" if key == type_key else ""
        col = col_left if i % 2 == 0 else col_right
        col.markdown(
            f"""
            <div class="type-card{active_class}">
                <div class="type-card-head">
                    <img class="type-card-icon" src="{get_type_icon_uri(key)}" alt="{meta['label']}"/>
                    <div>
                        <div class="metric-value">{meta['emoji']} {meta['label']}</div>
                        <div class="section-label">{meta['summary']}</div>
                    </div>
                </div>
                <div class="quiet-text">{meta['card_note']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ── 버튼 ──
    st.write("")
    if st.button("↩ 다시 테스트하기", use_container_width=True):
        reset_quiz_state()
        st.rerun()



if st.session_state["quiz_submitted"]:
    render_result()
else:
    render_quiz()
