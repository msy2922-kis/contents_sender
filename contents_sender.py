import streamlit as st
import requests

# 1. 페이지 설정 (브라우저 탭 이름만 설정)
st.set_page_config(page_title="Messenger", layout="centered")

# 2. 세션 상태 초기화 (메모리 효율화)
if 'msg_input' not in st.session_state:
    st.session_state.msg_input = ""

# 3. 발송 로직 (스트리밍 방식 적용)
def send_telegram():
    msg = st.session_state.msg_input.strip()
    file = st.session_state.file_up
    
    if not msg and not file:
        st.warning("내용을 입력하세요.")
        return

    token = st.secrets["TELEGRAM_TOKEN"]
    chat_id = st.secrets["CHAT_ID"]
    
    payload = {"chat_id": chat_id}
    
    # 스포일러 처리 로직
    if st.session_state.get('use_spoiler') and msg:
        msg = f"<tg-spoiler>{msg.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')}</tg-spoiler>"
        payload["parse_mode"] = "HTML"

    try:
        if file:
            # 파일 스트리밍 전송 (메모리 절약)
            url = f"https://api.telegram.org/bot{token}/sendDocument"
            payload["caption"] = msg
            files = {"document": (file.name, file)}
            resp = requests.post(url, data=payload, files=files)
        else:
            # 텍스트 전송
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            payload["text"] = msg
            resp = requests.post(url, json=payload)

        if resp.status_code == 200:
            st.success("발송 완료")
            st.session_state.msg_input = "" # 입력창 초기화
        else:
            st.error(f"오류: {resp.status_code}")
    except Exception as e:
        st.error(f"통신 에러: {e}")

# 4. 심플 UI 구성
# 제목과 설명 이미지 제거, 간결한 입력창 위주 배치
st.text_area("Message", height=200, key="msg_input", placeholder="전송할 내용을 입력하세요...")

# 체크박스와 파일 업로더를 가로로 배치하여 공간 절약
col1, col2 = st.columns([1, 2])
with col1:
    st.checkbox("Spoiler", key="use_spoiler")
with col2:
    st.file_uploader("Upload", type=["jpg", "png", "pdf"], key="file_up", label_visibility="collapsed")

# 전송 버튼 (강조색 적용)
st.button("SEND", type="primary", on_click=send_telegram, use_container_width=True)
