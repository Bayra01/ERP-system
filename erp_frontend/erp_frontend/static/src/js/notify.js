// Мэдэгдэл ба харилцаа — /api/notifications. Системийн мэдэгдлийн текстийг event + data-аас монголоор угсарна.
TABS.nt={perm:null,render:()=>rNt()};
let ntFilter="all",ntPage=1,ntRecipients=null,ntItems=[];
const NT_SIZE=20;
const NT_FILTERS={all:["Бүгд",{}],unread:["Уншаагүй",{unread:true}],message:["Мессеж",{kind:"message"}],system:["Системийн",{kind:"system"}],sent:["Илгээсэн",{box:"sent"}]};
const EV={
  "order.confirmed":["Захиалга батлагдлаа",d=>`${d.order_no} — бараа бэлтгэх`],
  "order.picking":["Захиалга бэлтгэгдэж байна",d=>d.order_no],
  "order.submitted":["Харилцагч захиалга өглөө",d=>`${d.order_no} — ${d.customer_name||""} · батлах`],
  "order.shipped":["Захиалга илгээгдлээ",d=>`${d.order_no} — хүргэлтэд бэлэн`],
  "order.delivered":["Захиалга хүргэгдлээ",d=>`${d.order_no} — нэхэмжлэх үүслээ`],
  "order.cancelled":["Захиалга цуцлагдлаа",d=>d.order_no],
  "stock.shortage":["Үлдэгдэл дутуу",d=>`${ordName(d.order_id)}: ${(d.shortages||[]).length} бараа хүрэлцэхгүй (${d.stage==="shipped"?"илгээх үед":"батлах үед"})`],
  "shipment.failed":["Хүргэлт амжилтгүй",d=>`${ordName(d.order_id)}: ${d.reason||""}`],
  "trip.started":["Аялал эхэллээ",d=>d.trip_no],
  "user.registered":["Шинэ бүртгэлийн хүсэлт",d=>`${d.full_name||d.username} (${d.username}) — ${ROLE[d.role]||d.role}. Ажилтнууд хэсгээс батална уу.`],
  "trip.completed":["Аялал дууслаа",d=>`${d.trip_no} — ${(d.delivered||[]).length} хүргэгдсэн${(d.failed||[]).length?`, ${d.failed.length} амжилтгүй`:""}`],
};
// «Хэрэглэгч» (харилцагч)-д өөрийн захиалгын явцыг ойлгомжтой хэлээр.
const EV_CUSTOMER={
  "order.confirmed":["Захиалга баталгаажлаа",d=>`${d.order_no} — бэлтгэлд орно`],
  "order.picking":["Захиалга бэлтгэгдэж байна",d=>d.order_no],
  "order.shipped":["Захиалга илгээгдлээ",d=>`${d.order_no} — хүргэлтэд гарахад бэлэн`],
  "order.delivered":["Захиалга хүргэгдлээ",d=>`${d.order_no} — баярлалаа!`],
  "order.cancelled":["Захиалга цуцлагдлаа",d=>d.order_no],
  "trip.started":["Захиалга замд гарлаа",()=>"Хүргэлтийн машин хөдөллөө. «Миний захиалга» хэсгээс хаана явааг харна уу."],
};
const WARN_EV=new Set(["stock.shortage","shipment.failed","order.cancelled"]);
const ROLES={user:"Бүх хэрэглэгч",dispatcher:"Бүх диспетчер",warehouse:"Бүх агуулахын ажилтан",driver:"Бүх жолооч",accountant:"Бүх нягтлан",admin:"Бүх админ"};
// Timezone-гүй хугацаа (SQLite) = UTC.
const toDate=iso=>new Date(/[zZ]|[+-]\d\d:?\d\d$/.test(iso)?iso:iso+"Z");
const ago=iso=>{const s=(Date.now()-toDate(iso))/1000;return s<60?"дөнгөж сая":s<3600?`${Math.floor(s/60)} мин өмнө`:s<86400?`${Math.floor(s/3600)} цаг өмнө`:day(iso)};
const icon=id=>`<svg><use href="#${id}"/></svg>`;

const rNt=run(async()=>{
  chips("ntf",Object.entries(NT_FILTERS).map(([k,[l]])=>[k,l]),ntFilter,"ntSet");
  const r=await api("/notifications",{query:{...NT_FILTERS[ntFilter][1],page:ntPage,size:NT_SIZE}});
  const sent=ntFilter==="sent";ntItems=r.items;
  $("ntl").innerHTML=r.items.map(n=>{
    const ev=me.role==="user"&&EV_CUSTOMER[n.event]?EV_CUSTOMER:EV;
    const msg=n.event==="message",[title,body]=msg?[n.title,n.message]:[ev[n.event]?.[0]||n.title,ev[n.event]?ev[n.event][1](n.data||{}):n.message];
    const unread=!n.is_read&&!sent,meta=[];
    if(msg)meta.push(sent?`→ ${esc(n.recipient_name)}`:`${esc(n.sender_name||"")}-аас`);
    if(n.data?.order_id&&!msg)meta.push(me.role==="user"?`<a href="#" onclick="openMyOrder(${n.data.order_id});return false">Захиалга харах</a>`:`<a href="/orders/#order/${n.data.order_id}">Захиалга харах</a>`);
    if(me.role==="user"&&n.event==="trip.started")meta.push(`<a href="#po">Миний захиалга</a>`);
    if(n.data?.trip_id&&can("routing:read"))meta.push(`<a href="#" onclick="openRoute(${n.data.trip_id});return false">Маршрут харах</a>`);
    if(n.event==="user.registered"&&can("auth:users"))meta.push(`<a href="#us">Ажилтнууд → батлах</a>`);
    if(msg&&!sent&&n.sender_id)meta.push(`<a href="#" onclick="event.stopPropagation();ntReply(${n.id});return false">Хариулах</a>`);
    return `<li class="${unread?"unread":""}" ${unread?`onclick="ntRead(${n.id},this)"`:""}>
      <span class="nico ${msg?"msg":WARN_EV.has(n.event)?"warn":""}" aria-hidden="true">${icon(msg?"i-mail":WARN_EV.has(n.event)?"i-alert":"i-nt")}</span>
      <div><div class="nhead"><span class="ntitle">${unread?'<span class="dot-unread" aria-label="Уншаагүй"></span>':""}${esc(title)}</span><time datetime="${esc(n.created_at)}">${ago(n.created_at)}</time></div>
      <div class="nbody">${esc(body)}</div>
      ${meta.length?`<div class="nmeta">${meta.join("<span aria-hidden=\"true\">·</span>")}</div>`:""}</div></li>`}).join("")
    ||`<li class="empty">${sent?"Илгээсэн мессеж алга":"Мэдэгдэл алга"}</li>`;
  const pages=Math.max(1,Math.ceil(r.total/NT_SIZE));
  $("ntp").hidden=r.total<=NT_SIZE;
  $("ntp").innerHTML=`<span>${ntPage} / ${pages} хуудас · нийт ${r.total}</span><span class="head-actions"><button class="btn small" ${ntPage>1?"":"disabled"} onclick="ntGo(-1)">← Өмнөх</button><button class="btn small" ${ntPage<pages?"":"disabled"} onclick="ntGo(1)">Дараах →</button></span>`;
  bell();
});
function ntSet(k){ntFilter=k;ntPage=1;rNt()}
function ntGo(d){ntPage+=d;rNt()}
const ntRead=run(async(id,li)=>{await api(`/notifications/${id}/read`,{method:"POST"});li.classList.remove("unread");li.onclick=null;li.querySelector(".dot-unread")?.remove();bell()});
const ntReadAll=run(async()=>{await api("/notifications/read-all",{method:"POST"});rNt()});

async function ntLoadRecipients(){
  if(ntRecipients)return;
  ntRecipients=await api("/notifications/recipients");
  $("ntto").innerHTML=`<option value="">Сонгох…</option><optgroup label="Хэрэглэгч">`+
    ntRecipients.map(u=>`<option value="u${u.id}">${esc(u.full_name||u.username)} · ${ROLE[u.role]||u.role}</option>`).join("")+
    `</optgroup><optgroup label="Бүлэг">`+Object.entries(ROLES).filter(([r])=>ntRecipients.some(u=>u.role===r)).map(([r,l])=>`<option value="r${r}">${l}</option>`).join("")+`</optgroup>`;
}
const ntCompose=run(async()=>{
  await ntLoadRecipients();openModal("m-msg");
  $("ntct").textContent="Шинэ мессеж";$("ntto-l").hidden=false;$("ntto").required=true;$("ntre").value="";
});
function ntReply(id){
  const n=ntItems.find(x=>x.id===id);if(!n)return;
  openModal("m-msg");
  $("ntct").textContent=`Хариу: ${n.sender_name||""}`;$("ntto-l").hidden=true;$("ntto").required=false;
  $("ntre").value=id;$("ntti").value=n.title.startsWith("Re: ")?n.title:"Re: "+n.title;
  setTimeout(()=>$("ntmsg").focus(),0);
}
const ntSend=run(async e=>{e.preventDefault();
  const body={title:$("ntti").value.trim(),message:$("ntmsg").value.trim()},to=$("ntto").value,re=$("ntre").value;
  if(re)body.reply_to=+re;else if(to.startsWith("u"))body.to_user_id=+to.slice(1);else if(to.startsWith("r"))body.role=to.slice(1);
  else throw new Error("Хүлээн авагч сонгоно уу");
  const r=await api("/notifications/send",{method:"POST",body});
  closeModal();
  $("ntok").textContent=`Мессеж илгээгдлээ (${r.sent} хүлээн авагч)`;$("ntok").hidden=false;setTimeout(()=>$("ntok").hidden=true,4000);
  if(ntFilter==="sent")rNt();
});
