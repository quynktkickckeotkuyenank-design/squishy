"""Squishy Dream Shop - Flask app (MVP).
Chạy:  pip install -r requirements.txt  &&  python app.py
Mở:    http://127.0.0.1:5000      Admin: http://127.0.0.1:5000/admin
"""
import os, re, io, uuid, secrets, sqlite3, unicodedata
from datetime import datetime, timedelta
from functools import wraps
from flask import (Flask, g, send_from_directory, render_template, request, redirect, url_for,
                   session, flash, abort, Response)

try:
    import qrcode, qrcode.image.svg
except ImportError:  # chưa cài thư viện qrcode
    qrcode = None

BASE = os.path.dirname(os.path.abspath(__file__))
# Nơi lưu database + ảnh. Khi deploy: trỏ DATA_DIR tới ổ đĩa bền vững (vd /var/data)
DATA_DIR = os.environ.get("DATA_DIR", BASE)
DB_PATH = os.path.join(DATA_DIR, "shop.db")
UPLOAD = os.path.join(DATA_DIR, "uploads")
os.makedirs(UPLOAD, exist_ok=True)
FMT = "%Y-%m-%d %H:%M:%S"

# ====== THÔNG TIN NGÂN HÀNG (VietQR) ======
BANK_BIN = "970418"            # BIDV
BANK_ACCOUNT = "8800067380"
BANK_OWNER = "LE NGOC QUYNH ANH"
BANK_NAME = "BIDV - PGD Văn Thánh"

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "doi-key-nay-khi-deploy")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "squishy123")  # NHỚ ĐỔI
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax",
                  SESSION_COOKIE_SECURE=os.environ.get("PRODUCTION") == "1")
if os.environ.get("PRODUCTION") == "1" and (
        app.secret_key == "doi-key-nay-khi-deploy" or ADMIN_PASSWORD == "squishy123"):
    raise RuntimeError("Chạy public phải đặt biến môi trường SECRET_KEY và ADMIN_PASSWORD (khác mặc định).")

@app.route("/uploads/<path:name>")
def uploaded(name):
    return send_from_directory(UPLOAD, name)

STATUSES = {
    "pending": "Chờ thanh toán", "paid": "Đã thanh toán", "processing": "Đang xử lý",
    "shipped": "Đã gửi hàng", "done": "Hoàn tất", "cancelled": "Đã hủy",
}

# ====================== DATABASE ======================
def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(_):
    d = g.pop("db", None)
    if d: d.close()

def init_db():
    c = sqlite3.connect(DB_PATH)
    c.executescript("""
    CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT);
    CREATE TABLE IF NOT EXISTS products(
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, sku TEXT, description TEXT,
        image TEXT, cny REAL, type TEXT DEFAULT 'instock', stock INTEGER DEFAULT 0,
        weight REAL DEFAULT 0, surcharge INTEGER DEFAULT 4000, price INTEGER DEFAULT 0,
        link TEXT, active INTEGER DEFAULT 1, created_at TEXT);
    CREATE TABLE IF NOT EXISTS orders(
        id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT UNIQUE,
        buyer_name TEXT, buyer_phone TEXT,
        ship_name TEXT, ship_phone TEXT, ship_address TEXT,
        total INTEGER, status TEXT DEFAULT 'pending', created_at TEXT);
    CREATE TABLE IF NOT EXISTS order_items(
        id INTEGER PRIMARY KEY AUTOINCREMENT, order_id INTEGER, product_id INTEGER,
        name TEXT, qty INTEGER, unit_price INTEGER);
    CREATE TABLE IF NOT EXISTS dismissed(product_id INTEGER, order_id INTEGER,
        PRIMARY KEY(product_id, order_id));
    """)
    defaults = {"cny_rate": "4000", "markup_percent": "120", "default_surcharge": "4000",
                "heavy_kg": "1", "shop_name": "Squishy Dream Shop"}
    for k, v in defaults.items():
        c.execute("INSERT OR IGNORE INTO settings VALUES(?,?)", (k, v))
    c.commit(); c.close()

def setting(key, cast=str):
    r = db().execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    return cast(r["value"]) if r else None

def base_price(cny):
    """Giá bán cơ bản = Giá nhập (¥) × 4.000đ × 120% (chỉnh trong Cài đặt). VD 10¥ -> 48.000đ."""
    return round(cny * setting("cny_rate", float) * setting("markup_percent", float) / 100)

def unit_price(p):
    return int(p["price"])  # = giá cơ bản + tiền cân (đã lưu sẵn)

@app.template_filter("vnd")
def vnd(n):
    return f"{int(n or 0):,}".replace(",", ".") + "đ"

@app.context_processor
def inject():
    cart = session.get("cart", {})
    n_alerts = len(low_sales_alerts()) if session.get("admin") else 0
    return dict(cart_count=sum(cart.values()), STATUSES=STATUSES, n_alerts=n_alerts,
                shop_name=setting("shop_name") or "Squishy Dream Shop",
                BANK_NAME=BANK_NAME, BANK_ACCOUNT=BANK_ACCOUNT, BANK_OWNER=BANK_OWNER)

# ====================== VIETQR ======================
def _tlv(i, v): return f"{i}{len(v):02d}{v}"

def crc16(s):
    crc = 0xFFFF
    for ch in s.encode():
        crc ^= ch << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return f"{crc:04X}"

def vietqr_payload(amount, memo):
    """Chuỗi VietQR (EMVCo) đã gắn sẵn số tiền + nội dung chuyển khoản."""
    consumer = _tlv("00", BANK_BIN) + _tlv("01", BANK_ACCOUNT)
    mai = _tlv("00", "A000000727") + _tlv("01", consumer) + _tlv("02", "QRIBFTTA")
    s = (_tlv("00", "01") + _tlv("01", "12") + _tlv("38", mai) + _tlv("53", "704")
         + _tlv("54", str(int(amount))) + _tlv("58", "VN") + _tlv("62", _tlv("08", memo)) + "6304")
    return s + crc16(s)

@app.route("/qr/<code>.svg")
def qr(code):
    o = db().execute("SELECT * FROM orders WHERE code=?", (code,)).fetchone() or abort(404)
    if qrcode is None:
        abort(500, "Chưa cài thư viện qrcode: pip install qrcode")
    img = qrcode.make(vietqr_payload(o["total"], o["code"]), box_size=10, border=2,
                      image_factory=qrcode.image.svg.SvgPathImage)
    buf = io.BytesIO(); img.save(buf)
    return Response(buf.getvalue(), mimetype="image/svg+xml")

# ====================== KHÁCH HÀNG ======================
@app.route("/")
def index():
    t = request.args.get("type")
    q = "SELECT * FROM products WHERE active=1"
    args = []
    if t in ("instock", "preorder"):
        q += " AND type=?"; args.append(t)
    return render_template("index.html", products=db().execute(q + " ORDER BY id DESC", args).fetchall(), t=t)

@app.route("/p/<int:pid>")
def product(pid):
    p = db().execute("SELECT * FROM products WHERE id=? AND active=1", (pid,)).fetchone() or abort(404)
    return render_template("product.html", p=p)

@app.route("/cart/add", methods=["POST"])
def cart_add():
    pid, qty = request.form.get("pid", ""), max(1, int(request.form.get("qty", 1) or 1))
    cart = session.get("cart", {}); cart[pid] = cart.get(pid, 0) + qty
    session["cart"] = cart
    flash("Đã thêm vào giỏ hàng ✨")
    return redirect(request.referrer or url_for("index"))

def cart_lines():
    lines, total = [], 0
    for pid, qty in session.get("cart", {}).items():
        p = db().execute("SELECT * FROM products WHERE id=? AND active=1", (pid,)).fetchone()
        if p:
            lines.append(dict(p=p, qty=qty, sub=unit_price(p) * qty)); total += unit_price(p) * qty
    return lines, total

@app.route("/cart", methods=["GET", "POST"])
def cart():
    if request.method == "POST":  # cập nhật số lượng
        cart = {}
        for k, v in request.form.items():
            if k.startswith("q_") and v.isdigit() and int(v) > 0:
                cart[k[2:]] = int(v)
        session["cart"] = cart
        return redirect(url_for("cart"))
    lines, total = cart_lines()
    return render_template("cart.html", lines=lines, total=total)

def new_code():
    while True:
        c = "SQ" + "".join(secrets.choice("ABCDEFGHJKLMNPQRSTUVWXYZ23456789") for _ in range(6))
        if not db().execute("SELECT 1 FROM orders WHERE code=?", (c,)).fetchone():
            return c

@app.route("/checkout", methods=["POST"])
def checkout():
    lines, total = cart_lines()
    name, phone = request.form.get("name", "").strip(), request.form.get("phone", "").strip()
    if not lines or not name or not re.fullmatch(r"[0-9+ ]{9,13}", phone):
        flash("Vui lòng nhập tên và số điện thoại hợp lệ."); return redirect(url_for("cart"))
    d = db()
    for l in lines:  # kiểm tra tồn kho hàng có sẵn
        p = l["p"]
        if p["type"] == "instock" and l["qty"] > p["stock"]:
            flash(f"'{p['name']}' chỉ còn {p['stock']} chiếc."); return redirect(url_for("cart"))
    code = new_code()
    cur = d.execute("INSERT INTO orders(code,buyer_name,buyer_phone,ship_name,ship_phone,ship_address,total,created_at)"
                    " VALUES(?,?,?,?,?,?,?,?)", (code, name, phone, name, phone, "", total, datetime.now().strftime(FMT)))
    for l in lines:
        p = l["p"]
        d.execute("INSERT INTO order_items(order_id,product_id,name,qty,unit_price) VALUES(?,?,?,?,?)",
                  (cur.lastrowid, p["id"], p["name"], l["qty"], unit_price(p)))
        if p["type"] == "instock":
            d.execute("UPDATE products SET stock=stock-? WHERE id=?", (l["qty"], p["id"]))
    d.commit(); session["cart"] = {}
    return redirect(url_for("order", code=code))

def get_order(code):
    o = db().execute("SELECT * FROM orders WHERE code=?", (code,)).fetchone() or abort(404)
    items = db().execute("SELECT * FROM order_items WHERE order_id=?", (o["id"],)).fetchall()
    return o, items

@app.route("/order/<code>")
def order(code):
    o, items = get_order(code)
    return render_template("order.html", o=o, items=items)

@app.route("/order/<code>/ship", methods=["POST"])
def order_ship(code):
    o, _ = get_order(code)
    if o["status"] in ("shipped", "done", "cancelled"):
        flash("Đơn đã gửi/hủy nên không sửa được thông tin nữa."); return redirect(url_for("order", code=code))
    n, p, a = (request.form.get(k, "").strip() for k in ("ship_name", "ship_phone", "ship_address"))
    if not (n and a and re.fullmatch(r"[0-9+ ]{9,13}", p)):
        flash("Vui lòng nhập đủ tên người nhận, SĐT và địa chỉ."); return redirect(url_for("order", code=code))
    db().execute("UPDATE orders SET ship_name=?,ship_phone=?,ship_address=? WHERE id=?", (n, p, a, o["id"]))
    db().commit(); flash("Đã lưu thông tin nhận hàng 💌")
    return redirect(url_for("order", code=code))

@app.route("/track", methods=["GET", "POST"])
def track():
    if request.method == "POST":
        code, phone = request.form.get("code", "").strip().upper(), request.form.get("phone", "").strip()
        o = db().execute("SELECT code FROM orders WHERE code=? AND (buyer_phone=? OR ship_phone=?)",
                         (code, phone, phone)).fetchone()
        if o: return redirect(url_for("order", code=o["code"]))
        flash("Không tìm thấy đơn, kiểm tra lại mã đơn và SĐT nha.")
    return render_template("track.html")

# ====================== ADMIN ======================
def admin_required(f):
    @wraps(f)
    def w(*a, **k):
        if not session.get("admin"): return redirect(url_for("admin_login"))
        return f(*a, **k)
    return w

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if secrets.compare_digest(request.form.get("password", ""), ADMIN_PASSWORD):
            session["admin"] = True; return redirect(url_for("admin"))
        flash("Sai mật khẩu.")
    return render_template("admin_login.html")

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None); return redirect(url_for("index"))

def low_sales_alerts():
    """Sản phẩm đăng ≥ 7 ngày mà trong 7 ngày qua chỉ bán được đúng 1 chiếc
    -> báo để chủ shop nhắn khách (qua web báo cáo)."""
    cut = (datetime.now() - timedelta(days=7)).strftime(FMT)
    rows = db().execute("""
        SELECT p.id pid, p.name pname FROM products p
        JOIN order_items oi ON oi.product_id=p.id JOIN orders o ON o.id=oi.order_id
        WHERE o.status!='cancelled' AND o.created_at>=? AND p.created_at<=?
        GROUP BY p.id HAVING SUM(oi.qty)=1""", (cut, cut)).fetchall()
    out = []
    for r in rows:
        o = db().execute("""SELECT o.id oid,o.code,o.buyer_name,o.buyer_phone,o.ship_name,o.ship_phone
            FROM orders o JOIN order_items oi ON oi.order_id=o.id
            WHERE oi.product_id=? AND o.status!='cancelled' AND o.created_at>=?""", (r["pid"], cut)).fetchone()
        if o and not db().execute("SELECT 1 FROM dismissed WHERE product_id=? AND order_id=?",
                                  (r["pid"], o["oid"])).fetchone():
            out.append(dict(r) | dict(o))
    return out

@app.route("/admin")
@admin_required
def admin():
    d = db()
    stats = dict(
        orders=d.execute("SELECT COUNT(*) FROM orders WHERE status!='cancelled'").fetchone()[0],
        revenue=d.execute("SELECT COALESCE(SUM(total),0) FROM orders WHERE status IN ('paid','processing','shipped','done')").fetchone()[0],
        pending=d.execute("SELECT COUNT(*) FROM orders WHERE status='pending'").fetchone()[0])
    return render_template("admin.html", alerts=low_sales_alerts(), stats=stats)

@app.route("/admin/alert/dismiss", methods=["POST"])
@admin_required
def alert_dismiss():
    db().execute("INSERT OR IGNORE INTO dismissed VALUES(?,?)", (request.form["pid"], request.form["oid"]))
    db().commit(); return redirect(url_for("admin"))

@app.route("/admin/products")
@admin_required
def admin_products():
    return render_template("admin_products.html", products=db().execute("SELECT * FROM products ORDER BY id DESC").fetchall())

@app.route("/admin/products/new", methods=["GET", "POST"])
@app.route("/admin/products/<int:pid>", methods=["GET", "POST"])
@admin_required
def admin_product(pid=None):
    d = db()
    p = d.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone() if pid else None
    heavy = setting("heavy_kg", float)
    if request.method == "POST":
        f = request.form
        try:
            cny, weight = float(f["cny"]), float(f.get("weight") or 0)
            stock = int(f.get("stock") or 0)
            sur = f.get("surcharge", "").strip()
            sur = int(sur) if sur else setting("default_surcharge", int)
        except ValueError:
            flash("Giá Tệ / khối lượng / tồn kho không hợp lệ."); return redirect(request.url)
        if weight > heavy and not f.get("surcharge", "").strip():
            flash(f"Sản phẩm nặng hơn {heavy:g}kg: nhập tiền cân cộng thêm cho mỗi sản phẩm."); return redirect(request.url)
        price = base_price(cny) + sur
        img = p["image"] if p else ""
        file = request.files.get("image")
        if file and file.filename:
            ext = os.path.splitext(file.filename)[1].lower()
            if ext not in (".jpg", ".jpeg", ".png", ".webp", ".gif"):
                flash("Chỉ nhận ảnh jpg/png/webp/gif."); return redirect(request.url)
            img = uuid.uuid4().hex + ext; file.save(os.path.join(UPLOAD, img))
        vals = (f["name"], f.get("sku", ""), f.get("description", ""), img, cny, f.get("type", "instock"),
                stock, weight, sur, price, f.get("link", ""), 1 if f.get("active") else 0)
        if p:
            d.execute("UPDATE products SET name=?,sku=?,description=?,image=?,cny=?,type=?,stock=?,weight=?,surcharge=?,price=?,link=?,active=? WHERE id=?", vals + (pid,))
        else:
            d.execute("INSERT INTO products(name,sku,description,image,cny,type,stock,weight,surcharge,price,link,active,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                      vals + (datetime.now().strftime(FMT),))
        d.commit(); flash("Đã lưu sản phẩm ✨")
        return redirect(url_for("admin_products"))
    return render_template("admin_product.html", p=p, heavy=heavy,
                           rate=setting("cny_rate", float), markup=setting("markup_percent", float),
                           default_sur=setting("default_surcharge", int))

@app.route("/admin/products/<int:pid>/delete", methods=["POST"])
@admin_required
def admin_product_delete(pid):
    db().execute("UPDATE products SET active=0 WHERE id=?", (pid,)); db().commit()
    flash("Đã ẩn sản phẩm."); return redirect(url_for("admin_products"))

@app.route("/admin/orders")
@admin_required
def admin_orders():
    orders = db().execute("SELECT * FROM orders ORDER BY id DESC").fetchall()
    items = {}
    for it in db().execute("SELECT * FROM order_items").fetchall():
        items.setdefault(it["order_id"], []).append(it)
    return render_template("admin_orders.html", orders=orders, items=items)

@app.route("/admin/orders/<int:oid>/status", methods=["POST"])
@admin_required
def admin_order_status(oid):
    st = request.form.get("status")
    if st not in STATUSES: abort(400)
    d = db(); o = d.execute("SELECT * FROM orders WHERE id=?", (oid,)).fetchone() or abort(404)
    if st == "cancelled" and o["status"] != "cancelled":  # trả lại tồn kho hàng có sẵn
        for it in d.execute("SELECT oi.* FROM order_items oi JOIN products p ON p.id=oi.product_id WHERE oi.order_id=? AND p.type='instock'", (oid,)):
            d.execute("UPDATE products SET stock=stock+? WHERE id=?", (it["qty"], it["product_id"]))
    d.execute("UPDATE orders SET status=? WHERE id=?", (st, oid)); d.commit()
    return redirect(url_for("admin_orders"))

@app.route("/admin/settings", methods=["GET", "POST"])
@admin_required
def admin_settings():
    d = db()
    if request.method == "POST":
        for k in ("cny_rate", "markup_percent", "default_surcharge", "heavy_kg", "shop_name"):
            d.execute("UPDATE settings SET value=? WHERE key=?", (request.form[k], k))
        d.commit()
        if request.form.get("recalc"):  # tính lại giá toàn bộ sản phẩm
            for p in d.execute("SELECT * FROM products").fetchall():
                d.execute("UPDATE products SET price=? WHERE id=?", (base_price(p["cny"]) + p["surcharge"], p["id"]))
            d.commit()
        flash("Đã lưu cài đặt."); return redirect(url_for("admin_settings"))
    s = {r["key"]: r["value"] for r in d.execute("SELECT * FROM settings")}
    return render_template("admin_settings.html", s=s)

init_db()
if __name__ == "__main__":
    app.run(debug=True)
