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
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
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
    "<h3 style='color:#0088cc;'>Screenshot Viewer</h3>",
    unsafe_allow_html=True,
)

# -- 4-1. 클립보드 붙여넣기 (paste 이벤트 기반) --------------------------------
PASTE_HTML = """
<div id="paste-zone" tabindex="0" contenteditable="true" style="
    border: 2px dashed #0088cc; border-radius: 10px; padding: 30px;
    text-align: center; cursor: pointer; background: #f0f8ff;
    outline: none; min-height: 80px; font-family: sans-serif;
    transition: all 0.2s;
">
    <div style="color:#333; font-size:15px; font-weight:600; margin-bottom:6px;">
        여기를 클릭한 후 Ctrl+V 로 붙여넣기
    </div>
    <div style="color:#888; font-size:12px;">
        캡처 도구(Win+Shift+S)로 화면 캡처 → 이 영역 클릭 → Ctrl+V
    </div>
</div>
<div id="status" style="margin-top:8px; font-size:13px; font-weight:600;"></div>
<img id="preview" style="max-width:100%; max-height:250px; margin-top:10px; border-radius:6px; display:none;" />

<script>
const pasteZone = document.getElementById('paste-zone');
const status = document.getElementById('status');
const preview = document.getElementById('preview');

// 자동 포커스
pasteZone.focus();

// 클릭시 포커스
pasteZone.addEventListener('click', () => pasteZone.focus());

// 포커스 스타일
pasteZone.addEventListener('focus', () => {
    pasteZone.style.borderColor = '#005fa3';
    pasteZone.style.background = '#e0f0ff';
});
pasteZone.addEventListener('blur', () => {
    if (!preview.src) {
        pasteZone.style.borderColor = '#0088cc';
        pasteZone.style.background = '#f0f8ff';
    }
});

// 붙여넣기 이벤트
pasteZone.addEventListener('paste', (e) => {
    e.preventDefault();
    e.stopPropagation();

    // contenteditable에 이미지가 삽입되는 것 방지
    pasteZone.innerHTML = '<div style="color:#333; font-size:15px; font-weight:600;">이미지 처리 중...</div>';

    const items = e.clipboardData.items;
    let found = false;

    for (const item of items) {
        if (item.type.startsWith('image/')) {
            found = true;
            const blob = item.getAsFile();
            const reader = new FileReader();

            reader.onload = (ev) => {
                const dataUrl = ev.target.result;

                // 미리보기 표시
                preview.src = dataUrl;
                preview.style.display = 'block';

                // 스타일 변경
                pasteZone.style.borderColor = '#00aa55';
                pasteZone.style.borderStyle = 'solid';
                pasteZone.style.background = '#f0fff5';
                pasteZone.innerHTML = '<div style="color:#00aa55; font-size:15px; font-weight:600;">✓ 이미지가 붙여넣어졌습니다</div>';

                status.style.color = '#0088cc';
                status.textContent = '저장 중...';

                // Streamlit으로 데이터 전송
                window.parent.postMessage({
                    isStreamlitMessage: true,
                    type: "streamlit:setComponentValue",
                    value: dataUrl
                }, "*");

                adjustHeight();
            };
            reader.readAsDataURL(blob);
            break;
        }
    }

    if (!found) {
        pasteZone.innerHTML = `
            <div style="color:#333; font-size:15px; font-weight:600; margin-bottom:6px;">
                여기를 클릭한 후 Ctrl+V 로 붙여넣기
            </div>
            <div style="color:#888; font-size:12px;">
                캡처 도구(Win+Shift+S)로 화면 캡처 → 이 영역 클릭 → Ctrl+V
            </div>`;
        status.style.color = '#cc0000';
        status.textContent = '클립보드에 이미지가 없습니다.';
        adjustHeight();
    }
});

// 텍스트 입력 차단 (contenteditable이지만 타이핑 방지)
pasteZone.addEventListener('keydown', (e) => {
    if (!(e.ctrlKey && e.key === 'v') && !e.metaKey) {
        e.preventDefault();
    }
});

function adjustHeight() {
    const h = document.body.scrollHeight + 10;
    window.parent.postMessage({ type: "streamlit:setFrameHeight", height: h }, "*");
}
adjustHeight();
</script>
"""

paste_result = components.html(PASTE_HTML, height=130, scrolling=False)

# paste 이벤트로 받은 데이터 처리
if paste_result and isinstance(paste_result, str) and paste_result.startswith("data:image"):
    save_base64_image(paste_result)
    st.success("캡처가 저장되었습니다!")
    st.rerun()

# -- 4-2. 파일 업로드 ----------------------------------------------------------
uploaded = st.file_uploader(
    "또는 파일 직접 업로드",
    type=["png", "jpg", "jpeg", "bmp", "gif", "webp"],
    accept_multiple_files=True,
)

if uploaded:
    for f in uploaded:
        save_uploaded(f)
    st.success(f"{len(uploaded)}개 파일이 업로드되었습니다.")
    st.rerun()

# -- 5. UI: 갤러리 ------------------------------------------------------------
st.divider()

images = get_captures()

if not images:
    st.info("캡처된 스크린샷이 없습니다.")
else:
    st.markdown(f"**총 {len(images)}장**")

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
                    st.caption(f"{img_path.name}  |  {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
                    if st.button("삭제", key=f"del_{idx}"):
                        delete_capture(img_path)
                        st.rerun()
