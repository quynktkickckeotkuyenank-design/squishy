# Muốn sửa gì → mở file nào
| Việc | File |
|---|---|
| Tên app, STK, link Zalo/FB/IG/Threads/TikTok, hệ số giá, KPI, PIN | `js/config.js` |
| Nội dung rule mua hàng (popup mở web) | `js/rules.js` |
| Thêm/sửa sản phẩm | `js/products.js` |
| Màu, font, bong bóng, mèo mờ | `css/style.css` |
| Giao diện khách (giỏ, QR, thanh toán thành công, tra cứu, tab Liên kết) | `js/shop.js` |
| Duyệt đơn, KPI, lợi nhuận, xuất ship | `js/admin.js` |
| Nơi lưu dữ liệu (đổi sang database) | `js/store.js` |
| Ngân hàng / SPX / Zalo | `integrations/bank.js` `spx.js` `zalo.js` |

# Lộ trình liên kết (khi bạn có tài khoản)
Web chỉ chạy ở trình duyệt nên KHÔNG được chứa API key. Cần 1 backend nhỏ (Cloudflare Workers / Vercel / Node):
1. **Ngân hàng:** đăng ký SePay hoặc Casso, nối TK BIDV 8800067380 → họ gọi webhook về backend khi có tiền, nội dung CK chứa mã đơn (NPxxxx) → backend lưu "đã nhận" → cung cấp `GET /paid?code=`. Dán URL backend ở tab **Liên kết**; web tự hiện màn "Thanh toán thành công".
2. **SPX:** xin quyền API/tài khoản đối tác của Shopee Express (SPX). Backend giữ key, nhận `POST /shipments` (người nhận, SĐT, địa chỉ, sản phẩm) → gọi SPX → trả `{tracking_code}`. Chỉnh payload trong `integrations/spx.js`. Chưa có tài khoản thì web dùng mã giả SPXMOCK.
3. **Zalo:** đăng ký Zalo OA, backend gọi API gửi tin; chỉnh `integrations/zalo.js`.
4. **Dữ liệu:** hiện lưu trong trình duyệt (chỉ máy bạn thấy). Khi lên web thật cần database (Supabase/Firebase) → sửa `js/store.js`. PIN admin hiện chỉ là tạm, cần đăng nhập thật phía server.
