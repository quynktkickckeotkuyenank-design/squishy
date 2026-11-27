/* 💾 LƯU DỮ LIỆU (localStorage). Sau này đổi sang server/database: chỉ sửa file này */
const Store={
 get(k,d){try{const v=JSON.parse(localStorage.getItem('noopi_'+k));return v??d}catch(e){return d}},
 set(k,v){try{localStorage.setItem('noopi_'+k,JSON.stringify(v))}catch(e){}},
 orders(){return this.get('orders',[])},
 save(o){const a=this.orders(),i=a.findIndex(x=>x.id===o.id);i<0?a.unshift(o):a[i]=o;this.set('orders',a)}
};
const fmt=n=>(n||0).toLocaleString('vi-VN')+'đ';
const md=s=>s.replace(/\*\*(.+?)\*\*/g,'<b>$1</b>');
