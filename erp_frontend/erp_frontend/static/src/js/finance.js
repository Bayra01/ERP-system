// Санхүүгийн тайлан — /api/finance (camelCase, Array). Графикууд гадны сангүй, SVG/HTML.
TABS.fn={perm:"finance:read",render:()=>rFn()};
const mnt=n=>Number(n||0).toLocaleString("mn-MN",{maximumFractionDigits:0})+" ₮";
const compact=n=>Number(n).toLocaleString("mn-MN",{notation:"compact",maximumFractionDigits:1});
const SERIES=[["invoiced","Нэхэмжилсэн","--s1"],["collected","Орсон төлбөр","--s2"],["expenses","Зардал","--s3"]];
const AGE={"current":"Хугацаа болоогүй","1-30":"1–30 хоног хэтэрсэн","31-60":"31–60 хоног","61-90":"61–90 хоног","90+":"90+ хоног"};
const invT={paid:["Төлөгдсөн","ok"],partial:["Хэсэгчлэн","in"],unpaid:["Төлөгдөөгүй","wn"],overdue:["Хугацаа хэтэрсэн","er"]};
const MON=m=>{const[y,mo]=m.split("-");return `${+mo}-р сар${mo==="01"?" "+y:""}`};
const isoDay=d=>`${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,"0")}-${String(d.getDate()).padStart(2,"0")}`;
let fnRangeKey="6",fnInvStatus="",fnInvoices=[],fnCur=null;

function fnRange(k){
  fnRangeKey=k;const t=new Date();
  const f=k==="ytd"?new Date(t.getFullYear(),0,1):new Date(t.getFullYear(),t.getMonth()-(+k)+1,1);
  $("ff").value=isoDay(f);$("ft").value=isoDay(t);rFn();
}
function fnCustom(){fnRangeKey="custom";rFn()}
function fnStatus(s){fnInvStatus=s;rFn()}

const rFn=run(async()=>{
  if(!$("ff").value){fnRange(fnRangeKey);return}
  chips("fnr",[["3","3 сар"],["6","6 сар"],["12","12 сар"],["ytd","Энэ он"]],fnRangeKey,"fnRange");
  chips("fisc",[["","Бүгд"],["unpaid","Төлөгдөөгүй"],["partial","Хэсэгчлэн"],["overdue","Хугацаа хэтэрсэн"],["paid","Төлөгдсөн"]],fnInvStatus,"fnStatus");
  const [r,inv]=await Promise.all([api("/finance/reports/summary",{query:{date_from:$("ff").value,date_to:$("ft").value}}),
    api("/finance/invoices",{query:{status:fnInvStatus}})]);
  fnInvoices=inv;
  const T=r.totals;
  kpis("fnk",[["Нэхэмжилсэн",mnt(T.invoiced)],["Орсон төлбөр",mnt(T.collected)],["Зардал",mnt(T.expenses)],
    ["Цэвэр урсгал",mnt(T.net),T.net<0?"neg":""],["Нийт авлага",mnt(T.outstanding)],["Хугацаа хэтэрсэн",mnt(T.overdue),T.overdue>0?"warn":""]]);
  $("fnleg").innerHTML=SERIES.map(([,l,c])=>`<span><i style="background:var(${c})"></i>${l}</span>`).join("");
  columns($("fnc1"),r.monthly);
  $("fnt1").innerHTML=`<thead><tr><th>Сар</th>${SERIES.map(s=>`<th class="num">${s[1]}</th>`).join("")}</tr></thead><tbody>`+
    r.monthly.map(m=>`<tr><td>${MON(m.month)}</td>${SERIES.map(([k])=>`<td class="num">${mnt(m[k])}</td>`).join("")}</tr>`).join("")+"</tbody>";
  hbars($("fnc2"),r.aging.map(a=>({label:AGE[a.bucket],value:a.amount,note:`${a.count} нэхэмжлэх`})),"Авлага алга");
  hbars($("fnc3"),r.expensesByCategory.map(e=>({label:e.category,value:e.amount})),"Энэ хугацаанд зардал алга");
  $("fntd").innerHTML=`<thead><tr><th>Харилцагч</th><th class="num">Нэхэмжлэх</th><th class="num">Хэтэрсэн</th><th class="num">Үлдэгдэл</th></tr></thead><tbody>`+
    (r.topDebtors.map(d=>`<tr><td>${esc(d.customer)}</td><td class="num">${d.invoices}</td><td class="num ${d.overdue>0?"er":"mu"}">${mnt(d.overdue)}</td><td class="num"><b>${mnt(d.balance)}</b></td></tr>`).join("")||emptyRow(4,"Авлага алга"))+"</tbody>";
  const write=can("finance:write");
  $("fni").innerHTML=inv.map((i,n)=>`<tr><td>${esc(i.number)}</td><td>${esc(i.customer)}${i.orderId?`<span class="sub">${esc(ordName(i.orderId))}</span>`:""}</td><td>${day(i.issued)}<span class="sub">→ ${day(i.due)}</span></td>
    <td class="num">${mnt(i.amount)}</td><td class="num">${mnt(i.paid)}</td><td class="num"><b>${mnt(i.balance)}</b></td><td>${tag(invT,i.status)}</td>
    <td class="act">${write&&i.balance>0?`<button class="btn small" onclick="fnPay(${n})">Төлбөр</button>`:""}</td></tr>`).join("")||emptyRow(8,"Нэхэмжлэх алга");
  if(!$("custs").children.length&&can("masterdata:read"))
    $("custs").innerHTML=(await items("/masterdata/customers")).map(c=>`<option value="${esc(c.name)}">`).join("");
});

// Бүлэгчилсэн багана: сар бүр 3 багана, нэг тэнхлэг, 4px бөөрөнхий орой, суурьтаа шулуун.
function columns(el,rows){
  const W=Math.max(320,el.clientWidth||640),H=260,L=56,R=8,Tp=12,B=30,pw=W-L-R,ph=H-Tp-B;
  const max=Math.max(1,...rows.flatMap(m=>SERIES.map(([k])=>m[k])));
  const step=niceStep(max/4),top=Math.ceil(max/step)*step,y=v=>Tp+ph-(v/top)*ph;
  const band=pw/rows.length,bw=Math.max(4,Math.min(24,(band*.72-4)/3)),gw=bw*3+4;
  let g="";
  for(let v=0;v<=top+1e-9;v+=step)g+=`<line x1="${L}" x2="${W-R}" y1="${y(v)}" y2="${y(v)}" class="grid"/><text x="${L-8}" y="${y(v)+4}" text-anchor="end" class="axis">${compact(v)}</text>`;
  rows.forEach((m,i)=>{
    const x0=L+band*i+(band-gw)/2;
    SERIES.forEach(([k,,c],j)=>{const h=y(0)-y(m[k]);if(h>0.5)g+=`<path d="${colPath(x0+j*(bw+2),y(m[k]),bw,h)}" fill="var(${c})"/>`});
    g+=`<text x="${L+band*i+band/2}" y="${H-10}" text-anchor="middle" class="axis">${band<64?+m.month.slice(5)+"-р":MON(m.month)}</text>`;
    g+=`<rect x="${L+band*i}" y="${Tp}" width="${band}" height="${ph}" class="hit" data-i="${i}"/>`;
  });
  el.innerHTML=`<svg viewBox="0 0 ${W} ${H}" width="100%" role="img" aria-label="Сарын нэхэмжлэл, төлбөр, зардал">${g}</svg>`;
  el.querySelectorAll(".hit").forEach(h=>{
    const m=rows[+h.dataset.i];
    h.onmousemove=e=>tip(e,`<b>${MON(m.month)}</b>`+SERIES.map(([k,l,c])=>`<div><i style="background:var(${c})"></i>${l}<span>${mnt(m[k])}</span></div>`).join(""));
    h.onmouseleave=()=>tip();
  });
}
function colPath(x,y,w,h){const r=Math.min(4,w/2,h);return `M${x},${y+h}V${y+r}Q${x},${y} ${x+r},${y}H${x+w-r}Q${x+w},${y} ${x+w},${y+r}V${y+h}Z`}
function niceStep(raw){const p=10**Math.floor(Math.log10(raw||1)),f=raw/p;return (f<=1?1:f<=2?2:f<=5?5:10)*p}

// Хэвтээ багана (нэг цуваа): нэр зүүнд, утга баганын үзүүрт. 0 утга юу ч зурахгүй.
function hbars(el,rows,empty){
  const max=Math.max(...rows.map(r=>r.value),0);
  if(!max){el.innerHTML=`<p class="muted">${empty}</p>`;return}
  el.innerHTML=`<div class="hbars">`+rows.map(r=>`<div class="hb">
    <span class="hl">${esc(r.label)}</span><span class="ht">${r.value>0?`<i style="width:${r.value/max*100}%"></i>`:""}<em>${mnt(r.value)}</em></span></div>`).join("")+`</div>`;
  el.querySelectorAll(".hb").forEach((b,i)=>{const r=rows[i];
    b.onmousemove=e=>tip(e,`<b>${esc(r.label)}</b><div>${mnt(r.value)}${r.note?" · "+esc(r.note):""}</div>`);b.onmouseleave=()=>tip()});
}

function tip(e,html){
  const t=$("tip");if(!e){t.hidden=true;return}
  t.innerHTML=html;t.hidden=false;
  const x=Math.min(e.clientX+14,innerWidth-t.offsetWidth-8),y=e.clientY+14+t.offsetHeight>innerHeight?e.clientY-t.offsetHeight-10:e.clientY+14;
  t.style.left=x+"px";t.style.top=y+"px";
}

function fnPay(n){
  fnCur=fnInvoices[n];openModal("m-pay");
  $("mp-info").textContent=`${fnCur.number} · ${fnCur.customer} — үлдэгдэл ${mnt(fnCur.balance)}`;
  $("mp-a").value=fnCur.balance;$("mp-a").max=fnCur.balance;$("mp-d").value=today();
}
const fnPayDo=run(async e=>{e.preventDefault();
  await api("/finance/payments",{method:"POST",body:{invoiceId:fnCur.id,amount:+$("mp-a").value,method:$("mp-m").value,date:$("mp-d").value||null}});
  closeModal();rFn();
});
const fnInvoice=run(async e=>{e.preventDefault();
  await api("/finance/invoices",{method:"POST",body:{customer:$("fic").value.trim(),amount:+$("fia").value,due:$("fid").value||null,notes:$("fin").value.trim()||null}});
  closeModal();rFn();
});
const fnExpense=run(async e=>{e.preventDefault();
  await api("/finance/expenses",{method:"POST",body:{category:$("fec").value.trim(),vendor:$("fev").value.trim(),amount:+$("fea").value,date:$("fedt").value||null,status:$("fes").value}});
  closeModal();rFn();
});

// Сонгосон хугацааны тайланг Excel файлаар татна. Сервер 2 минутын нэг удаагийн холбоос өгч,
// браузер түүгээр ердийн файл шиг татна (blob/программ click ашиглахгүй — бүх браузерт найдвартай).
const fnExport=run(async()=>{
  const btn=$("fnx"),label=btn.textContent;btn.disabled=true;btn.textContent="Бэлдэж байна…";
  try{
    const r=await api("/finance/reports/export-link",{method:"POST",query:{date_from:$("ff").value,date_to:$("ft").value}});
    window.location.assign(r.url);
    notice(`Тайлан татагдаж байна (${$("ff").value} – ${$("ft").value}). Файл «Downloads» хавтсанд хадгалагдана.`);
  }finally{setTimeout(()=>{btn.disabled=false;btn.textContent=label},1500)}
});
