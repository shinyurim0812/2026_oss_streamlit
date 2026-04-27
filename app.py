from __future__ import annotations

import streamlit as st

from utils import (
    APP_TITLE,
    STUDENT_ID,
    STUDENT_NAME,
    apply_global_styles,
    ensure_initialized,
    measure_preprocessing_time,
    get_type_score_preview,
    clear_all_cached_data,
    sidebar_status_box,
)


st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🎲",
    layout="wide",
    initial_sidebar_state="expanded",
)

ensure_initialized()
apply_global_styles()
sidebar_status_box()

st.markdown(
    f"""
    <div class="hero-card">
        <div class="hero-kicker">QUEST & ADVENTURE GUIDE</div>
        <h1>🎲 {APP_TITLE}</h1>
        <div class="hero-badges">
            <span class="pill identity-pill">🎓 학번 2023204093</span>
            <span class="pill identity-pill">👤 이름 신유림</span>
        </div>

    </div>
    """,
    unsafe_allow_html=True,
)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        """
        <div class="menu-card">
            <div class="menu-icon">🧩</div>
            <h3>보드게임 성향 퀴즈</h3>
            <p>7개의 질문에 답하면 보드게임 성향 4가지인 (전략, 파티, 협력, 테마) 중 나와 맞는 유형 판별 + 맞춤형 보드게임 top3를 제시해줍니다.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        """
        <div class="menu-card">
            <div class="menu-icon">👤</div>
            <h3>로그인 & 개인 기록</h3>
            <p>로그인 후 최근 결과와 이전 기록을 확인하고, 비밀번호를 변경할 수 있습니다.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col3:
    st.markdown(
        """
        <div class="menu-card">
            <div class="menu-icon">⚡</div>
            <h3>데이터 전처리 캐싱</h3>
            <p>원본 CSV에 없는 4가지 유형 점수를 미리 계산하고, st.cache_data로 재사용해 결과 계산 속도를 높였습니다.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

st.markdown(
    """
    <div class="panel-card" style="text-align: center; max-width: 600px; margin: 0 auto;">
        <h3 style="margin-top:0.2rem; color: #4A3525; margin-bottom: 0.5rem;">📜 앱 여정 시작하기</h3>
        <p style="color: #4A3525; font-size: 1rem; margin-bottom: 0.5rem;">2만여 개의 전설적인 게임들 속에서 당신과 운명적으로 매칭될 아이템을 찾아드립니다.</p>
    </div>
    <style>
    @keyframes swirlBorder {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    @keyframes pulseGlow {
        0% { box-shadow: 0 0 20px rgba(139, 90, 43, 0.4); transform: scale(1); filter: brightness(1); }
        50% { box-shadow: 0 0 50px rgba(139, 90, 43, 0.8), 0 0 80px rgba(214, 168, 124, 0.5); transform: scale(1.08); filter: brightness(1.2); }
        100% { box-shadow: 0 0 20px rgba(139, 90, 43, 0.4); transform: scale(1); filter: brightness(1); }
    }
    /* 버튼 타겟팅 */
    div.stButton > button[kind="primary"] {
        margin: 2.5rem auto !important;
        display: block !important;
        max-width: 450px !important;
        height: 100px !important; /* 포탈 높이 확보 */
        font-size: 1.4rem !important;
        font-weight: 900 !important;
        border-radius: 999px !important;
        border: 4px solid rgba(255, 252, 247, 0.4) !important;
        background: linear-gradient(45deg, #4E382A, #7A5B44, #C28E60, #7A5B44) !important;
        background-size: 300% 300% !important;
        animation: swirlBorder 3s linear infinite, pulseGlow 2s infinite ease-in-out !important;
        color: #FDF8F5 !important;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        cursor: pointer !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.write("")
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("🌀 모험의 차원문 열기 (RESET & START)", type="primary", use_container_width=True):
        from utils import reset_quiz_state
        reset_quiz_state()
        st.session_state["intro_played"] = False
        st.switch_page("pages/02_문제_페이지.py")


st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

# ── 캐싱 기능 시연 섹션 ──
st.subheader("⚡ 보드게임 데이터 전처리 및 전처리 결과 캐싱")
st.caption(
    """
    원본 CSV에는 바로 사용할 수 있는 유형 정보가 없습니다.
    그래서 이 앱은 실행 시 **20,343개의 보드게임 전체를 전처리**하여
    유형 점수, 대표 유형, 플레이 시간/난이도 구간 정보를 먼저 계산합니다.
    이 전처리 결과를 캐시에 저장해두고, 이후 퀴즈 결과 계산과 보드게임 매칭에 재사용합니다.
    """
)
st.markdown(
    """
    <div class="dataset-note">
        <strong>사용 데이터</strong><br>
        Kaggle의 <code>Board Games</code> 데이터셋
        (<code>andrewmvd/board-games</code>)을 바탕으로 정리한 CSV를 사용했습니다.
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown(
    """
    <div class="panel-card accent-card">
        <div class="section-label">전처리에서 한 작업</div>
        <p class="quiet-text" style="margin-top:0.45rem;">
            - mechanics, domains 태그 분리<br>
            - play_time 기반 time_bucket 생성<br>
            - complexity_average 기반 complexity_bucket 생성<br>
            - 4개 유형 점수 계산<br>
            - dominant_type 계산
        </p>
        <div class="section-label" style="margin-top:1rem;">왜 캐싱이 필요한가</div>
        <p class="quiet-text" style="margin-top:0.45rem;">
            같은 CSV를 다시 읽고, 2만 개 전체 게임에 대해 위 전처리를 매번 반복하면 시간이 오래 걸립니다.<br>
            그래서 <strong>전처리 결과 전체를 st.cache_data로 저장</strong>해두고, 다음 실행부터는 다시 계산하지 않고 재사용합니다.
        </p>
        <div class="section-label" style="margin-top:1rem;">캐싱 활용 위치</div>
        <p class="quiet-text" style="margin-top:0.45rem;">
            저장된 전처리 결과는 이후 퀴즈 결과 화면에서 유형 판별 이후 인원수, 플레이 시간, 난이도 필터링과 최종 게임 매칭에 그대로 사용됩니다.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

if "cached_run_count" not in st.session_state:
    st.session_state["cached_run_count"] = 0

_tab_no_cache, _tab_cached = st.tabs(["🐢 캐싱 없이 실행", "⚡ 캐싱 적용 실행"])

with _tab_no_cache:
    st.markdown(
        """
        <div class="panel-card">
            <div class="section-label">매번 전체 전처리 수행 (✋ 캐싱 미적용)</div>
            <p class="quiet-text" style="margin-top:0.5rem;">
                매 실행마다 CSV를 새로 읽고, 태그 분리·버킷 생성·유형 점수 계산·dominant_type 계산을 다시 수행합니다.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("🐢 실행 (캐시 X)", use_container_width=True, key="btn_no_cache"):
        with st.spinner("🐢 20,343개 보드게임 유형 분류 중... (캐싱 없음)"):
            elapsed, df_result = measure_preprocessing_time(use_cache=False)
        st.session_state["demo_uncached_time"] = elapsed
        st.error(f"⏱️ 소요 시간: **{elapsed:.2f}초** — 캐싱이 없으니 매번 이 시간이 반복됩니다.")
        st.markdown("**분류 결과 예시 (전체 전처리 결과)**")
        st.dataframe(
            get_type_score_preview(df_result, n=None, rank_limit=None),
            use_container_width=True,
            hide_index=True,
        )

with _tab_cached:
    st.markdown(
        """
        <div class="panel-card accent-card">
            <div class="section-label">첫 실행 시 저장, 이후 재사용 (⚡ @st.cache_data)</div>
            <p class="quiet-text" style="margin-top:0.5rem;">
                첫 실행은 CSV 로드와 전처리 결과를 계산하고 저장하므로 시간이 걸립니다.<br>
                두 번째 실행부터는 <strong>저장된 전처리 결과 전체를 재사용하므로 즉시 표시</strong>됩니다.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    btn_label = "⚡ 실행 (캐시 O)"
    if st.button(btn_label, use_container_width=True, key="btn_cached"):
        is_first_run = (st.session_state["cached_run_count"] == 0)
        
        elapsed_c, df_result_c = measure_preprocessing_time(use_cache=True)
        st.session_state["cached_run_count"] += 1
        st.session_state["demo_cached_time"] = elapsed_c
        
        if is_first_run:
            st.warning(f"⏳ 소요 시간: **{elapsed_c:.2f}초** — (첫 실행) 데이터를 분석하고 캐시에 저장했습니다.")
        else:
            st.success(f"⚡ 소요 시간: **{elapsed_c:.4f}초** — (재실행) 캐싱된 결과를 즉시 재사용합니다!")
            uncached = st.session_state.get("demo_uncached_time")
            if uncached:
                speedup = uncached / max(elapsed_c, 0.00001)
                c1, c2, c3 = st.columns(3)
                c1.metric("🐢 캐싱 없이", f"{uncached:.2f}초")
                c2.metric("⚡ 캐싱 재사용", f"{elapsed_c:.4f}초", delta=f"-{uncached - elapsed_c:.2f}초", delta_color="inverse")
                c3.metric("🚀 속도 향상", f"{speedup:.0f}배")
                
        st.markdown("**분류 결과 (캐싱된 전체 데이터 재사용)**")
        st.dataframe(
            get_type_score_preview(df_result_c, n=None, rank_limit=None),
            use_container_width=True,
            hide_index=True,
        )

# 캐시 무효화 영역
st.markdown("")
_inv_col, _btn_col = st.columns([2, 1])
with _inv_col:
    st.caption("개념 확인: 캐시를 비우면 다시 '첫 실행' 상태로 돌아가 연산 및 저장 시간이 걸리게 됩니다.")
with _btn_col:
    if st.button("🗑️ 캐싱 전체 무효화", use_container_width=True, key="btn_clear_cache"):
        clear_all_cached_data()
        st.session_state.pop("demo_uncached_time", None)
        st.session_state.pop("demo_cached_time", None)
        st.session_state["cached_run_count"] = 0
        st.success("데이터 캐시와 측정 기록이 모두 초기화되었습니다.")
        st.rerun()
