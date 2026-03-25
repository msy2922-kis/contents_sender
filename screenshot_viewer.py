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


# -- 4. UI: 헤더 & 캡처/업로드 -------------------------------------------------
st.markdown(
    "<h3 style='color:#0088cc;'>Screenshot Viewer</h3>",
    unsafe_allow_html=True,
)

# -- 4-1. 브라우저 화면 캡처 컴포넌트 ------------------------------------------
CAPTURE_COMPONENT = """
<html>
<head>
<script src="https://cdn.jsdelivr.net/npm/streamlit-component-lib@latest/dist/streamlit-component-lib.js"></script>
<style>
    body { margin: 0; padding: 0; }
    #captureBtn {
        background-color: #0088cc; color: white; border: none;
        padding: 10px 24px; border-radius: 6px; font-size: 15px;
        font-weight: 600; cursor: pointer; width: 100%;
    }
    #captureBtn:hover { background-color: #006da3; }
    #crop-overlay {
        display: none; position: fixed; top: 0; left: 0;
        width: 100vw; height: 100vh; z-index: 999999; cursor: crosshair;
    }
    #crop-canvas { width: 100%; height: 100%; }
    #crop-hint {
        position: fixed; top: 12px; left: 50%; transform: translateX(-50%);
        background: rgba(0,0,0,0.75); color: white; padding: 8px 20px;
        border-radius: 8px; font-size: 14px; z-index: 1000000;
    }
</style>
</head>
<body>

<button id="captureBtn">화면 캡처</button>

<div id="crop-overlay">
    <canvas id="crop-canvas"></canvas>
    <div id="crop-hint">마우스로 캡처할 영역을 드래그하세요 (ESC 취소)</div>
</div>

<script>
// Streamlit 컴포넌트 초기화
function sendToStreamlit(data) {
    window.parent.postMessage({
        type: "streamlit:setComponentValue",
        value: data
    }, "*");
}

function setFrameHeight(h) {
    window.parent.postMessage({
        type: "streamlit:setFrameHeight",
        height: h
    }, "*");
}

// 높이 설정
setFrameHeight(45);

const btn = document.getElementById('captureBtn');
const overlay = document.getElementById('crop-overlay');
const canvas = document.getElementById('crop-canvas');
const ctx = canvas.getContext('2d');

let fullImage = null;
let startX = 0, startY = 0, dragging = false;

btn.addEventListener('click', async () => {
    try {
        const stream = await navigator.mediaDevices.getDisplayMedia({
            video: { cursor: 'never' }
        });

        const video = document.createElement('video');
        video.srcObject = stream;
        await video.play();
        await new Promise(r => setTimeout(r, 300));

        const tmpCanvas = document.createElement('canvas');
        tmpCanvas.width = video.videoWidth;
        tmpCanvas.height = video.videoHeight;
        tmpCanvas.getContext('2d').drawImage(video, 0, 0);

        stream.getTracks().forEach(t => t.stop());
        fullImage = tmpCanvas;

        // 오버레이를 부모 윈도우(Streamlit)에 추가
        const parentDoc = window.parent.document;
        let parentOverlay = parentDoc.getElementById('capture-crop-overlay');
        if (!parentOverlay) {
            parentOverlay = parentDoc.createElement('div');
            parentOverlay.id = 'capture-crop-overlay';
            parentOverlay.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:999999;cursor:crosshair;display:block;';
            const parentCanvas = parentDoc.createElement('canvas');
            parentCanvas.id = 'capture-crop-canvas';
            parentCanvas.style.cssText = 'width:100%;height:100%;display:block;';
            parentOverlay.appendChild(parentCanvas);
            const hint = parentDoc.createElement('div');
            hint.style.cssText = 'position:fixed;top:12px;left:50%;transform:translateX(-50%);background:rgba(0,0,0,0.75);color:white;padding:8px 20px;border-radius:8px;font-size:14px;z-index:1000000;';
            hint.textContent = '마우스로 캡처할 영역을 드래그하세요 (ESC 취소)';
            parentOverlay.appendChild(hint);
            parentDoc.body.appendChild(parentOverlay);
        } else {
            parentOverlay.style.display = 'block';
        }

        const pCanvas = parentDoc.getElementById('capture-crop-canvas');
        const pCtx = pCanvas.getContext('2d');
        pCanvas.width = window.parent.innerWidth;
        pCanvas.height = window.parent.innerHeight;
        pCtx.drawImage(fullImage, 0, 0, pCanvas.width, pCanvas.height);

        let sx = 0, sy = 0, isDragging = false;

        function onMouseDown(e) {
            sx = e.clientX; sy = e.clientY;
            isDragging = true;
        }
        function onMouseMove(e) {
            if (!isDragging) return;
            pCtx.drawImage(fullImage, 0, 0, pCanvas.width, pCanvas.height);
            pCtx.fillStyle = 'rgba(0,0,0,0.4)';
            pCtx.fillRect(0, 0, pCanvas.width, pCanvas.height);
            const rx = Math.min(sx, e.clientX), ry = Math.min(sy, e.clientY);
            const rw = Math.abs(e.clientX - sx), rh = Math.abs(e.clientY - sy);
            pCtx.clearRect(rx, ry, rw, rh);
            pCtx.drawImage(fullImage,
                rx * (fullImage.width / pCanvas.width),
                ry * (fullImage.height / pCanvas.height),
                rw * (fullImage.width / pCanvas.width),
                rh * (fullImage.height / pCanvas.height),
                rx, ry, rw, rh);
            pCtx.strokeStyle = '#00aaff';
            pCtx.lineWidth = 2;
            pCtx.strokeRect(rx, ry, rw, rh);
        }
        function onMouseUp(e) {
            if (!isDragging) return;
            isDragging = false;
            cleanup();
            const rx = Math.min(sx, e.clientX), ry = Math.min(sy, e.clientY);
            const rw = Math.abs(e.clientX - sx), rh = Math.abs(e.clientY - sy);
            if (rw < 10 || rh < 10) return;
            const ratioX = fullImage.width / pCanvas.width;
            const ratioY = fullImage.height / pCanvas.height;
            const cropCanvas = parentDoc.createElement('canvas');
            cropCanvas.width = Math.round(rw * ratioX);
            cropCanvas.height = Math.round(rh * ratioY);
            cropCanvas.getContext('2d').drawImage(fullImage,
                Math.round(rx * ratioX), Math.round(ry * ratioY),
                cropCanvas.width, cropCanvas.height,
                0, 0, cropCanvas.width, cropCanvas.height);
            const dataUrl = cropCanvas.toDataURL('image/png');
            sendToStreamlit(dataUrl);
        }
        function onKeyDown(e) {
            if (e.key === 'Escape') { isDragging = false; cleanup(); }
        }
        function cleanup() {
            parentOverlay.style.display = 'none';
            parentDoc.removeEventListener('mousedown', onMouseDown);
            parentDoc.removeEventListener('mousemove', onMouseMove);
            parentDoc.removeEventListener('mouseup', onMouseUp);
            parentDoc.removeEventListener('keydown', onKeyDown);
        }
        parentDoc.addEventListener('mousedown', onMouseDown);
        parentDoc.addEventListener('mousemove', onMouseMove);
        parentDoc.addEventListener('mouseup', onMouseUp);
        parentDoc.addEventListener('keydown', onKeyDown);

    } catch(e) {
        // 사용자가 공유 취소
    }
});
</script>
</body>
</html>
"""

capture_result = components.html(CAPTURE_COMPONENT, height=50)

# 캡처 데이터 수신 처리
if capture_result and isinstance(capture_result, str) and capture_result.startswith("data:image"):
    save_base64_image(capture_result)
    st.success("캡처가 저장되었습니다.")
    st.rerun()

# -- 4-2. 파일 업로드 ----------------------------------------------------------
uploaded = st.file_uploader(
    "스크린샷 업로드",
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
    st.info("캡처된 스크린샷이 없습니다. 화면을 캡처하거나 이미지를 업로드하세요.")
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
