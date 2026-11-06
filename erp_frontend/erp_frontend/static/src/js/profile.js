// Миний мэдээлэл — бүх хэрэглэгчид: өөрийн бүртгэл, нэр засах, нууц үг солих, сүүлийн үйлдлүүд.
// /api/auth/me, PATCH /api/auth/me, /api/auth/me/activity
TABS.me={perm:null,render:()=>rMe()};
const MY_ACTION={login:"Нэвтэрсэн",login_denied:"Нэвтрэх эрхгүй",update:"Мэдээлэл зассан",password:"Нууц үг сольсон",
  register:"Бүртгүүлсэн",send:"Мессеж илгээсэн",create:"Үүсгэсэн",status:"Төлөв солисон",export:"Тайлан татсан"};
const MY_FIELD={full_name:"Овог нэр"};
const MY_MOD={orders:"Захиалга",warehouse:"Агуулах",transport:"Тээвэр",routing:"Маршрут",finance:"Санхүү",notifications:"Мэдэгдэл"};

const rMe=run(async()=>{
  const [u,act]=await Promise.all([api("/auth/me"),api("/auth/me/activity")]);
  me=u;$("un").textContent=u.full_name||u.username;
  const initials=(u.full_name||u.username).split(/\s+/).map(w=>w[0]).join("").slice(0,2).toUpperCase();
  $("mea").textContent=initials;$("men").textContent=u.full_name||u.username;
  $("meu").textContent=u.username;$("mer").innerHTML=`<span class="pill ac">${esc(ROLE[u.role]||u.role)}</span>`;
  $("mes").innerHTML=u.is_active?'<span class="pill ok">Идэвхтэй</span>':'<span class="pill mu">Идэвхгүй</span>';
  $("mec").textContent=u.created_at?localTime(u.created_at).slice(0,10):"—";
  $("mem").innerHTML=u.modules.map(m=>`<span>${MY_MOD[m]||m}</span>`).join("");
  $("me-n").value=u.full_name||"";
  $("meact").innerHTML=act.map(a=>`<tr><td>${localTime(a.created_at)}</td><td>${esc(MY_ACTION[a.action]||a.action)}</td>
    <td class="mu">${a.detail?.module?esc(MY_MOD[a.detail.module]||a.detail.module)+" модуль":a.detail?.fields?esc(a.detail.fields.map(f=>MY_FIELD[f]||f).join(", ")):""}</td></tr>`).join("")
    ||emptyRow(3,"Үйлдэл алга");
});
const meSave=run(async e=>{e.preventDefault();
  const name=$("me-n").value.trim();
  if(name===(me.full_name||""))return notice("Өөрчлөлт алга");
  await api("/auth/me",{method:"PATCH",body:{full_name:name}});
  notice("Нэр шинэчлэгдлээ");rMe();
});
