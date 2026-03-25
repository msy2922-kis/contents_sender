import streamlit as st
import streamlit.components.v1 as components
import base64
from pathlib import Path
from datetime import datetime
st.set_page_config(page_title="Screenshot Viewer", layout="wide")
CAPTURES_DIR = Path(__file__).parent / "captures"
CAPTURES_DIR.mkdir(parents=True, exist_ok=True)
# -- 헬퍼 ----------------------------------------------------------------------
def get_captures() -> list[Path]:
    exts = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"}
    files = [f for f in CAPTURES_DIR.iterdir() if f.suffix.lower() in exts]
    files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    return files
def save_base64_image(b64data: str) -> Path:
    if "," in b64data:
        b64data = b64data.split(",", 1)[1]
    img_bytes = base64.b64decode(b64data)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    fp = CAPTURES_DIR / f"capture_{ts}.png"
    fp.write_bytes(img_bytes)
    return fp
# -- 쿼리 파라미터로 이미지 수신 -----------------------------------------------
if "pasted_image" in st.query_params:
    b64 = st.query_params["pasted_image"]
    if b64 and b64.startswith("data:image"):
        save_base64_image(b64)
    st.query_params.clear()
    st.rerun()
# -- 메인 UI -------------------------------------------------------------------
st.markdown("<h3 style='color:#0088cc'>Screenshot Viewer</h3>", unsafe_allow_html=True)
components.html("""
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:transparent;overflow-x:hidden}
#z{
  border:2px dashed #0088cc;border-radius:14px;padding:50px 20px;
  text-align:center;cursor:pointer;background:rgba(0,136,204,.04);
  outline:none;transition:.25s;display:flex;flex-direction:column;
  align-items:center;justify-content:center;gap:8px;min-height:200px;
}
#z:hover,#z:focus{border-color:#005fa3;background:rgba(0,136,204,.10);box-shadow:0 0 0 4px rgba(0,136,204,.06)}
#z.ok{border:2px solid #00aa55;background:rgba(0,170,85,.05);padding:16px 20px}
#m{color:#ccc;font-size:15px;font-weight:600}
#s{color:#888;font-size:11px}
#p{width:100%;border-radius:8px;border:1px solid rgba(255,255,255,.08);
   box-shadow:0 4px 16px rgba(0,0,0,.25);margin-top:10px;display:none}
.sv{margin-top:12px;padding:8px 32px;background:#0088cc;color:#fff;border:none;
    border-radius:8px;font-size:13px;font-weight:600;cursor:pointer;transition:.2s}
.sv:hover{background:#006aa3}
.sv:disabled{background:#555;cursor:not-allowed}
</style>
<div id="z" tabindex="0">
  <div id="m">여기를 클릭한 후 Ctrl+V 로 붙여넣기</div>
  <div id="s">캡처 도구(Win+Shift+S) → 이 영역 클릭 → Ctrl+V</div>
  <img id="p"/>
  <button class="sv" id="sv" style="display:none">💾 저장</button>
</div>
<script>
const z=document.getElementById('z'),m=document.getElementById('m'),
      s=document.getElementById('s'),p=document.getElementById('p'),
      sv=document.getElementById('sv');
let cur=null;
const H=()=>setTimeout(()=>window.parent.postMessage({type:"streamlit:setFrameHeight",
  height:document.documentElement.scrollHeight+10},"*"),80);
z.focus();
z.addEventListener('click',()=>z.focus());
document.addEventListener('paste',e=>{
  e.preventDefault();
  for(const i of e.clipboardData.items){
    if(i.type.startsWith('image/')){
      const r=new FileReader();
      r.onloadend=()=>{
        cur=r.result;
        m.style.color='#00cc66';m.textContent='Ctrl+V 로 교체 가능';
        s.textContent='';z.classList.add('ok');
        p.src=cur;p.style.display='block';
        sv.style.display='inline-block';sv.disabled=false;sv.textContent='💾 저장';
        p.onload=()=>H();
      };
      r.readAsDataURL(i.getAsFile());return;
    }
  }
  m.style.color='#ff4444';m.textContent='클립보드에 이미지가 없습니다';
  setTimeout(()=>{m.style.color='#ccc';m.textContent='여기를 클릭한 후 Ctrl+V 로 붙여넣기';
    s.textContent='캡처 도구(Win+Shift+S) → 이 영역 클릭 → Ctrl+V';},2000);
});
sv.addEventListener('click',()=>{
  if(!cur)return;
  sv.disabled=true;sv.textContent='저장 중...';
  const u=new URL(window.parent.location.href);
  u.searchParams.set('pasted_image',cur);
  window.parent.location.href=u.toString();
});
z.addEventListener('keydown',e=>{if(!(e.ctrlKey&&e.key==='v')&&!(e.metaKey&&e.key==='v'))e.preventDefault();});
H();
</script>
""", height=500, scrolling=False)
# -- 갤러리 --------------------------------------------------------------------
images = get_captures()
if images:
    st.divider()
    st.markdown(f"**저장된 캡처 ({len(images)})**")
    cols_per_row = 3
    for i in range(0, len(images), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, col_el in enumerate(cols):
            idx = i + j
            if idx < len(images):
                img_path = images[idx]
                with col_el:
                    st.image(str(img_path), use_container_width=True)
                    mtime = datetime.fromtimestamp(img_path.stat().st_mtime)
                    st.caption(mtime.strftime("%Y-%m-%d %H:%M:%S"))
                    if st.button("🗑️ 삭제", key=f"del_{idx}"):
                        img_path.unlink()
                        st.rerun()
