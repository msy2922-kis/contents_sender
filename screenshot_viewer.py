import streamlit as st
import streamlit.components.v1 as components
st.set_page_config(page_title="Screenshot Viewer", layout="wide")
# -- 인증 ---------------------------------------------------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
def check_password() -> bool:
    if st.session_state.authenticated:
        return True
    st.markdown(
        "<div style='text-align:center;padding:40px 0 20px'>"
        "<div style='font-size:28px;font-weight:700;color:#0088cc'>Screenshot Viewer</div>"
        "<div style='font-size:13px;color:#7d8590;margin-top:6px'>접근 제한 구역</div>"
        "</div>",
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
# -- UI ------------------------------------------------------------------------
st.markdown("<h3 style='color:#0088cc'>📸 Screenshot Viewer</h3>", unsafe_allow_html=True)
PASTE_HTML = """
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:transparent;overflow-x:hidden}
#z{
  border:2px dashed #0088cc;border-radius:14px;padding:60px 20px;
  text-align:center;cursor:pointer;background:rgba(0,136,204,.04);
  outline:none;transition:.25s;display:flex;flex-direction:column;
  align-items:center;justify-content:center;gap:10px;min-height:240px;
}
#z:hover,#z:focus{border-color:#005fa3;background:rgba(0,136,204,.10);box-shadow:0 0 0 4px rgba(0,136,204,.06)}
#z.ok{border-color:#00aa55;border-style:solid;background:rgba(0,170,85,.05);padding:20px}
.ic{font-size:40px}
#m{color:#ccc;font-size:16px;font-weight:600}
#s{color:#888;font-size:12px;line-height:1.5}
#p{max-width:100%;border-radius:8px;border:1px solid rgba(255,255,255,.08);
   box-shadow:0 4px 16px rgba(0,0,0,.25);margin-top:12px;display:none}
</style>
<div id="z" tabindex="0">
  <div class="ic" id="ic">📋</div>
  <div id="m">여기를 클릭한 후 Ctrl+V 로 붙여넣기</div>
  <div id="s">캡처 도구(Win+Shift+S)로 화면 캡처 → 이 영역 클릭 → Ctrl+V</div>
  <img id="p"/>
</div>
<script>
const z=document.getElementById('z'),ic=document.getElementById('ic'),
      m=document.getElementById('m'),s=document.getElementById('s'),
      p=document.getElementById('p');
const H=()=>setTimeout(()=>{
  window.parent.postMessage({type:"streamlit:setFrameHeight",height:document.documentElement.scrollHeight+10},"*");
},80);
z.focus();
z.addEventListener('click',()=>z.focus());
document.addEventListener('paste',e=>{
  e.preventDefault();
  for(const i of e.clipboardData.items){
    if(i.type.startsWith('image/')){
      const r=new FileReader();
      r.onloadend=()=>{
        ic.textContent='✅';
        m.style.color='#00cc66';
        m.textContent='이미지가 붙여넣어졌습니다';
        s.textContent='다시 Ctrl+V 하면 교체됩니다';
        z.classList.add('ok');
        p.src=r.result;
        p.style.display='block';
        p.onload=()=>H();
      };
      r.readAsDataURL(i.getAsFile());
      return;
    }
  }
  m.style.color='#ff4444';m.textContent='❌ 클립보드에 이미지가 없습니다';
  s.textContent='Win+Shift+S로 캡처 후 다시 시도해주세요.';
  setTimeout(()=>{m.style.color='#ccc';m.textContent='여기를 클릭한 후 Ctrl+V 로 붙여넣기';
    s.textContent='캡처 도구(Win+Shift+S)로 화면 캡처 → 이 영역 클릭 → Ctrl+V';},3000);
});
z.addEventListener('keydown',e=>{if(!(e.ctrlKey&&e.key==='v')&&!(e.metaKey&&e.key==='v'))e.preventDefault();});
H();
</script>
"""
components.html(PASTE_HTML, height=280, scrolling=True)
