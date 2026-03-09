import streamlit as st
import requests
import json

# 1. 페이지 설정
st.set_page_config(page_title="KIS FICC Messenger", layout="centered")

# 2. 세션 상태 초기화
for key in ['msg_input', 'subject_input']:
    if key not in st.session_state:
        st.session_state[key] = ""

# 3. 발송 로직 (순차적 발송 방식)
def send_telegram():
    subj = st.session_state.subject_input.strip()
    msg = st.session_state.msg_input.strip()
    uploaded_files = st.session_state.file_up 
    
    if not subj and not msg and not uploaded_files:
        st.warning("내용을 입력하세요.")
        return

    token = st.secrets["TELEGRAM_TOKEN"]
    chat_id = st.secrets["CHAT_ID"]
    
    # [양식 구성]
    full_text = '<b><a href="https://t.me/">KIS FICC Sales InFo.</a></b>\n\n'
    if subj:
        full_text += f"<b>{subj}</b>\n\n"
    if msg:
        safe_msg = msg.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
        full_text += f"<tg-spoiler>{safe_msg}</tg-spoiler>" if st.session_state.get('use_spoiler') else safe_msg

    try:
        # STEP 1: 텍스트 메시지를 먼저 발송합니다.
        url_msg = f"https://api.telegram.org/bot{token}/sendMessage"
        resp_msg = requests.post(url_msg, json={"chat_id": chat_id, "text": full_text, "parse_mode": "HTML"})
        
        if resp_msg.status_code == 200:
            msg_id = resp_msg.json()['result']['message_id']
            
            # STEP 2: 파일이 있다면 해당 메시지에 답장(Reply) 형식으로 붙입니다.
            if uploaded_files:
                # 여러 개일 경우 묶어서 답장
                if len(uploaded_files) > 1:
                    url_file = f"https://api.telegram.org/bot{token}/sendMediaGroup"
                    media = []
                    files = {}
                    for i, file in enumerate(uploaded_files):
                        file_id = f"file_{i}"
                        media.append({
                            "type": "photo" if file.type.startswith("image") else "document",
                            "media": f"attach://{file_id}",
                            "reply_to_message_id": msg_id # 원본 메시지에 답장
                        })
                        files[file_id] = (file.name, file)
                    requests.post(url_file, data={"chat_id": chat_id, "media": json.dumps(media)}, files=files)
                
                # 하나일 경우 단일 답장
                else:
                    file = uploaded_files[0]
                    method = "sendPhoto" if file.type.startswith("image") else "sendDocument"
                    url_file = f"https://api.telegram.org/bot{token}/{method}"
                    f_key = "photo" if file.type.startswith("image") else "document"
                    requests.post(url_file, data={"chat_id": chat_id, "reply_to_message_id": msg_id}, files={f_key: (file.name, file)})

            st.success("✅ 텍스트 우선 발송 완료")
            st.session_state.subject_input = ""
            st.session_state.msg_input = ""
        else:
            st.error(f"❌ 발송 실패: {resp_msg.text}")
            
    except Exception as e:
        st.error(f"에러 발생: {e}")

# 4. UI 구성
st.markdown("<h3 style='color: #0088cc;'>KIS FICC Sales InFo.</h3>", unsafe_allow_html=True)
st.text_input("제목 (Subject)", key="subject_input")
st.text_area("내용 (Message)", height=200, key="msg_input")

col1, col2 = st.columns([1, 2])
with col1:
    st.checkbox("Spoiler", key="use_spoiler")
with col2:
    st.file_uploader("Upload (Max 4)", type=["jpg", "png", "pdf"], key="file_up", accept_multiple_files=True, label_visibility="collapsed")

st.button("SEND", type="primary", on_click=send_telegram, use_container_width=True)
