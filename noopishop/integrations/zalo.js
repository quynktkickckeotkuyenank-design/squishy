/* 💬 ZALO: hiện tại mở chat Zalo shop. Muốn tự nhắn khách → đăng ký Zalo OA rồi dán Backend URL */
const Zalo={
 link(){return CONFIG.SOCIAL.zalo},
 async notify(o,text){const u=Store.get('int',{}).zalo;if(!u)return false;
  try{await fetch(u+'/send',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({phone:o.phone,text})});return true}catch(e){return false}}
};
