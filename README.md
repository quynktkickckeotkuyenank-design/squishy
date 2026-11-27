# Squishy Dream Shop

Web bán squishy: giỏ hàng, QR VietQR tự gắn số tiền, nhập địa chỉ ship sau khi đặt, quản trị sản phẩm/đơn,
tiền cân (mặc định 4k/sản phẩm, hàng > 1kg thì hỏi mức riêng), thông báo sản phẩm sau 7 ngày chỉ bán được 1.

## Chạy thử trên máy
    pip install -r requirements.txt
    python app.py
Admin: /admin (mật khẩu mặc định `squishy123`, chỉ dùng khi chạy thử).

## Biến môi trường khi chạy public
| Biến | Ý nghĩa |
|---|---|
| `PRODUCTION=1` | bật chế độ public (bắt buộc đổi 2 biến dưới) |
| `SECRET_KEY` | chuỗi ngẫu nhiên dài |
| `ADMIN_PASSWORD` | mật khẩu trang quản trị |
| `DATA_DIR` | thư mục BỀN VỮNG chứa `shop.db` và `uploads/` |

## Lưu ý
- Database là SQLite + ảnh lưu trên đĩa: hosting phải có ổ đĩa bền vững, nếu không mất dữ liệu mỗi lần deploy.
- Đổi thông tin ngân hàng ở đầu `app.py` (BANK_*).
