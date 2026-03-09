import streamlit as st
import requests
import json

# ── 1. 페이지 설정 ────────────────────────────────────────────────────────────
st.set_page_config(page_title="KIS FICC Messenger", layout="centered")

# ── 0. 인증 체크 ──────────────────────────────────────────────────────────────
def check_auth():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.markdown("<h3 style='color:#0088cc;'>KIS FICC Sales InFo.</h3>", unsafe_allow_html=True)
        pw = st.text_input("비밀번호를 입력하세요", type="password")
        if st.button("로그인"):
            if pw == st.secrets["PASSWORD"]:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("❌ 비밀번호가 틀렸습니다.")
        st.stop()

check_auth()

# ── 2. 세션 상태 초기화 (불필요한 반복 실행 방지) ─────────────────────────────
if "initialized" not in st.session_state:
    st.session_state.msg_input     = ""
    st.session_state.subject_input = ""
    st.session_state.initialized   = True

# ── 3. 헬퍼: HTML 특수문자 이스케이프 ────────────────────────────────────────
def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

# ── 4. 헬퍼: 발송용 전문 텍스트 조립 (문자열 연결 대신 리스트 join) ─────────────
def _build_message(subj: str, msg: str, use_spoiler: bool) -> str:
    parts = ['<b><a href="https://t.me/">KIS FICC Sales InFo.</a></b>', ""]
    if subj:
        parts += [f"<b>{_escape(subj)}</b>", ""]
    if msg:
        body = _escape(msg)
        parts.append(f"<tg-spoiler>{body}</tg-spoiler>" if use_spoiler else body)
    return "\n".join(parts)

# ── 5. 헬퍼: Telegram API 공통 POST ──────────────────────────────────────────
def _post(token: str, method: str, **kwargs) -> requests.Response:
    return requests.post(
        f"https://api.telegram.org/bot{token}/{method}",
        timeout=15,
        **kwargs,
    )

# ── 6. 발송 로직 ──────────────────────────────────────────────────────────────
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

    # 파일 분류 (한 번만 수행)
    images = [f for f in uploaded_files if f.type.startswith("image/")]
    docs   = [f for f in uploaded_files if not f.type.startswith("image/")]

    try:
        # ── [A] 텍스트 / 이미지 발송 ──────────────────────────────────────────
        if images:
            resp = _send_images(token, chat_id, images, full_text)
            if resp.status_code != 200:
                st.error(f"❌ 실패: {resp.text}")
                return
        elif not docs:
            resp = _post(
                token, "sendMessage",
                json={"chat_id": chat_id, "text": full_text, "parse_mode": "HTML"},
            )
            if resp.status_code != 200:
                st.error(f"❌ 실패: {resp.text}")
                return

        # ── [B] PDF / 문서 순차 발송 ──────────────────────────────────────────
        for i, doc in enumerate(docs):
            caption_for_doc = full_text if (i == 0 and not images) else ""
            payload = {
                "chat_id": chat_id,
                "show_caption_above_media": True,
            }
            if caption_for_doc:
                payload["caption"]    = caption_for_doc
                payload["parse_mode"] = "HTML"
            doc_resp = _post(
                token, "sendDocument",
                data=payload,
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
    """이미지 1장 또는 앨범(복수) 발송."""
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

    # 복수 이미지 → sendMediaGroup
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
