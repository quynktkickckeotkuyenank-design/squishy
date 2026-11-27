/* 🚀 KHỞI ĐỘNG: tab, modal, rule mở web. Thêm tab mới: thêm vào TABS */
const TABS={shop:['🧸 Sản phẩm',()=>Shop.home()],cart:['🛒 Giỏ hàng',()=>Shop.cartView()],track:['🔎 Tra cứu',()=>Shop.trackView()],admin:['👑 Quản trị',()=>Admin.view()],int:['🔗 Liên kết',()=>Shop.intView()]};
const Main={
 cur:'shop',
 nav(t){this.cur=t;document.getElementById('tabs').innerHTML=Object.entries(TABS).map(([k,v])=>`<button class="${k===t?'on':''}" onclick="Main.nav('${k}')">${v[0]}</button>`).join('');
  document.getElementById('view').innerHTML=TABS[t][1]()},
 modal(h){const m=document.getElementById('modal');m.innerHTML=`<div class="box">${h}</div>`;m.classList.add('show')},
 close(){document.getElementById('modal').classList.remove('show')},
 rules(){const R=RULES;this.modal(`<h2>Thông báo nhỏ từ Squishy 💗</h2>${R.top.map(t=>`<div class="pill top">${md(t)}</div>`).join('')}
  ${R.items.map(r=>`<div class="pill"><em>${r[0]}</em><span>${md(r[1])}</span></div>`).join('')}<h3>${md(R.bottom)}</h3><button onclick="Main.close()">Mình đã đọc rồi nha ✨</button>`)}
};
document.getElementById('appName').textContent=CONFIG.APP_NAME;
document.getElementById('foot').innerHTML=Object.entries(CONFIG.SOCIAL).filter(e=>e[1]).map(([k,v])=>`<a href="${v}" target="_blank">${k}</a>`).join('·')+`<p class="small">© ${CONFIG.SHOP_NAME}</p>`;
Main.nav('shop');Main.rules(); // rule hiện ngay khi mở web
