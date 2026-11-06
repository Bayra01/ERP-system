// Миний захиалга — «Хэрэглэгч» (харилцагч): захиалга өгөх, хаана явааг хянах. /api/portal/*
// Зөвхөн өөрийн захиалга (backend нь User.customer_id-аар шүүнэ).
TABS.po={perm:"portal:use",visible:()=>me.role==="user",render:()=>rPo()};
const PO_ST={draft:["Хүлээн авсан","in"],confirmed:["Баталсан","in"],picking:["Бэлтгэж буй","wn"],shipped:["Замд","ac"],delivered:["Хүргэгдсэн","ok"],cancelled:["Цуцлагдсан","er"]};
const PO_STEPS=[["draft","Захиалга өгсөн"],["confirmed","Баталсан"],["picking","Бэлтгэж буй"],["shipped","Замд"],["delivered","Хүргэгдсэн"]];
const PO_INV={paid:["Төлөгдсөн","ok"],partial:["Хэсэгчлэн төлсөн","in"],unpaid:["Төлөгдөөгүй","wn"],overdue:["Хугацаа хэтэрсэн","er"]};
const pmnt=n=>Number(n||0).toLocaleString("mn-MN",{maximumFractionDigits:0})+" ₮";
let poOrders=[],poSel=null,poProducts=[],poAddr=[],poLineSeq=0;

function openMyOrder(id){poSel=id;show("po")}
const rPo=run(async()=>{
  poOrders=await api("/portal/orders");
  const active=poOrders.filter(o=>["draft","confirmed","picking","shipped"].includes(o.status)).length;
  kpis("pok",[["Нийт захиалга",poOrders.length],["Идэвхтэй",active],["Замд яваа",poOrders.filter(o=>o.status==="shipped").length],
    ["Хүргэгдсэн",poOrders.filter(o=>o.status==="delivered").length]]);
  $("pob").innerHTML=poOrders.map(o=>`<tr class="link ${o.id===poSel?"hi":""}" tabindex="0" onclick="poOpen(${o.id})" onkeydown="event.key==='Enter'&&poOpen(${o.id})">
    <td><b>${esc(o.order_no)}</b><span class="sub">${day(o.order_date)}</span></td><td><span class="wrap">${esc(o.summary)}</span></td>
    <td class="num">${pmnt(o.total_amount)}</td><td>${tag(PO_ST,o.status)}</td></tr>`).join("")
    ||emptyRow(4,"Захиалга алга. «+ Захиалга өгөх» товчоор эхлээрэй.");
  if(!poOrders.some(o=>o.id===poSel))poSel=poOrders[0]?.id??null;
  if(poSel)await poDetail(poSel);else $("pod").innerHTML=`<p class="muted" style="margin:0">Захиалга сонгоход явц нь энд харагдана.</p>`;
});
const poOpen=run(async id=>{poSel=id;document.querySelectorAll("#pob tr").forEach((r,i)=>r.classList.toggle("hi",poOrders[i]?.id===id));await poDetail(id)});

async function poDetail(id){
  const o=await api(`/portal/orders/${id}`),t=o.trip,sh=o.shipment,inv=o.invoice;
  const idx=PO_STEPS.findIndex(s=>s[0]===o.status),cancelled=o.status==="cancelled";
  const when=st=>o.history.find(h=>h.to_status===st)?.created_at;
  const steps=`<ol class="steps ${cancelled?"cancelled":""}">${PO_STEPS.map(([k,l],i)=>{
    const cls=cancelled?"":i<idx?"done":i===idx?(k==="delivered"?"done":"cur"):"";
    return `<li class="${cls}"><i aria-hidden="true">${cls==="done"?"✓":i+1}</i><span>${l}</span><small>${when(k)?localTime(when(k)).slice(5):""}</small></li>`}).join("")}</ol>`;
  let track="";
  if(cancelled)track=`<div class="track er">Захиалга цуцлагдсан${o.history.at(-1)?.note?": "+esc(o.history.at(-1).note):""}.</div>`;
  else if(t&&t.status==="in_progress")track=`<div class="track live"><b>Таны захиалга замд явж байна</b>
    <div>Машин <b>${esc(t.vehicle_plate)}</b> · Жолооч ${esc(t.driver_name)}${t.driver_phone?` · <a href="tel:${esc(t.driver_phone)}">${esc(t.driver_phone)}</a>`:""}</div>
    <div>Таны захиалга <b>${t.stops_total} зогсоолоос ${t.my_stop}-рт</b> · ${t.stops_done} зогсоол хүргэгдсэн${t.my_stop>t.stops_done+1?` · таны өмнө ${t.my_stop-t.stops_done-1} зогсоол`:t.my_stop===t.stops_done+1?" · <b>дараагийн зогсоол нь та</b>":""}</div></div>`;
  else if(t&&t.status==="planned")track=`<div class="track">Аялалд оноогдсон: <b>${day(t.planned_date)}</b>-нд машин <b>${esc(t.vehicle_plate)}</b>-ээр хүргэнэ.</div>`;
  else if(sh?.status==="delivered")track=`<div class="track ok">Хүргэгдсэн: <b>${localTime(sh.delivered_at)}</b></div>`;
  else if(sh?.status==="failed")track=`<div class="track er">Хүргэлт амжилтгүй болсон: ${esc(sh.failed_reason||"")}. Дахин хүргэлтэд оруулна.</div>`;
  else if(o.status==="draft")track=`<div class="track">Захиалгыг хүлээн авлаа. Диспетчер шалгаад баталгаажуулна.</div>`;
  else if(o.status==="confirmed")track=`<div class="track">Баталгаажсан. Агуулахад бэлтгэлд орно.</div>`;
  else if(o.status==="picking")track=`<div class="track">Агуулахад бэлтгэж байна. Удахгүй хүргэлтэд гарна.</div>`;
  else if(o.status==="shipped")track=`<div class="track">Илгээгдсэн. Хүргэлтийн машинд ачигдаж байна.</div>`;
  $("pod").innerHTML=`
    <div class="panel-head" style="padding:0 0 12px"><h2 style="font-size:18px">${esc(o.order_no)} ${tag(PO_ST,o.status)}</h2>
      ${o.status==="draft"?`<button class="btn small danger" onclick="poCancel(${o.id})">Цуцлах</button>`:""}</div>
    ${steps}${track}
    <dl class="kv" style="margin:16px 0">
      <div><dt>Хүргэх хаяг</dt><dd>${o.delivery_location?esc(o.delivery_location.name)+(o.delivery_location.address?`<span class="sub">${esc(o.delivery_location.address)}</span>`:""):"—"}</dd></div>
      <div><dt>Хүсэлтэй огноо</dt><dd>${day(o.requested_delivery_date)}</dd></div>
      <div><dt>Нийт дүн</dt><dd>${pmnt(o.total_amount)}</dd></div>
      ${o.notes?`<div><dt>Тэмдэглэл</dt><dd>${esc(o.notes)}</dd></div>`:""}
    </dl>
    <div class="scroll"><table><thead><tr><th>Бараа</th><th class="num">Тоо</th><th class="num">Үнэ</th><th class="num">Дүн</th></tr></thead><tbody>
      ${o.lines.map(l=>`<tr><td>${esc(l.product)}</td><td class="num">${fmt(l.quantity)} <span class="mu">${esc(l.unit)}</span></td><td class="num">${pmnt(l.unit_price)}</td><td class="num">${pmnt(l.line_total)}</td></tr>`).join("")}
    </tbody></table></div>
    ${inv?`<div class="invbox"><div><b>Нэхэмжлэх ${esc(inv.number)}</b> ${tag(PO_INV,inv.status)}<span class="sub">Төлөх хугацаа: ${day(inv.due)}</span></div>
      <div class="num">Төлсөн ${pmnt(inv.paid)} / ${pmnt(inv.amount)}<span class="sub">Үлдэгдэл: <b>${pmnt(inv.balance)}</b></span></div></div>`:""}`;
}
const poCancel=run(async id=>{
  if(!confirm("Захиалгыг цуцлах уу?"))return;
  await api(`/portal/orders/${id}/cancel`,{method:"POST"});notice("Захиалга цуцлагдлаа");rPo();
});

// ---------------- Захиалга өгөх
const poNew=run(async()=>{
  [poProducts,poAddr]=await Promise.all([api("/portal/products"),api("/portal/addresses")]);
  openModal("m-po");
  $("po-a").innerHTML=poAddr.map(a=>`<option value="${a.id}">${esc(a.name)}${a.address?" — "+esc(a.address):""}</option>`).join("")+`<option value="new">+ Шинэ хаяг нэмэх…</option>`;
  poAddrToggle();$("po-lines").innerHTML="";poAddLine();
});
function poAddrToggle(){const n=$("po-a").value==="new";$("po-new").hidden=!n;$("po-an").required=n}
function poAddLine(){
  const k=++poLineSeq;
  $("po-lines").insertAdjacentHTML("beforeend",`<div class="po-line" id="pol${k}">
    <select aria-label="Бараа" required onchange="poTotal()"><option value="">Бараа сонгох…</option>${poProducts.map(p=>`<option value="${p.id}" data-price="${p.price}">${esc(p.name)} — ${pmnt(p.price)}/${esc(p.unit)}</option>`).join("")}</select>
    <input type="number" min="0.001" step="any" value="1" aria-label="Тоо" required oninput="poTotal()">
    <button type="button" class="btn small" aria-label="Мөр устгах" onclick="document.getElementById('pol${k}').remove();poTotal()">✕</button></div>`);
  poTotal();
}
function poTotal(){
  let s=0;document.querySelectorAll("#po-lines .po-line").forEach(r=>{const o=r.querySelector("select").selectedOptions[0];s+=(+o?.dataset.price||0)*(+r.querySelector("input").value||0)});
  $("po-t").textContent=pmnt(s);
}
const poSubmit=run(async e=>{e.preventDefault();
  const lines=[...document.querySelectorAll("#po-lines .po-line")].map(r=>({product_id:+r.querySelector("select").value,quantity:r.querySelector("input").value}));
  if(!lines.length)throw new Error("Дор хаяж нэг бараа нэмнэ үү");
  let loc=$("po-a").value;
  if(loc==="new"){
    const a=await api("/portal/addresses",{method:"POST",body:{name:$("po-an").value.trim(),address:$("po-ad").value.trim()||null}});
    loc=a.id;
  }
  const o=await api("/portal/orders",{method:"POST",body:{delivery_location_id:loc?+loc:null,
    requested_delivery_date:$("po-d").value?`${$("po-d").value}T00:00:00`:null,notes:$("po-n").value.trim()||null,lines}});
  closeModal();poSel=o.id;notice(`Захиалга ${o.order_no} илгээгдлээ. Баталгаажих үед мэдэгдэл ирнэ.`);rPo();
});
