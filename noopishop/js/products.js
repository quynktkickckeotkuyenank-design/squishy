/* 🧸 SẢN PHẨM – thêm/sửa tại đây. type: "stock" (có sẵn) | "pre" (pre-order) */
window.PRODUCTS=[
 {id:"SQ01",name:"Squishy Bánh Bao Mèo",emoji:"🐱",cny:10,type:"stock",stock:5},
 {id:"SQ02",name:"Squishy Thỏ Dâu",emoji:"🐰",cny:25,type:"pre",stock:0},
 {id:"SQ03",name:"Squishy Gấu Mochi",emoji:"🐻",cny:18,type:"pre",stock:0},
 {id:"SQ04",name:"Squishy Bánh Kem",emoji:"🍰",cny:50,type:"stock",stock:2}
].map(p=>({...p,cost:p.cny*CONFIG.PRICING.cnyToVnd,price:Math.round(p.cny*CONFIG.PRICING.cnyToVnd*CONFIG.PRICING.markup)}));
