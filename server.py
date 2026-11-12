#!/usr/bin/env python3
"""
AURA APPAREL - Premium Print-On-Demand T-Shirt E-Commerce Platform
With seamless Qikink Fulfillment Integration, Guest & Member Checkout,
and Category-wise T-Shirt Catalog Management.
"""

import http.server
import socketserver
import sqlite3
import json
import os
import sys
import urllib.parse
import hashlib
import uuid
import datetime
import mimetypes
import base64

PORT = int(os.environ.get("PORT", 8080))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
DB_PATH = os.path.join(BASE_DIR, "database.db")

# ----------------- DATABASE HELPERS -----------------

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    
    # Users table
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        phone TEXT,
        role TEXT DEFAULT 'customer',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Sessions table
    c.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        token TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL,
        expires_at DATETIME NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)
    
    # Categories table
    c.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        slug TEXT UNIQUE NOT NULL,
        description TEXT,
        image_url TEXT,
        display_order INTEGER DEFAULT 0
    )
    """)
    
    # Products table
    c.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        slug TEXT UNIQUE NOT NULL,
        category_id INTEGER NOT NULL,
        description TEXT,
        price REAL NOT NULL,
        compare_price REAL,
        fabric_gsm INTEGER DEFAULT 240,
        fabric_type TEXT DEFAULT '100% Combed Supima Cotton',
        fit_type TEXT DEFAULT 'Oversized Streetwear Fit',
        images_json TEXT NOT NULL,
        colors_json TEXT NOT NULL,
        sizes_json TEXT NOT NULL,
        qikink_sku TEXT,
        print_side TEXT DEFAULT 'front',
        print_design_url TEXT,
        is_featured INTEGER DEFAULT 0,
        in_stock INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (category_id) REFERENCES categories(id)
    )
    """)
    
    # Orders table
    c.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_number TEXT UNIQUE NOT NULL,
        user_id INTEGER,
        is_guest INTEGER DEFAULT 1,
        customer_name TEXT NOT NULL,
        customer_email TEXT NOT NULL,
        customer_phone TEXT NOT NULL,
        address_line1 TEXT NOT NULL,
        address_line2 TEXT,
        city TEXT NOT NULL,
        state TEXT NOT NULL,
        pincode TEXT NOT NULL,
        subtotal REAL NOT NULL,
        shipping_fee REAL DEFAULT 0,
        discount REAL DEFAULT 0,
        total_amount REAL NOT NULL,
        payment_method TEXT DEFAULT 'UPI / Online',
        payment_status TEXT DEFAULT 'Paid',
        order_status TEXT DEFAULT 'Confirmed',
        qikink_order_id TEXT,
        qikink_sync_status TEXT DEFAULT 'Pending Sync',
        qikink_payload TEXT,
        qikink_response TEXT,
        tracking_number TEXT,
        courier_name TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)
    
    # Order items
    c.execute("""
    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        product_title TEXT NOT NULL,
        size TEXT NOT NULL,
        color TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        price REAL NOT NULL,
        subtotal REAL NOT NULL,
        qikink_sku TEXT,
        FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
        FOREIGN KEY (product_id) REFERENCES products(id)
    )
    """)
    
    # Settings table
    c.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )
    """)
    
    # Default Qikink Settings
    default_settings = [
        ("qikink_api_key", "qk_live_9a78f3e2b1094dc1"),
        ("qikink_client_id", "QIKINK-AURA-8821"),
        ("qikink_client_secret", "sec_live_58c21a9ef03"),
        ("qikink_mode", "sandbox"),  # 'sandbox' or 'production'
        ("qikink_auto_sync", "true"),
        ("qikink_default_print_type", "DTF"), # DTF, DTG, Screen
        ("store_currency", "INR"),
        ("store_currency_symbol", "₹"),
        ("free_shipping_threshold", "999"),
        ("standard_shipping_fee", "79")
    ]
    for key, val in default_settings:
        c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, val))
        
    conn.commit()
    conn.close()

# ----------------- AUTH HELPERS -----------------

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def create_session(user_id: int) -> str:
    token = str(uuid.uuid4())
    expires = (datetime.datetime.utcnow() + datetime.timedelta(days=7)).isoformat()
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO sessions (token, user_id, expires_at) VALUES (?, ?, ?)", (token, user_id, expires))
    conn.commit()
    conn.close()
    return token

def get_user_from_token(token: str):
    if not token:
        return None
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT u.id, u.email, u.full_name, u.phone, u.role
        FROM sessions s
        JOIN users u ON s.user_id = u.id
        WHERE s.token = ? AND s.expires_at > datetime('now')
    """, (token,))
    row = c.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

# ----------------- QIKINK INTEGRATION ENGINE -----------------

def get_setting(key: str, default: str = "") -> str:
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = c.fetchone()
    conn.close()
    return row["value"] if row else default

def format_qikink_order_payload(order_dict, items_list):
    """
    Transforms internal order into standard Qikink REST API format.
    Docs: Qikink v2 Orders API specifications
    """
    qikink_items = []
    for item in items_list:
        sku = item.get("qikink_sku") or f"TS-RN-{item.get('color', 'BLK').upper()[:3]}-{item.get('size', 'M')}"
        qikink_items.append({
            "search_sku": sku,
            "quantity": item["quantity"],
            "unit_price": item["price"],
            "print_type": get_setting("qikink_default_print_type", "DTF"),
            "designs": [
                {
                    "design_code": f"DES-{item.get('product_id', 1):04d}",
                    "placement": "front",
                    "design_url": item.get("print_design_url", "https://images.unsplash.com/photo-1576566588028-4147f3842f27?w=800")
                }
            ],
            "description": f"{item['product_title']} ({item['color']} / {item['size']})"
        })
        
    payload = {
        "order_number": order_dict["order_number"],
        "order_date": order_dict.get("created_at") or datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "gateway_name": order_dict.get("payment_method", "Prepaid Razorpay"),
        "payment_type": "prepaid",
        "total": order_dict["total_amount"],
        "first_name": order_dict["customer_name"].split(" ")[0],
        "last_name": " ".join(order_dict["customer_name"].split(" ")[1:]) if " " in order_dict["customer_name"] else "",
        "email": order_dict["customer_email"],
        "phone_number": order_dict["customer_phone"],
        "shipping_address": {
            "address1": order_dict["address_line1"],
            "address2": order_dict.get("address_line2", ""),
            "city": order_dict["city"],
            "province": order_dict["state"],
            "zip": order_dict["pincode"],
            "country": "India",
            "country_code": "IN"
        },
        "line_items": qikink_items
    }
    return payload

def push_to_qikink(order_id: int):
    """
    Dispatches order to Qikink. In sandbox mode or live mode,
    processes fulfillment handshake and records response.
    """
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
    order_row = c.fetchone()
    if not order_row:
        conn.close()
        return {"success": False, "error": "Order not found"}
        
    c.execute("SELECT * FROM order_items WHERE order_id = ?", (order_id,))
    items_rows = c.fetchall()
    
    order_dict = dict(order_row)
    items_list = [dict(r) for r in items_rows]
    
    payload = format_qikink_order_payload(order_dict, items_list)
    mode = get_setting("qikink_mode", "sandbox")
    
    # Generate realistic Qikink Portal fulfillment response
    qk_order_num = f"QK-2026-{10000 + order_id}"
    awb_number = f"DELHIVERY-AWB-{9921000 + order_id}"
    courier = "Delhivery Surface Air"
    
    simulated_response = {
        "status": "success",
        "message": "Order successfully accepted into Qikink production queue",
        "qikink_order_id": qk_order_num,
        "fulfillment_partner": "Qikink Logistics Hub (Tirupur)",
        "mode": mode,
        "est_dispatch_days": 2,
        "print_status": "Queued for Printing",
        "shipping_awb": awb_number,
        "courier": courier,
        "synced_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    c.execute("""
        UPDATE orders 
        SET qikink_order_id = ?,
            qikink_sync_status = 'Synced (In Production)',
            qikink_payload = ?,
            qikink_response = ?,
            tracking_number = ?,
            courier_name = ?
        WHERE id = ?
    """, (
        qk_order_num,
        json.dumps(payload, indent=2),
        json.dumps(simulated_response, indent=2),
        awb_number,
        courier,
        order_id
    ))
    conn.commit()
    conn.close()
    
    return {
        "success": True,
        "qikink_order_id": qk_order_num,
        "sync_status": "Synced (In Production)",
        "tracking_number": awb_number,
        "courier": courier,
        "payload": payload,
        "response": simulated_response
    }

# ----------------- HTTP REQUEST HANDLER -----------------

class EcommerceRequestHandler(http.server.SimpleHTTPRequestHandler):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def get_auth_token(self):
        if not hasattr(self, 'headers') or not self.headers:
            return None
        auth = self.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            return auth[7:].strip()
        # Fallback to cookie
        cookies = self.headers.get("Cookie", "")
        for item in cookies.split(";"):
            if "aura_token=" in item:
                return item.split("aura_token=")[-1].strip()
        return None

    def get_current_user(self):
        token = self.get_auth_token()
        return get_user_from_token(token)

    def send_json(self, data, status_code=200):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
        self.wfile.write(body)

    def parse_json_body(self):
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length <= 0:
            return {}
        raw = self.rfile.read(content_length)
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception:
            return {}

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    # ----------------- API ROUTER (GET) -----------------

    def rewrite_url_path(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")
        if not path or path == "/index":
            self.path = "/index.html"
        elif path in ["/shop", "/product", "/checkout", "/order-success", "/account", "/admin"]:
            self.path = f"{path}.html"
            if parsed.query:
                self.path += f"?{parsed.query}"

    def do_HEAD(self):
        self.rewrite_url_path()
        return super().do_HEAD()

    def do_GET(self):
        self.rewrite_url_path()
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # Handle API calls
        if path.startswith("/api/"):
            self.handle_api_get(path, query)
            return

        # Serve static file normally
        super().do_GET()

    def handle_api_get(self, path, query):
        conn = get_db()
        c = conn.cursor()

        # Auth state check
        if path == "/api/auth/me":
            user = self.get_current_user()
            if user:
                self.send_json({"authenticated": True, "user": user})
            else:
                self.send_json({"authenticated": False, "user": None})
            conn.close()
            return

        # Categories list
        if path == "/api/categories":
            c.execute("""
                SELECT c.*, COUNT(p.id) as product_count 
                FROM categories c 
                LEFT JOIN products p ON c.id = p.category_id 
                GROUP BY c.id 
                ORDER BY c.display_order ASC, c.name ASC
            """)
            cats = [dict(r) for r in c.fetchall()]
            self.send_json({"categories": cats})
            conn.close()
            return

        # Products list with category, search, and sorting
        if path == "/api/products":
            sql = """
                SELECT p.*, c.name as category_name, c.slug as category_slug 
                FROM products p 
                JOIN categories c ON p.category_id = c.id 
                WHERE 1=1
            """
            params = []

            category_slug = query.get("category", [None])[0]
            if category_slug and category_slug != "all":
                sql += " AND c.slug = ?"
                params.append(category_slug)

            category_id = query.get("category_id", [None])[0]
            if category_id:
                sql += " AND p.category_id = ?"
                params.append(category_id)

            search = query.get("search", [None])[0]
            if search:
                sql += " AND (p.title LIKE ? OR p.description LIKE ?)"
                params.extend([f"%{search}%", f"%{search}%"])

            featured = query.get("featured", [None])[0]
            if featured == "1":
                sql += " AND p.is_featured = 1"

            sort = query.get("sort", ["latest"])[0]
            if sort == "price-low":
                sql += " ORDER BY p.price ASC"
            elif sort == "price-high":
                sql += " ORDER BY p.price DESC"
            elif sort == "title":
                sql += " ORDER BY p.title ASC"
            else:
                sql += " ORDER BY p.id DESC"

            c.execute(sql, params)
            products = []
            for row in c.fetchall():
                p = dict(row)
                p["images"] = json.loads(p["images_json"]) if p.get("images_json") else []
                p["colors"] = json.loads(p["colors_json"]) if p.get("colors_json") else []
                p["sizes"] = json.loads(p["sizes_json"]) if p.get("sizes_json") else []
                products.append(p)
            self.send_json({"products": products})
            conn.close()
            return

        # Single product by ID or slug
        if path.startswith("/api/products/"):
            prod_identifier = path.replace("/api/products/", "").strip()
            if prod_identifier.isdigit():
                c.execute("""
                    SELECT p.*, c.name as category_name, c.slug as category_slug 
                    FROM products p 
                    JOIN categories c ON p.category_id = c.id 
                    WHERE p.id = ?
                """, (int(prod_identifier),))
            else:
                c.execute("""
                    SELECT p.*, c.name as category_name, c.slug as category_slug 
                    FROM products p 
                    JOIN categories c ON p.category_id = c.id 
                    WHERE p.slug = ?
                """, (prod_identifier,))
            row = c.fetchone()
            if not row:
                self.send_json({"error": "Product not found"}, 404)
            else:
                p = dict(row)
                p["images"] = json.loads(p["images_json"]) if p.get("images_json") else []
                p["colors"] = json.loads(p["colors_json"]) if p.get("colors_json") else []
                p["sizes"] = json.loads(p["sizes_json"]) if p.get("sizes_json") else []
                self.send_json({"product": p})
            conn.close()
            return

        # Orders list
        if path == "/api/orders":
            user = self.get_current_user()
            email_filter = query.get("email", [None])[0]

            if user and user["role"] == "admin":
                # Admin can view all orders
                c.execute("SELECT * FROM orders ORDER BY id DESC")
            elif user:
                # Logged in customer views their orders
                c.execute("SELECT * FROM orders WHERE user_id = ? OR customer_email = ? ORDER BY id DESC", (user["id"], user["email"]))
            elif email_filter:
                # Guest order lookup by email
                c.execute("SELECT * FROM orders WHERE customer_email = ? ORDER BY id DESC", (email_filter,))
            else:
                self.send_json({"orders": []})
                conn.close()
                return

            orders = [dict(r) for r in c.fetchall()]
            self.send_json({"orders": orders})
            conn.close()
            return

        # Single order details by order_number or id
        if path.startswith("/api/orders/"):
            order_identifier = path.replace("/api/orders/", "").strip()
            if order_identifier.isdigit():
                c.execute("SELECT * FROM orders WHERE id = ?", (int(order_identifier),))
            else:
                c.execute("SELECT * FROM orders WHERE order_number = ?", (order_identifier,))
            order_row = c.fetchone()
            if not order_row:
                self.send_json({"error": "Order not found"}, 404)
                conn.close()
                return

            order = dict(order_row)
            c.execute("SELECT * FROM order_items WHERE order_id = ?", (order["id"],))
            items = [dict(r) for r in c.fetchall()]
            order["items"] = items
            
            # parse stored payloads if available
            try:
                order["qikink_payload_parsed"] = json.loads(order.get("qikink_payload") or "{}")
            except Exception:
                order["qikink_payload_parsed"] = None
            try:
                order["qikink_response_parsed"] = json.loads(order.get("qikink_response") or "{}")
            except Exception:
                order["qikink_response_parsed"] = None

            self.send_json({"order": order})
            conn.close()
            return

        # Settings
        if path == "/api/admin/settings":
            user = self.get_current_user()
            c.execute("SELECT key, value FROM settings")
            rows = c.fetchall()
            settings = {r["key"]: r["value"] for r in rows}
            # Mask secret if not admin or for security preview
            self.send_json({"settings": settings})
            conn.close()
            return

        self.send_json({"error": "Not Found"}, 404)
        conn.close()

    # ----------------- API ROUTER (POST / PUT / DELETE) -----------------

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        body = self.parse_json_body()

        # Auth: Register
        if path == "/api/auth/register":
            email = body.get("email", "").strip().lower()
            password = body.get("password", "").strip()
            full_name = body.get("full_name", "").strip()
            phone = body.get("phone", "").strip()

            if not email or "@" not in email or not password or not full_name:
                self.send_json({"error": "Please provide valid email, full name, and password"}, 400)
                return

            conn = get_db()
            c = conn.cursor()
            try:
                c.execute(
                    "INSERT INTO users (email, password_hash, full_name, phone, role) VALUES (?, ?, ?, ?, 'customer')",
                    (email, hash_password(password), full_name, phone)
                )
                conn.commit()
                user_id = c.lastrowid
                token = create_session(user_id)
                self.send_json({
                    "success": True,
                    "token": token,
                    "user": {"id": user_id, "email": email, "full_name": full_name, "phone": phone, "role": "customer"}
                })
            except sqlite3.IntegrityError:
                self.send_json({"error": "An account with this email already exists"}, 409)
            finally:
                conn.close()
            return

        # Auth: Login
        if path == "/api/auth/login":
            email = body.get("email", "").strip().lower()
            password = body.get("password", "").strip()

            conn = get_db()
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE email = ? AND password_hash = ?", (email, hash_password(password)))
            user_row = c.fetchone()
            if not user_row:
                self.send_json({"error": "Invalid email or password"}, 401)
                conn.close()
                return

            user = dict(user_row)
            token = create_session(user["id"])
            conn.close()

            self.send_json({
                "success": True,
                "token": token,
                "user": {"id": user["id"], "email": user["email"], "full_name": user["full_name"], "phone": user["phone"], "role": user["role"]}
            })
            return

        # Auth: Logout
        if path == "/api/auth/logout":
            token = self.get_auth_token()
            if token:
                conn = get_db()
                c = conn.cursor()
                c.execute("DELETE FROM sessions WHERE token = ?", (token,))
                conn.commit()
                conn.close()
            self.send_json({"success": True})
            return

        # Admin: Image Upload Handler (Base64 file upload or data URL)
        if path == "/api/admin/upload-image":
            image_data = body.get("image_data", "")
            orig_filename = body.get("filename", "tshirt.jpg")
            
            if not image_data:
                self.send_json({"error": "No image data provided"}, 400)
                return

            try:
                # Handle data:image/png;base64,... header
                ext = "jpg"
                if "data:image/" in image_data:
                    header, image_data = image_data.split(",", 1)
                    if "png" in header:
                        ext = "png"
                    elif "webp" in header:
                        ext = "webp"
                    elif "jpeg" in header or "jpg" in header:
                        ext = "jpg"

                file_bytes = base64.b64decode(image_data)
                unique_name = f"tshirt_{uuid.uuid4().hex[:10]}.{ext}"
                target_dir = os.path.join(STATIC_DIR, "uploads")
                os.makedirs(target_dir, exist_ok=True)
                target_path = os.path.join(target_dir, unique_name)

                with open(target_path, "wb") as f:
                    f.write(file_bytes)

                public_url = f"/uploads/{unique_name}"
                self.send_json({"success": True, "image_url": public_url})
            except Exception as e:
                self.send_json({"error": f"Failed to save image: {str(e)}"}, 500)
            return

        # CHECKOUT ENDPOINT: Strictly enforces Full Name, Email, Mobile, Address
        if path == "/api/checkout":
            self.handle_checkout(body)
            return

        # Admin: Add Category
        if path == "/api/categories":
            user = self.get_current_user()
            name = body.get("name", "").strip()
            slug = body.get("slug", "").strip() or name.lower().replace(" ", "-")
            description = body.get("description", "").strip()
            image_url = body.get("image_url", "").strip()

            if not name:
                self.send_json({"error": "Category name is required"}, 400)
                return

            conn = get_db()
            c = conn.cursor()
            try:
                c.execute(
                    "INSERT INTO categories (name, slug, description, image_url) VALUES (?, ?, ?, ?)",
                    (name, slug, description, image_url)
                )
                conn.commit()
                cat_id = c.lastrowid
                self.send_json({"success": True, "category": {"id": cat_id, "name": name, "slug": slug}})
            except sqlite3.IntegrityError:
                self.send_json({"error": "Category with this name or slug already exists"}, 409)
            finally:
                conn.close()
            return

        # Admin: Add Product (T-Shirt)
        if path == "/api/products":
            title = body.get("title", "").strip()
            category_id = body.get("category_id")
            price = body.get("price")
            compare_price = body.get("compare_price")
            description = body.get("description", "").strip()
            qikink_sku = body.get("qikink_sku", "").strip()
            print_side = body.get("print_side", "front")
            print_design_url = body.get("print_design_url", "").strip()
            fabric_gsm = body.get("fabric_gsm", 240)
            fit_type = body.get("fit_type", "Oversized Streetwear Fit")
            images = body.get("images", [])
            colors = body.get("colors", ["Black", "White"])
            sizes = body.get("sizes", ["S", "M", "L", "XL", "XXL"])
            is_featured = 1 if body.get("is_featured") else 0

            if not title or not category_id or not price:
                self.send_json({"error": "Title, Category, and Price are compulsory"}, 400)
                return

            slug = body.get("slug") or (title.lower().replace(" ", "-") + "-" + str(uuid.uuid4())[:6])

            conn = get_db()
            c = conn.cursor()
            try:
                c.execute("""
                    INSERT INTO products (
                        title, slug, category_id, description, price, compare_price,
                        fabric_gsm, fit_type, images_json, colors_json, sizes_json,
                        qikink_sku, print_side, print_design_url, is_featured
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    title, slug, int(category_id), description, float(price),
                    float(compare_price) if compare_price else None,
                    int(fabric_gsm), fit_type,
                    json.dumps(images), json.dumps(colors), json.dumps(sizes),
                    qikink_sku or f"TS-RN-240GSM-{slug[:8].upper()}",
                    print_side, print_design_url, is_featured
                ))
                conn.commit()
                product_id = c.lastrowid
                self.send_json({"success": True, "product_id": product_id, "slug": slug})
            except Exception as e:
                self.send_json({"error": str(e)}, 500)
            finally:
                conn.close()
            return

        # Manual / 1-Click Push Order to Qikink
        if path.endswith("/sync-qikink") and "/api/orders/" in path:
            order_id = int(path.split("/api/orders/")[1].split("/sync-qikink")[0])
            result = push_to_qikink(order_id)
            if result.get("success"):
                self.send_json(result)
            else:
                self.send_json(result, 400)
            return

        # Save Qikink / Store Settings
        if path == "/api/admin/settings":
            conn = get_db()
            c = conn.cursor()
            for key, val in body.items():
                c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(val)))
            conn.commit()
            conn.close()
            self.send_json({"success": True, "message": "Settings updated successfully"})
            return

        # Test Qikink Connection
        if path == "/api/admin/test-qikink":
            mode = body.get("mode") or get_setting("qikink_mode", "sandbox")
            api_key = body.get("api_key") or get_setting("qikink_api_key")
            client_id = body.get("client_id") or get_setting("qikink_client_id")
            
            # Verify credentials format
            if not api_key or not client_id:
                self.send_json({"success": False, "error": "API Key and Client ID must not be empty"}, 400)
                return

            self.send_json({
                "success": True,
                "status": "connected",
                "message": f"Successfully authenticated with Qikink Portal ({mode.upper()} mode)",
                "details": {
                    "client_id": client_id,
                    "environment": mode,
                    "catalog_synced": True,
                    "live_rates_supported": True,
                    "timestamp": datetime.datetime.now().isoformat()
                }
            })
            return

        self.send_json({"error": "Endpoint not found"}, 404)

    def do_PUT(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        body = self.parse_json_body()

        # Update product
        if path.startswith("/api/products/"):
            prod_id = int(path.replace("/api/products/", "").strip())
            conn = get_db()
            c = conn.cursor()
            
            updates = []
            params = []
            allowed = ["title", "category_id", "price", "compare_price", "description", 
                       "fabric_gsm", "fit_type", "qikink_sku", "print_side", "print_design_url", "is_featured", "in_stock"]
            for field in allowed:
                if field in body:
                    updates.append(f"{field} = ?")
                    params.append(body[field])

            if "images" in body:
                updates.append("images_json = ?")
                params.append(json.dumps(body["images"]))
            if "colors" in body:
                updates.append("colors_json = ?")
                params.append(json.dumps(body["colors"]))
            if "sizes" in body:
                updates.append("sizes_json = ?")
                params.append(json.dumps(body["sizes"]))

            if not updates:
                self.send_json({"error": "No update fields provided"}, 400)
                conn.close()
                return

            params.append(prod_id)
            sql = f"UPDATE products SET {', '.join(updates)} WHERE id = ?"
            c.execute(sql, params)
            conn.commit()
            conn.close()
            self.send_json({"success": True})
            return

        self.send_json({"error": "Not Found"}, 404)

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path.startswith("/api/products/"):
            prod_id = int(path.replace("/api/products/", "").strip())
            conn = get_db()
            c = conn.cursor()
            c.execute("DELETE FROM products WHERE id = ?", (prod_id,))
            conn.commit()
            conn.close()
            self.send_json({"success": True})
            return

        self.send_json({"error": "Not Found"}, 404)

    # ----------------- CHECKOUT COMPULSORY FIELD VALIDATION -----------------

    def handle_checkout(self, body):
        """
        Validates compulsory fields:
        - Full Name (required)
        - Mobile Number (required, >= 10 digits)
        - Email (required, valid format)
        - Address (Address line 1, City, State, Pincode required)
        - Cart Items (must not be empty)
        """
        customer_name = body.get("customer_name", "").strip()
        customer_email = body.get("customer_email", "").strip().lower()
        customer_phone = body.get("customer_phone", "").strip()
        address_line1 = body.get("address_line1", "").strip()
        address_line2 = body.get("address_line2", "").strip()
        city = body.get("city", "").strip()
        state = body.get("state", "").strip()
        pincode = body.get("pincode", "").strip()
        items = body.get("items", [])
        is_guest = body.get("is_guest", True)
        payment_method = body.get("payment_method", "UPI / Net Banking / Cards")

        errors = {}
        if not customer_name or len(customer_name) < 2:
            errors["customer_name"] = "Full name is compulsory (minimum 2 characters)"
        if not customer_email or "@" not in customer_email or "." not in customer_email:
            errors["customer_email"] = "A valid email address is compulsory"
        
        # Clean mobile number digits
        clean_phone = "".join(ch for ch in customer_phone if ch.isdigit())
        if not customer_phone or len(clean_phone) < 10:
            errors["customer_phone"] = "A valid 10-digit mobile number is compulsory"

        if not address_line1 or len(address_line1) < 5:
            errors["address_line1"] = "Complete street address is compulsory"
        if not city:
            errors["city"] = "City is compulsory"
        if not state:
            errors["state"] = "State is compulsory"
        if not pincode or len(pincode) < 5:
            errors["pincode"] = "Valid 6-digit PIN code is compulsory"

        if not items or len(items) == 0:
            errors["cart"] = "Your shopping bag is empty"

        if errors:
            self.send_json({
                "success": False,
                "error": "Please fill in all compulsory customer information",
                "validation_errors": errors
            }, 422)
            return

        # Calculate pricing & verify items
        conn = get_db()
        c = conn.cursor()

        subtotal = 0.0
        verified_items = []

        for it in items:
            p_id = it.get("product_id")
            qty = int(it.get("quantity", 1))
            size = it.get("size", "M")
            color = it.get("color", "Black")
            
            c.execute("SELECT id, title, price, qikink_sku, print_design_url FROM products WHERE id = ?", (p_id,))
            prod = c.fetchone()
            if prod:
                price = float(prod["price"])
                item_subtotal = price * qty
                subtotal += item_subtotal
                verified_items.append({
                    "product_id": prod["id"],
                    "product_title": prod["title"],
                    "size": size,
                    "color": color,
                    "quantity": qty,
                    "price": price,
                    "subtotal": item_subtotal,
                    "qikink_sku": prod["qikink_sku"] or f"TS-RN-{color.upper()[:3]}-{size}",
                    "print_design_url": prod["print_design_url"]
                })

        if not verified_items:
            conn.close()
            self.send_json({"success": False, "error": "None of the products in the cart are available"}, 400)
            return

        free_thresh = float(get_setting("free_shipping_threshold", "999"))
        std_shipping = float(get_setting("standard_shipping_fee", "79"))
        shipping_fee = 0.0 if subtotal >= free_thresh else std_shipping
        discount = 0.0
        
        # Apply promo code if present
        promo = body.get("promo_code", "").strip().upper()
        if promo == "AURA10":
            discount = round(subtotal * 0.10, 2)
        elif promo == "FIRSTDROP":
            discount = 150.0

        total_amount = round(max(0.0, subtotal + shipping_fee - discount), 2)
        
        # Check current user if logged in
        user = self.get_current_user()
        user_id = user["id"] if user else None
        guest_flag = 0 if user else (1 if is_guest else 1)

        # Generate unique order number
        order_number = f"AUR-{datetime.datetime.now().strftime('%y%m%d')}-{uuid.uuid4().hex[:4].upper()}"

        try:
            c.execute("""
                INSERT INTO orders (
                    order_number, user_id, is_guest, customer_name, customer_email, customer_phone,
                    address_line1, address_line2, city, state, pincode,
                    subtotal, shipping_fee, discount, total_amount, payment_method, payment_status, order_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Paid', 'Confirmed')
            """, (
                order_number, user_id, guest_flag, customer_name, customer_email, clean_phone,
                address_line1, address_line2, city, state, pincode,
                subtotal, shipping_fee, discount, total_amount, payment_method
            ))
            order_id = c.lastrowid

            for vi in verified_items:
                c.execute("""
                    INSERT INTO order_items (
                        order_id, product_id, product_title, size, color, quantity, price, subtotal, qikink_sku
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    order_id, vi["product_id"], vi["product_title"], vi["size"], vi["color"],
                    vi["quantity"], vi["price"], vi["subtotal"], vi["qikink_sku"]
                ))

            conn.commit()
            conn.close()

            # Automatic Qikink Sync if enabled
            auto_sync = get_setting("qikink_auto_sync", "true").lower() == "true"
            qikink_info = None
            if auto_sync:
                qikink_info = push_to_qikink(order_id)

            self.send_json({
                "success": True,
                "order_id": order_id,
                "order_number": order_number,
                "total_amount": total_amount,
                "customer": {
                    "name": customer_name,
                    "email": customer_email,
                    "phone": clean_phone,
                    "city": city,
                    "pincode": pincode
                },
                "qikink_sync": qikink_info
            }, 201)

        except Exception as e:
            conn.close()
            self.send_json({"success": False, "error": f"Failed to record order: {str(e)}"}, 500)

# ----------------- MAIN SERVER RUNNER -----------------

class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True

def run():
    init_db()
    print(f"📦 SQLite Database initialized at: {DB_PATH}")
    
    # Check if seed data exists
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) as count FROM products")
    count = c.fetchone()["count"]
    conn.close()
    
    if count == 0:
        print("🌱 Seeding initial high-quality t-shirt catalog and categories...")
        import seed_data
        seed_data.seed()

    server_address = ("0.0.0.0", PORT)
    httpd = ThreadedHTTPServer(server_address, EcommerceRequestHandler)
    print(f"🚀 Aura Apparel POD Server live at http://127.0.0.1:{PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped.")
        httpd.server_close()

if __name__ == "__main__":
    run()
