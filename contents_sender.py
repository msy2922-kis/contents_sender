import streamlit as st
import requests
import json

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
    uploaded_files = st.session_state.file_up 
    
    if not subj and not msg and not uploaded_files:
        st.warning("전송할 내용이나 파일을 입력하세요.")
        return

    token = st.secrets["TELEGRAM_TOKEN"]
    chat_id = st.secrets["CHAT_ID"]
    
    # [가독성 강화 양식]
    # 1. 헤더: 링크 트릭을 사용하여 파란색으로 표시 (클릭해도 이동하지 않는 형식)
    full_text = '<b><a href="https://t.me/">KIS FICC Sales InFo.</a></b>\n\n'
    
    # 2. 제목: 대괄호와 굵은 글씨로 강조
    if subj:
        full_text += f"<b>[{subj}]</b>\n\n"
    
    # 3. 내용: 구분선 대신 여백 활용 및 본문 배치
    if msg:
        if st.session_state.get('use_spoiler'):
            safe_msg = msg.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
            full_text += f"<tg-spoiler>{safe_msg}</tg-spoiler>"
        else:
            full_text += msg.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')

    try:
        # 공통 설정
        base_payload = {
            "chat_id": chat_id,
            "parse_mode": "HTML"
        }

        # [A] 파일이 여러 개인 경우 (앨범 발송)
        if uploaded_files and len(uploaded_files) > 1:
            url = f"https://api.telegram.org/bot{token}/sendMediaGroup"
            media = []
            files = {}
            for i, file in enumerate(uploaded_files):
                file_id = f"file_{i}"
                media_item = {
                    "type": "photo" if file.type.startswith("image") else "document",
                    "media": f"attach://{file_id}",
                    "show_caption_above_media": True 
                }
                if i == 0:
                    media_item["caption"] = full_text
                    media_item["parse_mode"] = "HTML"
                media.append(media_item)
                files[file_id] = (file.name, file)
            resp = requests.post(url, data={"chat_id": chat_id, "media": json.dumps(media)}, files=files)
        
        # [B] 파일이 하나인 경우
        elif uploaded_files:
            file = uploaded_files[0]
            url = f"https://api.telegram.org/bot{token}/sendDocument"
            payload = {**base_payload, "caption": full_text, "show_caption_above_media": True}
            files = {"document": (file.name, file)}
            resp = requests.post(url, data=payload, files=files)
            
        # [C] 텍스트만 있는 경우
        else:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            payload = {**base_payload, "text": full_text}
            resp = requests.post(url, json=payload)

        if resp.status_code == 200:
            st.success("✅ 발송 완료")
            st.session_state.subject_input = ""
            st.session_state.msg_input = ""
        else:
            st.error(f"❌ 실패: {resp.text}")
            
    except Exception as e:
        st.error(f"통신 에러: {e}")

# 4. UI 구성
st.markdown("<h3 style='color: #0088cc;'>KIS FICC Sales InFo.</h3>", unsafe_allow_html=True)

st.text_input("제목 (Subject)", key="subject_input", placeholder="제목을 입력하세요")
st.text_area("내용 (Message)", height=200, key="msg_input", placeholder="내용을 입력하세요")

col1, col2 = st.columns([1, 2])
with col1:
    st.checkbox("Spoiler", key="use_spoiler")
with col2:
    st.file_uploader("Upload (Max 4)", type=["jpg", "png", "pdf"], key="file_up", accept_multiple_files=True, label_visibility="collapsed")

st.button("SEND", type="primary", on_click=send_telegram, use_container_width=True)
