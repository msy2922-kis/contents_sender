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
    """captures/ 디렉토리에서 이미지 파일 목록을 최신순으로 반환합니다."""
    CAPTURES_DIR.mkdir(parents=True, exist_ok=True)
    files = [f for f in CAPTURES_DIR.iterdir() if f.suffix.lower() in IMAGE_EXTS]
    files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    return files


def save_uploaded(uploaded_file) -> Path:
    """업로드된 파일을 captures/ 디렉토리에 저장합니다."""
    CAPTURES_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = uploaded_file.name.replace(" ", "_")
    filepath = CAPTURES_DIR / f"upload_{timestamp}_{safe_name}"
    filepath.write_bytes(uploaded_file.getbuffer())
    return filepath


def save_base64_image(data_url: str) -> Path:
    """base64 data URL을 이미지 파일로 저장합니다."""
    CAPTURES_DIR.mkdir(parents=True, exist_ok=True)
    header, b64data = data_url.split(",", 1)
    img_bytes = base64.b64decode(b64data)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = CAPTURES_DIR / f"capture_{timestamp}.png"
    filepath.write_bytes(img_bytes)
    return filepath


def delete_capture(filepath: Path) -> None:
    """이미지 파일을 삭제합니다."""
    if filepath.exists():
        filepath.unlink()


# -- 4. UI: 헤더 & 캡처/업로드 -------------------------------------------------
st.markdown(
    "<h3 style='color:#0088cc;'>Screenshot Viewer</h3>",
    unsafe_allow_html=True,
)

# -- 4-1. 브라우저 화면 캡처 (getDisplayMedia + 드래그 영역 선택) ----------------
CAPTURE_JS = """
<div id="capture-btn-wrap">
    <button id="captureBtn" style="
        background-color:#0088cc; color:white; border:none; padding:10px 24px;
        border-radius:6px; font-size:15px; font-weight:600; cursor:pointer; width:100%;
    ">화면 캡처</button>
</div>

<!-- 영역 선택 오버레이 -->
<div id="crop-overlay" style="
    display:none; position:fixed; top:0; left:0; width:100vw; height:100vh;
    z-index:999999; cursor:crosshair;
">
    <canvas id="crop-canvas" style="width:100%; height:100%;"></canvas>
    <div style="
        position:fixed; top:12px; left:50%; transform:translateX(-50%);
        background:rgba(0,0,0,0.7); color:white; padding:8px 20px;
        border-radius:8px; font-size:14px; z-index:1000000;
    ">마우스로 캡처할 영역을 드래그하세요 (ESC 취소)</div>
</div>

<script>
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

        // 프레임 캡처 대기
        await new Promise(r => setTimeout(r, 200));

        const tmpCanvas = document.createElement('canvas');
        tmpCanvas.width = video.videoWidth;
        tmpCanvas.height = video.videoHeight;
        tmpCanvas.getContext('2d').drawImage(video, 0, 0);

        stream.getTracks().forEach(t => t.stop());

        fullImage = tmpCanvas;

        // 오버레이에 캡처된 화면 표시
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        ctx.drawImage(fullImage, 0, 0, canvas.width, canvas.height);
        overlay.style.display = 'block';

    } catch(e) {
        // 사용자가 공유 취소
    }
});

overlay.addEventListener('mousedown', (e) => {
    startX = e.clientX;
    startY = e.clientY;
    dragging = true;
});

overlay.addEventListener('mousemove', (e) => {
    if (!dragging) return;
    // 배경 다시 그리기
    ctx.drawImage(fullImage, 0, 0, canvas.width, canvas.height);
    // 선택 영역 외부 어둡게
    ctx.fillStyle = 'rgba(0,0,0,0.4)';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    // 선택 영역만 밝게
    const x = Math.min(startX, e.clientX);
    const y = Math.min(startY, e.clientY);
    const w = Math.abs(e.clientX - startX);
    const h = Math.abs(e.clientY - startY);
    ctx.clearRect(x, y, w, h);
    ctx.drawImage(fullImage, x, y, w, h, x, y, w, h);
    // 선택 영역 테두리
    ctx.strokeStyle = '#00aaff';
    ctx.lineWidth = 2;
    ctx.strokeRect(x, y, w, h);
});

overlay.addEventListener('mouseup', (e) => {
    if (!dragging) return;
    dragging = false;
    overlay.style.display = 'none';

    const x = Math.min(startX, e.clientX);
    const y = Math.min(startY, e.clientY);
    const w = Math.abs(e.clientX - startX);
    const h = Math.abs(e.clientY - startY);

    if (w < 10 || h < 10) return;

    // 원본 비율로 크롭
    const scaleX = fullImage.width / canvas.width;
    const scaleY = fullImage.height / canvas.height;
    const cropCanvas = document.createElement('canvas');
    cropCanvas.width = Math.round(w * scaleX);
    cropCanvas.height = Math.round(h * scaleY);
    cropCanvas.getContext('2d').drawImage(
        fullImage,
        Math.round(x * scaleX), Math.round(y * scaleY),
        cropCanvas.width, cropCanvas.height,
        0, 0, cropCanvas.width, cropCanvas.height
    );

    const dataUrl = cropCanvas.toDataURL('image/png');

    // Streamlit에 전송 (hidden input + form submit 방식 대신 query param)
    // Streamlit components 통신을 위해 hidden text_input에 값 설정
    const hiddenInput = window.parent.document.querySelectorAll('input[data-testid="stTextInput"]');
    // data URL을 세션에 전달하기 위해 textarea 사용
    const textareas = window.parent.document.querySelectorAll('textarea');
    for (const ta of textareas) {
        if (ta.getAttribute('aria-label') === 'capture_data_input') {
            const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                window.HTMLTextAreaElement.prototype, 'value'
            ).set;
            nativeInputValueSetter.call(ta, dataUrl);
            ta.dispatchEvent(new Event('input', { bubbles: true }));
            // 약간의 지연 후 폼 제출 버튼 클릭
            setTimeout(() => {
                const buttons = window.parent.document.querySelectorAll('button');
                for (const b of buttons) {
                    if (b.innerText === '캡처 저장') {
                        b.click();
                        break;
                    }
                }
            }, 300);
            break;
        }
    }
});

document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && overlay.style.display === 'block') {
        overlay.style.display = 'none';
        dragging = false;
    }
});
</script>
"""

st.components.v1.html(CAPTURE_JS, height=50)

# 캡처 데이터 수신용 hidden input
capture_data = st.text_area("capture_data_input", value="", height=1, label_visibility="collapsed")

col_save, col_upload = st.columns([1, 2])

with col_save:
    if st.button("캡처 저장", use_container_width=True):
        if capture_data and capture_data.startswith("data:image"):
            save_base64_image(capture_data)
            st.success("캡처가 저장되었습니다.")
            st.rerun()

with col_upload:
    uploaded = st.file_uploader(
        "스크린샷 업로드",
        type=["png", "jpg", "jpeg", "bmp", "gif", "webp"],
        accept_multiple_files=True,
        label_visibility="collapsed",
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
