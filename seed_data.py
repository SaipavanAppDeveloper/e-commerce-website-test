#!/usr/bin/env python3
"""
Seed initial categories, sample premium print-on-demand t-shirts,
and admin credentials.
"""

import sqlite3
import json
import os
import hashlib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")

def hash_pass(p):
    return hashlib.sha256(p.encode("utf-8")).hexdigest()

def seed():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # 1. Admin user
    c.execute("""
        INSERT OR IGNORE INTO users (id, email, password_hash, full_name, phone, role)
        VALUES (1, 'admin@auraapparel.com', ?, 'Store Manager', '+91 9876543210', 'admin')
    """, (hash_pass("admin123"),))

    # Demo Customer user
    c.execute("""
        INSERT OR IGNORE INTO users (id, email, password_hash, full_name, phone, role)
        VALUES (2, 'rahul@example.com', ?, 'Rahul Sharma', '+91 9898012345', 'customer')
    """, (hash_pass("rahul123"),))

    # 2. Categories
    categories = [
        (1, "Oversized Streetwear", "oversized-streetwear", "Drop-shoulder 240 GSM heavy-weight tees with contemporary urban silhouette", "https://images.unsplash.com/photo-1552374196-1ab2a1c593e8?w=800&q=80", 1),
        (2, "Anime & Manga", "anime-manga", "High-density Japanese graphic prints inspired by neo-Tokyo aesthetics", "https://images.unsplash.com/photo-1578632767115-351597cf2477?w=800&q=80", 2),
        (3, "Minimalist Typography", "minimalist-typography", "Clean geometric letterforms, Swiss typography, and subtle embroidery vibes", "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=800&q=80", 3),
        (4, "Cyberpunk & Techwear", "cyberpunk-techwear", "Glitched matrix, circuit runes, dystopian futurism with reflective accents", "https://images.unsplash.com/photo-1503342217505-b0a15ec3261c?w=800&q=80", 4),
        (5, "Vintage Acid Wash", "vintage-acid-wash", "Mineral washed grunge tees with hand-distressed vintage rock prints", "https://images.unsplash.com/photo-1503341455253-b2e723bb3dbb?w=800&q=80", 5)
    ]

    for cat in categories:
        c.execute("""
            INSERT OR REPLACE INTO categories (id, name, slug, description, image_url, display_order)
            VALUES (?, ?, ?, ?, ?, ?)
        """, cat)

    # 3. Premium T-Shirts
    tshirts = [
        {
            "title": "NEO-TOKYO 2099 Oversized Tee",
            "slug": "neo-tokyo-2099-oversized-tee",
            "category_id": 2,
            "description": "Crafted from 240 GSM ultra-heavy combed cotton with a dropped shoulder boxy cut. High-density DTF print featuring neo-Tokyo cyberpunk artwork that won't crack or fade after 50+ washes.",
            "price": 899.00,
            "compare_price": 1499.00,
            "fabric_gsm": 240,
            "fabric_type": "100% Combed Supima Cotton",
            "fit_type": "Oversized Boxy Fit",
            "images": [
                "https://images.unsplash.com/photo-1503342217505-b0a15ec3261c?w=1000&q=80",
                "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=1000&q=80"
            ],
            "colors": ["Pitch Black", "Vintage Beige", "Smoke Grey"],
            "sizes": ["S", "M", "L", "XL", "XXL"],
            "qikink_sku": "QK-TS-OVR-NT2099",
            "print_side": "back",
            "print_design_url": "https://images.unsplash.com/photo-1578632767115-351597cf2477?w=1000&q=80",
            "is_featured": 1
        },
        {
            "title": "CHAOS & HARMONY Minimalist Tee",
            "slug": "chaos-harmony-minimalist-tee",
            "category_id": 3,
            "description": "Understated luxury meets streetwear. Subtle kanji micro-print on left chest with an expansive architectural layout on the spine. 220 GSM breathable organic cotton with pre-shrunk bio-wash.",
            "price": 799.00,
            "compare_price": 1299.00,
            "fabric_gsm": 220,
            "fabric_type": "100% Organic Bio-Washed Cotton",
            "fit_type": "Relaxed Street Fit",
            "images": [
                "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=1000&q=80",
                "https://images.unsplash.com/photo-1583743814966-8936f5b7be1a?w=1000&q=80"
            ],
            "colors": ["Ghost White", "Pitch Black", "Olive Drab"],
            "sizes": ["S", "M", "L", "XL", "XXL"],
            "qikink_sku": "QK-TS-RLX-CH01",
            "print_side": "both",
            "print_design_url": "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=1000&q=80",
            "is_featured": 1
        },
        {
            "title": "CYBERNETIC SOUL Graphic Tee",
            "slug": "cybernetic-soul-graphic-tee",
            "category_id": 4,
            "description": "Inspired by 90s anime mecha blueprints and neural interfaces. Printed with Qikink precision HD DTF technology for vivid neon hues and pinpoint gradient resolution.",
            "price": 949.00,
            "compare_price": 1599.00,
            "fabric_gsm": 240,
            "fabric_type": "Combed Ring-Spun Cotton",
            "fit_type": "Oversized Streetwear Fit",
            "images": [
                "https://images.unsplash.com/photo-1618354691373-d851c5c3a990?w=1000&q=80",
                "https://images.unsplash.com/photo-1503342217505-b0a15ec3261c?w=1000&q=80"
            ],
            "colors": ["Obsidian Black", "Cyber Violet", "Acid Wash Grey"],
            "sizes": ["S", "M", "L", "XL", "XXL"],
            "qikink_sku": "QK-TS-OVR-CYB02",
            "print_side": "front",
            "print_design_url": "https://images.unsplash.com/photo-1618354691373-d851c5c3a990?w=1000&q=80",
            "is_featured": 1
        },
        {
            "title": "HEAVYWEIGHT ACID WASH Nirvana Homage",
            "slug": "acid-wash-nirvana-homage",
            "category_id": 5,
            "description": "Each piece is hand-treated with a custom mineral wash so no two tees are identical. Ultra-durable 260 GSM French Terry knit with reinforced double-needle ribbed collar.",
            "price": 1099.00,
            "compare_price": 1799.00,
            "fabric_gsm": 260,
            "fabric_type": "French Terry Knit Cotton",
            "fit_type": "Boxy Drop-Shoulder",
            "images": [
                "https://images.unsplash.com/photo-1503341455253-b2e723bb3dbb?w=1000&q=80",
                "https://images.unsplash.com/photo-1552374196-1ab2a1c593e8?w=1000&q=80"
            ],
            "colors": ["Charcoal Mineral", "Faded Indigo", "Vintage Sand"],
            "sizes": ["S", "M", "L", "XL", "XXL"],
            "qikink_sku": "QK-TS-TER-ACID99",
            "print_side": "front",
            "print_design_url": "https://images.unsplash.com/photo-1503341455253-b2e723bb3dbb?w=1000&q=80",
            "is_featured": 1
        },
        {
            "title": "INFINITE HORIZON Landscape Drop",
            "slug": "infinite-horizon-landscape-drop",
            "category_id": 1,
            "description": "Panoramic mountain contour line illustration with coordinates of Mount Fuji. Tailored for daily commute, festival weekends, and effortless layering.",
            "price": 849.00,
            "compare_price": 1399.00,
            "fabric_gsm": 240,
            "fabric_type": "100% Combed Cotton",
            "fit_type": "Oversized Streetwear Fit",
            "images": [
                "https://images.unsplash.com/photo-1576566588028-4147f3842f27?w=1000&q=80",
                "https://images.unsplash.com/photo-1583743814966-8936f5b7be1a?w=1000&q=80"
            ],
            "colors": ["Sage Green", "Off-White Cream", "Pitch Black"],
            "sizes": ["S", "M", "L", "XL", "XXL"],
            "qikink_sku": "QK-TS-OVR-HORIZ",
            "print_side": "back",
            "print_design_url": "https://images.unsplash.com/photo-1576566588028-4147f3842f27?w=1000&q=80",
            "is_featured": 0
        },
        {
            "title": "VOID PROTOCOL Heavy Metal Tee",
            "slug": "void-protocol-heavy-metal-tee",
            "category_id": 4,
            "description": "Dark brutalist iconography with thorny metallic font design. Printed with discharge and soft-touch pigment inks for zero hand-feel on fabric.",
            "price": 899.00,
            "compare_price": 1499.00,
            "fabric_gsm": 240,
            "fabric_type": "100% Ring-Spun Cotton",
            "fit_type": "Oversized Boxy",
            "images": [
                "https://images.unsplash.com/photo-1552374196-1ab2a1c593e8?w=1000&q=80",
                "https://images.unsplash.com/photo-1503342217505-b0a15ec3261c?w=1000&q=80"
            ],
            "colors": ["Pitch Black", "Washed Slate"],
            "sizes": ["M", "L", "XL", "XXL"],
            "qikink_sku": "QK-TS-OVR-VOID7",
            "print_side": "front",
            "print_design_url": "https://images.unsplash.com/photo-1552374196-1ab2a1c593e8?w=1000&q=80",
            "is_featured": 1
        }
    ]

    for p in tshirts:
        c.execute("""
            INSERT OR REPLACE INTO products (
                title, slug, category_id, description, price, compare_price,
                fabric_gsm, fabric_type, fit_type, images_json, colors_json, sizes_json,
                qikink_sku, print_side, print_design_url, is_featured, in_stock
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """, (
            p["title"], p["slug"], p["category_id"], p["description"], p["price"], p["compare_price"],
            p["fabric_gsm"], p["fabric_type"], p["fit_type"],
            json.dumps(p["images"]), json.dumps(p["colors"]), json.dumps(p["sizes"]),
            p["qikink_sku"], p["print_side"], p["print_design_url"], p["is_featured"]
        ))

    # Add 1 demo fulfilled order to display in Qikink tracking immediately!
    c.execute("""
        INSERT OR IGNORE INTO orders (
            id, order_number, user_id, is_guest, customer_name, customer_email, customer_phone,
            address_line1, address_line2, city, state, pincode,
            subtotal, shipping_fee, discount, total_amount, payment_method, payment_status, order_status,
            qikink_order_id, qikink_sync_status, tracking_number, courier_name, created_at
        ) VALUES (
            1, 'AUR-261109-7A9B', 2, 0, 'Rahul Sharma', 'rahul@example.com', '9898012345',
            'Flat 402, Skyline Residency, Indiranagar', '100ft Road Near Metro', 'Bengaluru', 'Karnataka', '560038',
            899.00, 0.00, 0.00, 899.00, 'UPI (PhonePe)', 'Paid', 'Dispatched',
            'QK-2026-10001', 'Synced (Dispatched)', 'DELHIVERY-AWB-9921001', 'Delhivery Express Air',
            datetime('now', '-2 days')
        )
    """)
    c.execute("""
        INSERT OR IGNORE INTO order_items (
            order_id, product_id, product_title, size, color, quantity, price, subtotal, qikink_sku
        ) VALUES (
            1, 1, 'NEO-TOKYO 2099 Oversized Tee', 'L', 'Pitch Black', 1, 899.00, 899.00, 'QK-TS-OVR-NT2099'
        )
    """)

    conn.commit()
    conn.close()
    print("✅ Seed completed successfully: Categories, Products, Admin, and Demo Order ready.")

if __name__ == "__main__":
    seed()
