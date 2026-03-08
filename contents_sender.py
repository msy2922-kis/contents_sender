import streamlit as st
import requests

# 1. 페이지 설정
st.set_page_config(page_title="KIS FICC Messenger", layout="centered")

# 2. 세션 상태 초기화
if 'msg_input' not in st.session_state:
    st.session_state.msg_input = ""
if 'subject_input' not in st.session_state:
    st.session_state.subject_input = ""

# 3. 발송 로직
def send_telegram():
    subj = st.session_state.subject_input.strip()
    msg = st.session_state.msg_input.strip()
    file = st.session_state.file_up
    
    if not subj and not msg and not file:
        st.warning("전송할 내용을 입력하세요.")
        return

    token = st.secrets["TELEGRAM_TOKEN"]
    chat_id = st.secrets["CHAT_ID"]
    
    # [양식 적용] 최상단 고정 문구 및 제목 결합
    # 텔레그램 HTML 파싱을 사용하여 굵게 처리
    full_text = "<b>KIS FICC Sales InFo.</b>\n"
    
    if subj:
        full_text += f"<b>**[{subj}]**</b>\n\n"
    else:
        full_text += "\n" # 제목이 없을 경우 한 줄 띄움
    
    # 본문 처리 (스포일러 여부 확인)
    if st.session_state.get('use_spoiler') and msg:
        safe_msg = msg.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
        full_text += f"<tg-spoiler>{safe_msg}</tg-spoiler>"
    else:
        full_text += msg.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')

    payload = {
        "chat_id": chat_id,
        "parse_mode": "HTML"
    }

    try:
        if file:
            url = f"https://api.telegram.org/bot{token}/sendDocument"
            payload["caption"] = full_text
            files = {"document": (file.name, file)}
            resp = requests.post(url, data=payload, files=files)
        else:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            payload["text"] = full_text
            resp = requests.post(url, json=payload)

        if resp.status_code == 200:
            st.success("발송 완료")
            st.session_state.subject_input = ""
            st.session_state.msg_input = ""
        else:
            st.error(f"오류: {resp.status_code}")
    except Exception as e:
        st.error(f"통신 에러: {e}")

# 4. UI 구성
# 사용자에게 보여지는 UI 제목 (초록색 텍스트 강조)
st.markdown("<h3 style='color: #2E8B57;'>KIS FICC Sales InFo.</h3>", unsafe_allow_html=True)

# 제목 입력창
st.text_input("제목 (Subject)", key="subject_input", placeholder="중요 뉴스 알림 등 제목을 입력하세요")

# 본문 입력창
st.text_area("내용 (Message)", height=200, key="msg_input", placeholder="상세 내용을 입력하세요")

col1, col2 = st.columns([1, 2])
with col1:
    st.checkbox("Spoiler", key="use_spoiler")
with col2:
    st.file_uploader("Upload", type=["jpg", "png", "pdf"], key="file_up", label_visibility="collapsed")

st.button("SEND", type="primary", on_click=send_telegram, use_container_width=True)
