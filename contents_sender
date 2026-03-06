import streamlit as st
import requests

# 페이지 기본 설정
st.set_page_config(page_title="텔레그램 메신저", page_icon="💬")

st.title("텔레그램 메시지 발송기 🚀")
st.write("웹에서 텍스트를 입력하면 연동된 텔레그램으로 즉시 발송됩니다.")

# Streamlit Cloud Secrets에서 키값 불러오기
# (로컬에서 테스트할 때는 .streamlit/secrets.toml 파일을 생성해서 사용합니다)
try:
    TELEGRAM_TOKEN = st.secrets["TELEGRAM_TOKEN"]
    CHAT_ID = st.secrets["CHAT_ID"]
except KeyError:
    st.error("⚠️ Streamlit Secrets에 TELEGRAM_TOKEN과 CHAT_ID가 설정되지 않았습니다. 대시보드에서 설정을 확인해주세요.")
    st.stop()

# 입력 폼 구성
message = st.text_area("전송할 메시지를 입력하세요:", height=150)

# 전송 버튼 로직
if st.button("텔레그램으로 전송", type="primary"):
    if message.strip(): # 공백만 입력된 경우 방지
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": CHAT_ID,
            "text": message
        }
        
        try:
            response = requests.post(url, json=payload)
            # HTTP 상태 코드가 200(성공)인 경우
            if response.status_code == 200:
                st.success("✅ 메시지가 성공적으로 발송되었습니다!")
            else:
                st.error(f"❌ 발송 실패 (에러 코드: {response.status_code})\n{response.text}")
        except Exception as e:
            st.error(f"❌ 통신 중 오류가 발생했습니다: {e}")
    else:
        st.warning("⚠️ 전송할 메시지 내용을 먼저 입력해주세요.")
