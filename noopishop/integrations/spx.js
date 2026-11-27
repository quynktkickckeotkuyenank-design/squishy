/* 🚚 SPX EXPRESS. Chưa liên kết → tạo mã giả (MOCK). Đã dán Backend URL ở tab "Liên kết" → gọi API thật qua backend */
const SPX={
 isConnected(){return !!(Store.get('int',{}).spx||'')},
 /* Tự điền thông tin đơn → tạo vận đơn → trả mã */
 async createShipment(o){
  const payload={receiver:{name:o.name,phone:o.phone,address:o.address},items:o.items.map(i=>({name:i.name,qty:i.qty})),cod:0,ref:o.id};
  const u=Store.get('int',{}).spx;
  if(u){try{const r=await fetch(u+'/shipments',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});return {code:(await r.json()).tracking_code,mock:false,payload}}catch(e){}}
  return {code:'SPXMOCK'+Math.random().toString(36).slice(2,9).toUpperCase(),mock:true,payload};
 }
};
