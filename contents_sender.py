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
# 텍스트창의 내용을 저장하고 조작하기 위해 'msg_input'이라는 빈 공간을 만듭니다.
if 'msg_input' not in st.session_state:
    st.session_state.msg_input = ""

# 3. 메시지 전송 함수 만들기 (버튼 클릭 시 실행될 동작)
def send_telegram_msg():
    # 세션 상태에 저장된 현재 텍스트창 내용을 가져옵니다.
    message = st.session_state.msg_input 
    
    if message.strip():
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": CHAT_ID,
            "text": message
        }
        try:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                st.success("✅ 메시지가 성공적으로 발송되었습니다!")
                
                # ★ 핵심: 발송 성공 시 세션 상태를 빈 문자열로 만들어 텍스트창을 초기화합니다 ★
                st.session_state.msg_input = "" 
                
            else:
                st.error(f"❌ 발송 실패 (에러 코드: {response.status_code})\n{response.text}")
        except Exception as e:
            st.error(f"❌ 통신 중 오류가 발생했습니다: {e}")
    else:
        st.warning("⚠️ 전송할 메시지 내용을 먼저 입력해주세요.")

# 4. 입력 폼 구성
# key="msg_input"을 추가하여 텍스트창을 위의 세션 상태와 연결합니다.
st.text_area("전송할 메시지를 입력하세요:", height=150, key="msg_input")

# 5. 전송 버튼
# on_click 속성을 사용하여 버튼이 눌렸을 때 send_telegram_msg 함수를 실행하도록 합니다.
st.button("텔레그램으로 전송", type="primary", on_click=send_telegram_msg)
