import streamlit as st
import requests
import json
from datetime import date, timedelta

# ── 1. 페이지 설정 ────────────────────────────────────────────────────────────
st.set_page_config(page_title="KIS FICC Messenger", layout="centered")

# ── 2. 세션 상태 초기화 ───────────────────────────────────────────────────────
if "initialized" not in st.session_state:
    st.session_state.msg_input     = ""
    st.session_state.subject_input = ""
    st.session_state.initialized   = True

# ── 3. 경제 이벤트 캘린더 ────────────────────────────────────────────────────

FIXED_EVENTS = {
    # 2025 FOMC
    date(2025, 1, 29): "🇺🇸 FOMC 금리결정",
    date(2025, 3, 19): "🇺🇸 FOMC 금리결정",
    date(2025, 5, 7):  "🇺🇸 FOMC 금리결정",
    date(2025, 6, 18): "🇺🇸 FOMC 금리결정",
    date(2025, 7, 30): "🇺🇸 FOMC 금리결정",
    date(2025, 9, 17): "🇺🇸 FOMC 금리결정",
    date(2025, 10, 29):"🇺🇸 FOMC 금리결정",
    date(2025, 12, 10):"🇺🇸 FOMC 금리결정",
    # 2026 FOMC
    date(2026, 1, 28): "🇺🇸 FOMC 금리결정",
    date(2026, 3, 18): "🇺🇸 FOMC 금리결정",
    date(2026, 5, 6):  "🇺🇸 FOMC 금리결정",
    date(2026, 6, 17): "🇺🇸 FOMC 금리결정",
    date(2026, 7, 29): "🇺🇸 FOMC 금리결정",
    date(2026, 9, 16): "🇺🇸 FOMC 금리결정",
    date(2026, 10, 28):"🇺🇸 FOMC 금리결정",
    date(2026, 12, 9): "🇺🇸 FOMC 금리결정",
    # 2025 한국은행 금통위
    date(2025, 1, 16): "🇰🇷 한국은행 금통위",
    date(2025, 2, 25): "🇰🇷 한국은행 금통위",
    date(2025, 4, 17): "🇰🇷 한국은행 금통위",
    date(2025, 5, 29): "🇰🇷 한국은행 금통위",
    date(2025, 7, 17): "🇰🇷 한국은행 금통위",
    date(2025, 8, 28): "🇰🇷 한국은행 금통위",
    date(2025, 10, 16):"🇰🇷 한국은행 금통위",
    date(2025, 11, 27):"🇰🇷 한국은행 금통위",
    # 2026 한국은행 금통위
    date(2026, 1, 15): "🇰🇷 한국은행 금통위",
    date(2026, 2, 26): "🇰🇷 한국은행 금통위",
    date(2026, 4, 16): "🇰🇷 한국은행 금통위",
    date(2026, 5, 28): "🇰🇷 한국은행 금통위",
    date(2026, 7, 16): "🇰🇷 한국은행 금통위",
    date(2026, 8, 27): "🇰🇷 한국은행 금통위",
    date(2026, 10, 15):"🇰🇷 한국은행 금통위",
    date(2026, 11, 26):"🇰🇷 한국은행 금통위",
}

# 미국 주요 경제지표 발표 패턴 (매월 고정 주기)
# CPI: 매월 둘째 주 수요일 전후 / NFP: 매월 첫째 주 금요일
# → FRED API로 실제 당일 발표 여부를 확인
US_FRED_SERIES = {
    "CPIAUCSL":          "🇺🇸 미국 CPI 발표",
    "CPILFESL":          "🇺🇸 미국 Core CPI 발표",
    "PAYEMS":            "🇺🇸 미국 NFP(비농업고용) 발표",
    "A191RL1Q225SBEA":   "🇺🇸 미국 GDP 발표",
    "UNRATE":            "🇺🇸 미국 실업률 발표",
}

# 국내 주요 경제지표 (통계청/한국은행 발표 패턴, 수동 관리)
KR_INDICATORS = {
    # 소비자물가: 매월 초 (보통 1~5일)
    date(2026, 2, 4):  "🇰🇷 국내 CPI 발표",
    date(2026, 3, 4):  "🇰🇷 국내 CPI 발표",
    date(2026, 4, 2):  "🇰🇷 국내 CPI 발표",
    date(2026, 5, 6):  "🇰🇷 국내 CPI 발표",
    date(2026, 6, 3):  "🇰🇷 국내 CPI 발표",
    # 수출입: 매월 1일 (익월 발표)
    date(2026, 2, 2):  "🇰🇷 수출입 동향 발표",
    date(2026, 3, 2):  "🇰🇷 수출입 동향 발표",
    date(2026, 4, 1):  "🇰🇷 수출입 동향 발표",
    date(2026, 5, 1):  "🇰🇷 수출입 동향 발표",
}

FIXED_EVENTS.update(KR_INDICATORS)


@st.cache_data(ttl=3600)
def fetch_fred_today_events() -> list[str]:
    """FRED API로 오늘 발표된 미국 경제지표 확인 (무료)."""
    today    = date.today().strftime("%Y-%m-%d")
    tomorrow = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
    events   = []

    for series_id, label in US_FRED_SERIES.items():
        try:
            url = (
                f"https://api.stlouisfed.org/fred/series/observations"
                f"?series_id={series_id}"
                f"&observation_start={today}"
                f"&observation_end={tomorrow}"
                f"&api_key=b241dfef1e5d2d12e46e5dfef18e20c7"
                f"&file_type=json"
            )
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                obs = resp.json().get("observations", [])
                if any(o["date"] == today for o in obs):
                    events.append(label)
        except Exception:
            pass
    return events


def get_today_events() -> list[str]:
    today    = date.today()
    tomorrow = today + timedelta(days=1)
    events   = []

    # 1) 오늘 고정 이벤트
    if today in FIXED_EVENTS:
        events.append(FIXED_EVENTS[today])

    # 2) FRED 실시간 미국 지표
    try:
        events.extend(fetch_fred_today_events())
    except Exception:
        pass

    # 3) 내일 예정 이벤트 (D-1 예고)
    if tomorrow in FIXED_EVENTS:
        events.append(f"⏰ 내일 예정: {FIXED_EVENTS[tomorrow]}")

    return events


def show_event_banner() -> None:
    events    = get_today_events()
    today_str = date.today().strftime("%Y년 %m월 %d일")

    if events:
        event_html = "　｜　".join(events)
        bg_style   = "background: linear-gradient(90deg, #0a2342, #1a3a5c); border-left: 4px solid #00aaff;"
        date_color = "#7ecfff"
        text_color = "#ffffff"
    else:
        event_html = "오늘 예정된 주요 이벤트 없음"
        bg_style   = "background: #1a1a2e; border-left: 4px solid #444;"
        date_color = "#888"
        text_color = "#aaa"

    st.markdown(
        f"""
        <div style="{bg_style} border-radius:6px; padding:10px 16px; margin-bottom:16px;">
            <div style="color:{date_color}; font-size:11px; margin-bottom:4px;">
                📅 {today_str} 주요 이벤트
            </div>
            <div style="color:{text_color}; font-size:13px; font-weight:600;">
                {event_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── 4. 헬퍼 함수들 ────────────────────────────────────────────────────────────
def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def _build_message(subj: str, msg: str, use_spoiler: bool) -> str:
    parts = ['<b><a href="https://t.me/">KIS FICC Sales InFo.</a></b>', ""]
    if subj:
        parts += [f"<b>{_escape(subj)}</b>", ""]
    if msg:
        body = _escape(msg)
        parts.append(f"<tg-spoiler>{body}</tg-spoiler>" if use_spoiler else body)
    return "\n".join(parts)

def _post(token: str, method: str, **kwargs) -> requests.Response:
    return requests.post(
        f"https://api.telegram.org/bot{token}/{method}",
        timeout=15,
        **kwargs,
    )

# ── 5. 발송 로직 ──────────────────────────────────────────────────────────────
def send_telegram() -> None:
    subj           = st.session_state.subject_input.strip()
    msg            = st.session_state.msg_input.strip()
    uploaded_files = st.session_state.get("file_up") or []

    if not subj and not msg and not uploaded_files:
        st.warning("내용을 입력하세요.")
        return

    token   = st.secrets["TELEGRAM_TOKEN"]
    chat_id = st.secrets["CHAT_ID"]

    full_text = _build_message(subj, msg, st.session_state.get("use_spoiler", False))
    images    = [f for f in uploaded_files if f.type.startswith("image/")]
    docs      = [f for f in uploaded_files if not f.type.startswith("image/")]

    try:
        if images:
            resp = _send_images(token, chat_id, images, full_text)
            if resp.status_code != 200:
                st.error(f"❌ 실패: {resp.text}")
                return
        else:
            resp = _post(
                token, "sendMessage",
                json={"chat_id": chat_id, "text": full_text, "parse_mode": "HTML"},
            )
            if resp.status_code != 200:
                st.error(f"❌ 실패: {resp.text}")
                return

        for doc in docs:
            doc_resp = _post(
                token, "sendDocument",
                data={"chat_id": chat_id},
                files={"document": (doc.name, doc)},
            )
            if doc_resp.status_code != 200:
                st.warning(f"⚠️ '{doc.name}' 발송 실패: {doc_resp.text}")

        st.success("✅ KIS FICC 양식 발송 완료")
        st.session_state.subject_input = ""
        st.session_state.msg_input     = ""

    except requests.exceptions.Timeout:
        st.error("❌ 요청 시간 초과 — 네트워크를 확인하세요.")
    except Exception as e:
        st.error(f"에러 발생: {e}")


def _send_images(token: str, chat_id: str, images: list, caption: str) -> requests.Response:
    if len(images) == 1:
        return _post(
            token, "sendPhoto",
            data={
                "chat_id": chat_id,
                "caption": caption,
                "parse_mode": "HTML",
                "show_caption_above_media": True,
            },
            files={"photo": (images[0].name, images[0])},
        )

    media = []
    files = {}
    for i, f in enumerate(images):
        fid  = f"file_{i}"
        item = {"type": "photo", "media": f"attach://{fid}", "show_caption_above_media": True}
        if i == 0:
            item["caption"]    = caption
            item["parse_mode"] = "HTML"
        media.append(item)
        files[fid] = (f.name, f)

    return _post(
        token, "sendMediaGroup",
        data={"chat_id": chat_id, "media": json.dumps(media)},
        files=files,
    )


# ── 6. UI ─────────────────────────────────────────────────────────────────────
show_event_banner()

st.markdown("<h3 style='color:#0088cc;'>KIS FICC Sales InFo.</h3>", unsafe_allow_html=True)

st.text_input("제목 (Subject)", key="subject_input", placeholder="제목을 입력하세요")
st.text_area("내용 (Message)", height=200, key="msg_input", placeholder="내용을 입력하세요")

col1, col2 = st.columns([1, 2])
with col1:
    st.checkbox("Spoiler", key="use_spoiler")
with col2:
    st.file_uploader(
        "Upload (Images & PDFs)",
        type=["jpg", "png", "pdf"],
        key="file_up",
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

st.button("SEND", type="primary", on_click=send_telegram, use_container_width=True)
