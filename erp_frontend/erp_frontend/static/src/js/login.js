// Нэвтрэх хуудас:
//   /login          — ерөнхий: нэвтэрсний дараа эрхтэй БҮХ модуль руугаа (Хянах самбар + цэс)
//   /login/<модуль> — тухайн модуль руу шууд
//   /login/admin    — ерөнхий хуудас, «Админ» сонголт урьдчилан сонгогдсон
// Хоёр сонголт: «Хэрэглэгч» (админ биш) ба «Админ». Backend (/api/auth/login, module, login_as)
// эрх, сонголтыг шалгаж, тохирохгүй бол 403 + шалтгаан (allowed / reason) буцаана.
const KEY="erp-token";
const MODULES={
  orders:       {name:"Захиалга", desc:"Захиалга үүсгэх, батлах, төлөв хянах", icon:"i-orders", home:"/orders/"},
  warehouse:    {name:"Агуулах",  desc:"Үлдэгдэл, орлого, зарлага, нөөцлөлт", icon:"i-wh", home:"/erp-ui#wh"},
  transport:    {name:"Тээвэр",   desc:"Аялал, хүргэлт, машин, жолооч", icon:"i-tr", home:"/erp-ui#tr"},
  routing:      {name:"Маршрут",  desc:"Зогсоолын дараалал, зай оновчлол", icon:"i-rt", home:"/erp-ui#rt"},
  finance:      {name:"Санхүү",   desc:"Нэхэмжлэх, төлбөр, зардал, тайлан", icon:"i-fn", home:"/erp-ui#fn"},
  notifications:{name:"Мэдэгдэл", desc:"Системийн мэдэгдэл, хамт олны мессеж", icon:"i-nt", home:"/erp-ui#nt"},
};
const GENERAL={name:"Нэвтрэх",icon:"i-user",home:"/erp-ui#db"};  // Хянах самбар: эрхтэй бүх модуль
const ROLE={admin:"Админ",dispatcher:"Диспетчер",driver:"Жолооч",warehouse:"Агуулахын ажилтан",accountant:"Нягтлан",user:"Хэрэглэгч"};
const $=id=>document.getElementById(id);
const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const registerPage=location.pathname==="/register";
const seg=location.pathname.split("/")[2]||"";
const module_=MODULES[seg]?seg:null;          // null = ерөнхий нэвтрэлт
const mod=module_?MODULES[module_]:GENERAL;
// Сонгосон нэвтрэх төрөл (?as=admin хаягт хадгална — refresh хийхэд алдагдахгүй).
let mode=seg==="admin"||new URLSearchParams(location.search).get("as")==="admin"?"admin":"user";
let token=null;try{token=localStorage.getItem(KEY)}catch{}
const setToken=t=>{try{t?localStorage.setItem(KEY,t):localStorage.removeItem(KEY)}catch{}};

// Зөвхөн энэ сайтын дотоод зам руу буцна (?next=/orders/#order/5).
function nextUrl(){
  const n=new URLSearchParams(location.search).get("next");
  return n&&n.startsWith("/")&&!n.startsWith("//")?n:mod.home;
}
const card=(k,m)=>`<a class="mcard" href="/login/${k}"><span class="micon"><svg><use href="#${m.icon}"/></svg></span><span><b>${m.name}</b><span class="muted">${m.desc}</span></span></a>`;

// Хадгалсан token хүчинтэй бол хэрэглэгчийг буцаана (хугацаа дууссан бол арилгана).
async function currentUser(){
  if(!token)return null;
  try{
    const r=await fetch("/api/auth/me",{headers:{Authorization:"Bearer "+token}});
    if(r.ok)return await r.json();
    if(r.status===401){setToken(null);token=null}
  }catch{}
  return null;
}
const who=u=>`<b>${esc(u.full_name||u.username)}</b> (${esc(ROLE[u.role]||u.role)})`;

function setMode(m){
  mode=m;$("le").hidden=true;
  const q=new URLSearchParams(location.search);m==="admin"?q.set("as","admin"):q.delete("as");
  const path=seg==="admin"?"/login":location.pathname;  // /login/admin → «Хэрэглэгч» сонговол ерөнхий хуудас
  history.replaceState(null,"",path+(q.toString()?"?"+q:""));
  document.querySelectorAll("#seg [data-as]").forEach(b=>{const on=b.dataset.as===m;b.classList.toggle("on",on);b.setAttribute("aria-selected",on)});
  const admin=m==="admin";
  $("lf").classList.toggle("admin",admin);
  $("lf").querySelector(".mi").setAttribute("href","#"+(admin?"i-admin":mod.icon));
  $("lf").querySelector(".mt").textContent=module_?(admin?`${mod.name} · Админ`:mod.name):(admin?"Админ нэвтрэлт":"Хэрэглэгчээр нэвтрэх");
  $("md").textContent=admin?"Зөвхөн системийн админ нэвтэрнэ"
    :module_?`${mod.name} модульд хэрэглэгчээр нэвтрэх`:"Эрхтэй бүх модуль руугаа нэвтэрнэ";
  $("lb").textContent=admin?"Админаар нэвтрэх":"Нэвтрэх";
  $("regl").hidden=admin;  // админ өөрөө бүртгүүлэхгүй
  document.title=`${module_?mod.name+" · ":""}${admin?"Админ нэвтрэлт":"Нэвтрэх"} · Logistics ERP`;
  if(!$("lf").hidden)$("lu").focus();
}

async function init(){
  if(registerPage)return initRegister();
  const user=await currentUser();
  $("single").hidden=false;
  if(module_){
    $("others").innerHTML=Object.entries(MODULES).filter(([k])=>k!==module_).map(([k,m])=>`<a href="/login/${k}">${m.name}</a>`).join("");
    $("back").hidden=false;
  }else{
    $("mgrid").innerHTML=Object.entries(MODULES).map(([k,m])=>card(k,m)).join("");
    $("chooser").hidden=false;
  }
  setMode(mode);
  // Өмнө нэвтэрсэн бол шууд оруулахгүй: үргэлжлүүлэх эсвэл өөр хэрэглэгчээр нэвтрэхийг сонгуулна.
  if(user){
    // Сонголт ба session-ий дүр таарах ёстой: «Хэрэглэгч» дээр админы session-оор үргэлжлүүлэхгүй, эсрэгээрээ ч мөн.
    const roleOk=mode==="admin"?user.role==="admin":user.role!=="admin";
    const ok=roleOk&&(!module_||user.modules.includes(module_));
    $("sess").querySelector(".mi").setAttribute("href","#"+(module_?mod.icon:mode==="admin"?"i-admin":"i-user"));
    $("sess").querySelector(".mt").textContent=module_?mod.name:"Logistics ERP";
    $("sess-who").innerHTML=`Та ${who(user)} нэрээр нэвтэрсэн байна`;
    $("sess-go").hidden=!ok;
    $("sess-no").hidden=ok;
    $("sess-no").textContent=ok?""
      :!roleOk&&mode==="admin"?"Энэ хэрэглэгч админ биш. Админаар нэвтрэх бол «Өөр хэрэглэгчээр нэвтрэх» дарна уу."
      :!roleOk?"Та одоо АДМИНААР нэвтэрсэн байна. Хэрэглэгчээр нэвтрэх бол «Өөр хэрэглэгчээр нэвтрэх» дарна уу."
      :`Энэ хэрэглэгч ${mod.name} модульд эрхгүй. Өөр хэрэглэгчээр нэвтэрнэ үү.`;
    $("sess").hidden=false;(ok?$("sess-go"):$("sess").querySelector(".btn:not(.primary)")).focus();
    return;
  }
  showForm();
}
function showForm(){$("sess").hidden=true;$("lf").hidden=false;$("lu").focus()}
// Нэвтрэх формыг харуулна. Хуучин session-ийг шинэ хэрэглэгч амжилттай нэвтэрсний дараа л солино
// (бусад таб шинэ хэрэглэгчээр шинэчлэгдэнэ; цуцалбал хуучин session хэвээр).
function switchUser(){showForm()}

async function doLogin(e){
  e.preventDefault();$("le").hidden=true;$("lb").disabled=true;
  try{
    let res,data=null;
    try{res=await fetch("/api/auth/login",{method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({username:$("lu").value.trim(),password:$("lp").value,module:module_,login_as:mode})})}
    catch{throw new Error("Серверт холбогдож чадсангүй")}
    try{data=await res.json()}catch{}
    // Сонголт таарахгүй: зөв сонголт руу нэг товшилтоор шилжүүлнэ.
    if(res.status===403&&data?.error?.reason){
      const toAdmin=data.error.reason==="use_admin";
      $("le").innerHTML=(toAdmin?"Та <b>админ</b> хэрэглэгч байна. «Админ» сонголтоор нэвтэрнэ үү."
        :`Энэ хэрэглэгч (<b>${esc(ROLE[data.error.role]||data.error.role)}</b>) админ биш. «Хэрэглэгч» сонголтоор нэвтэрнэ үү.`)+
        `<div class="allowed"><a href="#" onclick="setMode('${toAdmin?"admin":"user"}');return false">${toAdmin?"Админ":"Хэрэглэгч"} сонголт руу шилжих →</a></div>`;
      $("le").hidden=false;return;
    }
    if(res.status===403&&data?.error?.allowed){
      const ok=data.error.allowed.filter(k=>MODULES[k]);
      $("le").innerHTML=`Таны эрх (<b>${esc(ROLE[data.error.role]||data.error.role)}</b>) <b>${mod.name}</b> модульд хүрэлцэхгүй байна.`+
        `<div class="allowed"><a href="/login">Бүх модуль руугаа нэвтрэх</a>${ok.map(k=>`<a href="/login/${k}">${MODULES[k].name}</a>`).join("")}</div>`;
      $("le").hidden=false;return;
    }
    if(res.status===429)throw new Error(`Олон удаа буруу оролдлоо. ${data?.error?.retry_minutes||10} минутын дараа дахин оролдоно уу.`);
    if(res.status===401&&data?.error?.reason==="pending")
      throw new Error("Таны бүртгэл админы баталгаажуулалт хүлээж байна. Баталгаажсаны дараа нэвтэрнэ үү.");
    if(res.status===401&&data?.error?.reason==="inactive")
      throw new Error("Таны хэрэглэгч идэвхгүй болсон байна. Админд хандана уу.");
    if(res.status===401){
      const left=data?.error?.attempts_left;
      throw new Error("Хэрэглэгчийн нэр эсвэл нууц үг буруу"+(left!=null?(left<=2?` — ${left} оролдлого үлдлээ`:""):", эсвэл хэрэглэгч идэвхгүй байна"));
    }
    if(!res.ok)throw new Error(data?.error?.message||`Алдаа ${res.status}`);
    setToken(data.access_token);
    location.replace(nextUrl());
  }catch(err){$("le").textContent=err.message;$("le").hidden=false}
  finally{$("lb").disabled=false}
}
// ---------------- Бүртгүүлэх (/register)
const REG_ROLES=[["user","Хэрэглэгч","Миний мэдээлэл, мэдэгдэл, мессеж"],["dispatcher","Диспетчер","Захиалга, агуулах, тээвэр, маршрут, мэдэгдэл"],["warehouse","Агуулахын ажилтан","Захиалга, агуулах, мэдэгдэл"],
  ["driver","Жолооч","Тээвэр, маршрут, өөрийн аялал, мэдэгдэл"],["accountant","Нягтлан","Санхүү, захиалга харах, мэдэгдэл"]];
function initRegister(){
  document.title="Бүртгүүлэх · Logistics ERP";
  $("rr").innerHTML=REG_ROLES.map(([v,l])=>`<option value="${v}">${l}</option>`).join("");
  regHint();$("reg").hidden=false;$("rn").focus();
}
function regHint(){const r=REG_ROLES.find(x=>x[0]===$("rr").value);$("rrh").textContent=r?`Нэвтэрч болох: ${r[2]}.${r[0]==="user"?"":" Ажлын үүргийг админ баталгаажуулна."}`:""}
async function doRegister(e){
  e.preventDefault();$("re").hidden=true;
  if($("rp").value!==$("rp2").value){$("re").textContent="Нууц үг таарахгүй байна";$("re").hidden=false;$("rp2").focus();return}
  $("rb").disabled=true;
  try{
    let res,data=null;
    try{res=await fetch("/api/auth/register",{method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({full_name:$("rn").value.trim(),username:$("ru").value.trim(),password:$("rp").value,role:$("rr").value})})}
    catch{throw new Error("Серверт холбогдож чадсангүй")}
    try{data=await res.json()}catch{}
    if(res.status===409)throw new Error(`«${$("ru").value.trim()}» хэрэглэгчийн нэр бүртгэлтэй байна. Өөр нэр сонгоно уу.`);
    if(res.status===429)throw new Error("Олон бүртгэл илгээсэн байна. Түр хүлээгээд дахин оролдоно уу.");
    if(res.status===422)throw new Error("Мэдээлэл буруу байна: хэрэглэгчийн нэр 3+ латин тэмдэгт, нууц үг 6+ тэмдэгт байх ёстой.");
    if(!res.ok)throw new Error(data?.error?.message||`Алдаа ${res.status}`);
    $("rf").hidden=true;$("rokt").textContent=`Хэрэглэгчийн нэр: ${data.username}`;$("rok").hidden=false;
  }catch(err){$("re").textContent=err.message;$("re").hidden=false}
  finally{$("rb").disabled=false}
}
init();
