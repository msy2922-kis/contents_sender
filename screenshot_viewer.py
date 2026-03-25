import streamlit as st
import base64
from pathlib import Path
from datetime import datetime
# -- 1. 페이지 설정 -----------------------------------------------------------
st.set_page_config(page_title="Screenshot Viewer", layout="wide")
CAPTURES_DIR = Path(__file__).parent / "captures"
# -- 2. 세션 상태 초기화 -------------------------------------------------------
if "initialized" not in st.session_state:
    st.session_state.initialized = True
    st.session_state.authenticated = False
# -- 2-1. 접근 제한: 비밀번호 확인 ---------------------------------------------
def check_password() -> bool:
    if st.session_state.get("authenticated"):
        return True
    st.markdown(
        """
        <div style="text-align:center; padding: 40px 0 20px;">
            <div style="font-size:28px; font-weight:700; color:#0088cc; letter-spacing:.02em;">
                Screenshot Viewer
            </div>
            <div style="font-size:13px; color:#7d8590; margin-top:6px;">
                접근 제한 구역
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    pw = st.text_input("비밀번호", type="password", placeholder="비밀번호를 입력하세요")
    if st.button("확인", use_container_width=True, type="primary"):
        if pw == st.secrets["APP_PASSWORD"]:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("비밀번호가 올바르지 않습니다.")
    return False
if not check_password():
    st.stop()
# -- 3. 헬퍼 함수 -------------------------------------------------------------
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"}
def get_captures() -> list[Path]:
    CAPTURES_DIR.mkdir(parents=True, exist_ok=True)
    files = [f for f in CAPTURES_DIR.iterdir() if f.suffix.lower() in IMAGE_EXTS]
    files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    return files
def save_base64_image(b64data: str) -> Path:
    CAPTURES_DIR.mkdir(parents=True, exist_ok=True)
    if "," in b64data:
        b64data = b64data.split(",", 1)[1]
    img_bytes = base64.b64decode(b64data)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filepath = CAPTURES_DIR / f"capture_{timestamp}.png"
    filepath.write_bytes(img_bytes)
    return filepath
def save_uploaded(uploaded_file) -> Path:
    CAPTURES_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = uploaded_file.name.replace(" ", "_")
    filepath = CAPTURES_DIR / f"upload_{timestamp}_{safe_name}"
    filepath.write_bytes(uploaded_file.getbuffer())
    return filepath
def delete_capture(filepath: Path) -> None:
    if filepath.exists():
        filepath.unlink()
# -- 4. UI ---------------------------------------------------------------------
st.markdown(
    "<h3 style='color:#0088cc;'>📸 Screenshot Viewer</h3>",
    unsafe_allow_html=True,
)
# -- 4-1. 클립보드 붙여넣기 (streamlit-paste-button) ---------------------------
# 설치: pip install streamlit-paste-button
try:
    from streamlit_paste_button import paste_image_button
    paste_result = paste_image_button(
        label="📋 클립보드에서 붙여넣기 (Ctrl+V 후 이 버튼 클릭)",
        text_color="#0088cc",
        background_color="transparent",
        hover_background_color="rgba(0,136,204,0.08)",
        errors="raise",
    )
    if paste_result.image_data is not None:
        # 미리보기 표시
        st.image(
            paste_result.image_data,
            caption="📌 붙여넣은 이미지 미리보기",
            use_container_width=True,
        )
        if st.button("💾 저장하기", type="primary", use_container_width=True):
            import io
            buf = io.BytesIO()
            paste_result.image_data.save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode()
            save_base64_image(f"data:image/png;base64,{b64}")
            st.success("✅ 캡처가 저장되었습니다!")
            st.rerun()
except ImportError:
    st.warning(
        "⚠️ 클립보드 붙여넣기를 사용하려면 패키지 설치가 필요합니다:"
    )
    st.code("pip install streamlit-paste-button", language="bash")
    st.info("설치 후 앱을 재시작하면 클립보드 붙여넣기가 활성화됩니다.")
# -- 4-2. 파일 업로드 ----------------------------------------------------------
st.markdown("---")
uploaded = st.file_uploader(
    "또는 파일 직접 업로드",
    type=["png", "jpg", "jpeg", "bmp", "gif", "webp"],
    accept_multiple_files=True,
)
if uploaded:
    for f in uploaded:
        save_uploaded(f)
    st.success(f"✅ {len(uploaded)}개 파일이 업로드되었습니다.")
    st.rerun()
# -- 5. UI: 갤러리 ------------------------------------------------------------
st.divider()
images = get_captures()
if not images:
    st.info("📭 캡처된 스크린샷이 없습니다.")
else:
    st.markdown(f"**📷 총 {len(images)}장**")
    cols_per_row = 3
    for i in range(0, len(images), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, col in enumerate(cols):
            idx = i + j
            if idx < len(images):
                img_path = images[idx]
                with col:
                    st.image(str(img_path), use_container_width=True)
                    mtime = datetime.fromtimestamp(img_path.stat().st_mtime)
                    st.caption(
                        f"{img_path.name}  |  {mtime.strftime('%Y-%m-%d %H:%M:%S')}"
                    )
                    if st.button("🗑️ 삭제", key=f"del_{idx}"):
                        delete_capture(img_path)
                        st.rerun()
