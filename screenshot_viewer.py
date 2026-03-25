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
    st.session_state.pending_capture = None

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


def save_uploaded(uploaded_file) -> Path:
    CAPTURES_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = uploaded_file.name.replace(" ", "_")
    filepath = CAPTURES_DIR / f"upload_{timestamp}_{safe_name}"
    filepath.write_bytes(uploaded_file.getbuffer())
    return filepath


def save_base64_image(data_url: str) -> Path:
    CAPTURES_DIR.mkdir(parents=True, exist_ok=True)
    header, b64data = data_url.split(",", 1)
    img_bytes = base64.b64decode(b64data)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = CAPTURES_DIR / f"capture_{timestamp}.png"
    filepath.write_bytes(img_bytes)
    return filepath


def delete_capture(filepath: Path) -> None:
    if filepath.exists():
        filepath.unlink()


# -- 4. UI: 헤더 ---------------------------------------------------------------
st.markdown(
    "<h3 style='color:#0088cc;'>Screenshot Viewer</h3>",
    unsafe_allow_html=True,
)

# -- 4-1. 클립보드 붙여넣기 캡처 컴포넌트 --------------------------------------
PASTE_COMPONENT = """
<html>
<head>
<style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }

    #paste-zone {
        border: 2px dashed #0088cc;
        border-radius: 10px;
        padding: 25px;
        text-align: center;
        cursor: pointer;
        background: #f0f8ff;
        transition: all 0.2s;
        outline: none;
    }
    #paste-zone:hover, #paste-zone:focus {
        background: #e0f0ff;
        border-color: #005fa3;
    }
    #paste-zone.has-image {
        border-style: solid;
        border-color: #00aa55;
        background: #f0fff5;
    }
    .step { color: #333; font-size: 14px; margin: 4px 0; }
    .step b { color: #0088cc; }
    .hint { color: #888; font-size: 12px; margin-top: 8px; }
    #status { margin-top: 10px; font-size: 13px; font-weight: 600; }
    #preview { max-width: 100%; max-height: 200px; margin-top: 10px; border-radius: 6px; display: none; }
    #save-btn {
        display: none; margin-top: 10px; padding: 8px 20px;
        background: #0088cc; color: white; border: none;
        border-radius: 6px; font-size: 14px; font-weight: 600;
        cursor: pointer; width: 100%;
    }
    #save-btn:hover { background: #006da3; }
</style>
</head>
<body>

<div id="paste-zone" tabindex="0">
    <div class="step">① <b>Win + Shift + S</b> 를 눌러 화면 영역을 캡처</div>
    <div class="step">② 이 영역을 클릭한 후 <b>Ctrl + V</b> 로 붙여넣기</div>
    <div class="hint">또는 캡처된 이미지를 직접 Ctrl+V로 붙여넣으세요</div>
</div>
<div id="status"></div>
<img id="preview" />
<button id="save-btn">캡처 저장</button>

<script>
const pasteZone = document.getElementById('paste-zone');
const status = document.getElementById('status');
const preview = document.getElementById('preview');
const saveBtn = document.getElementById('save-btn');
let capturedDataUrl = null;

// 페이지 로드시 자동 포커스
pasteZone.focus();

// 붙여넣기 이벤트 (paste-zone과 document 모두)
function handlePaste(e) {
    const items = (e.clipboardData || e.originalEvent.clipboardData).items;
    for (const item of items) {
        if (item.type.startsWith('image/')) {
            e.preventDefault();
            const blob = item.getAsFile();
            const reader = new FileReader();
            reader.onload = function(ev) {
                capturedDataUrl = ev.target.result;
                preview.src = capturedDataUrl;
                preview.style.display = 'block';
                saveBtn.style.display = 'block';
                pasteZone.classList.add('has-image');
                status.style.color = '#00aa55';
                status.textContent = '이미지가 붙여넣어졌습니다. "캡처 저장" 버튼을 눌러주세요.';
                // iframe 높이 자동 조절
                adjustHeight();
            };
            reader.readAsDataURL(blob);
            return;
        }
    }
    status.style.color = '#cc0000';
    status.textContent = '클립보드에 이미지가 없습니다. Win+Shift+S로 먼저 캡처하세요.';
}

pasteZone.addEventListener('paste', handlePaste);
document.addEventListener('paste', handlePaste);

// 저장 버튼 클릭
saveBtn.addEventListener('click', function() {
    if (!capturedDataUrl) return;

    try {
        // 부모 문서(Streamlit)의 hidden textarea에 데이터 설정
        const parentDoc = window.parent.document;
        const textareas = parentDoc.querySelectorAll('textarea');
        let targetTA = null;

        for (const ta of textareas) {
            // capture_data 라벨을 가진 textarea 찾기
            const label = ta.closest('[data-testid="stTextArea"]');
            if (label) {
                targetTA = ta;
                break;
            }
        }

        if (targetTA) {
            // React 내부 상태 업데이트를 위한 트릭
            const nativeSetter = Object.getOwnPropertyDescriptor(
                HTMLTextAreaElement.prototype, 'value'
            ).set;
            nativeSetter.call(targetTA, capturedDataUrl);
            targetTA.dispatchEvent(new Event('input', { bubbles: true }));
            targetTA.dispatchEvent(new Event('change', { bubbles: true }));

            // "저장 실행" 버튼 클릭
            setTimeout(() => {
                const buttons = parentDoc.querySelectorAll('button[kind="primary"]');
                for (const b of buttons) {
                    if (b.textContent.includes('저장 실행')) {
                        b.click();
                        break;
                    }
                }
            }, 500);

            status.textContent = '저장 중...';
        } else {
            status.style.color = '#cc0000';
            status.textContent = '오류: Streamlit 위젯을 찾을 수 없습니다.';
        }
    } catch(err) {
        status.style.color = '#cc0000';
        status.textContent = '오류: ' + err.message;
    }
});

function adjustHeight() {
    const height = document.body.scrollHeight + 20;
    window.parent.postMessage({
        type: "streamlit:setFrameHeight",
        height: height
    }, "*");
}

// 초기 높이 설정
adjustHeight();
</script>
</body>
</html>
"""

components.html(PASTE_COMPONENT, height=150, scrolling=False)

# -- 4-2. 캡처 데이터 수신 (hidden) --------------------------------------------
capture_data = st.text_area("capture_data", key="capture_data", label_visibility="collapsed")

if st.button("저장 실행", type="primary", use_container_width=True):
    if capture_data and capture_data.startswith("data:image"):
        save_base64_image(capture_data)
        st.success("캡처가 저장되었습니다!")
        st.session_state.capture_data = ""
        st.rerun()

# -- 4-3. 파일 업로드 ----------------------------------------------------------
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
