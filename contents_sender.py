import streamlit as st
import requests
import json
from PIL import Image
import io

# 1. 페이지 및 세션 설정
st.set_page_config(page_title="KIS FICC Messenger", layout="centered")
for key in ['msg_input', 'subject_input']:
    if key not in st.session_state:
        st.session_state[key] = ""

# 2. 이미지를 정방형(1:1)으로 만드는 함수
def make_square(file):
    image = Image.open(file)
    # 이미지 포맷 유지 (RGBA인 경우 RGB로 변환하여 배경색 처리 가능)
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")
    
    width, height = image.size
    new_size = max(width, height)
    
    # ★ 수정 포인트: 검은색 배경의 정방형 도화지 생성 (0, 0, 0)
    new_image = Image.new("RGB", (new_size, new_size), (0, 0, 0))
    # 이미지를 중앙에 배치
    new_image.paste(image, ((new_size - width) // 2, (new_size - height) // 2))
    
    # 메모리에 저장 후 반환
    img_byte_arr = io.BytesIO()
    # 검은색 배경에는 JPEG가 잘 어울리며 용량도 최적화됩니다.
    new_image.save(img_byte_arr, format='JPEG', quality=90)
    img_byte_arr.seek(0)
    return img_byte_arr

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
    if subj: full_text += f"<b>{subj}</b>\n\n"
    if msg:
        safe_msg = msg.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
        full_text += f"<tg-spoiler>{safe_msg}</tg-spoiler>" if st.session_state.get('use_spoiler') else safe_msg

    try:
        images = [f for f in uploaded_files if f.type.startswith("image")] if uploaded_files else []
        docs = [f for f in uploaded_files if not f.type.startswith("image")] if uploaded_files else []

        # 이미지 처리 및 발송 (정방형 가공)
        if images:
            url = f"https://api.telegram.org/bot{token}/sendMediaGroup"
            media = []
            files = {}
            for i, f in enumerate(images):
                file_id = f"file_{i}"
                # 검은색 여백으로 가공된 이미지 가져오기
                processed_img = make_square(f)
                
                item = {"type": "photo", "media": f"attach://{file_id}"}
                if i == 0:
                    item["caption"] = full_text
                    item["parse_mode"] = "HTML"
                media.append(item)
                files[file_id] = (f"img_{i}.jpg", processed_img)
            
            resp = requests.post(url, data={"chat_id": chat_id, "media": json.dumps(media)}, files=files)
        else:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            resp = requests.post(url, json={"chat_id": chat_id, "text": full_text, "parse_mode": "HTML"})

        # PDF 발송 (메시지 하단에 나열)
        if resp.status_code == 200 and docs:
            for doc in docs:
                url_doc = f"https://api.telegram.org/bot{token}/sendDocument"
                requests.post(url_doc, data={"chat_id": chat_id}, files={"document": (doc.name, doc)})

        if resp.status_code == 200:
            st.success("✅ 검은색 여백 정방형 발송 완료")
            st.session_state.subject_input = ""
            st.session_state.msg_input = ""
        else:
            st.error(f"❌ 실패: {resp.text}")
            
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
    st.file_uploader("Upload", type=["jpg", "png", "pdf"], key="file_up", accept_multiple_files=True, label_visibility="collapsed")

st.button("SEND", type="primary", on_click=send_telegram, use_container_width=True)
