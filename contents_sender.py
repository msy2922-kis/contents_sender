import streamlit as st
import requests

# 페이지 기본 설정
st.set_page_config(page_title="텔레그램 메신저", page_icon="💬")

st.title("텔레그램 메시지 발송기 🚀")
st.write("웹에서 텍스트를 입력하면 연동된 텔레그램으로 즉시 발송됩니다.")

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
# ★ 스포일러 체크박스 상태를 저장할 공간도 초기화합니다.
if 'use_spoiler' not in st.session_state:
    st.session_state.use_spoiler = False

# 3. 메시지 전송 함수 만들기 (버튼 클릭 시 실행될 동작)
def send_telegram_msg():
    message = st.session_state.msg_input 
    use_spoiler = st.session_state.use_spoiler # 현재 체크박스 상태 가져오기
    
    if message.strip():
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        
        # 기본 페이로드 구성
        payload = {
            "chat_id": CHAT_ID,
            "text": message
        }
        
        # ★ 스포일러가 체크되어 있다면 텍스트 변환 및 파라미터 추가
        if use_spoiler:
            # HTML 태그 인식 오류 방지
            safe_msg = message.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            # 스포일러 태그 씌우기
            payload["text"] = f"<tg-spoiler>{safe_msg}</tg-spoiler>"
            payload["parse_mode"] = "HTML"

        try:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                st.success("✅ 메시지가 성공적으로 발송되었습니다!")
                # 발송 성공 시 텍스트창 초기화
                st.session_state.msg_input = "" 
            else:
                st.error(f"❌ 발송 실패 (에러 코드: {response.status_code})\n{response.text}")
        except Exception as e:
            st.error(f"❌ 통신 중 오류가 발생했습니다: {e}")
    else:
        st.warning("⚠️ 전송할 메시지 내용을 먼저 입력해주세요.")

# 4. 입력 폼 구성
st.text_area("전송할 메시지를 입력하세요:", height=150, key="msg_input")

# ★ 스포일러 옵션 체크박스 추가 (key를 부여해 세션 상태와 연결)
st.checkbox("👀 텍스트 스포일러(블러) 처리하기", key="use_spoiler")

# 5. 전송 버튼
st.button("텔레그램으로 전송", type="primary", on_click=send_telegram_msg)
