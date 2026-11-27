/* 👑 TRANG QUẢN TRỊ: duyệt đơn, KPI, lợi nhuận, xuất ship */
const Admin={
 ok:false,
 view(){if(!this.ok)return `<div class="card"><h3>Đăng nhập quản trị</h3><input id="pin" type="password" placeholder="Mã PIN"><button onclick="Admin.login()">Vào</button></div>`;
  const os=Store.orders(),good=os.filter(o=>o.status!=='pending'),
  rev=good.reduce((s,o)=>s+o.total,0),cost=good.reduce((s,o)=>s+o.items.reduce((a,i)=>a+i.cost*i.qty,0),0),profit=rev-cost,
  k=CONFIG.KPI,pp=Math.min(100,profit/k.monthlyProfit*100),po=Math.min(100,good.length/k.monthlyOrders*100);
  return `<div class="kpi"><div>Đơn chờ<b>${os.filter(o=>o.status==='pending').length}</b></div><div>Đã duyệt<b>${good.length}</b></div><div>Doanh thu<b>${fmt(rev)}</b></div><div>Vốn nhập<b>${fmt(cost)}</b></div><div>Lợi nhuận<b>${fmt(profit)}</b></div></div>
  <div class="card"><b>KPI lợi nhuận</b> ${fmt(profit)} / ${fmt(k.monthlyProfit)} (${pp.toFixed(0)}%)<div class="bar"><i style="width:${pp}%"></i></div>
  <br><b>KPI số đơn</b> ${good.length} / ${k.monthlyOrders} (${po.toFixed(0)}%)<div class="bar"><i style="width:${po}%"></i></div></div>
  <div class="card" style="overflow:auto"><table><tr><th>Đơn</th><th>Khách</th><th>Tiền</th><th>Lãi</th><th>TT</th><th>Mã vận đơn</th><th></th></tr>
  ${os.map(o=>{const pr=o.total-o.items.reduce((a,i)=>a+i.cost*i.qty,0);return `<tr><td>${o.id}</td><td>${o.name}<br>${o.phone}</td><td>${fmt(o.total)}<br>${o.paid?'💚 đã CK':'chưa CK'}</td><td>${fmt(pr)}</td><td>${o.status}</td><td>${o.tracking||'-'}</td>
  <td>${o.status==='pending'?`<button onclick="Admin.approve('${o.id}')">Duyệt</button>`:o.status==='approved'?`<button onclick="Admin.ship('${o.id}')">Xuất ship</button>`:'✔'}</td></tr>`}).join('')||'<tr><td>Chưa có đơn</td></tr>'}</table></div>`},
 login(){if(pin.value===CONFIG.ADMIN_PIN){this.ok=true;Main.nav('admin')}else alert('Sai PIN')},
 approve(id){const o=Store.orders().find(x=>x.id===id);o.status='approved';Store.save(o);Zalo.notify(o,`Đơn ${id} đã được xác nhận 💗`);Main.nav('admin')},
 async ship(id){const o=Store.orders().find(x=>x.id===id),r=await SPX.createShipment(o);
  o.tracking=r.code;o.status='shipped';Store.save(o);
  alert(`Mã vận đơn: ${r.code}${r.mock?'\n(MÃ GIẢ – chưa liên kết SPX)':''}\nĐã tự điền: ${r.payload.receiver.name} - ${r.payload.receiver.phone}`);Main.nav('admin')}
};
