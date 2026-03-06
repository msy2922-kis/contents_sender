import streamlit as st
import requests

# 페이지 기본 설정
st.set_page_config(page_title="텔레그램 메신저", page_icon="💬")

st.title("텔레그램 메시지 발송기 🚀")
st.write("텍스트, 이미지, PDF 파일을 텔레그램으로 즉시 발송합니다.")

# 1. API 키 불러오기
try:
    TELEGRAM_TOKEN = st.secrets["TELEGRAM_TOKEN"]
    CHAT_ID = st.secrets["CHAT_ID"]
except KeyError:
    st.error("⚠️ Streamlit Secrets에 TELEGRAM_TOKEN과 CHAT_ID가 설정되지 않았습니다.")
    st.stop()

# 2. 세션 상태(session_state) 초기화
if 'msg_input' not in st.session_state:
    st.session_state.msg_input = ""
if 'use_spoiler' not in st.session_state:
    st.session_state.use_spoiler = False

# 3. 메시지 및 파일 전송 함수
def send_telegram_all():
    message = st.session_state.msg_input 
    use_spoiler = st.session_state.use_spoiler
    # 파일 업로더에서 파일 가져오기 (세션 상태가 아닌 직접 접근)
    uploaded_file = st.session_state.file_up 
    
    # 텍스트와 파일이 모두 없는 경우 방지
    if not message.strip() and uploaded_file is None:
        st.warning("⚠️ 전송할 메시지나 파일을 입력해주세요.")
        return

    # 텍스트 가공 (스포일러 여부)
    formatted_text = message
    parse_mode = None
    if use_spoiler and message.strip():
        safe_msg = message.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        formatted_text = f"<tg-spoiler>{safe_msg}</tg-spoiler>"
        parse_mode = "HTML"

    try:
        if uploaded_file is not None:
            # [A] 파일이 있는 경우 (이미지, PDF 공통: sendDocument 사용)
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument"
            data = {"chat_id": CHAT_ID, "caption": formatted_text}
            if parse_mode:
                data["parse_mode"] = parse_mode
            
            # 파일 데이터 준비
            files = {"document": (uploaded_file.name, uploaded_file.getvalue())}
            response = requests.post(url, data=data, files=files)
        else:
            # [B] 텍스트만 있는 경우
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            payload = {"chat_id": CHAT_ID, "text": formatted_text}
            if parse_mode:
                payload["parse_mode"] = parse_mode
            response = requests.post(url, json=payload)

        if response.status_code == 200:
            st.success("✅ 성공적으로 발송되었습니다!")
            # 발송 성공 시 입력창 초기화
            st.session_state.msg_input = "" 
        else:
            st.error(f"❌ 발송 실패: {response.text}")
            
    except Exception as e:
        st.error(f"❌ 오류가 발생했습니다: {e}")

# 4. UI 구성
# 텍스트 입력창
st.text_area("전송할 메시지를 입력하세요:", height=150, key="msg_input")

# 스포일러 옵션
st.checkbox("👀 텍스트 스포일러(블러) 처리하기", key="use_spoiler")

# 파일 업로더 추가 (이미지 및 PDF 제한)
st.file_uploader("이미지 또는 PDF 파일을 선택하세요:", 
                 type=["jpg", "jpeg", "png", "pdf"], 
                 key="file_up")

# 5. 전송 버튼
st.button("텔레그램으로 전송", type="primary", on_click=send_telegram_all)
