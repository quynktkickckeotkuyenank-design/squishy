/* 🛍️ GIAO DIỆN KHÁCH: sản phẩm, giỏ hàng, thanh toán, tra cứu */
const Shop={
 cart:{},
 home(){return `<div class="grid">${PRODUCTS.map(p=>`<div class="card"><div class="emoji">${p.emoji}</div><h3>${p.name}</h3>
  <span class="tag ${p.type}">${p.type==='pre'?'Pre-order 10-17 ngày':'Có sẵn ('+p.stock+')'}</span>
  <p class="price">${fmt(p.price)}</p><button onclick="Shop.add('${p.id}')">+ Thêm giỏ</button></div>`).join('')}</div>`},
 add(id){this.cart[id]=(this.cart[id]||0)+1;alert('Đã thêm vào giỏ 💗');Main.nav('cart')},
 total(){return Object.entries(this.cart).reduce((s,[id,q])=>s+PRODUCTS.find(p=>p.id===id).price*q,0)},
 cartView(){const e=Object.entries(this.cart);if(!e.length)return '<div class="card">Giỏ hàng đang trống 🧺</div>';
  return `<div class="card"><table>${e.map(([id,q])=>{const p=PRODUCTS.find(x=>x.id===id);return `<tr><td>${p.emoji} ${p.name}</td><td>x${q}</td><td>${fmt(p.price*q)}</td></tr>`}).join('')}</table>
  <p class="price">Tổng: ${fmt(this.total())}</p>
  <input id="cn" placeholder="Họ tên người nhận"><input id="cp" placeholder="Số điện thoại"><input id="ca" placeholder="Địa chỉ nhận hàng">
  <p class="small">Nhớ kiểm tra kỹ thông tin trước khi đặt nha 💗</p><button onclick="Shop.checkout()">Đặt hàng & thanh toán</button></div>`},
 checkout(){const name=cn.value.trim(),phone=cp.value.trim(),address=ca.value.trim();
  if(!name||!/^0\d{9}$/.test(phone)||!address)return alert('Nhập đủ họ tên, SĐT (10 số), địa chỉ nha!');
  const items=Object.entries(this.cart).map(([id,q])=>{const p=PRODUCTS.find(x=>x.id===id);return {id,name:p.name,qty:q,price:p.price,cost:p.cost}});
  const o={id:'NP'+Date.now().toString(36).toUpperCase(),name,phone,address,items,total:this.total(),status:'pending',paid:false,tracking:'',date:new Date().toISOString()};
  Store.save(o);this.cart={};this.pay(o)},
 pay(o){Main.modal(`<h2>Quét mã để thanh toán 💳</h2><img src="${Bank.qr(o.total,o.id)}" alt="VietQR" style="max-width:260px;width:100%;border-radius:20px">
  <p><b>${CONFIG.BANK.name}</b><br>${CONFIG.BANK.account} • ${CONFIG.BANK.branch}<br>Nội dung CK: <b>${o.id}</b> • ${fmt(o.total)}</p>
  <button onclick="Shop.paid('${o.id}')">Mình đã chuyển khoản ✔</button>`);
  /* Nếu đã nối webhook ngân hàng: tự kiểm tra mỗi 4s */
  if(Bank.isConnected()){const t=setInterval(async()=>{if(await Bank.checkPaid(o)){clearInterval(t);Shop.paid(o.id)}},4000)}},
 paid(id){const o=Store.orders().find(x=>x.id===id);o.paid=true;Store.save(o);Zalo.notify(o,`Shop đã nhận đơn ${o.id}`);
  Main.modal(`<div class="ok">✓</div><h2>Thanh toán thành công!</h2><p>Mã đơn: <b>${o.id}</b></p><span class="note">⏳ Đơn đang chờ xác nhận</span>
  <p class="small">Lưu mã đơn để tra cứu nha 💗</p><button onclick="Main.close();Main.nav('track')">Tra cứu đơn</button>`)},
 trackView(){return `<div class="card"><h3>Tra cứu đơn hàng 🔎</h3><input id="tc" placeholder="Mã đơn hoặc mã vận đơn SPX"><input id="tp" placeholder="Số điện thoại đặt hàng">
  <button onclick="Shop.track()">Tra cứu</button><div id="tr"></div></div>`},
 track(){const c=tc.value.trim().toUpperCase(),p=tp.value.trim();
  const o=Store.orders().find(x=>(x.id===c||(x.tracking&&x.tracking.toUpperCase()===c))&&x.phone===p);
  const L={pending:'⏳ Đơn đang chờ xác nhận',approved:'✅ Shop đã xác nhận, đang chuẩn bị hàng',shipped:'🚚 Đã giao cho SPX'};
  tr.innerHTML=o?`<p><b>${o.id}</b> – ${L[o.status]}<br>Mã vận đơn: ${o.tracking||'chưa có'}<br>Tổng: ${fmt(o.total)}</p>`:'<p>Không tìm thấy đơn 🥲</p>'},
 /* Tab Liên kết: dán URL backend khi đã có tài khoản */
 intView(){const i=Store.get('int',{});const f=(k,t,h)=>`<div class="card"><h3>${t} <span class="tag ${i[k]?'':'pre'}">${i[k]?'Đã nhập URL':'Chưa liên kết'}</span></h3><p class="small">${h}</p>
  <input id="i_${k}" value="${i[k]||''}" placeholder="Backend URL (vd https://api.cuaban.com)"><button onclick="Shop.saveInt('${k}')">Lưu</button></div>`;
  return f('bank','Ngân hàng (SePay/Casso webhook)','Tự xác nhận tiền vào → bật màn hình thanh toán thành công.')+f('spx','SPX Express','Khách đặt xong → bấm "Xuất ship" tự điền thông tin & nhảy mã vận đơn.')+f('zalo','Zalo OA','Tự nhắn khách khi có đơn / đổi trạng thái.')+'<p class="small">Xem docs/WORKFLOW.md để biết cách tạo backend. Không dán API key vào web!</p>'},
 saveInt(k){const i=Store.get('int',{});i[k]=document.getElementById('i_'+k).value.trim();Store.set('int',i);Main.nav('int')}
};
