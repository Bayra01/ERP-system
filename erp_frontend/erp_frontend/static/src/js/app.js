// Logistics ERP — Агуулах, Тээвэр (+ route.js, finance.js, notify.js). FastAPI backend: /api/...
// Token-ийг захиалгын React апптай ижил "erp-token" түлхүүрээр хадгална (нэг origin дээр нэг нэвтрэлт).
const KEY="erp-token";
let token=null;try{token=localStorage.getItem(KEY)}catch{}
let me=null,warehouses=[],products=[],locations=[],vehicles=[],drivers=[],shipments=[],orderNo={};
const $=id=>document.getElementById(id);
const fmt=n=>Number(n||0).toLocaleString("mn-MN",{maximumFractionDigits:2});
const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const day=iso=>iso?String(iso).slice(0,10):"—";
// Огноо-цагийг хэрэглэгчийн орон нутгийн цагаар. Timezone-гүй утга (SQLite) = UTC.
const localTime=iso=>{if(!iso)return "—";const d=new Date(/[zZ]|[+-]\d\d:?\d\d$/.test(iso)?iso:iso+"Z");
  const p=n=>String(n).padStart(2,"0");return `${d.getFullYear()}-${p(d.getMonth()+1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`};
const today=()=>new Date().toISOString().slice(0,10);
const can=p=>!!me&&(me.permissions.includes("*")||me.permissions.includes(p));
const kpis=(el,list)=>{$(el).innerHTML=list.map(([l,v,c])=>`<div class="kpi"><span>${l}</span><b class="${c||""}">${v}</b></div>`).join("")};
const emptyRow=(cols,text)=>`<tr><td class="empty" colspan="${cols}">${text}</td></tr>`;
const chips=(el,opts,cur,fn)=>{$(el).innerHTML=opts.map(([v,l])=>`<button class="chip ${v===cur?"on":""}" onclick="${fn}('${v}')">${l}</button>`).join("")};
let timer;const debounce=fn=>{clearTimeout(timer);timer=setTimeout(fn,250)};

// Таб бүр: харах эрх + зурах функц. route.js, finance.js, notify.js өөрсдийгөө энд бүртгэнэ.
const TABS={wh:{perm:"warehouse:read",render:()=>rWh()},tr:{perm:"transport:read",render:()=>rTr()}};
const WRITE_ONLY={".w-only":"warehouse:write",".tw-only":"transport:write",".r-only":"routing:write",".f-only":"finance:write"};
const ROLE={admin:"Админ",dispatcher:"Диспетчер",driver:"Жолооч",warehouse:"Агуулахын ажилтан",accountant:"Нягтлан",user:"Хэрэглэгч"};

// ---------------- API
function setToken(t){token=t;try{t?localStorage.setItem(KEY,t):localStorage.removeItem(KEY)}catch{}}
async function api(path,{method="GET",body,query}={}){
  const qs=query?"?"+new URLSearchParams(Object.entries(query).filter(([,v])=>v!==""&&v!=null)):"";
  const headers={};if(body!==undefined)headers["Content-Type"]="application/json";if(token)headers.Authorization="Bearer "+token;
  let res;
  try{res=await fetch("/api"+path+qs,{method,headers,body:body===undefined?undefined:JSON.stringify(body)})}
  catch{throw new Error("Серверт холбогдож чадсангүй")}
  if(res.status===204)return null;
  let data=null;try{data=await res.json()}catch{}
  if(!res.ok){
    if(res.status===401&&token){setToken(null);showLogin()}
    const d=data?.detail;
    throw new Error(data?.error?.message||(Array.isArray(d)?d.map(x=>`${(x.loc||[]).slice(1).join(".")}: ${x.msg}`).join("; "):d)||`Алдаа ${res.status}`);
  }
  return data;
}
const items=async(path,query={})=>(await api(path,{query:{size:200,...query}})).items;
function fail(e){const el=$("err");el.className="alert";el.textContent=e.message||String(e);clearTimeout(fail.t);fail.t=setTimeout(()=>el.classList.add("hidden"),6000)}
// Modal нээлттэй бол алдааг тэнд нь харуулна.
const run=fn=>async(...a)=>{try{await fn(...a)}catch(e){modalOpen?modalError(e):fail(e)}};

// ---------------- Modal
let modalOpen=null;
function openModal(id){
  closeModal();modalOpen=$(id);modalOpen.hidden=false;
  modalOpen.querySelector(".alert")?.remove();
  setTimeout(()=>modalOpen?.querySelector("input:not([type=hidden]),select,textarea")?.focus(),0);
}
function closeModal(){if(!modalOpen)return;modalOpen.hidden=true;modalOpen.querySelector("form")?.reset();modalOpen=null}
function modalError(e){
  let el=modalOpen.querySelector(".alert");
  if(!el){el=document.createElement("p");el.className="alert";el.setAttribute("role","alert");modalOpen.querySelector(".actions").before(el)}
  el.textContent=e.message||String(e);
}
document.addEventListener("keydown",e=>{if(e.key==="Escape")closeModal()});
document.addEventListener("mousedown",e=>{if(e.target.classList?.contains("scrim"))closeModal()});

// ---------------- Нэвтрэх, навигаци
// Нэвтрэлт модуль бүрийн /login/<модуль> хуудсаар явна (login.js).
const HASH_MODULE={wh:"warehouse",tr:"transport",rt:"routing",fn:"finance",nt:"notifications"};
const loginUrl=next=>`/login/${HASH_MODULE[location.hash.slice(1)]||""}`+(next?`?next=${encodeURIComponent(location.pathname+location.hash)}`:"");
function showLogin(){location.replace(loginUrl(true))}
// Нэг браузерт token хуваалцдаг: өөр таб дээр нэвтрэх/гарах үед энэ табыг шинэчилнэ
// (хуучин хэрэглэгчийн цэс, товч үлдэхээс сэргийлнэ).
window.addEventListener("storage",e=>{
  if(e.key!==KEY||e.newValue===token)return;
  if(!e.newValue){token=null;location.replace(loginUrl(true))}else location.reload();
});
function logout(){clearInterval(boot.poll);setToken(null);me=null;location.replace(loginUrl(false))}
function openMyPass(){openModal("m-mypass")}
const doMyPass=run(async e=>{e.preventDefault();
  if($("my-n").value!==$("my-c").value)throw new Error("Шинэ нууц үг таарахгүй байна");
  await api("/auth/me/password",{method:"POST",body:{old_password:$("my-o").value,new_password:$("my-n").value}});
  closeModal();notice("Нууц үг солигдлоо");
});
function notice(text){const el=$("err");el.textContent=text;el.className="notice";clearTimeout(fail.t);fail.t=setTimeout(()=>{el.className="alert hidden"},4000)}

async function boot(){
  if(!token)return showLogin();
  try{me=await api("/auth/me")}catch{return showLogin()}
  $("app").classList.remove("hidden");
  $("un").textContent=me.full_name||me.username;$("ur").textContent=ROLE[me.role]||me.role;
  // Таб харагдах эсэх: visible() (тусгай нөхцөл) эсвэл perm (null = бүгд).
  for(const k in TABS)$("t-"+k).hidden=!(TABS[k].visible?TABS[k].visible():TABS[k].perm===null||can(TABS[k].perm));
  $("t-or").hidden=!can("orders:read");
  for(const [sel,p] of Object.entries(WRITE_ONLY))document.querySelectorAll(sel).forEach(el=>el.hidden=!can(p));
  try{
    if(can("masterdata:read"))await loadRefs();  // «Хэрэглэгч» үүрэгт мастер өгөгдөл хэрэггүй
    if(can("orders:read"))(await items("/orders")).forEach(o=>orderNo[o.id]=o.order_no);
  }catch(e){fail(e)}
  bell();clearInterval(boot.poll);boot.poll=setInterval(bell,30000);
  const want=location.hash.slice(1);
  // Анхдагч: Хянах самбар (ажилтан) → Миний захиалга (хэрэглэгч) → Миний мэдээлэл
  show(TABS[want]&&!$("t-"+want).hidden?want:["db","po","me"].find(k=>TABS[k]&&!$("t-"+k).hidden)||"me",true);
}
// Байршил, бараа (сонголтуудад). Мастер өгөгдөл өөрчлөгдөхөд дахин дуудна.
async function loadRefs(){
  [locations,products]=await Promise.all([items("/masterdata/locations",{is_active:true}),items("/masterdata/products",{is_active:true})]);
  warehouses=locations.filter(l=>l.type==="warehouse");
  const opts=warehouses.map(w=>`<option value="${w.id}">${esc(w.name)}</option>`).join("");
  const keep=$("wf").value;
  $("wf").innerHTML=`<option value="">Бүх агуулах</option>`+opts;$("wf").value=keep;$("nw").innerHTML=opts;
  $("tf").innerHTML=`<option value="">— сонгоогүй —</option>`+opts;
  $("skus").innerHTML=products.map(p=>`<option value="${esc(p.sku)}">${esc(p.name)}</option>`).join("");
}
const bell=run(async()=>{const n=(await api("/notifications/unread-count")).count;$("bn").textContent=n>99?"99+":n;$("bn").hidden=!n});

function show(k,force){
  // force=false: hash солиход hashchange дахин дуудна. force=true: event үүсгэхгүйгээр шууд зурна.
  if(k&&location.hash.slice(1)!==k){if(!force){location.hash=k;return}history.replaceState(null,"","#"+k)}
  for(const x in TABS){$(x).classList.toggle("hidden",x!==k);$("t-"+x).classList.toggle("active",x===k)}
  closeModal();window.scrollTo(0,0);
  if(k)TABS[k].render();else fail(new Error("Харах эрхтэй модуль алга. Захиалга руу орно уу."));
}
// Эрхгүй (эсвэл байхгүй) таб руу хаягаар орох оролдлого: одоогийн таб дээр үлдэж, хаягийг нь засна.
window.addEventListener("hashchange",()=>{
  if(!me)return;
  const k=location.hash.slice(1);
  if(TABS[k]&&!$("t-"+k).hidden)return show(k,true);
  const cur=Object.keys(TABS).find(x=>!$(x).classList.contains("hidden"));
  if(cur)history.replaceState(null,"","#"+cur);
});

// ---------------- Агуулах
const stT={ok:["Хэвийн","ok"],low:["Бага үлдэгдэл","wn"],out:["Дууссан","er"]};
const mvT={in:"Орлого",out:"Зарлага",adjust:"Тооллого",transfer_in:"Шилжүүлэг (+)",transfer_out:"Шилжүүлэг (−)"};
const tag=(m,s)=>{const[t,c]=m[s]||[s,"mu"];return `<span class="pill ${c}">${esc(t)}</span>`};
let whStatus="",whRows=[],whCur=null;
function whSet(s){whStatus=s;rWh()}

const rWh=run(async()=>{
  const w=$("wf").value;
  chips("sfc",[["","Бүгд"],["ok","Хэвийн"],["low","Бага үлдэгдэл"],["out","Дууссан"]],whStatus,"whSet");
  const [stock,sum,moves,short]=await Promise.all([
    items("/warehouse/stock",{q:$("q").value.trim(),location_id:w,status:whStatus}),
    api("/warehouse/summary",{query:{location_id:w}}),
    items("/warehouse/movements",{location_id:w,size:10}),
    api("/warehouse/reservations",{query:{status:"short"}})]);
  whShort(short);
  whRows=stock;
  const write=can("warehouse:write");
  kpis("whk",[["Нийт нэр төрөл",sum.products],["Нийт үлдэгдэл",fmt(sum.total_on_hand)],["Нөөцлөсөн",fmt(sum.total_reserved)],
    ["Бага үлдэгдэлтэй",sum.low,sum.low?"warn":""],["Дууссан",sum.out,sum.out?"neg":""]]);
  $("wb").innerHTML=stock.map((i,n)=>{const c=stT[i.status][1];const max=Math.max(i.min_level*2,i.on_hand,1);
    return `<tr><td>${esc(i.sku)}</td><td>${esc(i.product_name)}</td><td>${esc(i.location_name)}</td>
    <td class="num">${fmt(i.on_hand)} <span class="mu">${esc(i.unit)}</span></td><td class="num">${fmt(i.reserved)}</td><td class="num">${fmt(i.available)}</td>
    <td><div class="lvl ${c}" title="Доод түвшин: ${fmt(i.min_level)}"><i style="width:${Math.min(100,i.on_hand/max*100)}%"></i></div></td>
    <td>${tag(stT,i.status)}</td>
    <td class="act">${write?`<button class="btn small" onclick="openOut(${n})" ${i.available>0?"":"disabled"}>Зарлага</button><button class="btn small" onclick="openMin(${n})">Доод түвшин</button>`:""}</td></tr>`}).join("")
    ||emptyRow(9,"Илэрц алга");
  $("mv").innerHTML=moves.map(m=>`<tr><td>${day(m.created_at)}</td><td>${mvT[m.type]||esc(m.type)}${m.ref_type==="order"?` <span class="mu">· ${esc(orderNo[m.ref_id]||"захиалга #"+m.ref_id)}</span>`:""}</td><td>${esc(m.product_name)}</td><td>${esc(m.location_name)}</td>
    <td class="num ${m.quantity<0?"er":"ok"}">${m.quantity>0?"+":""}${fmt(m.quantity)}</td><td class="num">${fmt(m.balance_after)}</td></tr>`).join("")||emptyRow(6,"Хөдөлгөөн алга");
});
function fillName(){const p=products.find(x=>x.sku===$("nc").value.trim());if(p)$("nn").value=p.name}
const addItem=run(async e=>{e.preventDefault();
  const sku=$("nc").value.trim();let p=products.find(x=>x.sku===sku);
  if(!p){
    const name=$("nn").value.trim();if(!name)throw new Error("Шинэ барааны нэрийг оруулна уу");
    p=await api("/masterdata/products",{method:"POST",body:{sku,name}});products.push(p);
    $("skus").insertAdjacentHTML("beforeend",`<option value="${esc(p.sku)}">${esc(p.name)}</option>`);
  }
  await api("/warehouse/movements",{method:"POST",body:{location_id:+$("nw").value,product_id:p.id,type:"in",quantity:$("nq").value}});
  closeModal();rWh();
});
function openOut(n){whCur=whRows[n];openModal("m-out");$("mo-info").textContent=`${whCur.product_name} · ${whCur.location_name} — боломжит ${fmt(whCur.available)} ${whCur.unit}`;$("mo-q").max=whCur.available}
function openMin(n){whCur=whRows[n];openModal("m-min");$("mm-q").value=whCur.min_level}
const doOut=run(async e=>{e.preventDefault();
  await api("/warehouse/movements",{method:"POST",body:{location_id:whCur.location_id,product_id:whCur.product_id,type:"out",quantity:$("mo-q").value,note:$("mo-n").value.trim()||null}});
  closeModal();rWh();
});
const doMin=run(async e=>{e.preventDefault();await api(`/warehouse/stock/${whCur.id}`,{method:"PATCH",body:{min_level:$("mm-q").value}});closeModal();rWh()});

// Нөөц дутуу (short) захиалгууд: бараа бүрийн нийт боломжит үлдэгдэлтэй харьцуулж харуулна.
async function whShort(rows){
  $("shp").hidden=!rows.length;if(!rows.length)return;
  const avail={};
  for(const pid of new Set(rows.map(r=>r.product_id)))
    avail[pid]=(await items("/warehouse/stock",{product_id:pid})).reduce((a,s)=>a+s.available,0);
  const write=can("warehouse:write"),pname=id=>products.find(p=>p.id===id)?.name||`#${id}`;
  // Товчийг захиалга бүрийн эхний мөрөнд нэг удаа.
  const first=(r,i)=>rows.findIndex(x=>x.order_id===r.order_id)===i;
  $("shb").innerHTML=rows.map((r,i)=>`<tr><td>${esc(ordName(r.order_id))}</td><td>${esc(pname(r.product_id))}</td><td class="num">${fmt(r.quantity)}</td>
    <td class="num ${avail[r.product_id]>=r.quantity?"ok":"er"}">${fmt(avail[r.product_id])}</td>
    <td class="act">${write&&first(r,i)?`<button class="btn small" onclick="whRetry(${r.order_id})">Дахин нөөцлөх</button>`:""}</td></tr>`).join("");
}
const whRetry=run(async oid=>{
  const res=await api(`/warehouse/orders/${oid}/reserve`,{method:"POST"});
  const left=res.filter(r=>r.status==="short").length;
  notice(left?`${ordName(oid)}: ${left} бараа дутуу хэвээр байна`:`${ordName(oid)}: бүх бараа нөөцлөгдлөө`);rWh();
});

// Агуулах хооронд шилжүүлэх
function openTransfer(){
  const opts=warehouses.map(w=>`<option value="${w.id}">${esc(w.name)}</option>`).join("");
  $("mt-p").innerHTML=`<option value="">Сонгох…</option>`+products.map(p=>`<option value="${p.id}">${esc(p.name)} (${esc(p.sku)})</option>`).join("");
  openModal("m-transfer");$("mt-f").innerHTML=opts;$("mt-t").innerHTML=opts;
  if(warehouses[1])$("mt-t").value=warehouses[1].id;
  $("mt-info").textContent="Илгээх агуулахын боломжит үлдэгдлээс хасаж, хүлээн авах агуулахад нэмнэ.";
}
const transferInfo=run(async()=>{
  const pid=+$("mt-p").value,from=+$("mt-f").value;if(!pid||!from)return;
  const s=(await items("/warehouse/stock",{product_id:pid,location_id:from}))[0];
  $("mt-info").textContent=`Боломжит үлдэгдэл: ${fmt(s?.available||0)} ${s?.unit||""}`;$("mt-q").max=s?.available||0;
});
const doTransfer=run(async e=>{e.preventDefault();
  if($("mt-f").value===$("mt-t").value)throw new Error("Илгээх, хүлээн авах агуулах ижил байна");
  await api("/warehouse/transfers",{method:"POST",body:{from_location_id:+$("mt-f").value,to_location_id:+$("mt-t").value,
    product_id:+$("mt-p").value,quantity:$("mt-q").value,note:$("mt-n").value.trim()||null}});
  closeModal();notice("Шилжүүлэг хийгдлээ");rWh();
});

// ---------------- Тээвэр
const trT={planned:["Төлөвлөсөн","in"],in_progress:["Замд","wn"],completed:["Дууссан","ok"],cancelled:["Цуцлагдсан","mu"]};
const vT={available:["Чөлөөтэй","ok"],on_trip:["Замд","wn"],maintenance:["Засварт","er"]};
const vType={truck:"Ачааны машин",van:"Фургон",car:"Суудлын"};
const shT={pending:["Хүлээгдэж буй","in"],assigned:["Оноогдсон","ac"],in_transit:["Замд","wn"],delivered:["Хүргэгдсэн","ok"],failed:["Амжилтгүй","er"],cancelled:["Цуцлагдсан","mu"]};
const locName=id=>locations.find(l=>l.id===id)?.name||"—";
const ordName=id=>orderNo[id]||`#${id}`;
let trStatus="";
function trSet(s){trStatus=s;rTr()}

const rTr=run(async()=>{
  const write=can("transport:write"),driver=me.role==="driver";
  chips("tsc",[["","Бүгд"],["planned","Төлөвлөсөн"],["in_progress","Замд"],["completed","Дууссан"],["cancelled","Цуцлагдсан"]],trStatus,"trSet");
  const [all,vs,ds,ships,orders]=await Promise.all([
    driver?items("/transport/my/trips"):items("/transport/trips"),items("/transport/vehicles"),items("/transport/drivers"),
    driver?Promise.resolve([]):items("/transport/shipments",{status:"pending,assigned,failed"}),
    can("orders:read")?items("/orders"):Promise.resolve([])]);
  vehicles=vs;drivers=ds;shipments=ships;orders.forEach(o=>orderNo[o.id]=o.order_no);
  const cnt=s=>all.filter(t=>t.status===s).length;
  kpis("trk",[["Нийт аялал",all.length],["Замд яваа",cnt("in_progress")],["Төлөвлөсөн",cnt("planned")],["Дууссан",cnt("completed")],
    ...(driver?[]:[["Хүргэлт хүлээж буй",ships.filter(s=>s.status!=="assigned").length]])]);
  const trips=trStatus?all.filter(t=>t.status===trStatus):all;
  $("tb").innerHTML=trips.map(t=>{
    let act="";
    if(t.status==="planned"&&write)act+=`<button class="btn small" onclick="tripAct(${t.id},'start')">Гаргах</button><button class="btn small danger" onclick="tripAct(${t.id},'cancel')">Цуцлах</button>`;
    if(t.status==="in_progress"&&(write||driver))act+=`<button class="btn small" onclick="deliverAll(${t.id})">Хүргэсэн</button>`;
    const no=esc(t.trip_no||t.id),link=t.stops&&can("routing:read");
    return `<tr><td>${link?`<a href="#rt" onclick="openRoute(${t.id});return false" title="Маршрут харах">${no}</a>`:no}<span class="sub">${day(t.planned_date)}</span></td><td>${esc(t.depot_name||"—")} → ${t.stops} зогсоол${t.stops?` <span class="mu">(${t.delivered}/${t.stops})</span>`:""}</td>
    <td>${esc(t.vehicle_plate)}<span class="sub">${esc(t.driver_name)}</span></td><td class="num">${fmt(t.weight_kg)} кг</td>
    <td class="num">${t.total_distance_km!=null?fmt(t.total_distance_km)+" км":"—"}</td><td>${tag(trT,t.status)}</td><td class="act">${act}</td></tr>`}).join("")
    ||emptyRow(7,"Аялал алга");
  $("sbp").hidden=driver;
  $("sb").innerHTML=ships.map(s=>`<tr><td>${esc(ordName(s.order_id))}</td><td>${esc(locName(s.location_id))}</td><td class="num">${fmt(s.weight_kg)} кг</td>
    <td>${s.ready?'<span class="ok">Тийм</span>':'<span class="wn">Үгүй</span>'}</td><td>${tag(shT,s.status)}${s.failed_reason?` <span class="mu small">${esc(s.failed_reason)}</span>`:""}</td></tr>`).join("")
    ||emptyRow(5,"Хүлээгдэж буй хүргэлт алга");
  $("vb").innerHTML=vs.map(v=>`<tr><td>${esc(v.plate_no)}</td><td>${esc(vType[v.type]||v.type)}</td><td class="num">${v.capacity_kg?fmt(v.capacity_kg)+" кг":"—"}</td><td>${tag(vT,v.status)}</td></tr>`).join("")||emptyRow(4,"Машин бүртгээгүй");
  $("db").innerHTML=ds.map(d=>`<tr><td>${esc(d.full_name)}</td><td>${esc(d.phone||"—")}</td><td>${d.user_id?'<span class="pill ok">Холбогдсон</span>':'<span class="mu">—</span>'}</td></tr>`).join("")||emptyRow(3,"Жолооч бүртгээгүй");
});

function openTrip(){
  $("tv").innerHTML=`<option value="">Сонгох…</option>`+vehicles.filter(v=>v.is_active&&v.status!=="maintenance").map(v=>`<option value="${v.id}">${esc(v.plate_no)}${v.capacity_kg?` · ${fmt(v.capacity_kg)} кг`:""}</option>`).join("");
  $("tdr").innerHTML=`<option value="">Сонгох…</option>`+drivers.filter(d=>d.is_active).map(d=>`<option value="${d.id}">${esc(d.full_name)}</option>`).join("");
  const free=shipments.filter(s=>s.status!=="assigned");
  $("tsl").innerHTML=free.map(s=>`<label><input type="checkbox" value="${s.id}" data-kg="${s.weight_kg}"><span>${esc(ordName(s.order_id))} → ${esc(locName(s.location_id))} <span class="mu">· ${fmt(s.weight_kg)} кг${s.ready?"":" · илгээгдээгүй"}</span></span></label>`).join("")
    ||`<div class="empty">Оноох хүргэлт алга. Захиалгыг «Бэлтгэж эхлэх» болгоход үүснэ.</div>`;
  openModal("m-trip");$("td").value=today();tripLoad();
}
// Сонгосон ачааг машины даацтай харьцуулж харуулна.
function tripLoad(){
  const sel=[...$("tsl").querySelectorAll("input:checked")],kg=sel.reduce((a,x)=>a+ +x.dataset.kg,0);
  const cap=vehicles.find(v=>v.id===+$("tv").value)?.capacity_kg||0;
  $("tsw").innerHTML=sel.length?`· ${sel.length} сонгосон, ${fmt(kg)} кг${cap?` / ${fmt(cap)} кг`:""}${cap&&kg>cap?' <b class="er">даац хэтэрсэн</b>':""}`:"";
}
document.addEventListener("change",e=>{if(e.target.closest?.("#m-trip"))tripLoad()});
const addTrip=run(async e=>{e.preventDefault();
  const ids=[...$("tsl").querySelectorAll("input:checked")].map(x=>+x.value);
  await api("/transport/trips",{method:"POST",body:{vehicle_id:+$("tv").value,driver_id:+$("tdr").value,
    depot_location_id:$("tf").value?+$("tf").value:null,planned_date:$("td").value,notes:$("tn").value.trim()||null,shipment_ids:ids}});
  closeModal();rTr();
});
const addVehicle=run(async e=>{e.preventDefault();
  await api("/transport/vehicles",{method:"POST",body:{plate_no:$("vp").value.trim(),type:$("vt").value,capacity_kg:+$("vc").value||0}});closeModal();rTr();
});
const addDriver=run(async e=>{e.preventDefault();
  await api("/transport/drivers",{method:"POST",body:{full_name:$("dn").value.trim(),phone:$("dp").value.trim()||null,license_no:$("dl").value.trim()||null}});closeModal();rTr();
});
const tripAct=run(async(id,a)=>{
  if(a==="cancel"&&!confirm("Аяллыг цуцлах уу? Хүргэлтүүд чөлөөлөгдөнө."))return;
  await api(`/transport/trips/${id}/${a}`,{method:"POST"});rTr();bell();
});
const deliverAll=run(async id=>{
  const t=await api(`/transport/trips/${id}`);const left=t.shipments.filter(s=>s.status==="in_transit");
  if(!left.length){await api(`/transport/trips/${id}/complete`,{method:"POST"})}
  else{if(!confirm(`${left.length} хүргэлтийг хүргэгдсэн болгох уу?`))return;
    for(const s of left)await api(`/transport/shipments/${s.id}/deliver`,{method:"POST"})}
  rTr();bell();
});

// boot()-г index.html бүх скриптийг ачаалсны дараа дуудна.
