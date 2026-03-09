import streamlit as st
import requests
import json

# 1. 페이지 설정
st.set_page_config(page_title="KIS FICC Messenger", layout="centered")

# 2. 세션 상태 초기화
for key in ['msg_input', 'subject_input']:
    if key not in st.session_state:
        st.session_state[key] = ""

# 3. 발송 로직
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
        # 파일 분류 (이미지 vs PDF/기타)
        images = [f for f in uploaded_files if f.type.startswith("image")] if uploaded_files else []
        docs = [f for f in uploaded_files if not f.type.startswith("image")] if uploaded_files else []

        # 1. 텍스트 + 이미지 발송 (이미지가 있으면 첫 번째 이미지에 텍스트 결합)
        if images:
            if len(images) > 1:
                url = f"https://api.telegram.org/bot{token}/sendMediaGroup"
                media = []
                files = {}
                for i, f in enumerate(images):
                    file_id = f"file_{i}"
                    item = {"type": "photo", "media": f"attach://{file_id}"}
                    if i == 0:
                        item["caption"] = full_text
                        item["parse_mode"] = "HTML"
                    media.append(item)
                    files[file_id] = (f.name, f)
                resp = requests.post(url, data={"chat_id": chat_id, "media": json.dumps(media)}, files=files)
            else:
                url = f"https://api.telegram.org/bot{token}/sendPhoto"
                resp = requests.post(url, data={"chat_id": chat_id, "caption": full_text, "parse_mode": "HTML"}, files={"photo": (images[0].name, images[0])})
        else:
            # 이미지 없이 텍스트만 발송
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            resp = requests.post(url, json={"chat_id": chat_id, "text": full_text, "parse_mode": "HTML"})

        # 2. PDF 파일이 있다면 버튼 형식으로 추가 발송
        if resp.status_code == 200 and docs:
            for doc in docs:
                url_doc = f"https://api.telegram.org/bot{token}/sendDocument"
                # 파일 전송 (버튼 없이 파일만 전송하여 텍스트 하단에 나열되도록 함)
                # 만약 외부 링크가 있다면 여기서 Inline Keyboard를 사용할 수 있으나, 
                # 직접 파일 전송 시에는 파일이 메시지 아래에 순차적으로 쌓이게 됩니다.
                requests.post(url_doc, data={"chat_id": chat_id}, files={"document": (doc.name, doc)})

        if resp.status_code == 200:
            st.success("✅ KIS FICC 양식 발송 완료")
            st.session_state.subject_input = ""
            st.session_state.msg_input = ""
        else:
            st.error(f"❌ 실패: {resp.text}")
            
    except Exception as e:
        st.error(f"에러 발생: {e}")

# 4. UI 구성
st.markdown("<h3 style='color: #0088cc;'>KIS FICC Sales InFo.</h3>", unsafe_allow_html=True)
st.text_input("제목 (Subject)", key="subject_input", placeholder="제목을 입력하세요")
st.text_area("내용 (Message)", height=200, key="msg_input", placeholder="내용을 입력하세요")

col1, col2 = st.columns([1, 2])
with col1:
    st.checkbox("Spoiler", key="use_spoiler")
with col2:
    st.file_uploader("Upload (Images & PDFs)", type=["jpg", "png", "pdf"], key="file_up", accept_multiple_files=True, label_visibility="collapsed")

st.button("SEND", type="primary", on_click=send_telegram, use_container_width=True)
