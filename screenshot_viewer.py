import streamlit as st
import streamlit.components.v1 as components
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
# -- 4. 쿼리 파라미터로 전달된 이미지 처리 (핵심!) ----------------------------
# iframe에서 base64 데이터를 부모 페이지의 query param으로 전달하는 방식
query_params = st.query_params
if "pasted_image" in query_params:
    b64data = query_params["pasted_image"]
    if b64data and b64data.startswith("data:image"):
        save_base64_image(b64data)
        st.query_params.clear()
        st.rerun()
# -- 5. UI ---------------------------------------------------------------------
st.markdown(
    "<h3 style='color:#0088cc;'>📸 Screenshot Viewer</h3>",
    unsafe_allow_html=True,
)
# -- 5-1. 클립보드 붙여넣기 영역 -----------------------------------------------
# 방법: paste 이벤트로 이미지를 받고, hidden input에 base64를 담아
#        Streamlit의 text_input으로 전달
st.markdown(
    """
    <style>
    /* 숨긴 텍스트 입력 필드 스타일링 */
    div[data-testid="stTextInput"] label p {
        font-size: 0px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
# 붙여넣기 영역 (순수 HTML/JS, 미리보기 전용)
PASTE_COMPONENT = """
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: transparent; }
  #paste-zone {
    border: 2px dashed #0088cc;
    border-radius: 12px;
    padding: 28px 20px;
    text-align: center;
    cursor: pointer;
    background: rgba(0, 136, 204, 0.04);
    outline: none;
    transition: all 0.25s ease;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 6px;
  }
  #paste-zone:hover, #paste-zone:focus {
    border-color: #005fa3;
    background: rgba(0, 136, 204, 0.10);
    box-shadow: 0 0 0 4px rgba(0, 136, 204, 0.06);
  }
  #paste-zone.has-image {
    border-color: #00aa55;
    border-style: solid;
    background: rgba(0, 170, 85, 0.05);
  }
  .icon { font-size: 28px; }
  #msg { color: #ccc; font-size: 14px; font-weight: 600; }
  #sub-msg { color: #888; font-size: 11px; line-height: 1.4; }
  #preview { margin-top: 14px; text-align: center; display: none; }
  #preview img {
    max-width: 100%;
    max-height: 280px;
    border-radius: 8px;
    border: 1px solid rgba(255,255,255,0.08);
    box-shadow: 0 4px 16px rgba(0,0,0,0.25);
  }
  .save-btn {
    margin-top: 14px;
    padding: 10px 40px;
    background: #0088cc;
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
  }
  .save-btn:hover { background: #006aa3; transform: translateY(-1px); }
  .save-btn:active { transform: translateY(0); }
  .save-btn:disabled { background: #555; cursor: not-allowed; }
</style>
<div id="paste-zone" tabindex="0">
  <div class="icon">📋</div>
  <div id="msg">여기를 클릭한 후 Ctrl+V 로 붙여넣기</div>
  <div id="sub-msg">캡처 도구(Win+Shift+S)로 화면 캡처 → 이 영역 클릭 → Ctrl+V</div>
</div>
<div id="preview">
  <img id="preview-img" />
  <br/>
  <button class="save-btn" id="save-btn">💾 저장하기</button>
</div>
<script>
const pasteZone = document.getElementById('paste-zone');
const msg = document.getElementById('msg');
const subMsg = document.getElementById('sub-msg');
const preview = document.getElementById('preview');
const previewImg = document.getElementById('preview-img');
const saveBtn = document.getElementById('save-btn');
let currentBase64 = null;
function updateHeight() {
    setTimeout(() => {
        const h = document.documentElement.scrollHeight + 10;
        window.parent.postMessage({ type: "streamlit:setFrameHeight", height: h }, "*");
    }, 100);
}
pasteZone.focus();
pasteZone.addEventListener('click', () => pasteZone.focus());
document.addEventListener('paste', (e) => {
    e.preventDefault();
    const items = e.clipboardData.items;
    for (const item of items) {
        if (item.type.startsWith('image/')) {
            const blob = item.getAsFile();
            const reader = new FileReader();
            reader.onloadend = () => {
                currentBase64 = reader.result;
                // 메시지 업데이트
                msg.style.color = '#00cc66';
                msg.textContent = '✓ 이미지가 붙여넣어졌습니다!';
                subMsg.textContent = '아래 미리보기를 확인하고 저장 버튼을 눌러주세요. 다시 Ctrl+V로 교체 가능.';
                pasteZone.classList.add('has-image');
                // 미리보기 표시
                previewImg.src = currentBase64;
                preview.style.display = 'block';
                saveBtn.disabled = false;
                saveBtn.textContent = '💾 저장하기';
                updateHeight();
            };
            reader.readAsDataURL(blob);
            return;
        }
    }
    msg.style.color = '#ff4444';
    msg.textContent = '❌ 클립보드에 이미지가 없습니다';
    subMsg.textContent = 'Win+Shift+S로 캡처 후 다시 시도해주세요.';
    setTimeout(() => {
        msg.style.color = '#ccc';
        msg.textContent = '여기를 클릭한 후 Ctrl+V 로 붙여넣기';
        subMsg.textContent = '캡처 도구(Win+Shift+S)로 화면 캡처 → 이 영역 클릭 → Ctrl+V';
    }, 3000);
});
// 저장 버튼 클릭: 부모 페이지의 URL에 base64를 query param으로 전달
saveBtn.addEventListener('click', () => {
    if (!currentBase64) return;
    saveBtn.disabled = true;
    saveBtn.textContent = '⏳ 저장 중...';
    // 부모 Streamlit 페이지의 URL에 쿼리 파라미터 추가하여 리로드
    const parentUrl = new URL(window.parent.location.href);
    parentUrl.searchParams.set('pasted_image', currentBase64);
    window.parent.location.href = parentUrl.toString();
});
// Ctrl+V 외 입력 차단
pasteZone.addEventListener('keydown', (e) => {
    if (!(e.ctrlKey && e.key === 'v') && !(e.metaKey && e.key === 'v')) {
        e.preventDefault();
    }
});
updateHeight();
</script>
"""
# ★ 높이를 충분히 설정 (붙여넣기 시 동적으로 늘어남)
components.html(PASTE_COMPONENT, height=160, scrolling=True)
# -- 5-2. 파일 업로드 ----------------------------------------------------------
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
# -- 6. UI: 갤러리 ------------------------------------------------------------
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
