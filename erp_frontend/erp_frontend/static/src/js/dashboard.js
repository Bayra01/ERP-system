// Хянах самбар — хэрэглэгчийн эрхэд тохирсон тойм: KPI, анхаарах зүйлс, түргэн үйлдэл, сүүлийн захиалгууд.
// Шинэ endpoint шаардахгүй: модуль бүрийн байгаа API-г зэрэг дуудна.
// «Хэрэглэгч» үүрэгт (зөвхөн мэдэгдэл) хянах самбар хэрэггүй — «Миний мэдээлэл» нээгдэнэ.
TABS.db={perm:null,visible:()=>me.modules.some(m=>m!=="notifications"),render:()=>rDb()};
const ORD_ST={draft:["Ноорог","mu"],confirmed:["Баталсан","in"],picking:["Бэлтгэж буй","wn"],shipped:["Илгээсэн","ac"],delivered:["Хүргэгдсэн","ok"],cancelled:["Цуцлагдсан","er"]};
const WEEKDAY=["Ням","Даваа","Мягмар","Лхагва","Пүрэв","Баасан","Бямба"];
const money=n=>Number(n||0).toLocaleString("mn-MN",{maximumFractionDigits:0})+" ₮";
const none=Promise.resolve(null);

const rDb=run(async()=>{
  const now=new Date(),h=now.getHours();
  $("dbh").textContent=`${h<12?"Өглөөний мэнд":h<18?"Өдрийн мэнд":"Оройн мэнд"}, ${me.full_name||me.username}`;
  $("dbs").textContent=`${now.getFullYear()} оны ${now.getMonth()+1}-р сарын ${now.getDate()}, ${WEEKDAY[now.getDay()]} гараг · ${ROLE[me.role]||me.role}`;
  const driver=me.role==="driver",T=today();
  const [orders,custs,wsum,short,trips,ships,fin,unread,pending]=await Promise.all([
    can("orders:read")?items("/orders"):none,
    can("orders:read")?items("/masterdata/customers"):none,
    can("warehouse:read")?api("/warehouse/summary"):none,
    can("warehouse:read")?api("/warehouse/reservations",{query:{status:"short"}}):none,
    can("transport:read")?(driver?items("/transport/my/trips"):items("/transport/trips",{status:"planned,in_progress"})):none,
    can("transport:write")?items("/transport/shipments",{status:"pending,failed"}):none,
    can("finance:read")?api("/finance/reports/summary"):none,
    api("/notifications/unread-count"),
    can("auth:users")?api("/auth/users").then(us=>us.filter(u=>u.pending)):none]);
  if(orders)orders.forEach(o=>orderNo[o.id]=o.order_no);
  const cnt=(list,f)=>list?list.filter(f).length:0;
  const active=cnt(orders,o=>["confirmed","picking","shipped"].includes(o.status));

  // ---- KPI
  const k=[];
  if(orders)k.push(["Идэвхтэй захиалга",active]);
  if(wsum)k.push(["Бага / дууссан үлдэгдэл",`${wsum.low} / ${wsum.out}`,wsum.out?"neg":wsum.low?"warn":""]);
  if(trips)k.push([driver?"Миний идэвхтэй аялал":"Замд яваа аялал",cnt(trips,t=>t.status==="in_progress")]);
  if(fin)k.push(["Хугацаа хэтэрсэн авлага",money(fin.totals.overdue),fin.totals.overdue>0?"warn":""]);
  k.push(["Уншаагүй мэдэгдэл",unread.count]);
  kpis("dbk",k);

  // ---- Анхаарах зүйлс: [өнгө, текст, холбоос/үйлдэл]
  const todo=[];
  const add=(tone,text,href,cta)=>todo.push({tone,text,href,cta});
  if(orders){
    const draft=cnt(orders,o=>o.status==="draft"),conf=cnt(orders,o=>o.status==="confirmed"),pick=cnt(orders,o=>o.status==="picking");
    if(draft&&can("orders:write"))add("in",`<b>${draft}</b> ноорог захиалга батлахыг хүлээж байна`,"/orders/","Захиалга");
    if(conf&&can("orders:fulfil"))add("wn",`<b>${conf}</b> батлагдсан захиалгыг бэлтгэж эхлэх`,"/orders/","Захиалга");
    if(pick&&can("orders:fulfil"))add("wn",`<b>${pick}</b> захиалга бэлтгэгдэж байна — илгээх`,"/orders/","Захиалга");
  }
  if(wsum&&(wsum.low||wsum.out))add(wsum.out?"er":"wn",`<b>${wsum.out}</b> бараа дууссан, <b>${wsum.low}</b> бараа доод түвшнээс бага`,"#wh","Агуулах");
  if(short&&short.length)add("er",`<b>${new Set(short.map(r=>r.order_id)).size}</b> захиалгад нөөц хүрэлцэхгүй байна`,"#wh","Агуулах");
  if(ships){
    const ready=cnt(ships,s=>s.ready&&s.status==="pending"),failed=cnt(ships,s=>s.status==="failed");
    if(ready)add("wn",`<b>${ready}</b> илгээгдсэн захиалга аялалд оноогдоогүй`,"#tr","Тээвэр");
    if(failed)add("er",`<b>${failed}</b> хүргэлт амжилтгүй болсон — дахин оноох`,"#tr","Тээвэр");
  }
  if(trips){
    const due=trips.filter(t=>t.status==="planned"&&t.planned_date<=T);
    if(due.length)add(due.some(t=>t.planned_date<T)?"er":"wn",`<b>${due.length}</b> төлөвлөсөн аялал өнөөдөр эсвэл хоцорсон — гаргах`,driver?"#rt":"#tr",driver?"Маршрут":"Тээвэр");
    const mine=driver?trips.filter(t=>t.status==="in_progress"):[];
    if(mine.length)add("in",`Таны замд яваа аялал: <b>${mine.map(t=>esc(t.trip_no)).join(", ")}</b> — хүргэлтийг тэмдэглэх`,"#rt","Маршрут");
  }
  if(fin&&fin.totals.overdue>0){
    const n=fin.aging.filter(a=>a.bucket!=="current").reduce((a,b)=>a+b.count,0);
    add("er",`<b>${n}</b> нэхэмжлэхийн төлбөр хугацаа хэтэрсэн (${money(fin.totals.overdue)})`,"#fn","Санхүү");
  }
  if(pending&&pending.length)add("wn",`<b>${pending.length}</b> бүртгэлийн хүсэлт батлахыг хүлээж байна`,"#us","Ажилтнууд");
  if(unread.count)add("in",`<b>${unread.count}</b> уншаагүй мэдэгдэл`,"#nt","Мэдэгдэл");
  $("dbac").textContent=todo.length?`${todo.length} зүйл`:"";
  $("dbt").innerHTML=todo.map(t=>`<li><i class="tone ${t.tone}" aria-hidden="true"></i><span>${t.text}</span><a class="btn small" href="${t.href}">${t.cta} →</a></li>`).join("")
    ||`<li class="empty"><b class="ok">Бүх зүйл хэвийн байна.</b><br><span class="muted">Анхаарах зүйл алга.</span></li>`;

  // ---- Түргэн үйлдэл
  const q=[];
  // [холбоос эсвэл onclick-ийн код, нэр, дүрс]
  if(can("orders:write"))q.push(["/orders/#new","Шинэ захиалга","i-orders"]);
  if(can("warehouse:write"))q.push(["dbGo('wh',()=>openModal('m-receipt'))","Орлого авах","i-wh"]);
  if(can("transport:write"))q.push(["#tr","Аялал төлөвлөх","i-tr"]);
  if(can("routing:read"))q.push(["#rt",driver?"Миний маршрут":"Маршрут","i-rt"]);
  if(can("finance:write"))q.push(["dbGo('fn',()=>openModal('m-invoice'))","Нэхэмжлэх","i-fn"]);
  if(can("masterdata:write"))q.push(["#md","Харилцагч, бараа","i-md"]);
  q.push(["dbGo('nt',ntCompose)","Мессеж бичих","i-mail"]);
  const link=a=>/^[#/]/.test(a)?`href="${a}"`:`href="#" onclick="${a};return false"`;
  $("dbq").innerHTML=q.map(([a,l,ic])=>`<a class="qa" ${link(a)}><svg><use href="#${ic}"/></svg><span>${l}</span></a>`).join("");

  // ---- Сүүлийн захиалгууд
  $("dbop").hidden=!orders;
  if(orders){
    const cname=Object.fromEntries((custs||[]).map(c=>[c.id,c.name]));
    $("dbo").innerHTML=orders.slice(0,6).map(o=>`<tr><td><a href="/orders/#order/${o.id}">${esc(o.order_no||"#"+o.id)}</a></td><td>${esc(cname[o.customer_id]||"#"+o.customer_id)}</td>
      <td>${tag(ORD_ST,o.status)}</td><td class="num">${money(o.total_amount)}</td><td>${day(o.order_date)}</td></tr>`).join("")||emptyRow(5,"Захиалга алга");
  }
});
// Таб руу шилжээд (зурж дууссаны дараа) modal нээнэ.
async function dbGo(tab,then){show(tab,true);await new Promise(r=>setTimeout(r,50));then()}
