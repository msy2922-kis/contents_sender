import streamlit as st
import streamlit.components.v1 as components
import base64
from pathlib import Path
st.set_page_config(page_title="Screenshot Viewer", layout="wide")
CAPTURE_FILE = Path(__file__).parent / "captures" / "current.png"
CAPTURE_FILE.parent.mkdir(parents=True, exist_ok=True)
# -- 인증 ---------------------------------------------------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if not st.session_state.authenticated:
    st.markdown("<div style='text-align:center;padding:20px 0 10px'>"
                "<div style='font-size:22px;font-weight:700;color:#0088cc'>Screenshot Viewer</div></div>",
                unsafe_allow_html=True)
    pw = st.text_input("비밀번호", type="password", placeholder="비밀번호를 입력하세요")
    if st.button("확인", use_container_width=True, type="primary"):
        if pw == st.secrets["APP_PASSWORD"]:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("비밀번호가 올바르지 않습니다.")
    st.stop()
# -- 쿼리 파라미터로 붙여넣기 이미지 수신 → 파일 저장 --------------------------
if "pasted_image" in st.query_params:
    b64 = st.query_params["pasted_image"]
    if b64 and b64.startswith("data:image"):
        raw = b64.split(",", 1)[1] if "," in b64 else b64
        CAPTURE_FILE.write_bytes(base64.b64decode(raw))
    st.query_params.clear()
    st.rerun()
# -- 삭제 처리 -----------------------------------------------------------------
if "delete" in st.query_params:
    if CAPTURE_FILE.exists():
        CAPTURE_FILE.unlink()
    st.query_params.clear()
    st.rerun()
# -- 메인 UI -------------------------------------------------------------------
st.markdown("<h3 style='color:#0088cc'>Screenshot Viewer</h3>", unsafe_allow_html=True)
# 저장된 이미지가 있으면 base64로 읽어서 iframe에 전달
saved_b64 = ""
if CAPTURE_FILE.exists():
    saved_b64 = "data:image/png;base64," + base64.b64encode(CAPTURE_FILE.read_bytes()).decode()
components.html(f"""
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:transparent}}
#z{{
  border:2px dashed #0088cc;border-radius:14px;padding:50px 20px;
  text-align:center;cursor:pointer;background:rgba(0,136,204,.04);
  outline:none;transition:.25s;display:flex;flex-direction:column;
  align-items:center;justify-content:center;gap:8px;min-height:200px;
}}
#z:hover,#z:focus{{border-color:#005fa3;background:rgba(0,136,204,.10);box-shadow:0 0 0 4px rgba(0,136,204,.06)}}
#z.ok{{border:2px solid #00aa55;background:rgba(0,170,85,.05);padding:16px 20px}}
#m{{color:#ccc;font-size:15px;font-weight:600}}
#s{{color:#888;font-size:11px}}
#p{{width:100%;height:auto;border-radius:8px;border:1px solid rgba(255,255,255,.08);
   box-shadow:0 4px 16px rgba(0,0,0,.25);margin-top:10px;display:none}}
#btns{{margin-top:12px;display:none;gap:8px;justify-content:center}}
.btn{{padding:8px 24px;border:none;border-radius:8px;font-size:13px;font-weight:600;cursor:pointer;transition:.2s}}
.btn-save{{background:#0088cc;color:#fff}}.btn-save:hover{{background:#006aa3}}
.btn-del{{background:#cc3333;color:#fff}}.btn-del:hover{{background:#aa2222}}
.btn:disabled{{background:#555;cursor:not-allowed}}
</style>
<div id="z" tabindex="0">
  <div id="m">여기를 클릭한 후 Ctrl+V 로 붙여넣기</div>
  <div id="s">캡처 도구(Win+Shift+S) → 이 영역 클릭 → Ctrl+V</div>
  <img id="p"/>
  <div id="btns">
    <button class="btn btn-save" id="sv">저장</button>
    <button class="btn btn-del" id="dl">삭제</button>
  </div>
</div>
<script>
const z=document.getElementById('z'),m=document.getElementById('m'),
      s=document.getElementById('s'),p=document.getElementById('p'),
      btns=document.getElementById('btns'),
      sv=document.getElementById('sv'),dl=document.getElementById('dl');
let cur=null;
const saved="{saved_b64}";
function H(){{
  const h=document.documentElement.scrollHeight+20;
  window.parent.postMessage({{type:"streamlit:setFrameHeight",height:h}},"*");
}}
// 저장된 이미지가 있으면 바로 표시
if(saved){{
  cur=saved;
  m.style.color='#00cc66';m.textContent='Ctrl+V 로 교체 가능';
  s.textContent='';z.classList.add('ok');
  p.src=saved;p.style.display='block';
  btns.style.display='flex';
  sv.style.display='none'; // 이미 저장된 상태
  p.onload=()=>setTimeout(H,50);
}}
z.focus();
z.addEventListener('click',e=>{{if(e.target===sv||e.target===dl)return;z.focus();}});
document.addEventListener('paste',e=>{{
  e.preventDefault();
  for(const i of e.clipboardData.items){{
    if(i.type.startsWith('image/')){{
      const r=new FileReader();
      r.onloadend=()=>{{
        cur=r.result;
        m.style.color='#00cc66';m.textContent='새 이미지 붙여넣기 완료';
        s.textContent='저장 버튼을 눌러 유지하거나, Ctrl+V로 교체';
        z.classList.add('ok');
        p.src=cur;p.style.display='block';
        btns.style.display='flex';
        sv.style.display='inline-block';sv.disabled=false;sv.textContent='저장';
        p.onload=()=>setTimeout(H,50);
      }};
      r.readAsDataURL(i.getAsFile());return;
    }}
  }}
  m.style.color='#ff4444';m.textContent='클립보드에 이미지가 없습니다';
  setTimeout(()=>{{m.style.color='#ccc';m.textContent='여기를 클릭한 후 Ctrl+V 로 붙여넣기';
    s.textContent='캡처 도구(Win+Shift+S) → 이 영역 클릭 → Ctrl+V';}},2000);
}});
sv.addEventListener('click',()=>{{
  if(!cur)return;
  sv.disabled=true;sv.textContent='저장 중...';
  const u=new URL(window.parent.location.href);
  u.searchParams.set('pasted_image',cur);
  window.parent.location.href=u.toString();
}});
dl.addEventListener('click',()=>{{
  const u=new URL(window.parent.location.href);
  u.searchParams.set('delete','1');
  window.parent.location.href=u.toString();
}});
z.addEventListener('keydown',e=>{{
  if(!(e.ctrlKey&&e.key==='v')&&!(e.metaKey&&e.key==='v'))e.preventDefault();
}});
window.addEventListener('resize',()=>setTimeout(H,100));
H();
</script>
""", height=0)
