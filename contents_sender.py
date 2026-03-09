import html
import json

import requests
import streamlit as st

# ── 1. 페이지 설정 ────────────────────────────────────────────────────────────
st.set_page_config(page_title="KIS FICC Messenger", layout="centered")

# ── 2. 인증 체크 ──────────────────────────────────────────────────────────────
# [개선] check_auth()를 인라인으로 풀어 함수 호출 없이 명확하게 처리
if not st.session_state.get("authenticated"):
    st.markdown("<h3 style='color:#0088cc;'>KIS FICC Sales InFo.</h3>", unsafe_allow_html=True)
    pw = st.text_input("비밀번호를 입력하세요", type="password")
    if st.button("로그인"):
        if pw == st.secrets["PASSWORD"]:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("❌ 비밀번호가 틀렸습니다.")
    st.stop()

# ── 3. 모듈 레벨 상수 (secrets는 한 번만 읽기) ───────────────────────────────
# [개선] send_telegram()이 호출될 때마다 st.secrets 접근하던 것을 상수로 분리
TOKEN   = st.secrets["TELEGRAM_TOKEN"]
CHAT_ID = st.secrets["CHAT_ID"]

# ── 4. 세션 상태 초기화 ───────────────────────────────────────────────────────
# [개선] initialized 플래그 제거 → setdefault로 간결하게
st.session_state.setdefault("subject_input", "")
st.session_state.setdefault("msg_input", "")

# ── 5. 헬퍼 함수 ─────────────────────────────────────────────────────────────

EXPANDABLE_THRESHOLD = 200  # 이 글자 수 초과 시 자동으로 접힌 블록 처리

def _build_message(subj: str, msg: str, use_spoiler: bool) -> str:
    """발송용 전문 텍스트 조립.
    - msg가 EXPANDABLE_THRESHOLD 초과 시 → <blockquote expandable> 로 감싸서
      Telegram에서 '더 보기' 형태로 표시
    - use_spoiler 체크 시 → 본문 전체를 추가로 <tg-spoiler> 처리
    """
    parts = ['<b><a href="https://t.me/">KIS FICC Sales InFo.</a></b>', ""]
    if subj:
        parts += [f"<b>{html.escape(subj)}</b>", ""]
    if msg:
        body = html.escape(msg)
        if use_spoiler:
            body = f"<tg-spoiler>{body}</tg-spoiler>"
        if len(msg) > EXPANDABLE_THRESHOLD:
            body = f"<blockquote expandable>{body}</blockquote>"
        parts.append(body)
    return "\n".join(parts)


def _post(method: str, **kwargs) -> requests.Response:
    """Telegram API 공통 POST — token/chat_id는 상수에서 자동 주입."""
    # [개선] token 인자 제거, 상수 TOKEN 직접 사용
    return requests.post(
        f"https://api.telegram.org/bot{TOKEN}/{method}",
        timeout=15,
        **kwargs,
    )


def _check_resp(resp: requests.Response, label: str = "") -> bool:
    """응답 실패 시 에러 표시 후 False 반환."""
    # [개선] 중복된 status_code 검사 로직을 한 곳으로 통합
    if resp.status_code != 200:
        prefix = f"'{label}' " if label else ""
        st.error(f"❌ {prefix}발송 실패: {resp.text}")
        return False
    return True


def _send_images(images: list, caption: str) -> requests.Response:
    """이미지 1장 또는 앨범(복수) 발송."""
    if len(images) == 1:
        return _post(
            "sendPhoto",
            data={
                "chat_id": CHAT_ID,
                "caption": caption,
                "parse_mode": "HTML",
                "show_caption_above_media": True,
            },
            files={"photo": (images[0].name, images[0])},
        )

    # 복수 이미지 → sendMediaGroup
    media, files = [], {}
    for i, f in enumerate(images):
        fid  = f"file_{i}"
        item = {"type": "photo", "media": f"attach://{fid}", "show_caption_above_media": True}
        if i == 0:
            item["caption"]    = caption
            item["parse_mode"] = "HTML"
        media.append(item)
        files[fid] = (f.name, f)

    return _post(
        "sendMediaGroup",
        data={"chat_id": CHAT_ID, "media": json.dumps(media)},
        files=files,
    )


# ── 6. 발송 로직 ──────────────────────────────────────────────────────────────
def send_telegram() -> None:
    subj           = st.session_state.subject_input.strip()
    msg            = st.session_state.msg_input.strip()
    uploaded_files = st.session_state.get("file_up") or []

    if not subj and not msg and not uploaded_files:
        st.warning("내용을 입력하세요.")
        return

    full_text = _build_message(subj, msg, st.session_state.get("use_spoiler", False))
    images    = [f for f in uploaded_files if f.type.startswith("image/")]
    docs      = [f for f in uploaded_files if not f.type.startswith("image/")]

    try:
        # ── [A] 텍스트 / 이미지 발송 ──────────────────────────────────────────
        if images:
            if not _check_resp(_send_images(images, full_text)):
                return
        elif not docs:
            if not _check_resp(
                _post("sendMessage", json={"chat_id": CHAT_ID, "text": full_text, "parse_mode": "HTML"})
            ):
                return

        # ── [B] PDF / 문서 순차 발송 ──────────────────────────────────────────
        for i, doc in enumerate(docs):
            payload = {"chat_id": CHAT_ID, "show_caption_above_media": True}
            if i == 0 and not images:          # 첫 번째 PDF에만 캡션 포함
                payload["caption"]    = full_text
                payload["parse_mode"] = "HTML"
            _check_resp(
                _post("sendDocument", data=payload, files={"document": (doc.name, doc)}),
                label=doc.name,
            )

        st.success("✅ KIS FICC 양식 발송 완료")
        st.session_state.subject_input = ""
        st.session_state.msg_input     = ""

    except requests.exceptions.Timeout:
        st.error("❌ 요청 시간 초과 — 네트워크를 확인하세요.")
    except Exception as e:
        st.error(f"에러 발생: {e}")


# ── 7. UI ─────────────────────────────────────────────────────────────────────
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
