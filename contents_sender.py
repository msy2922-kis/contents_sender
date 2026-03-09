import streamlit as st
import requests
import json

# ── 1. 페이지 설정 ─────────────────────────────────────────────────────────────
st.set_page_config(page_title="KIS FICC Messenger", layout="centered")

# ── 2. 세션 상태 초기화 ────────────────────────────────────────────────────────
if "initialized" not in st.session_state:
    st.session_state.update(msg_input="", subject_input="", initialized=True)

# ── 3. 유틸리티 ───────────────────────────────────────────────────────────────
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

def _check(resp: requests.Response, label: str = "") -> bool:
    """200이 아니면 에러 표시 후 False 반환."""
    if resp.status_code != 200:
        prefix = f"'{label}' " if label else ""
        st.error(f"❌ {prefix}발송 실패: {resp.text}")
        return False
    return True

# ── 4. 이미지 발송 ─────────────────────────────────────────────────────────────
def _send_images(token: str, chat_id: str, images: list, caption: str) -> bool:
    if len(images) == 1:
        resp = _post(
            token, "sendPhoto",
            data={
                "chat_id": chat_id,
                "caption": caption,
                "parse_mode": "HTML",
                "show_caption_above_media": True,
            },
            files={"photo": (images[0].name, images[0])},
        )
    else:
        media, files = [], {}
        for i, f in enumerate(images):
            fid = f"file_{i}"
            item: dict = {"type": "photo", "media": f"attach://{fid}", "show_caption_above_media": True}
            if i == 0:
                item |= {"caption": caption, "parse_mode": "HTML"}
            media.append(item)
            files[fid] = (f.name, f)
        resp = _post(
            token, "sendMediaGroup",
            data={"chat_id": chat_id, "media": json.dumps(media)},
            files=files,
        )
    return _check(resp)

# ── 5. 발송 로직 ───────────────────────────────────────────────────────────────
def send_telegram() -> None:
    subj  = st.session_state.subject_input.strip()
    msg   = st.session_state.msg_input.strip()
    files = st.session_state.get("file_up") or []

    if not any([subj, msg, files]):
        st.warning("내용을 입력하세요.")
        return

    token     = st.secrets["TELEGRAM_TOKEN"]
    chat_id   = st.secrets["CHAT_ID"]
    full_text = _build_message(subj, msg, st.session_state.get("use_spoiler", False))
    is_image  = lambda f: f.type.startswith("image/")
    images    = [f for f in files if is_image(f)]
    docs      = [f for f in files if not is_image(f)]

    try:
        # [A] 텍스트 or 이미지 발송
        if images:
            if not _send_images(token, chat_id, images, full_text):
                return
        elif not docs:
            resp = _post(token, "sendMessage",
                         json={"chat_id": chat_id, "text": full_text, "parse_mode": "HTML"})
            if not _check(resp):
                return

        # [B] 문서 순차 발송
        # ✅ 수정: show_caption_above_media 제거 → 캡션이 메시지 아래에 위치
        for i, doc in enumerate(docs):
            caption = full_text if (i == 0 and not images) else ""
            payload: dict = {"chat_id": chat_id}
            if caption:
                payload |= {"caption": caption, "parse_mode": "HTML"}
            resp = _post(token, "sendDocument",
                         data=payload, files={"document": (doc.name, doc)})
            _check(resp, doc.name)

        st.success("✅ KIS FICC 양식 발송 완료")
        st.session_state.update(subject_input="", msg_input="")

    except requests.exceptions.Timeout:
        st.error("❌ 요청 시간 초과 — 네트워크를 확인하세요.")
    except Exception as e:
        st.error(f"에러 발생: {e}")

# ── 6. UI ──────────────────────────────────────────────────────────────────────
st.markdown("<h3 style='color:#0088cc;'>KIS FICC Sales InFo.</h3>", unsafe_allow_html=True)
st.text_input("제목 (Subject)", key="subject_input", placeholder="제목을 입력하세요")
st.text_area("내용 (Message)", height=200, key="msg_input", placeholder="내용을 입력하세요")

col1, col2 = st.columns([1, 2])
with col1:
    st.checkbox("Spoiler", key="use_spoiler")
with col2:
    st.file_uploader("Upload (Images & PDFs)", type=["jpg", "png", "pdf"],
                     key="file_up", accept_multiple_files=True, label_visibility="collapsed")

st.button("SEND", type="primary", on_click=send_telegram, use_container_width=True)
