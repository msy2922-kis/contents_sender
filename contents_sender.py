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
    # 1. 헤더: 링크 트릭을 이용한 파란색 표시
    full_text = '<b><a href="https://t.me/">KIS FICC Sales InFo.</a></b>\n\n'
    
    # 2. 제목: 기호 없이 굵은 글씨만 적용
    if subj:
        full_text += f"<b>{subj}</b>\n\n"
    
    # 3. 본문: 스포일러 및 HTML 특수문자 처리
    if msg:
        safe_msg = msg.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
        if st.session_state.get('use_spoiler'):
            full_text += f"<tg-spoiler>{safe_msg}</tg-spoiler>"
        else:
            full_text += safe_msg

    try:
        # 파일 분류 (이미지 vs PDF/기타)
        images = [f for f in uploaded_files if f.type.startswith("image")] if uploaded_files else []
        docs = [f for f in uploaded_files if not f.type.startswith("image")] if uploaded_files else []

        # [A] 이미지 발송 로직 (메시지 하단 배치 옵션 포함)
        if images:
            if len(images) > 1:
                # 여러 장일 때 (앨범 형태)
                url = f"https://api.telegram.org/bot{token}/sendMediaGroup"
                media = []
                files = {}
                for i, f in enumerate(images):
                    file_id = f"file_{i}"
                    item = {
                        "type": "photo", 
                        "media": f"attach://{file_id}",
                        "show_caption_above_media": True # ★ 메시지를 위로 보내는 옵션
                    }
                    if i == 0:
                        item["caption"] = full_text
                        item["parse_mode"] = "HTML"
                    media.append(item)
                    files[file_id] = (f.name, f)
                resp = requests.post(url, data={"chat_id": chat_id, "media": json.dumps(media)}, files=files)
            else:
                # 한 장일 때
                url = f"https://api.telegram.org/bot{token}/sendPhoto"
                payload = {
                    "chat_id": chat_id, 
                    "caption": full_text, 
                    "parse_mode": "HTML",
                    "show_caption_above_media": True # ★ 메시지를 위로 보내는 옵션
                }
                resp = requests.post(url, data=payload, files={"photo": (images[0].name, images[0])})
        else:
            # 이미지가 없을 때 텍스트만 발송
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            resp = requests.post(url, json={"chat_id": chat_id, "text": full_text, "parse_mode": "HTML"})

        # [B] PDF 발송 로직 (이미 발송된 메시지 아래에 순차적으로 첨부)
        if resp.status_code == 200 and docs:
            for doc in docs:
                url_doc = f"https://api.telegram.org/bot{token}/sendDocument"
                # PDF도 메시지 하단 배치를 위해 옵션 추가 (단일 문서 발송 시)
                payload_doc = {
                    "chat_id": chat_id,
                    "show_caption_above_media": True
                }
                requests.post(url_doc, data=payload_doc, files={"document": (doc.name, doc)})

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
