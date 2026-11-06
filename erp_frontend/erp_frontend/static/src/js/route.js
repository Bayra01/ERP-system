// Маршрут оновчлол — /api/routing. app.js-ийн $, api, esc, fmt, run, can, tag, trT, shT, kpis-г ашиглана.
let rtTrip=null,rtView=null,rtTrips=[];
TABS.rt={perm:"routing:read",render:()=>rRt()};

function openRoute(id){rtTrip=id;show("rt")}

const rRt=run(async()=>{
  rtTrips=me.role==="driver"?await items("/transport/my/trips"):await items("/transport/trips",{status:"planned,in_progress,completed"});
  rtTrips=rtTrips.filter(t=>t.stops>0);
  if(!rtTrips.some(t=>t.id===rtTrip))rtTrip=(rtTrips.find(t=>t.status==="planned")||rtTrips[0])?.id??null;
  rtList();$("rtmsg").hidden=true;
  if(rtTrip)await rtLoad();else{rtView=null;rtDraw()}
});
function rtList(){
  $("rtl").innerHTML=rtTrips.map(t=>`<button class="titem ${t.id===rtTrip?"on":""}" onclick="rtSelect(${t.id})">
    <span class="t1">${esc(t.trip_no)}<span class="mu">${t.total_distance_km!=null?fmt(t.total_distance_km)+" км":""}</span></span>
    <span class="t2"><span>${day(t.planned_date)} · ${esc(t.vehicle_plate)} · ${t.stops} зогсоол</span>${tag(trT,t.status)}</span></button>`).join("")
    ||`<div class="panel"><p class="muted" style="margin:0">Зогсоолтой аялал алга. Тээвэр хэсгээс аялал үүсгэнэ үү.</p></div>`;
}
const rtSelect=run(async id=>{rtTrip=id;rtList();$("rtmsg").hidden=true;await rtLoad()});
async function rtLoad(){rtView=await api(`/routing/trips/${rtTrip}`);rtDraw()}

function rtDraw(){
  const v=rtView,editable=v&&v.status==="planned"&&can("routing:write");
  // Явж буй аялал: жолооч (өөрийнх) эсвэл transport:write зогсоол бүрийг тэмдэглэнэ.
  const live=v&&v.status==="in_progress"&&(can("transport:write")||me.role==="driver");
  $("rtt").textContent=v?`${v.trip_no} · ${v.depot?.name||"агуулахгүй"}-аас эхэлнэ`:"Аяллын зогсоолуудын дараалал, зай";
  $("rto").hidden=!editable||v.stops.length<2;
  const noCoord=v?v.stops.filter(s=>s.lat==null).length:0;
  kpis("rtk",v?[["Нийт зай",fmt(v.total_distance_km)+" км"],["Зогсоол",v.stops.length],
    ["Хүргэгдсэн",v.stops.filter(s=>s.status==="delivered").length],["Координатгүй",noCoord,noCoord?"warn":""]]:[]);
  rtMap(v);
  const canGeo=can("masterdata:write");
  $("rts").innerHTML=v?v.stops.map((s,i)=>`<tr data-i="${i}" onmouseenter="rtHi(${i})" onmouseleave="rtHi(-1)">
    <td><span class="stopn">${i+1}</span></td>
    <td>${esc(s.location_name||"(хаяггүй)")}<span class="sub">${esc(ordName(s.order_id))}${s.address?" · "+esc(s.address):""}</span></td>
    <td class="num">${fmt(s.weight_kg)} кг</td>
    <td class="num">${s.leg_km!=null?fmt(s.leg_km)+" км":s.lat==null?(canGeo&&s.location_id?`<span class="geo"><input placeholder="өргөрөг" id="la${s.location_id}" aria-label="Өргөрөг"><input placeholder="уртраг" id="ln${s.location_id}" aria-label="Уртраг"><button class="btn small" onclick="rtGeo(${s.location_id})">OK</button></span>`:`<span class="wn">координатгүй</span>`):"—"}</td>
    <td>${tag(shT,s.status)}</td>
    <td class="act">${live&&s.status==="in_transit"?`<button class="btn small" onclick="rtDeliver(${i})">Хүргэсэн</button><button class="btn small danger" onclick="rtFail(${i})">Амжилтгүй</button>`:""}${editable?`<button class="btn small" aria-label="Дээш" ${i?"":"disabled"} onclick="rtMove(${i},-1)">↑</button><button class="btn small" aria-label="Доош" ${i<v.stops.length-1?"":"disabled"} onclick="rtMove(${i},1)">↓</button>`:""}</td></tr>`).join("")
    :emptyRow(6,"Аялал сонгоогүй");
}

// lat/lng -> SVG. Жижиг талбайд equirectangular (cos(lat) засвартай) хангалттай.
function rtMap(v){
  const svg=$("rtmap"),W=640,H=380,P=40;
  const pts=v?[...(v.depot&&v.depot.lat!=null?[{lat:v.depot.lat,lng:v.depot.lng}]:[]),...v.stops.filter(s=>s.lat!=null)]:[];
  if(!pts.length){svg.innerHTML=`<text x="${W/2}" y="${H/2}" text-anchor="middle" class="axis">${v?"Координаттай зогсоол алга":"Аялал сонгоогүй"}</text>`;return}
  const k=Math.cos((pts.reduce((a,p)=>a+p.lat,0)/pts.length)*Math.PI/180);
  const xs=pts.map(p=>p.lng*k),ys=pts.map(p=>p.lat);
  const [x0,x1,y0,y1]=[Math.min(...xs),Math.max(...xs),Math.min(...ys),Math.max(...ys)];
  const s=Math.min((W-2*P)/((x1-x0)||1e-9),(H-2*P)/((y1-y0)||1e-9),1e6),cx=(W-(x1-x0)*s)/2,cy=(H-(y1-y0)*s)/2;
  const xy=p=>[cx+(p.lng*k-x0)*s,cy+(y1-p.lat)*s];
  // Баруун талын цэгийн нэрийг зүүн тийш нь бичнэ (тайрагдахгүй).
  const lbl=(x,y,dy,t)=>x>W*.62?`<text x="${x-15}" y="${y+dy}" text-anchor="end" class="lbl">${t}</text>`:`<text x="${x+15}" y="${y+dy}" class="lbl">${t}</text>`;
  let path=[],out="",labels="";
  if(v.depot&&v.depot.lat!=null){const[x,y]=xy(v.depot);path.push([x,y]);
    out+=`<g><title>${esc(v.depot.name)} (эхлэл)</title><rect x="${x-8}" y="${y-8}" width="16" height="16" rx="3" class="depot"/></g>`;
    labels+=lbl(x,y,-12,esc(v.depot.name))}
  const many=v.stops.length>8;
  v.stops.forEach((st,i)=>{if(st.lat==null)return;const[x,y]=xy(st);
    if(path.length&&st.leg_km!=null&&!many){const[px,py]=path[path.length-1];
      if(Math.hypot(x-px,y-py)>70)labels+=`<text x="${(px+x)/2}" y="${(py+y)/2-6}" text-anchor="middle" class="leg">${fmt(st.leg_km)} км</text>`}
    path.push([x,y]);
    out+=`<g class="stop ${st.status==="delivered"?"done":""}" data-i="${i}" onmouseenter="rtHi(${i})" onmouseleave="rtHi(-1)"><title>${i+1}. ${esc(st.location_name)} — ${esc(ordName(st.order_id))}${st.leg_km!=null?`, ${fmt(st.leg_km)} км`:""}</title>
      <circle cx="${x}" cy="${y}" r="16" fill="transparent"/><circle cx="${x}" cy="${y}" r="11" class="dot"/><text x="${x}" y="${y+4}" text-anchor="middle" class="num">${i+1}</text></g>`;
    if(!many)labels+=lbl(x,y,18,esc(st.location_name||""))});
  const line=path.length>1?`<polyline points="${path.map(p=>p.join(",")).join(" ")}" class="route"/>`:"";
  svg.innerHTML=line+labels+out;
}
function rtHi(i){
  document.querySelectorAll("#rtmap .stop").forEach(g=>g.classList.toggle("hi",+g.dataset.i===i));
  document.querySelectorAll("#rts tr").forEach(r=>r.classList.toggle("hi",+r.dataset.i===i));
}

function rtSaved(r,what){
  rtView=r;rtDraw();
  const d=r.previous_km-r.total_distance_km;
  $("rtmsg").innerHTML=`${what}: <span class="mu">${fmt(r.previous_km)} км →</span> <b>${fmt(r.total_distance_km)} км</b>`+(d>0.005?` <span class="ok">· ${fmt(d)} км хэмнэлт</span>`:d<-0.005?` <span class="wn">· ${fmt(-d)} км нэмэгдлээ</span>`:"");
  $("rtmsg").hidden=false;
  const t=rtTrips.find(x=>x.id===r.trip_id);if(t){t.total_distance_km=r.total_distance_km;rtList()}
}
const rtOptimize=run(async()=>rtSaved(await api(`/routing/trips/${rtTrip}/optimize`,{method:"POST"}),"Оновчилсон"));
const rtMove=run(async(i,d)=>{
  const ids=rtView.stops.map(s=>s.shipment_id);[ids[i],ids[i+d]]=[ids[i+d],ids[i]];
  rtSaved(await api(`/routing/trips/${rtTrip}/sequence`,{method:"PUT",body:{shipment_ids:ids}}),"Дараалал өөрчлөгдлөө");
});
const rtGeo=run(async loc=>{
  const lat=parseFloat($("la"+loc).value),lng=parseFloat($("ln"+loc).value);
  if(!(Math.abs(lat)<=90&&Math.abs(lng)<=180))throw new Error("Координат буруу (жишээ: 47.92, 106.92)");
  await api(`/masterdata/locations/${loc}`,{method:"PATCH",body:{lat,lng}});
  const l=locations.find(x=>x.id===loc);if(l)Object.assign(l,{lat,lng});
  await rtLoad();
});

// Зогсоол бүрийн хүргэлт: хүргэсэн / амжилтгүй (шалтгаантай). Сүүлийн зогсоол шийдэгдэхэд аялал дуусна.
let rtStop=null;
const rtDeliver=run(async i=>{
  const s=rtView.stops[i];
  if(!confirm(`${i+1}. ${s.location_name||ordName(s.order_id)} — хүргэгдсэн гэж тэмдэглэх үү?`))return;
  await api(`/transport/shipments/${s.shipment_id}/deliver`,{method:"POST"});
  await rRt();bell();
});
function rtFail(i){rtStop=rtView.stops[i];openModal("m-fail");$("mf-info").textContent=`${i+1}. ${rtStop.location_name||""} · ${ordName(rtStop.order_id)}`}
function rtReason(v){if(v)$("mf-r").value=v}
const rtFailDo=run(async e=>{e.preventDefault();
  await api(`/transport/shipments/${rtStop.shipment_id}/fail`,{method:"POST",body:{reason:$("mf-r").value.trim()}});
  closeModal();await rRt();bell();
});
