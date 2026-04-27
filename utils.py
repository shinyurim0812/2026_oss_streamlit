from __future__ import annotations

import base64
import json
import re
from datetime import datetime
from pathlib import Path
from time import perf_counter

import pandas as pd
import streamlit as st


APP_TITLE = "나의 보드게임 성향 정밀 진단 테스트"
STUDENT_ID = "2023204093"
STUDENT_NAME = "신유림"
APP_STATE_PATH = Path("app_state.json")
DATASET_GLOB = "bgg_dataset*.csv"
ASSETS_DIR = Path("assets")

TYPE_META = {
    "strategy": {
        "label": "전술 지휘관 (Commander)",
        "emoji": "⚔️",
        "summary": "치밀한 설계와 장기적인 전략으로 승리를 쟁취하는 전술가",
        "analysis": "당신은 즉흥적인 행동보다 여러 수를 앞서 생각하고 판 전체를 통제하는 전투의 묘미에 강하게 끌립니다.",
        "detail": "당신은 얕은 승리보다, 자신의 선택들이 모여 거대한 승리의 톱니바퀴를 완성하는 과정에서 희열을 느낍니다. 복잡한 마법진을 해석하거나 체스판의 말들을 지휘하듯, 깊이 있는 사고력과 효율적 자원 관리를 요구하는 묵직한 전략 보드게임이 당신의 진정한 무대입니다.",
        "card_note": "전장의 흐름을 완벽하게 읽고 통제하는 두뇌형 플레이어.",
        "icon": "strategy.png",
    },
    "party": {
        "label": "유쾌한 음유시인 (Bard)",
        "emoji": "🪕",
        "summary": "규칙의 무게를 벗고 사람들에게 웃음을 선사하는 분위기 메이커",
        "analysis": "당신에게 완벽한 승리는 중요하지 않습니다. 모두가 크게 웃으며 즐긴 순간이 가장 가치 있는 전리품입니다.",
        "detail": "당신은 두꺼운 마법서를 읽는 것보다 류트를 뜯으며 즉흥적으로 노래하는 것을 좋아합니다. 게임의 룰을 오래 붙잡고 있기보다, 바로 부딪히고 떠들썩하게 파티원들과 호흡을 맞추는 파티 보드게임이 당신에게 최고의 휴식처가 됩니다.",
        "card_note": "어떤 파티에 들어가든 가장 큰 목소리로 웃고 떠드는 핵심 분위기 메이커.",
        "icon": "party.png",
    },
    "coop": {
        "label": "신뢰의 성기사 (Paladin)",
        "emoji": "🛡️",
        "summary": "개인의 영광보다 파티 전체의 생존과 목표 달성을 중시하는 수호자",
        "analysis": "당신은 서로 경쟁하여 상처를 내는 것보다, 각자의 능력을 맞춰 거대한 위협을 넘어서는 것을 즐깁니다.",
        "detail": "치열한 갈등보다 끈끈한 형제애를 원합니다. 당신은 한 명의 슈퍼스타가 되는 것보다 각자의 역할을 다해 협동하며 쓰러져가는 파티원을 부축할 때 가장 몰입합니다. 모두가 하나의 목적 아래 머리를 맞대고 위기를 극복해 나가는 협력 보드게임이 완벽하게 어울립니다.",
        "card_note": "승리도, 패배도 모두 함께 나눌 때 가치가 있다고 믿는 협동가의 표본.",
        "icon": "coop.png",
    },
    "theme": {
        "label": "낭만적 탐험가 (Explorer)",
        "emoji": "🗺️",
        "summary": "단순한 점수를 넘어 짙은 세계관과 이야기의 향취를 쫓는 모험가",
        "analysis": "당신에게 보드게임은 수치를 계산하는 도구가 아니라, 미지의 세계로 침투하는 차원문입니다.",
        "detail": "당신은 수치적인 '1점'을 더 얻기 위해 테마를 깨는 플레이를 극도로 싫어합니다. 몬스터 피부의 질감, 고대 유적의 먼지 냄새 등 시스템이 제공하는 서사에 푹 빠져들 때 카타르시스를 느낍니다. 탄탄한 스토리와 살아 숨 쉬는 세계관을 갖춘 테마 보드게임이야말로 당신의 진짜 이야기입니다.",
        "card_note": "규칙서 너머의 세계관에 가장 깊게 다이빙하는 서사 몰입형 플레이어.",
        "icon": "theme.png",
    },
}

QUESTIONS = [
    {
        "key": "q1",
        "title": "Q1. 모험가의 주점 (선호 게임 성향)",
        "caption": "당신은 먼지 쌓인 낡은 모험가의 주점에 들어섰습니다. 가장 먼저 눈에 띄는 바운티보드(의뢰 게시판)의 내용 중 가장 당신의 가슴을 뛰게 하는 임무는?",
        "options": [
            ("거대한 제국의 영토 확장 지휘 (전술)", "strategy"),
            ("주점 사람들과 벌이는 흥겨운 술자리 내기 (파티)", "party"),
            ("마을을 위협하는 드래곤을 막기 위한 토벌대 소집 (협력)", "coop"),
            ("고대 엘프어 파편이 적힌 비밀 유적지 탐사 (테마)", "theme"),
        ],
    },
    {
        "key": "q2",
        "title": "Q2. 파티원 모집 (선호 인원 수)",
        "caption": "임무를 완수하기 위해 동료를 모을 시간입니다. 당신이 선호하는 모험 파티의 총 인원수는 몇 명쯤입니까?",
        "options": [
            ("1~2명 (고독한 혼자, 혹은 최고의 단짝 1명)", 2),
            ("3~4명 (가장 안정적인 소규모 정예)", 4),
            ("5명 이상 (다다익선, 대규모 원정대)", 5),
            ("혼자든 수십 명이든 상관없다 (용병 체질)", 0),
        ],
    },
    {
        "key": "q3",
        "title": "Q3. 모험의 여정 길이 (플레이 시간)",
        "caption": "주점 주인이 묻습니다. \"이번 의뢰는 모래시계가 어느 정도 떨어질 때까지 걸릴 것 같소?\" 당신이 선호하는 1회 모험(플레이) 소요 시간은?",
        "options": [
            ("잠깐! 30분 내외의 가벼운 탐색", 1),
            ("해질녘 전까지 끝나는 1시간 남짓", 2),
            ("해가 저물 때까지 땀 흘리는 2시간의 혈투", 3),
            ("밤을 지새우는 대서사시의 여정 (2시간 이상)", 4),
        ],
    },
    {
        "key": "q4",
        "title": "Q4. 던전 입구의 고대 서적 (시스템 복잡도)",
        "caption": "목적지에 도착하니, 던전 문을 열기 위한 두꺼운 <마법 규칙서>가 놓여 있습니다. 당신의 반응은?",
        "options": [
            ("이건 너무 두꺼워! 글자가 적고 직관적인 게 좋다.", 1),
            ("조금 읽어보면 알 수 있는 적당히 체계화된 룰을 선호한다.", 2),
            ("오히려 복잡하고 논리적인 체계가 숨겨져 있을수록 흥분된다.", 3),
        ],
    },
    {
        "key": "q5",
        "title": "Q5. 결단의 순간 (핵심 플레이 가치)",
        "caption": "주사위는 던져졌고, 당신 앞에 갈림길이 나타났습니다. 당신이 궁극적으로 추구하는 '보드게임이라는 여정'의 진짜 목적은 무엇입니까?",
        "options": [
            ("치열한 두뇌 싸움에서 상대를 압도하는 짜릿한 승리", "strategy"),
            ("결과와 상관없이 그저 모두가 배꼽 빠지게 웃는 순간들", "party"),
            ("각자의 희생과 노력으로 공동의 파멸을 막아내는 쾌감", "coop"),
            ("마치 한 편의 소설 속 주인공이 되어 세계를 탐험하는 감각", "theme"),
        ],
    },
    {
        "key": "q6",
        "title": "Q6. 미로의 장기화 (지구력/최대 시간)",
        "caption": "생각보다 적들이 질기고, 미로가 복잡해서 모험의 결말이 늦어지고 있습니다. 이때의 당신은?",
        "options": [
            ("빨리 여관으로 돌아가 쉬고 싶어 안달이 난다.", 1),
            ("조금 지치지만 1시간 정도 더 가는 건 버틸 수 있다.", 2),
            ("오히려 좋아. 깊어진 여정은 내 인내심을 깎지 못한다.", 3),
            ("시간의 흐름조차 잊었다! 끝을 볼 때까지 완전 몰입 상태.", 4),
        ],
    },
    {
        "key": "q7",
        "title": "Q7. 여정의 전설 (기억에 남는 승리 방식)",
        "caption": "모든 여정이 끝난 후 10년 뒤, 오늘을 회상한다면 어떤 장면이 가장 빛날까요?",
        "options": [
            ("모두가 내 완벽한 계획에 속아 넘어간 그 기막힌 한 수", "strategy"),
            ("친구가 말도 안 되는 실수를 해서 배가 아프게 웃었던 밤", "party"),
            ("종말의 1초를 남겨두고 팀워크로 기적적인 역전을 이뤄낸 것", "coop"),
            ("스토리의 반전을 마주하며 등에 소름이 쫙 돋았던 그 감정", "theme"),
        ],
    },
    {
        "key": "q8",
        "title": "Q8. 주점의 마지막 잔 (추구하는 게임의 맛)",
        "caption": "주점 주인이 고생했다며 축배의 잔을 건넵니다. 다음에는 어떤 맛의 술(게임)을 원하냐고 묻습니다.",
        "options": [
            ("'다시 도전할 구석'이 너무나도 많은 묵직한 오크통 오크 숙성 와인", "strategy"),
            ("달달하고 톡 쏘며 누구나 마실 수 있는 스파클링 에일", "party"),
            ("동료들과 다 같이 잔을 부딪혀야 제맛인 바이킹의 벌꿀술", "coop"),
            ("특유의 향기로 나를 다른 기후의 지역으로 데려가 버리는 럼주", "theme"),
        ],
    },
]

TYPE_PRIORITY = {"strategy": 4, "coop": 3, "theme": 2, "party": 1}
TYPE_QUESTION_KEYS = ("q1", "q5", "q7", "q8")
RECOMMENDATION_QUESTION_KEYS = ("q2", "q3", "q4", "q6")
DISPLAY_QUESTION_ORDER = TYPE_QUESTION_KEYS + RECOMMENDATION_QUESTION_KEYS


def get_ordered_questions() -> list[dict]:
    question_map = {question["key"]: question for question in QUESTIONS}
    ordered_questions: list[dict] = []

    for display_number, key in enumerate(DISPLAY_QUESTION_ORDER, start=1):
        question = dict(question_map[key])
        question["display_number"] = display_number
        question["display_title"] = re.sub(r"^Q\d+\.", f"Q{display_number}.", question["title"])
        ordered_questions.append(question)

    return ordered_questions


def apply_global_styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

        /* ── 전체 배경 ── */
        .stApp {
            background: #F2EAE1;
            font-family: 'Inter', sans-serif;
        }
        
        /* ── 사이드바 정렬 조작 (내비게이션 아래로 밀기) ── */
        [data-testid="stSidebar"] {
            background: #ECE3D6;
            border-right: 1px solid rgba(92, 64, 51, 0.12);
        }
        [data-testid="stSidebarContent"] {
            display: flex;
            flex-direction: column;
        }
        [data-testid="stSidebarNav"] {
            order: 2;
        }
        [data-testid="stSidebarUserContent"] {
            order: 1;
            padding-bottom: 0;
        }

        /* ── 공통 카드 기반 ── */
        .hero-card, .panel-card, .result-card, .history-card, .analysis-card {
            background: #ffffff;
            border: 1px solid rgba(139, 90, 43, 0.35);
            border-radius: 16px;
            box-shadow: 0 4px 15px rgba(92, 64, 51, 0.1);
            transition: transform 0.22s ease, box-shadow 0.22s ease;
        }
        .panel-card:hover, .result-card:hover, .analysis-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 25px rgba(92, 64, 51, 0.15);
        }

        /* ── 히어로 카드 ── */
        .hero-card {
            padding: 1.8rem 2rem;
            margin-bottom: 1.2rem;
            background: linear-gradient(135deg, #7A5B44 0%, #4E382A 100%);
            color: #FDF8F5;
        }
        .hero-card h1 {
            margin: 0.15rem 0 0.6rem;
            font-size: 2.2rem;
            font-weight: 800;
            letter-spacing: -0.02em;
        }
        .hero-card p {
            margin: 0;
            line-height: 1.7;
            opacity: 0.95;
        }
        .hero-kicker {
            font-size: 0.82rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            opacity: 0.9;
            font-weight: 600;
            color: #E6D0BE;
        }
        .hero-badges, .badge-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.45rem;
            margin-top: 0.9rem;
        }
        .pill, .mini-pill {
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            padding: 0.3rem 0.72rem;
            font-size: 0.82rem;
            font-weight: 600;
            transition: background 0.18s ease;
        }
        .pill {
            background: rgba(255, 255, 255, 0.15);
            border: 1px solid rgba(255, 255, 255, 0.25);
        }
        .identity-pill {
            background: rgba(255, 248, 240, 0.18);
            border: 1px solid rgba(255, 255, 255, 0.32);
            padding: 0.45rem 0.92rem;
            font-size: 0.92rem;
            font-weight: 800;
            letter-spacing: 0.01em;
        }
        .hero-description {
            margin-top: 1.15rem;
        }
        .mini-pill {
            background: #f4efe8;
            color: #5c4333;
            border: 1px solid rgba(92, 64, 51, 0.1);
        }
        .mini-pill:hover {
            background: #ebe0d3;
        }

        /* ── 패널/결과 카드 기본 속성 ── */
        .panel-card, .result-card, .history-card, .analysis-card {
            padding: 1.2rem 1.4rem;
            color: #4b3a2d;
            margin-bottom: 0.8rem;
        }
        .accent-card {
            background: linear-gradient(180deg, #fffcf8 0%, #fbf3e8 100%);
        }
        .plain-list {
            margin: 0.4rem 0 0;
            padding-left: 1.1rem;
            line-height: 1.75;
        }
        .section-label {
            font-size: 0.84rem;
            color: #8A6D57;
            margin-bottom: 0.25rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }
        .metric-value {
            font-size: 1.15rem;
            font-weight: 800;
            color: #3b2b20;
        }
        .quiet-text {
            color: #6a5749;
            line-height: 1.65;
        }
        .menu-card {
            background: #fffdfa;
            border: 1px solid rgba(139, 90, 43, 0.24);
            border-radius: 18px;
            padding: 1.2rem 1.25rem;
            min-height: 205px;
            height: 100%;
            display: flex;
            flex-direction: column;
            box-shadow: 0 6px 18px rgba(92, 64, 51, 0.07);
            transition: transform 0.22s ease, box-shadow 0.22s ease, border-color 0.22s ease;
        }
        .menu-card:hover {
            transform: translateY(-4px);
            border-color: rgba(139, 90, 43, 0.38);
            box-shadow: 0 12px 26px rgba(92, 64, 51, 0.12);
        }
        .menu-card h3 {
            margin: 0.4rem 0 0.8rem;
            font-size: 1.65rem;
            line-height: 1.25;
            color: #2f2430;
        }
        .menu-card p {
            margin: 0;
            color: #5e4636;
            line-height: 1.7;
            font-size: 1.02rem;
            flex: 1;
        }
        .menu-icon {
            font-size: 1.55rem;
            line-height: 1;
        }
        .dataset-note {
            margin-top: 0.45rem;
            padding: 0.8rem 0.95rem;
            background: rgba(255, 255, 255, 0.78);
            border: 1px solid rgba(139, 90, 43, 0.18);
            border-radius: 12px;
            color: #6a5749;
            line-height: 1.65;
        }
        .dataset-note strong {
            color: #4b3a2d;
        }

        /* ── 퀴즈 질문 카드 ── */
        .question-card {
            background: #ffffff;
            border: 1px solid rgba(139, 90, 43, 0.35);
            border-radius: 16px;
            padding: 1.3rem 1.4rem;
            box-shadow: 0 4px 15px rgba(92, 64, 51, 0.1);
            margin-bottom: 1.2rem;
        }
        .question-step {
            display: inline-block;
            background: rgba(122, 91, 68, 0.1);
            color: #7A5B44;
            border-radius: 999px;
            padding: 0.25rem 0.75rem;
            font-size: 0.8rem;
            font-weight: 700;
            margin-bottom: 0.8rem;
        }
        .rank-badge {
            display: inline-block;
            background: linear-gradient(135deg, #7A5B44 0%, #4E382A 100%);
            color: #FDF8F5;
            border-radius: 999px;
            padding: 0.3rem 0.8rem;
            font-size: 0.82rem;
            font-weight: 700;
            margin-bottom: 0.65rem;
        }

        /* ── 버튼 강화 (인터랙티브 박스 클릭 스타일) ── */
        .stButton > button, .stForm button {
            border-radius: 12px;
            border: 2px solid rgba(139, 90, 43, 0.1) !important;
            background: #ffffff !important;
            color: #4A3525 !important;
            font-weight: 700 !important;
            min-height: 52px;
            box-shadow: 0 4px 12px rgba(92, 64, 51, 0.04) !important;
            transition: all 0.2s ease !important;
            text-align: left;
        }
        .stButton > button:hover, .stForm button:hover {
            transform: translateY(-2px);
            border-color: #A3826A !important;
            box-shadow: 0 8px 24px rgba(92, 64, 51, 0.1) !important;
            background: #FDF8F5 !important;
            color: #3b2b20 !important;
        }
        .stButton > button:active, .stForm button:active {
            transform: translateY(0px);
        }

        /* Primary 버튼 오버라이드 (선택된 활성 상태) */
        .stButton > button[data-baseweb="button"][kind="primary"] {
            border-color: #7A5B44 !important;
            background: #F5EAE0 !important;
            color: #4E382A !important;
            box-shadow: 0 0 0 1px #7A5B44, 0 6px 18px rgba(92, 64, 51, 0.1) !important;
        }
        /* 진짜 폼 제출, 중요 버튼들 */
        .stButton > button[key*="submit"], button[aria-label*="열어보기"] {
            background: linear-gradient(135deg, #7A5B44 0%, #4E382A 100%) !important;
            color: white !important;
            border: none !important;
            text-align: center;
        }
        button[aria-label*="열어보기"]:hover {
            filter: brightness(1.1);
        }

        /* ── 유형 히어로 / 그리드 카드 ── */
        .type-hero {
            display: grid;
            grid-template-columns: 80px 1fr;
            gap: 1.2rem;
            align-items: start;
        }
        .type-icon {
            width: 76px;
            height: 76px;
            padding: 0.6rem;
            border-radius: 18px;
            background: #FDF9F5;
            border: 2px solid rgba(139, 90, 43, 0.12);
        }
        .type-card {
            background: #ffffff;
            border: 1px solid rgba(139, 90, 43, 0.35);
            border-radius: 16px;
            padding: 1.1rem;
            min-height: 160px;
            box-shadow: 0 4px 15px rgba(92, 64, 51, 0.05);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .type-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 24px rgba(92, 64, 51, 0.08);
        }
        .type-card.active {
            border: 2px solid rgba(122, 91, 68, 0.4);
            background: #FDF9F5;
            box-shadow: 0 8px 24px rgba(92, 64, 51, 0.08);
        }
        .type-card-head {
            display: flex;
            gap: 0.8rem;
            align-items: center;
            margin-bottom: 0.7rem;
        }
        .type-card-icon {
            width: 48px;
            height: 48px;
            padding: 0.4rem;
            border-radius: 12px;
            background: #FDF9F5;
            border: 1px solid rgba(139, 90, 43, 0.12);
        }

        /* ── 난이도 게이지 바 ── */
        .gauge-wrap {
            display: flex;
            align-items: center;
            gap: 0.6rem;
        }
        .gauge-bar {
            flex: 1;
            height: 10px;
            background: #F0E6DD;
            border-radius: 99px;
            overflow: hidden;
        }
        .gauge-fill {
            height: 100%;
            border-radius: 99px;
            transition: width 0.4s ease;
        }
        .gauge-fill.easy { background: #81b884; }
        .gauge-fill.medium { background: #df9e51; }
        .gauge-fill.hard { background: #d76a6a; }

        /* ── 캐시/시스템 카드 ── */
        .cache-status-card {
            background: #FCF9F5;
            border: 1px solid rgba(139, 90, 43, 0.35);
            border-radius: 16px;
            box-shadow: 0 4px 15px rgba(92, 64, 51, 0.05);
            padding: 1.2rem 1.4rem;
            margin-top: 1rem;
        }
        .status-pill {
            display: inline-block;
            background: rgba(122, 91, 68, 0.12);
            color: #7A5B44;
            border-radius: 999px;
            padding: 0.3rem 0.8rem;
            font-size: 0.82rem;
            font-weight: 700;
            margin-bottom: 0.7rem;
        }

        /* ── 프로필 카드(사이드바/개인) ── */
        .profile-card {
            background: linear-gradient(135deg, #7A5B44 0%, #4E382A 100%);
            color: #FDF8F5;
            border-radius: 16px;
            padding: 1.3rem 1.4rem;
            margin-bottom: 0.6rem;
            box-shadow: 0 6px 18px rgba(92, 64, 51, 0.1);
        }
        .profile-card .section-label {
            color: rgba(253,248,245,0.75);
        }
        .profile-card .metric-value {
            color: #FDF8F5;
        }
        .record-summary {
            background: linear-gradient(180deg, #fffdfa 0%, #fbf3e8 100%);
            border: 1px solid rgba(139, 90, 43, 0.32);
            border-radius: 20px;
            padding: 1.15rem 1.2rem;
            box-shadow: 0 8px 22px rgba(92, 64, 51, 0.08);
            margin-bottom: 0.4rem;
        }
        .record-summary .metric-value {
            font-size: 1.22rem;
        }
        .recommendation-box {
            margin-top: 0.85rem;
            padding: 0.9rem 1rem;
            background: rgba(255, 255, 255, 0.76);
            border: 1px solid rgba(139, 90, 43, 0.18);
            border-radius: 14px;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.65);
        }
        .recommendation-title {
            display: block;
            margin-bottom: 0.35rem;
            font-size: 0.82rem;
            color: #8A6D57;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }

        .section-divider {
            border: none;
            border-top: 1px solid rgba(139, 90, 43, 0.12);
            margin: 1.8rem 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def ensure_initialized() -> None:
    ensure_app_state_file()
    ensure_session_state()


def ensure_app_state_file() -> None:
    state = {"users": {}}
    if APP_STATE_PATH.exists():
        content = APP_STATE_PATH.read_text(encoding="utf-8").strip()
        if content:
            try:
                state = json.loads(content)
            except json.JSONDecodeError:
                pass

    users = state.setdefault("users", {})
    for user in users.values():
        user.setdefault("password", "")
        user.setdefault("display_name", "")
        user.setdefault("latest_result", None)
        user.setdefault("history", [])

    APP_STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")





def load_app_state() -> dict:
    ensure_app_state_file()
    return json.loads(APP_STATE_PATH.read_text(encoding="utf-8"))


def save_app_state(state: dict) -> None:
    APP_STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def ensure_session_state() -> None:
    defaults = {
        "logged_in": False,
        "username": "",
        "display_name": "",
        "answers": {},
        "current_question_index": 0,
        "quiz_submitted": False,
        "current_result": None,
        "result_saved": False,
        "result_scroll_pending": False,
        "cache_demo": {},
        "cache_timing": {},  # 캐싱 실측 타이밍 저장
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def reset_quiz_state() -> None:
    st.session_state["answers"] = {}
    st.session_state["current_question_index"] = 0
    st.session_state["quiz_submitted"] = False
    st.session_state["current_result"] = None
    st.session_state["result_saved"] = False
    st.session_state["result_scroll_pending"] = False
    st.session_state["cache_demo"] = {}
    st.session_state["cache_timing"] = {}  # 다시 테스트 시 재측정


def logout_user() -> None:
    st.session_state["logged_in"] = False
    st.session_state["username"] = ""
    st.session_state["display_name"] = ""
    reset_quiz_state()


def authenticate_user(username: str, password: str) -> tuple[bool, str]:
    state = load_app_state()
    user = state["users"].get(username)
    if not user:
        return False, "존재하지 않는 사용자입니다."
    if user["password"] != password:
        return False, "비밀번호가 올바르지 않습니다."

    st.session_state["logged_in"] = True
    st.session_state["username"] = username
    st.session_state["display_name"] = user.get("display_name", username)
    return True, "로그인에 성공했습니다."


def register_user(username: str, password: str, display_name: str) -> tuple[bool, str]:
    state = load_app_state()
    if username in state["users"]:
        return False, "이미 존재하는 아이디입니다."
    
    state["users"][username] = {
        "password": password,
        "display_name": display_name,
        "latest_result": None,
        "history": [],
    }
    save_app_state(state)
    return True, "회원가입에 성공했습니다. 왼쪽 탭에서 로그인해 주세요."


def change_password(username: str, current_password: str, new_password: str) -> tuple[bool, str]:
    state = load_app_state()
    user = state["users"].get(username)
    if not user:
        return False, "사용자 정보를 찾지 못했습니다."
    if user["password"] != current_password:
        return False, "현재 비밀번호가 일치하지 않습니다."
    user["password"] = new_password
    save_app_state(state)
    return True, "비밀번호를 변경했습니다."


def get_current_user_state() -> dict | None:
    if not st.session_state["logged_in"]:
        return None
    return load_app_state()["users"].get(st.session_state["username"])


def delete_latest_result() -> None:
    """현재 사용자의 최신 결과를 삭제합니다."""
    state = load_app_state()
    user = state["users"].get(st.session_state["username"])
    if user:
        user["latest_result"] = None
        save_app_state(state)


def delete_history_entry(index: int) -> None:
    """현재 사용자의 이전 기록 중 특정 인덱스를 삭제합니다."""
    state = load_app_state()
    user = state["users"].get(st.session_state["username"])
    if user and 0 <= index < len(user.get("history", [])):
        # history 리스트의 해당 인덱스 삭제
        user["history"].pop(index)
        save_app_state(state)


def find_dataset_path() -> Path:
    dataset = next(Path(".").glob(DATASET_GLOB), None)
    if dataset is None:
        raise FileNotFoundError("보드게임 CSV 파일을 찾지 못했습니다.")
    return dataset


def _base_load_dataframe() -> pd.DataFrame:
    path = find_dataset_path()
    df = pd.read_csv(path)
    return df[
        [
            "Name",
            "Min Players",
            "Max Players",
            "Play Time",
            "Rating Average",
            "BGG Rank",
            "Complexity Average",
            "Mechanics",
            "Domains",
        ]
    ].copy()


@st.cache_data(show_spinner=False)
def load_boardgame_data_cached() -> pd.DataFrame:
    return _base_load_dataframe()


def load_boardgame_data_uncached() -> pd.DataFrame:
    return _base_load_dataframe()


def split_tags(raw_value: str) -> list[str]:
    return [item.strip() for item in str(raw_value).split(",") if item.strip()]


def to_time_bucket(play_time: float) -> int:
    if play_time <= 30:
        return 1
    if play_time <= 60:
        return 2
    if play_time <= 120:
        return 3
    return 4


def to_complexity_bucket(value: float) -> int:
    if value <= 1.8:
        return 1
    if value <= 3.0:
        return 2
    return 3


# ── 유형별 키워드 매핑 룰 (CSV에는 없는 정보, 앱이 직접 계산) ──
_TYPE_KEYWORDS: dict[str, dict[str, set[str]]] = {
    "strategy": {
        "domains": {"Strategy Games", "Abstract Games"},
        "mechanics": {
            "Worker Placement", "Area Control / Area Influence",
            "Deck, Bag, and Pool Building", "Network and Route Building",
            "Engine Building", "Auction / Bidding",
        },
    },
    "party": {
        "domains": {"Party Games", "Family Games"},
        "mechanics": {
            "Voting", "Bluffing", "Real-Time", "Take That",
            "Acting", "Storytelling",
        },
    },
    "coop": {
        "domains": set(),
        "mechanics": {
            "Cooperative Game", "Team-Based Game",
            "Semi-Cooperative Game", "Traitor Game",
        },
    },
    "theme": {
        "domains": {"Thematic Games", "Wargames"},
        "mechanics": {
            "Campaign / Battle Card Driven",
            "Scenario / Mission / Campaign Game",
            "Role Playing", "Narrative Choice / Paragraph",
        },
    },
}


def _calc_type_score(row: pd.Series, type_key: str) -> int:
    """한 게임 행에 대해 특정 유형의 매칭 점수를 반환합니다.

    domains 일치: 유형 성격을 강하게 규정하므로 2점
    mechanics 일치: 세부 메카닉 매칭이므로 1점씩
    """
    kw = _TYPE_KEYWORDS[type_key]
    score = len(set(row["domains_list"]) & kw["domains"]) * 2
    score += len(set(row["mechanics_list"]) & kw["mechanics"])
    return score


def _resolve_dominant_type(row: pd.Series) -> str:
    """4개 유형 점수 중 가장 높은 유형 키를 반환합니다. 동점 시 TYPE_PRIORITY 기준."""
    scores = {
        t: row[f"type_score_{t}"]
        for t in ("strategy", "party", "coop", "theme")
    }
    max_score = max(scores.values())
    if max_score == 0:
        return "strategy"  # 기본값
    candidates = [t for t, s in scores.items() if s == max_score]
    if len(candidates) == 1:
        return candidates[0]
    return max(candidates, key=lambda t: TYPE_PRIORITY[t])


def preprocess_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """CSV 원본 데이터를 앱에서 사용할 수 있도록 전처리합니다.

    핵심 작업:
    1. 컬럼명·타입 정규화
    2. 결측치 제거
    3. 태그 파싱 (mechanics_list, domains_list)
    4. 버킷 변환 (time_bucket, complexity_bucket)
    5. [유형 분류 선계산] CSV에 없는 유형 점수를 직접 계산하여 컬럼으로 추가
       → 2만 개 × 4유형 × 키워드 집합 교집합 연산 → 실제 수 초 소요
    """
    data = df.copy()
    data.columns = [
        "name",
        "min_players",
        "max_players",
        "play_time",
        "rating_average_raw",
        "bgg_rank",
        "complexity_raw",
        "mechanics",
        "domains",
    ]
    for col in ["min_players", "max_players", "play_time", "rating_average_raw", "bgg_rank", "complexity_raw"]:
        data[col] = pd.to_numeric(data[col], errors="coerce")
    data["rating_average"] = data["rating_average_raw"] / 100
    data["complexity_average"] = data["complexity_raw"] / 100
    data["mechanics"] = data["mechanics"].fillna("")
    data["domains"] = data["domains"].fillna("")
    data = data.dropna(
        subset=["min_players", "max_players", "play_time", "rating_average", "bgg_rank", "complexity_average"]
    ).copy()
    data["mechanics_list"] = data["mechanics"].apply(split_tags)
    data["domains_list"] = data["domains"].apply(split_tags)
    data["time_bucket"] = data["play_time"].apply(to_time_bucket)
    data["complexity_bucket"] = data["complexity_average"].apply(to_complexity_bucket)
    data["primary_domain"] = data["domains_list"].apply(lambda tags: tags[0] if tags else "기타")

    # ── [유형 분류 선계산] CSV에는 없는 정보, 앱이 직접 계산 ──
    # 각 게임이 전략/파티/협력/테마 유형에 얼마나 맞는지 점수화합니다.
    # axis=1 apply로 행마다 집합 교집합 연산 → 2만 행 처리 시 수 초 소요
    for type_key in ("strategy", "party", "coop", "theme"):
        data[f"type_score_{type_key}"] = data.apply(
            lambda row, t=type_key: _calc_type_score(row, t), axis=1
        )
    # 4개 점수 중 가장 높은 유형을 dominant_type으로 저장
    data["dominant_type"] = data.apply(_resolve_dominant_type, axis=1)

    return data


@st.cache_data(show_spinner="🎲 보드게임 유형 분류 데이터 준비 중...")
def preprocess_boardgame_data_cached() -> pd.DataFrame:
    """전처리 결과를 캐싱합니다. 첫 실행 후 재호출 시 즉시 반환됩니다."""
    return preprocess_dataframe(load_boardgame_data_cached())


def preprocess_boardgame_data_uncached() -> pd.DataFrame:
    """캐싱 없이 전처리를 실행합니다. 시연용으로만 사용합니다."""
    return preprocess_dataframe(load_boardgame_data_uncached())


def get_dataset_metrics() -> dict[str, object]:
    started = perf_counter()
    df = preprocess_boardgame_data_cached()
    elapsed = perf_counter() - started
    return {
        "dataset_name": find_dataset_path().name,
        "row_count": len(df),
        "load_time": elapsed,
    }


def measure_preprocessing_time(use_cache: bool) -> tuple[float, pd.DataFrame]:
    """전처리 소요 시간과 결과 DataFrame을 반환합니다.

    캐싱 시연 전용 함수입니다.
    use_cache=True 이면 @st.cache_data 적용된 함수를 호출하고,
    False 이면 캐싱 없이 매번 새로 계산합니다.
    """
    t0 = perf_counter()
    if use_cache:
        df = preprocess_boardgame_data_cached()
    else:
        df = preprocess_boardgame_data_uncached()
    return perf_counter() - t0, df


def get_type_score_preview(
    df: pd.DataFrame,
    n: int | None = 8,
    rank_limit: int | None = 500,
) -> pd.DataFrame:
    """시연용 유형 점수 미리보기 테이블을 반환합니다.

    BGG 상위 게임 중 유형 점수가 있는 게임 n개를 보기 좋게 정리합니다.
    """
    type_label_map = {
        "strategy": "♟️ 전략",
        "party": "🎉 파티",
        "coop": "🤝 협력",
        "theme": "🗺️ 테마",
    }
    preview_source = df.sort_values("bgg_rank")
    if rank_limit is not None:
        preview_source = preview_source[preview_source["bgg_rank"] <= rank_limit]
    if n is not None:
        preview_source = preview_source.head(n)

    preview = preview_source[
        [
            "name",
            "type_score_strategy",
            "type_score_party",
            "type_score_coop",
            "type_score_theme",
            "dominant_type",
            "rating_average",
        ]
    ].copy()
    preview["dominant_type"] = preview["dominant_type"].map(
        lambda t: type_label_map.get(t, t)
    )
    preview.columns = [
        "게임명", "전략점수", "파티점수", "협력점수", "테마점수", "분류유형", "평점"
    ]
    preview["평점"] = preview["평점"].round(1)
    return preview.reset_index(drop=True)


def clear_all_cached_data() -> None:
    st.cache_data.clear()


def compute_type_scores(answers: dict[str, object]) -> dict[str, int]:
    """유형 점수를 계산합니다.

    성향 진단 문항 4개를 각각 1점씩 반영합니다.
    최대 점수는 4점입니다.
    """
    scores = {key: 0 for key in TYPE_META}
    for question_key in TYPE_QUESTION_KEYS:
        scores[str(answers[question_key])] += 1
    return scores


def resolve_type(answers: dict[str, object], scores: dict[str, int]) -> str:
    """최고 점수 유형을 반환합니다. 동점이면 우선순위 기준을 적용합니다."""
    max_score = max(scores.values())
    candidates = [key for key, value in scores.items() if value == max_score]
    if len(candidates) == 1:
        return candidates[0]
    return max(candidates, key=lambda item: TYPE_PRIORITY[item])


def build_profile(answers: dict[str, object]) -> dict[str, int]:
    q3_time = int(answers["q3"])
    q6_time = int(answers["q6"])
    return {
        "players_preference": int(answers["q2"]),
        "q3_time": q3_time,
        "q6_time": q6_time,
        "time_preference": max(1, min(4, round((q3_time + q6_time) / 2))),
        "complexity_preference": int(answers["q4"]),
    }


def filter_candidates(df: pd.DataFrame, players_preference: int) -> pd.DataFrame:
    candidates = df[
        (df["play_time"] > 0)
        & (df["max_players"] > 0)
        & (df["rating_average"] >= 6.5)
        & (df["bgg_rank"] <= 5000)
    ].copy()
    if players_preference == 2:
        candidates = candidates[(candidates["min_players"] <= 2) & (candidates["max_players"] >= 2)]
    elif players_preference == 4:
        candidates = candidates[(candidates["min_players"] <= 4) & (candidates["max_players"] >= 3)]
    elif players_preference == 5:
        candidates = candidates[candidates["max_players"] >= 5]
    return candidates


def get_type_bonus(row: pd.Series, resolved_type: str) -> int:
    domains = set(row["domains_list"])
    mechanics = set(row["mechanics_list"])

    if resolved_type == "strategy":
        return (3 if "Strategy Games" in domains else 0) + (1 if "Abstract Games" in domains else 0)
    if resolved_type == "party":
        return (3 if "Party Games" in domains else 0) + (1 if "Family Games" in domains else 0)
    if resolved_type == "coop":
        return 4 if "Cooperative Game" in mechanics else 0

    theme_bonus = 3 if "Thematic Games" in domains else 0
    theme_keywords = {"Storytelling", "Campaign / Battle Card Driven", "Scenario / Mission / Campaign Game"}
    return theme_bonus + (1 if mechanics.intersection(theme_keywords) else 0)


def format_players_label(value: int) -> str:
    return {0: "상황마다 다름", 2: "1~2명", 4: "3~4명", 5: "5명 이상"}.get(value, "상황마다 다름")


def format_time_label(value: int) -> str:
    return {1: "30분 이내", 2: "30~60분", 3: "60~120분", 4: "120분 이상"}.get(value, "미정")


def format_complexity_label(value: int) -> str:
    return {1: "쉬움", 2: "보통", 3: "어려움"}.get(value, "보통")


def complexity_gauge_html(complexity_avg: float) -> str:
    """complexity_average(0~5 scale)를 받아 게이지 바 HTML을 반환합니다."""
    score = max(0.0, min(5.0, float(complexity_avg)))
    pct = round(score / 5.0 * 100)
    if score < 2.0:
        level_class, label = "easy", "입문"
    elif score < 3.5:
        level_class, label = "medium", "보통"
    else:
        level_class, label = "hard", "숙련"
    return (
        f'<div class="gauge-wrap">'
        f'<div class="gauge-bar"><div class="gauge-fill {level_class}" style="width:{pct}%"></div></div>'
        f'<span class="gauge-label {level_class}">{label} ({score:.1f}/5.0)</span>'
        f'</div>'
    )


@st.cache_data(show_spinner=False)
def png_data_uri(filename: str) -> str:
    path = ASSETS_DIR / filename
    encoded = base64.b64encode(path.read_bytes()).decode("utf-8")
    ext = Path(filename).suffix.lstrip(".")
    mime = "png" if ext == "png" else "svg+xml"
    return f"data:image/{mime};base64,{encoded}"


def get_type_icon_uri(type_key: str) -> str:
    return png_data_uri(TYPE_META[type_key]["icon"])


def build_meta_label(label: str, value: str) -> str:
    return f"{label}: {value}"


def get_option_contribution_label(q_key: str, value: str | int) -> str:
    """각 문항의 선택지가 결과에 어떤 기여를 하는지 설명 문구를 반환합니다."""
    type_map = {
        "strategy": "♟️ 전략 점수",
        "party": "🎉 파티 점수",
        "coop": "🤝 협력 점수",
        "theme": "🗺️ 테마 점수",
    }
    
    if q_key in TYPE_QUESTION_KEYS:
        weight = 1
        label = type_map.get(str(value), "기여")
        return f"{label} +{weight}점"
    
    if q_key == "q2":
        if value == 2: return "👥 인원 필터: 2인 이하"
        if value == 4: return "👥 인원 필터: 4인 이하"
        if value == 5: return "👥 인원 필터: 5인 이상"
        return "👥 인원 필터: 전체 (제한 없음)"
    
    if q_key in ("q3", "q6"):
        if value == 1: return "⏱️ 시간 선호: 입문(30분 내)"
        if value == 2: return "⏱️ 시간 선호: 보통(60분 내)"
        if value == 3: return "⏱️ 시간 선호: 숙련(120분 내)"
        return "⏱️ 시간 선호: 마라톤(120분 초과)"

    if q_key == "q4":
        if value == 1: return "🧠 난이도 선호: 입문"
        if value == 2: return "🧠 난이도 선호: 보통"
        return "🧠 난이도 선호: 숙련"
    
    return "기여도 분석 중"


def build_answer_breakdown(answers: dict[str, object]) -> list[dict]:
    """각 문항별 선택 답변과 점수/선호 기여 내용을 반환합니다."""
    breakdown = []
    for q in get_ordered_questions():
        key = q["key"]
        selected_value = answers.get(key)
        
        # 선택한 라벨 찾기
        selected_label = "미선택"
        for label, val in q["options"]:
            if val == selected_value:
                selected_label = label
                break
        
        breakdown.append({
            "question_title": q["display_title"],
            "selected_label": selected_label,
            "contribution": get_option_contribution_label(key, selected_value)
        })
    return breakdown


def measure_load_time_uncached() -> float:
    """캐시 없이 CSV 로드+전처리를 실행하고 걸린 시간(초)을 반환합니다."""
    t0 = perf_counter()
    preprocess_boardgame_data_uncached()
    return perf_counter() - t0


def measure_load_time_cached() -> float:
    """캐시 적용 상태에서 CSV 로드+전처리를 실행하고 걸린 시간(초)을 반환합니다."""
    t0 = perf_counter()
    preprocess_boardgame_data_cached()
    return perf_counter() - t0


def build_game_reason(row: pd.Series, resolved_type: str) -> str:
    """게임 데이터를 바탕으로 게임별로 다른 추천 이유 문장을 생성합니다."""
    domains = set(row["domains_list"])
    mechanics = set(row["mechanics_list"])
    parts: list[str] = []

    # ── 1) 유형별 핵심 도메인/메커닉 설명 ──
    if resolved_type == "coop":
        if "Cooperative Game" in mechanics:
            parts.append("협력 메커닉이 뚜렷해서 함께 위기를 헤쳐나가는 흐름이 자연스럽게 살아납니다")
        elif "Team-Based Game" in mechanics:
            parts.append("팀 기반 플레이가 설계되어 있어 역할 분담이 명확합니다")
        else:
            parts.append("공동 목표를 향해 함께 움직이는 구조로 협력 플레이어와 잘 맞습니다")
    elif resolved_type == "strategy":
        if "Strategy Games" in domains:
            if "Worker Placement" in mechanics:
                parts.append("일꾼 놓기 메커닉 중심으로 자원 배분과 장기 계획이 핵심입니다")
            elif "Area Control / Area Influence" in mechanics:
                parts.append("지역 통제 구조라 상대 움직임을 읽으며 판세를 설계하는 재미가 있습니다")
            elif "Deck, Bag, and Pool Building" in mechanics:
                parts.append("덱 빌딩 구조로 선택의 누적이 후반부 흐름을 결정합니다")
            else:
                parts.append("전략적 선택이 판 전체 흐름에 직접 영향을 주는 구조입니다")
        elif "Abstract Games" in domains:
            parts.append("순수 추상 전략 구조로 운의 요소 없이 실력 대결이 가능합니다")
        else:
            parts.append("계획과 판단을 중심으로 플레이를 이끌어가는 성격의 게임입니다")
    elif resolved_type == "party":
        if "Party Games" in domains:
            if "Voting" in mechanics or "Bluffing" in mechanics:
                parts.append("투표나 블러핑 요소가 있어 사람 간 반응이 재미의 핵심이 됩니다")
            elif "Real-Time" in mechanics:
                parts.append("실시간 진행이라 긴장감과 웃음이 자연스럽게 터집니다")
            else:
                parts.append("파티 게임 특유의 빠른 진입과 분위기 조성이 강점입니다")
        elif "Family Games" in domains:
            parts.append("가족이나 처음 보는 사람과도 금방 시작할 수 있는 접근성이 좋습니다")
        else:
            parts.append("규칙이 가볍고 다 같이 즐기는 흐름이 잘 맞는 성격의 게임입니다")
    else:  # theme
        if "Thematic Games" in domains:
            if "Storytelling" in mechanics:
                parts.append("이야기를 직접 만들어가는 스토리텔링 구조가 몰입을 높입니다")
            elif any(k in mechanics for k in ("Campaign / Battle Card Driven", "Scenario / Mission / Campaign Game")):
                parts.append("캠페인 구조로 회차를 거듭할수록 서사가 쌓이는 체험을 줍니다")
            else:
                parts.append("강한 테마성으로 세계관 안에 자연스럽게 빠져드는 게임입니다")
        elif "Wargames" in domains:
            parts.append("역사적 배경이나 전장 테마로 몰입감 있는 상황을 연출합니다")
        else:
            parts.append("분위기와 설정이 살아 있어 단순한 규칙 이상의 체험을 줍니다")

    # ── 2) 플레이 시간 설명 ──
    play_time = int(row["play_time"])
    min_p = int(row["min_players"])
    max_p = int(row["max_players"])
    player_note = f"{min_p}~{max_p}명" if min_p != max_p else f"{min_p}명"
    if play_time <= 30:
        parts.append(f"{player_note}이 30분 안에 가볍게 즐기기 알맞은 길이입니다")
    elif play_time <= 60:
        parts.append(f"{player_note} 기준 약 {play_time}분으로 부담 없이 집중할 수 있습니다")
    elif play_time <= 120:
        parts.append(f"약 {play_time}분 분량으로 몰입감 있게 플레이 흐름을 이어갈 수 있습니다")
    else:
        parts.append(f"약 {play_time}분의 긴 호흡으로 전략적 전개를 충분히 즐길 수 있습니다")

    # ── 3) 난이도 설명 ──
    complexity_bucket = int(row["complexity_bucket"])
    rating = round(float(row["rating_average"]), 1)
    bgg_rank = int(row["bgg_rank"])
    if complexity_bucket == 1:
        parts.append(f"규칙이 가벼워 처음 접하는 사람도 빠르게 적응할 수 있습니다 (BGG 평점 {rating}점)")
    elif complexity_bucket == 2:
        parts.append(f"적당한 난이도로 손맛이 살아 있고 BGG 평점 {rating}점으로 평가가 좋습니다")
    else:
        parts.append(f"높은 난이도를 즐기는 플레이어에게 잘 맞습니다 (BGG 평점 {rating}점, 랭킹 {bgg_rank:,}위)")

    return " ".join(parts[:3])


def build_match_analysis(row: pd.Series, resolved_type: str) -> str:
    """추천 카드용 매칭 분석 문장을 생성합니다."""
    domains = [tag for tag in row.get("domains_list", []) if tag]
    domain_text = ", ".join(domains[:2]) if domains else "기타 장르"
    min_p = int(row["min_players"])
    max_p = int(row["max_players"])
    player_text = f"{min_p}~{max_p}인" if min_p != max_p else f"{min_p}인"
    play_time = int(row["play_time"])
    rating = round(float(row["rating_average"]), 1)

    intro = build_game_reason(row, resolved_type)
    details = (
        f"플레이 인원은 {player_text}이고, 예상 플레이 시간은 약 {play_time}분임. "
        f"BGG 평점은 {rating}점이며, 주요 장르는 {domain_text} 쪽에 가까움."
    )
    return f"{intro} {details}"


def describe_recommendation(item: dict[str, object], resolved_type: str) -> str:
    reasons = [str(item["generated_reason"])]

    if bool(item.get("matched_time")):
        reasons.append("선호한 플레이 시간 조건도 통과했습니다")
    if bool(item.get("matched_complexity")):
        reasons.append("원하는 난이도 조건도 충족했습니다")

    return " ".join(reasons[:2]).strip() + "."


def build_recommendations(df: pd.DataFrame, resolved_type: str, profile: dict[str, int]) -> tuple[list[dict], dict[str, int]]:
    user_time = profile["time_preference"]
    user_complexity = profile["complexity_preference"]

    base_candidates = filter_candidates(df, 0)
    type_filtered = base_candidates[base_candidates["dominant_type"] == resolved_type].copy()

    condition_candidates = type_filtered.copy()
    if profile["players_preference"] == 2:
        condition_candidates = condition_candidates[
            (condition_candidates["min_players"] <= 2) & (condition_candidates["max_players"] >= 2)
        ]
    elif profile["players_preference"] == 4:
        condition_candidates = condition_candidates[
            (condition_candidates["min_players"] <= 4) & (condition_candidates["max_players"] >= 3)
        ]
    elif profile["players_preference"] == 5:
        condition_candidates = condition_candidates[condition_candidates["max_players"] >= 5]

    condition_candidates = condition_candidates[condition_candidates["time_bucket"] == user_time].copy()
    complexity_candidates = condition_candidates[
        condition_candidates["complexity_bucket"] == user_complexity
    ].copy()

    final_candidates = complexity_candidates

    ranked = final_candidates.sort_values(
        by=["bgg_rank", "rating_average"],
        ascending=[True, False],
    ).head(3)

    recommendations = []
    for rank_index, (_, row) in enumerate(ranked.iterrows(), start=1):
        recommendations.append(
            {
                "rank_index": rank_index,
                "name": row["name"],
                "players_text": f"{int(row['min_players'])}~{int(row['max_players'])}명",
                "play_time_text": f"{int(row['play_time'])}분",
                "complexity_text": format_complexity_label(int(row["complexity_bucket"])),
                "complexity_gauge": complexity_gauge_html(float(row["complexity_average"])),
                "domain": row["primary_domain"],
                "rating": round(float(row["rating_average"]), 1),
                "rating_display": f"⭐ {round(float(row['rating_average']), 1)}/10",
                "bgg_rank": int(row["bgg_rank"]),
                "generated_reason": build_game_reason(row, resolved_type),
                "reason": "",
                "time_score": 1,
                "complexity_score": 1,
                "type_bonus": 0,
                "recommend_score": 0,
                "matched_time": True,
                "matched_complexity": True,
            }
        )

    for item in recommendations:
        item["reason"] = describe_recommendation(item, resolved_type)

    stats = {
        "type_filtered_count": len(type_filtered),
        "condition_filtered_count": len(condition_candidates),
        "complexity_filtered_count": len(complexity_candidates),
        "filtered_count": len(final_candidates),
        "total_count": len(df),
    }
    return recommendations, stats


def calculate_result(df: pd.DataFrame, answers: dict[str, str]) -> dict:
    # A. 성향 점수 계산
    scores = compute_type_scores(answers)
    # Q5 가중치 등은 compute_type_scores 내부에 이미 반영됨
    resolved_type = resolve_type(answers, scores)
    
    # B. 사용자 프로필 정리
    profile = build_profile(answers)
    
    # C. 순차 필터링 알고리즘
    # Step 0: 기본 품질 필터 (상위 5000위 이내, 평점 6.5 이상)
    candidates = df[
        (df["rating_average"] >= 6.5) & 
        (df["bgg_rank"] <= 5000) & 
        (df["bgg_rank"] > 0)
    ].copy()
    
    # Step 1: 성향 필터링 (주 유형 일치)
    type_matches = candidates[candidates["dominant_type"] == resolved_type].copy()
    if len(type_matches) >= 3:
        candidates = type_matches
        
    # Step 2: 인원 필터링
    p_pref = profile["players_preference"]
    if p_pref == 2:
        p_mask = (candidates["min_players"] <= 2) & (candidates["max_players"] >= 2)
    elif p_pref == 4:
        p_mask = (candidates["min_players"] <= 4) & (candidates["max_players"] >= 3)
    elif p_pref == 5:
        p_mask = candidates["max_players"] >= 5
    else:
        p_mask = pd.Series(True, index=candidates.index)
    
    player_matches = candidates[p_mask].copy()
    if len(player_matches) >= 3:
        candidates = player_matches

    # Step 3: 플레이 시간 필터링
    user_time_val = int(profile["time_preference"])
    time_matches = candidates[candidates["time_bucket"] == user_time_val].copy()
    if len(time_matches) >= 3:
        candidates = time_matches

    # Step 4: 난이도 필터링
    user_comp_val = int(profile["complexity_preference"])
    complexity_matches = candidates[candidates["complexity_bucket"] == user_comp_val].copy()
    if len(complexity_matches) >= 3:
        candidates = complexity_matches

    final_candidates = candidates.sort_values(
        by=["bgg_rank", "rating_average"],
        ascending=[True, False]
    )
    final_three = final_candidates.head(3)
    
    recommendations = []
    for i, (_, row) in enumerate(final_three.iterrows(), 1):
        recommendations.append({
            "rank_index": i,
            "name": row["name"],
            "players_text": f"{int(row['min_players'])}~{int(row['max_players'])}인",
            "play_time_text": f"{int(row['play_time'])}분",
            "rating_display": f"⭐ {row['rating_average']:.1f}/10",
            "complexity_gauge": complexity_gauge_html(float(row["complexity_average"])),
            "domain": row["domains"] if "domains" in row else "Board Game",
            "reason": build_match_analysis(row, resolved_type)
        })
        
    return {
        "resolved_type": resolved_type,
        "type_scores": scores,
        "profile": profile,
        "recommendations": recommendations,
        "stats": {
            "total_count": len(df),
            "filtered_count": len(final_candidates)
        },
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }



def get_cache_status_meta() -> dict[str, object]:
    df = preprocess_boardgame_data_cached()
    return {
        "functions": [
            "load_boardgame_data_cached()",
            "preprocess_boardgame_data_cached()",
        ],
        "targets": ["CSV 로드", "전처리"],
        "row_count": len(df),
        "dataset_name": find_dataset_path().name,
    }


def persist_result(username: str, result: dict[str, object]) -> None:
    state = load_app_state()
    user = state["users"][username]
    type_key = result["resolved_type"]
    latest_result = {
        "timestamp": result["timestamp"],
        "type_key": type_key,
        "type_label": f"{TYPE_META[type_key]['emoji']} {TYPE_META[type_key]['label']}",
        "players_preference": format_players_label(result["profile"]["players_preference"]),
        "time_preference": format_time_label(result["profile"]["time_preference"]),
        "complexity_preference": format_complexity_label(result["profile"]["complexity_preference"]),
        "top_games": [item["name"] for item in result["recommendations"]],
    }
    user["latest_result"] = latest_result
    history = user.setdefault("history", [])
    history.insert(0, latest_result)
    user["history"] = history[:10]
    save_app_state(state)


def ensure_result_saved(result: dict[str, object]) -> None:
    if st.session_state["result_saved"]:
        return
    persist_result(st.session_state["username"], result)
    st.session_state["result_saved"] = True


def sidebar_status_box() -> None:
    with st.sidebar:
        if st.session_state.get("logged_in"):
            st.markdown(
                f"""
                <div class="profile-card" style="margin-top: 0.5rem; margin-bottom: 0.5rem;">
                    <div class="section-label">이용자 정보</div>
                    <div class="metric-value">👤 {st.session_state['username']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("로그아웃", use_container_width=True, key="sidebar_logout_btn"):
                logout_user()
                st.rerun()
        else:
            st.markdown(
                """
                <div class="profile-card" style="margin-top: 0.5rem; background: #E6D0BE; color: #5c4333;">
                    <div class="section-label" style="color: rgba(92,67,51,0.7);">접속 상태</div>
                    <div class="metric-value" style="color: #4A3525;">로그인이 필요합니다</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
