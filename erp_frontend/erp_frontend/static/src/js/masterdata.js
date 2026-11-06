// Мастер өгөгдөл — /api/masterdata/{customers,products,locations}. Нэг тохиргооноос жагсаалт, форм зурна.
TABS.md={perm:"masterdata:read",render:()=>rMd()};
const LOC_TYPE={warehouse:["Агуулах","ac"],customer:["Хүргэх хаяг","in"],depot:["Депо","mu"]};
const MD={
  customers:{label:"Харилцагч",one:"харилцагч",search:"Нэр, код, утсаар хайх",
    cols:[["Код",r=>esc(r.code)],["Нэр",r=>`${esc(r.name)}<span class="sub">${r.type==="individual"?"Хувь хүн":"Байгууллага"}${r.register_no?" · РД "+esc(r.register_no):""}</span>`],
      ["Утас",r=>esc(r.phone||"—")],["И-мэйл",r=>esc(r.email||"—")],["Хаяг",r=>`<span class="wrap">${esc(r.address||"—")}</span>`]],
    fields:[{k:"name",l:"Нэр",req:1,wide:1},{k:"code",l:"Код",ph:"Хоосон бол автоматаар"},{k:"type",l:"Төрөл",opts:[["company","Байгууллага"],["individual","Хувь хүн"]]},
      {k:"register_no",l:"Регистрийн дугаар"},{k:"phone",l:"Утас"},{k:"email",l:"И-мэйл",type:"email"},{k:"address",l:"Хаяг",wide:1}]},
  products:{label:"Бараа",one:"бараа",search:"Нэр, кодоор хайх",
    cols:[["Код",r=>esc(r.sku)],["Нэр",r=>esc(r.name)],["Нэгж",r=>esc(r.unit)],["Жин",r=>fmt(r.weight_kg)+" кг",1],["Эзэлхүүн",r=>fmt(r.volume_m3)+" м³",1],["Үнэ",r=>fmt(r.price)+" ₮",1]],
    fields:[{k:"sku",l:"Код (SKU)",req:1},{k:"name",l:"Нэр",req:1},{k:"unit",l:"Хэмжих нэгж",ph:"ш, кг, м, шуудай"},{k:"price",l:"Үнэ, ₮",type:"number"},
      {k:"weight_kg",l:"Нэгжийн жин, кг",type:"number",hint:"Тээврийн ачааг тооцоход"},{k:"volume_m3",l:"Нэгжийн эзэлхүүн, м³",type:"number"}]},
  locations:{label:"Байршил",one:"байршил",search:"Нэр, хаягаар хайх",
    filter:[["","Бүх төрөл"],["warehouse","Агуулах"],["customer","Хүргэх хаяг"],["depot","Депо"]],
    cols:[["Нэр",r=>`${esc(r.name)}<span class="sub">${esc(r.address||"")}</span>`],["Төрөл",r=>tag(LOC_TYPE,r.type)],
      ["Харилцагч",r=>esc(mdCust[r.customer_id]||"—")],["Координат",r=>r.lat!=null?`${r.lat.toFixed(4)}, ${r.lng.toFixed(4)}`:'<span class="wn">байхгүй</span>']],
    fields:[{k:"name",l:"Нэр",req:1,wide:1},{k:"type",l:"Төрөл",opts:[["warehouse","Агуулах"],["customer","Хүргэх хаяг"],["depot","Депо"]]},
      {k:"customer_id",l:"Харилцагч",opts:"customers"},{k:"address",l:"Хаяг",wide:1},
      {k:"lat",l:"Өргөрөг",type:"number",ph:"47.9184",hint:"Маршрут тооцоход хэрэгтэй"},{k:"lng",l:"Уртраг",type:"number",ph:"106.9177"}]},
};
let mdKind="customers",mdPage=1,mdRows=[],mdCur=null,mdCust={};
const MD_SIZE=50;
function mdSet(k){mdKind=k;mdPage=1;$("mdq").value="";$("mdf").value="";rMd()}
function mdGo(d){mdPage+=d;rMd()}

const rMd=run(async()=>{
  const c=MD[mdKind],write=can("masterdata:write");
  chips("mdt",Object.entries(MD).map(([k,v])=>[k,v.label]),mdKind,"mdSet");
  $("mdq").placeholder=c.search;$("mdadd").textContent=`+ ${c.label} нэмэх`;
  document.querySelectorAll(".md-w").forEach(el=>el.hidden=!write);
  $("mdf").hidden=!c.filter;
  if(c.filter&&!$("mdf").options.length)$("mdf").innerHTML=c.filter.map(([v,l])=>`<option value="${v}">${l}</option>`).join("");
  if(mdKind==="locations"&&!Object.keys(mdCust).length)
    (await items("/masterdata/customers")).forEach(x=>mdCust[x.id]=x.name);
  const r=await api(`/masterdata/${mdKind}`,{query:{q:$("mdq").value.trim(),page:mdPage,size:MD_SIZE,...(c.filter?{type:$("mdf").value}:{})}});
  mdRows=r.items;
  $("mdh").innerHTML=`<tr>${c.cols.map(([l,,n])=>`<th class="${n?"num":""}">${l}</th>`).join("")}<th>Төлөв</th><th></th></tr>`;
  $("mdb").innerHTML=r.items.map((row,i)=>`<tr>${c.cols.map(([,f,n])=>`<td class="${n?"num":""}">${f(row)}</td>`).join("")}
    <td>${row.is_active?'<span class="pill ok">Идэвхтэй</span>':'<span class="pill mu">Идэвхгүй</span>'}</td>
    <td class="act">${write?`<button class="btn small" onclick="mdEdit(${i})">Засах</button><button class="btn small danger" onclick="mdDelete(${i})">Устгах</button>`:""}</td></tr>`).join("")
    ||emptyRow(c.cols.length+2,$("mdq").value?"Илэрц алга":`${c.label} бүртгээгүй байна`);
  const pages=Math.max(1,Math.ceil(r.total/MD_SIZE));
  $("mdp").hidden=r.total<=MD_SIZE;
  $("mdp").innerHTML=`<span>${mdPage} / ${pages} хуудас · нийт ${r.total}</span><span class="head-actions"><button class="btn small" ${mdPage>1?"":"disabled"} onclick="mdGo(-1)">← Өмнөх</button><button class="btn small" ${mdPage<pages?"":"disabled"} onclick="mdGo(1)">Дараах →</button></span>`;
});

async function mdForm(row){
  const c=MD[mdKind];
  if(c.fields.some(f=>f.opts==="customers")&&!Object.keys(mdCust).length)
    (await items("/masterdata/customers")).forEach(x=>mdCust[x.id]=x.name);
  const opt=f=>f.opts==="customers"?[["","— байхгүй —"],...Object.entries(mdCust)]:f.opts;
  $("mdform").innerHTML=c.fields.map(f=>{
    const v=row?.[f.k]??"",id=`md-${f.k}`;
    const input=f.opts?`<select id="${id}">${opt(f).map(([ov,ol])=>`<option value="${ov}" ${String(v)===String(ov)?"selected":""}>${esc(ol)}</option>`).join("")}</select>`
      :`<input id="${id}" type="${f.type==="number"?"number":f.type||"text"}" ${f.type==="number"?'step="any"':""} value="${esc(v)}" ${f.req?"required":""} placeholder="${esc(f.ph||"")}">`;
    return `<label class="${f.wide?"wide":""}">${f.l}${f.req?' <span class="er">*</span>':""}${input}${f.hint?`<span class="hint">${f.hint}</span>`:""}</label>`;
  }).join("")+(row?`<label class="check wide"><input type="checkbox" id="md-is_active" ${row.is_active?"checked":""}> Идэвхтэй (сонголтуудад харагдана)</label>`:"");
}
const mdNew=run(async()=>{mdCur=null;await mdForm(null);openModal("m-md");$("m-md-h").textContent=`${MD[mdKind].label} нэмэх`});
const mdEdit=run(async i=>{mdCur=mdRows[i];await mdForm(mdCur);openModal("m-md");$("m-md-h").textContent=`${MD[mdKind].label} засах`});
const mdSave=run(async e=>{e.preventDefault();
  const body={};
  for(const f of MD[mdKind].fields){
    const raw=$(`md-${f.k}`).value.trim();
    if(f.type==="number")body[f.k]=raw===""?(["lat","lng"].includes(f.k)?null:0):Number(raw);
    else if(f.k==="customer_id")body[f.k]=raw?Number(raw):null;
    else body[f.k]=raw||(f.req||f.opts?raw:null);
  }
  if(mdKind==="customers"&&!body.code)delete body.code;
  if(mdKind==="products"&&!body.unit)body.unit="ш";
  if(mdCur){
    body.is_active=$("md-is_active").checked;
    // Зөвхөн өөрчлөгдсөн талбарыг илгээнэ (үйлдлийн түүхэнд яг юу засагдсан нь үлдэнэ).
    for(const k of Object.keys(body))if(String(body[k]??"")===String(mdCur[k]??"")||(typeof body[k]==="number"&&body[k]===Number(mdCur[k])))delete body[k];
    if(Object.keys(body).length)await api(`/masterdata/${mdKind}/${mdCur.id}`,{method:"PATCH",body});
  }
  else await api(`/masterdata/${mdKind}`,{method:"POST",body});
  closeModal();if(mdKind==="customers")mdCust={};await loadRefs();rMd();
});
const mdDelete=run(async i=>{
  const row=mdRows[i],c=MD[mdKind];
  if(!confirm(`«${row.name}» ${c.one}-г устгах уу?\nӨмнөх захиалга, түүхэнд нөлөөлөхгүй, зөвхөн шинэ сонголтуудаас алга болно.`))return;
  await api(`/masterdata/${mdKind}/${row.id}`,{method:"DELETE"});
  if(mdKind==="customers")mdCust={};await loadRefs();rMd();
});
