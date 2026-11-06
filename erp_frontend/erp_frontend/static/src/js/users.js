// Ажилтнууд — /api/auth/users, /api/auth/roles (зөвхөн админ, "auth:users").
TABS.us={perm:"auth:users",render:()=>rUs()};
const MOD_NAME={orders:"Захиалга",warehouse:"Агуулах",transport:"Тээвэр",routing:"Маршрут",finance:"Санхүү",notifications:"Мэдэгдэл"};
const ROLE_DESC={user:"Өөрийн мэдээлэл, мэдэгдэл, мессеж",admin:"Бүх модуль, ажилтан удирдах",dispatcher:"Захиалга, тээвэр, маршрут",driver:"Өөрийн аялал, хүргэлт",
  warehouse:"Агуулах, захиалга бэлтгэх",accountant:"Санхүү, захиалга харах"};
let usList=[],usRoles=[],usRole="",usCur=null,usPending=[];
function usSet(r){usRole=r;usDraw()}

const rUs=run(async()=>{
  let all;
  [all,usRoles]=await Promise.all([api("/auth/users"),api("/auth/roles")]);
  usPending=all.filter(u=>u.pending);usList=all.filter(u=>!u.pending);
  const active=usList.filter(u=>u.is_active).length;
  kpis("usk",[["Нийт ажилтан",usList.length],["Идэвхтэй",active],["Идэвхгүй",usList.length-active,usList.length-active?"warn":""],
    ["Админ",usList.filter(u=>u.role==="admin"&&u.is_active).length],["Бүртгэлийн хүсэлт",usPending.length,usPending.length?"warn":""]]);
  usPendingDraw();
  $("mu-r").innerHTML=usRoles.map(r=>`<option value="${r.role}">${ROLE[r.role]||r.role}</option>`).join("");
  const mods=Object.keys(MOD_NAME);
  $("usr").innerHTML=`<thead><tr><th>Дүр</th>${mods.map(m=>`<th class="num">${MOD_NAME[m]}</th>`).join("")}</tr></thead><tbody>`+
    usRoles.map(r=>`<tr><td>${ROLE[r.role]||r.role}<span class="sub">${ROLE_DESC[r.role]||""}</span></td>${mods.map(m=>`<td class="num">${r.modules.includes(m)?'<span class="yes" aria-label="Тийм">✓</span>':'<span class="no" aria-label="Үгүй">—</span>'}</td>`).join("")}</tr>`).join("")+"</tbody>";
  usDraw();
  $("aufu").innerHTML=`<option value="">Бүх ажилтан</option>`+usList.map(u=>`<option value="${u.id}">${esc(u.full_name||u.username)}</option>`).join("");
  auLoad(1);
});
function usDraw(){
  chips("usc",[["","Бүгд"],...usRoles.map(r=>[r.role,ROLE[r.role]||r.role])],usRole,"usSet");
  const q=$("usq").value.trim().toLowerCase();
  const rows=usList.map((u,i)=>[u,i]).filter(([u])=>(!usRole||u.role===usRole)&&(!q||(u.full_name+" "+u.username).toLowerCase().includes(q)));
  $("usb").innerHTML=rows.map(([u,i])=>{const self=u.id===me.id;
    return `<tr><td>${esc(u.full_name||u.username)}${self?' <span class="pill ac">Та</span>':""}<span class="sub">${esc(u.username)}</span></td>
    <td>${esc(ROLE[u.role]||u.role)}</td>
    <td><div class="mods">${u.modules.map(m=>`<span>${MOD_NAME[m]||m}</span>`).join("")}</div></td>
    <td>${u.is_active?'<span class="pill ok">Идэвхтэй</span>':'<span class="pill mu">Идэвхгүй</span>'}</td>
    <td class="act"><button class="btn small" onclick="usEdit(${i})">Засах</button><button class="btn small" onclick="usPass(${i})">Нууц үг</button>${self?"":
      u.is_active?`<button class="btn small danger" onclick="usToggle(${i})">Идэвхгүй болгох</button>`:`<button class="btn small" onclick="usToggle(${i})">Идэвхжүүлэх</button>`}</td></tr>`}).join("")
    ||emptyRow(5,"Ажилтан олдсонгүй");
}
function usRoleHint(){
  const r=usRoles.find(x=>x.role===$("mu-r").value);
  $("mu-hint").textContent=r?`Нэвтэрч болох: ${r.modules.map(m=>MOD_NAME[m]).join(", ")}`:"";
}
function usNew(){
  usCur=null;openModal("m-user");
  $("mu-h").textContent="Ажилтан нэмэх";$("mu-info").textContent="Ажилтан өөрийн хэрэглэгчийн нэр, нууц үгээр модуль бүрийн нэвтрэх хуудсаар нэвтэрнэ.";
  $("mu-u").disabled=false;$("mu-pl").hidden=false;$("mu-p").required=true;$("mu-al").hidden=true;$("mu-r").disabled=false;
  $("mu-r").value="dispatcher";usRoleHint();
}
function usEdit(i){
  usCur=usList[i];const self=usCur.id===me.id;openModal("m-user");
  $("mu-h").textContent="Ажилтан засах";$("mu-info").textContent=self?"Өөрийн дүр, идэвхийг өөрчлөх боломжгүй.":"";
  $("mu-u").value=usCur.username;$("mu-u").disabled=true;$("mu-n").value=usCur.full_name;
  $("mu-r").value=usCur.role;$("mu-r").disabled=self;$("mu-pl").hidden=true;$("mu-p").required=false;
  $("mu-al").hidden=self;$("mu-a").checked=usCur.is_active;usRoleHint();
}
const usSave=run(async e=>{e.preventDefault();
  const body={full_name:$("mu-n").value.trim(),role:$("mu-r").value};
  if(usCur){
    if(usCur.id!==me.id)body.is_active=$("mu-a").checked;else delete body.role;
    await api(`/auth/users/${usCur.id}`,{method:"PATCH",body});
  }else{
    await api("/auth/users",{method:"POST",body:{...body,username:$("mu-u").value.trim(),password:$("mu-p").value}});
  }
  closeModal();rUs();
});
const usToggle=run(async i=>{
  const u=usList[i];
  if(u.is_active&&!confirm(`${u.full_name||u.username}-г идэвхгүй болгох уу? Тэр нэвтэрч чадахгүй болно.`))return;
  await api(`/auth/users/${u.id}`,{method:"PATCH",body:{is_active:!u.is_active}});rUs();
});
function usPass(i){usCur=usList[i];openModal("m-pass");$("mp2-info").textContent=`${usCur.full_name||usCur.username} (${usCur.username})`}
const usPassDo=run(async e=>{e.preventDefault();
  await api(`/auth/users/${usCur.id}`,{method:"PATCH",body:{password:$("mp2-p").value}});
  closeModal();notice("Нууц үг шинэчлэгдлээ");
});

// ---------------- Үйлдлийн түүх (core_audit_logs)
const AU_ACTION={login:"Нэвтэрсэн",login_denied:"Нэвтрэх эрхгүй",create:"Үүсгэсэн",update:"Зассан",delete:"Устгасан",status:"Төлөв солисон",
  password:"Нууц үг сольсон",in:"Орлого",out:"Зарлага",adjust:"Тооллого",transfer:"Шилжүүлэг",reserve:"Нөөцөлсөн",start:"Аялал эхлүүлсэн",
  cancel:"Цуцалсан",complete:"Дуусгасан",deliver:"Хүргэсэн",fail:"Хүргэлт амжилтгүй",optimize:"Маршрут оновчилсон",sequence:"Дараалал солисон",send:"Мессеж илгээсэн",
  register:"Бүртгүүлсэн",approve:"Бүртгэл баталсан",reject:"Бүртгэл татгалзсан",export:"Тайлан татсан"};
const AU_ENTITY={"auth.User":"Ажилтан","orders.Order":"Захиалга","masterdata.Customer":"Харилцагч","masterdata.Product":"Бараа","masterdata.Location":"Байршил",
  "warehouse.Movement":"Агуулахын хөдөлгөөн","warehouse.Stock":"Үлдэгдэл","warehouse.Reservation":"Нөөцлөлт","transport.Vehicle":"Машин","transport.Driver":"Жолооч",
  "transport.Trip":"Аялал","transport.Shipment":"Хүргэлт","routing.Trip":"Маршрут","finance.Invoice":"Нэхэмжлэх","finance.Payment":"Төлбөр",
  "finance.Expense":"Зардал","notifications.Message":"Мессеж"};
const AU_SIZE=15;let auPage=1;
function auDetail(r){
  const d=r.detail||{};
  if(r.action==="status")return `${STATUS_MN[d.from]||d.from} → ${STATUS_MN[d.to]||d.to}`;
  if(r.action==="login"||r.action==="login_denied")return d.module?(MOD_NAME[d.module]||d.module)+" модуль":"";
  if(d.fields)return d.fields.join(", ");
  if(d.total_distance_km!=null)return `${fmt(d.total_distance_km)} км`;
  if(d.reason)return d.reason;
  if(d.to)return `→ ${d.to}${d.count>1?` (${d.count})`:""}`;
  return "";
}
const STATUS_MN={draft:"Ноорог",confirmed:"Баталсан",picking:"Бэлтгэж буй",shipped:"Илгээсэн",delivered:"Хүргэгдсэн",cancelled:"Цуцлагдсан"};
const auLoad=run(async page=>{
  auPage=page;
  const r=await api("/auth/audit",{query:{user_id:$("aufu").value,entity:$("aufe").value,page,size:AU_SIZE}});
  $("aub").innerHTML=r.items.map(a=>`<tr><td>${localTime(a.created_at)}</td><td>${esc(a.user_name||"Систем")}</td>
    <td>${a.action==="login_denied"?'<span class="er">':""}${esc(AU_ACTION[a.action]||a.action)}${a.action==="login_denied"?"</span>":""}</td>
    <td>${esc(AU_ENTITY[a.entity]||a.entity)}${a.entity_id?` <span class="mu">#${esc(a.entity_id)}</span>`:""}</td>
    <td><span class="wrap mu">${esc(auDetail(a))}</span></td></tr>`).join("")||emptyRow(5,"Түүх алга");
  const pages=Math.max(1,Math.ceil(r.total/AU_SIZE));
  $("aup").innerHTML=`<span>${page} / ${pages} хуудас · нийт ${r.total}</span><span class="head-actions"><button class="btn small" ${page>1?"":"disabled"} onclick="auLoad(${page-1})">← Өмнөх</button><button class="btn small" ${page<pages?"":"disabled"} onclick="auLoad(${page+1})">Дараах →</button></span>`;
});

// ---------------- Бүртгэлийн хүсэлт (/register-ээр өөрөө бүртгүүлсэн, батлагдаагүй)
function usPendingDraw(){
  $("usp").hidden=!usPending.length;
  const opts=sel=>usRoles.filter(r=>r.role!=="admin").map(r=>`<option value="${r.role}" ${r.role===sel?"selected":""}>${ROLE[r.role]||r.role}</option>`).join("");
  $("uspb").innerHTML=usPending.map((u,i)=>`<tr><td>${esc(u.full_name||u.username)}<span class="sub">${esc(u.username)}</span></td>
    <td>${localTime(u.created_at)}</td><td>${esc(ROLE[u.role]||u.role)}</td>
    <td><select id="usp-r${i}" aria-label="Олгох үүрэг" style="width:auto;min-width:170px">${opts(u.role)}</select></td>
    <td class="act"><button class="btn small primary" onclick="usApprove(${i})">Батлах</button><button class="btn small danger" onclick="usReject(${i})">Татгалзах</button></td></tr>`).join("");
}
const usApprove=run(async i=>{
  const u=usPending[i],role=$(`usp-r${i}`).value;
  await api(`/auth/users/${u.id}/approve`,{method:"POST",body:{role}});
  notice(`${u.full_name||u.username} батлагдлаа (${ROLE[role]||role}). Одоо нэвтэрч болно.`);rUs();bell();
});
const usReject=run(async i=>{
  const u=usPending[i];
  if(!confirm(`${u.full_name||u.username} (${u.username})-ийн бүртгэлийн хүсэлтийг татгалзах уу? Бүртгэл устна.`))return;
  await api(`/auth/users/${u.id}/reject`,{method:"POST"});
  notice(`${u.username}-ийн хүсэлт татгалзагдлаа`);rUs();
});
