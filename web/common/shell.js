/* 在一体窗口（web/shell）里运行时的配合：
   · 页头的「另一个程序 ↗」链接换成 照片筛选｜照片编辑（｜胶片冲印）切换按钮；
   · ⌘1／⌘2／⌘3（Windows 上 Ctrl）切换；胶片冲印是单独安装的程序，装了才有第三个页签；
   · 切换语言时通知外层，两个界面一起刷新。
   单独在浏览器里打开时（地址里没有 shell=1）什么也不做。 */
(function(){
  const IN=new URLSearchParams(location.search).get("shell")=="1"&&window.parent!==window;
  window.SHELL=IN;
  window.shellPost=m=>{if(IN)window.parent.postMessage(m,"*")};
  if(!IN)return;
  document.documentElement.classList.add("in-shell");
  addEventListener("message",e=>{if(e.source!==window.parent)return;const d=e.data||{};if(d.pc=="reload")location.reload()});
  const APPS=["cull","edit"].concat(window.I18N&&I18N.film?["film"]:[]);      // 装了胶片冲印就多一个页签
  addEventListener("keydown",e=>{const i="123".indexOf(e.key);if((e.metaKey||e.ctrlKey)&&i>=0&&APPS[i]){e.preventDefault();shellPost({pc:"switch",to:APPS[i]})}});
  window.shellNav=function(current){
    const h=document.querySelector("header h1");if(h)h.textContent=T("common.app.suite");
    const a=document.querySelector(".xlink");if(!a)return;
    const seg=document.createElement("div");seg.className="appswitch";seg.setAttribute("role","tablist");
    seg.innerHTML=APPS.map((k,i)=>`<button role="tab" data-app="${k}" class="${k==current?"on":""}" title="⌘${i+1}">${T("common.app."+k)}</button>`).join("");
    seg.querySelectorAll("button").forEach(b=>b.onclick=()=>{if(b.dataset.app!=current)shellPost({pc:"switch",to:b.dataset.app})});
    a.replaceWith(seg)};
})();
