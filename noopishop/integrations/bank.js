/* 🏦 NGÂN HÀNG + VIETQR. Tự xác nhận tiền vào cần webhook (SePay/Casso) → xem docs/WORKFLOW.md */
const Bank={
 qr(amount,code){const b=CONFIG.BANK;return `https://img.vietqr.io/image/${b.bin}-${b.account}-compact2.png?amount=${amount}&addInfo=${encodeURIComponent(code)}&accountName=${encodeURIComponent(b.name)}`},
 isConnected(){return !!(Store.get('int',{}).bank||'')},
 /* Gọi backend của bạn: GET {url}/paid?code=MÃ_ĐƠN → {paid:true/false} */
 async checkPaid(order){const u=Store.get('int',{}).bank;if(!u)return false;
  try{const r=await fetch(`${u}/paid?code=${order.id}`);return (await r.json()).paid===true}catch(e){return false}}
};
