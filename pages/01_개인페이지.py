from __future__ import annotations

import streamlit as st

from utils import (
    APP_TITLE,
    TYPE_META,
    apply_global_styles,
    authenticate_user,
    build_meta_label,
    change_password,
    delete_history_entry,
    delete_latest_result,
    ensure_initialized,
    get_type_icon_uri,
    get_current_user_state,
    register_user,
    sidebar_status_box,
)


st.set_page_config(page_title=f"{APP_TITLE} - 개인페이지", page_icon="👤", layout="wide")

ensure_initialized()
apply_global_styles()
sidebar_status_box()

st.title("👤 개인페이지")
st.caption("로그인, 비밀번호 변경, 최신 결과와 이전 기록을 확인하는 공간입니다.")

# ────────────────────────────────────────
# 섹션 1: 로그인 & 프로필
# ────────────────────────────────────────
if not st.session_state["logged_in"]:
    st.markdown(
        """
        <div class="panel-card" style="max-width:420px; margin-bottom: 20px;">
            <h3>🔒 인증이 필요합니다</h3>
            <p class="quiet-text">퀴즈와 기록을 보려면 로그인하거나 회원가입하세요.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    tab_login, tab_register = st.tabs(["🔑 로그인", "✨ 회원가입"])
    
    with tab_login:
        with st.form("login_form"):
            username = st.text_input("아이디", placeholder="예: 2023204093, yurim 등")
            password = st.text_input("비밀번호", type="password")
            submitted = st.form_submit_button("로그인", type="primary", use_container_width=True)
        if submitted:
            success, message = authenticate_user(username.strip(), password)
            if success:
                st.success(message)
                st.rerun()
            st.error(message)
            
    with tab_register:
        with st.form("register_form"):
            reg_username = st.text_input("새 아이디", placeholder="사용할 아이디 (문자/숫자)")
            reg_password = st.text_input("새 비밀번호", type="password")
            reg_display_name = st.text_input("이름 (닉네임)", placeholder="앱에 표시될 이름을 지정하세요")
            reg_submitted = st.form_submit_button("회원가입", type="primary", use_container_width=True)
        if reg_submitted:
            if not reg_username or not reg_password or not reg_display_name:
                st.error("모든 항목을 한 글자 이상 입력해 주세요.")
            else:
                success, message = register_user(reg_username.strip(), reg_password, reg_display_name.strip())
                if success:
                    st.success(message)
                else:
                    st.error(message)
else:
    # ── 프로필 카드 ──
    st.markdown(
        f"""
        <div class="profile-card">
            <div class="section-label">현재 사용자</div>
            <div class="metric-value" style="font-size:1.4rem;">{st.session_state['display_name']}</div>
            <div style="margin-top:0.4rem; opacity:0.85; font-size:0.9rem;"><strong>ID :</strong> {st.session_state['username']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── 비밀번호 변경 (접기) ──
    with st.expander("🔑 비밀번호 변경"):
        with st.form("change_password_form"):
            current_password = st.text_input("현재 비밀번호", type="password")
            new_password = st.text_input("새 비밀번호", type="password")
            confirm_password = st.text_input("새 비밀번호 확인", type="password")
            changed = st.form_submit_button("비밀번호 변경")
        if changed:
            if not new_password:
                st.error("새 비밀번호를 입력해 주세요.")
            elif new_password != confirm_password:
                st.error("새 비밀번호 확인이 일치하지 않습니다.")
            else:
                success, message = change_password(st.session_state["username"], current_password, new_password)
                if success:
                    st.success(message)
                else:
                    st.error(message)

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # ────────────────────────────────────────
    # 섹션 2: 가장 최근 결과
    # ────────────────────────────────────────
    col_res_title, col_res_del = st.columns([5, 1])
    with col_res_title:
        st.subheader("📊 가장 최근 결과")
    
    user_state = get_current_user_state()
    latest_result = user_state.get("latest_result") if user_state else None

    if latest_result:
        with col_res_del:
            if st.button("🗑️ 삭제", key="del_latest", help="최근 결과를 삭제합니다."):
                delete_latest_result()
                st.rerun()

    if not latest_result:
        st.caption("아직 저장된 퀴즈 결과가 없습니다. 문제 페이지에서 퀴즈를 풀어보세요!")
    else:
        latest_type_key = latest_result.get("type_key", "strategy")
        latest_meta = TYPE_META.get(latest_type_key, {})
        icon_uri = get_type_icon_uri(latest_type_key)
        st.markdown(
            f"""
            <div class="record-summary">
                <div class="type-card-head">
                    <img class="type-card-icon" src="{icon_uri}" alt="{latest_result['type_label']}"/>
                    <div>
                        <div class="metric-value">{latest_meta.get('emoji', '')} {latest_result['type_label']}</div>
                        <div class="section-label">🕐 {latest_result['timestamp']}</div>
                    </div>
                </div>
                <div class="badge-row" style="margin-top:0.6rem;">
                    <span class="mini-pill">👥 {build_meta_label('인원', latest_result['players_preference'])}</span>
                    <span class="mini-pill">⏱ {build_meta_label('시간', latest_result['time_preference'])}</span>
                    <span class="mini-pill">🧠 {build_meta_label('난이도', latest_result['complexity_preference'])}</span>
                </div>
                <div class="recommendation-box">
                    <span class="recommendation-title">🎮 추천 게임</span>
                    <div class="quiet-text">{", ".join(latest_result['top_games'])}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # ────────────────────────────────────────
    # 섹션 3: 이전 기록 타임라인
    # ────────────────────────────────────────
    st.subheader("📜 이전 기록")
    history = user_state.get("history", []) if user_state else []

    if not history:
        st.caption("저장된 기록이 없습니다.")
    else:
        # 최신순으로 보여주기 위해 역순 반복 (pop(i)를 위해 인덱스 계산 주의)
        # 삭제 편의성을 위해 루프 돌릴 때 원래 인덱스 매칭
        for i in reversed(range(len(history))):
            entry = history[i]
            entry_type_key = entry.get("type_key", "strategy")
            entry_meta = TYPE_META.get(entry_type_key, {})
            
            col_entry, col_entry_del = st.columns([5, 1])
            with col_entry:
                with st.expander(f"{entry_meta.get('emoji', '')} {entry['timestamp']} · {entry['type_label']}"):
                    icon_uri = get_type_icon_uri(entry_type_key)
                    st.markdown(
                        f"""
                        <div class="record-summary">
                            <div class="type-card-head">
                                <img class="type-card-icon" src="{icon_uri}" alt="{entry['type_label']}"/>
                                <div>
                                    <div class="metric-value">{entry_meta.get('emoji', '')} {entry['type_label']}</div>
                                    <div class="section-label">결과 유형</div>
                                </div>
                            </div>
                            <div class="badge-row" style="margin-top:0.5rem;">
                                <span class="mini-pill">👥 {build_meta_label('인원', entry['players_preference'])}</span>
                                <span class="mini-pill">⏱ {build_meta_label('시간', entry['time_preference'])}</span>
                                <span class="mini-pill">🧠 {build_meta_label('난이도', entry['complexity_preference'])}</span>
                            </div>
                            <div class="recommendation-box">
                                <span class="recommendation-title">🎮 추천 게임</span>
                                <div class="quiet-text">{", ".join(entry['top_games'])}</div>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            with col_entry_del:
                if st.button("🗑️", key=f"del_entry_{i}", help="이 기록을 삭제합니다."):
                    delete_history_entry(i)
                    st.rerun()
