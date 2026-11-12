# ⚡ AURA APPAREL - Premium Print-On-Demand (POD) T-Shirt E-Commerce Platform

A production-grade, luxury streetwear e-commerce platform built specifically for the **Print-On-Demand (POD) T-Shirt Business** with seamless **Qikink Portal Integration**, **Category-Wise Catalog Management**, **Dedicated Checkout**, and **Compulsory Customer Verification**.

---

## 🌟 Key Features Built Exactly to Requirements

### 1. 💎 Premium Streetwear Aesthetic
- **Visual Design**: Sleek dark-mode aesthetic with luxury glassmorphism, flame orange accents (`#FF5E36`), clean typography (`Syne` & `Plus Jakarta Sans`), and micro-interactions.
- **Interactive T-Shirt Previews**: High-resolution photography, 240+ GSM badges, color swatches, size selectors, and interactive mockup switchers.
- **Floating Cart Drawer**: Real-time persistent local storage shopping bag, free shipping progress bar (unlocked at ₹999), and instant checkout shortcut.

### 2. 📂 Category-Wise T-Shirt Catalog & Easy Admin Creation
- **Curated Default Categories**:
  - `Oversized Streetwear` (Drop-shoulder 240 GSM boxy tees)
  - `Anime & Manga` (Neo-Tokyo high-density DTF graphics)
  - `Minimalist Typography` (Subtle embroidery & Swiss typography)
  - `Cyberpunk & Techwear` (Glitched blueprints & futuristic runes)
  - `Vintage Acid Wash` (Mineral-treated grunge rock tees)
- **Storefront Filtering**: Filter by category pills, search bar with debounce, and sort by latest / price / alphabetical.
- **Admin Portal T-Shirt Creator (`/admin`)**:
  - Assign or create categories on the fly.
  - Set fabric GSM (180, 220, 240, 260 GSM French Terry).
  - Add colorways and available size variants (S, M, L, XL, XXL, 3XL).
  - Map Qikink Master SKU and print placement (Front, Back, Both).
  - Instant live mockup preview and single-click catalog publishing.

### 3. ⚡ Qikink Portal Logistics & Dropshipping Integration
- **Direct REST API Architecture**: Implements Qikink's order creation payload structure (`order_number`, `shipping_address`, `line_items`, `search_sku`, `print_type: DTF`, `designs`).
- **Portal Management Hub (`/admin -> Qikink Portal Hub`)**:
  - Configure **API Key**, **Client ID**, **Client Secret**.
  - Toggle between **Sandbox** (testing/dry run) and **Production** (live Tirupur hub).
  - **Live API Handshake Button**: Real-time ping testing connection status and latency.
  - **1-Click Qikink Sync**: Push orders to the printing queue automatically or manually per order.
  - **Payload Inspector**: View the raw JSON transmitted to Qikink.
  - **Automated Tracking Updates**: Syncs courier partner (Delhivery, BlueDart, Shadowfax) and live AWB number.

### 4. 👤 Account Sign-In + Seamless Guest Checkout
- **Customer Accounts**: Register, Login, Session Management, Order History, and Profile details.
- **Guest Checkout**: Customers are **never forced** to create an account or password to complete an order! They can simply toggle `Continue as Guest` on the checkout page.
- **Guest Tracking**: Guests can track their orders at any time on `/account` using only their order email.

### 5. 🛒 Dedicated Checkout Page (`/checkout`)
- Standalone, distraction-free luxury checkout layout.
- Order review sidebar with item thumbnails, size & color tags, promo coupon box (supports codes `FIRSTDROP` for ₹150 OFF and `AURA10` for 10% OFF).
- Dynamic calculations for subtotal, shipping fee, discounts, and payable total.

### 6. 🛡️ Strict Compulsory Customer Information Enforced
To ensure zero delivery failures with Indian courier partners and Qikink dispatch, the checkout system **compulsorily requires and validates**:
1. **Full Name** (Compulsory, minimum 2 characters)
2. **Email Address** (Compulsory, valid email format for order confirmation & tracking)
3. **Mobile Number** (Compulsory, 10-digit Indian phone number required for delivery OTP)
4. **Complete Street Address** (House/Flat No., Building, Street Name compulsory)
5. **City** (Compulsory)
6. **State** (Compulsory, selection dropdown covering all Indian States/UTs)
7. **PIN Code** (Compulsory, valid 6-digit postal code)

> **Validation Enforcement**: Both client-side (real-time visual red borders, helper hints, and focus scrolling) and server-side (HTTP 422 JSON validation rejection) guarantee no order can ever be placed without complete customer data.

---

## 🚀 Running the Store

The server runs on Python 3 (using standard library modules: zero npm/pip dependencies required!).

### Start Server:
```bash
python3 server.py
```
Server starts on `http://127.0.0.1:8080` (or custom `PORT=XXXX python3 server.py`).

---

## 🔑 Demo & Admin Credentials

| Role | Email | Password | Access |
|---|---|---|---|
| **Store Admin** | `admin@auraapparel.com` | `admin123` | Full access to `/admin` dashboard, Qikink settings, T-shirt CRUD, order sync |
| **Demo Customer** | `rahul@example.com` | `rahul123` | Customer order history, sample past order tracking |
| **Guest** | *No account needed* | *No password* | Instant checkout with compulsory contact info |

---

## 📁 Project Architecture

```
├── database.db             # SQLite database (Users, Categories, Products, Orders, Qikink Settings)
├── server.py               # Backend HTTP server, SQLite ORM, REST API, & Qikink integration engine
├── seed_data.py            # Initial catalog seeding with streetwear categories & 240 GSM drops
├── static/
│   ├── css/
│   │   └── style.css       # Design system, glassmorphism, responsive grid, animations
│   ├── js/
│   │   ├── app.js          # Core API client, auth manager, toast notification system
│   │   └── cart.js         # Persistent shopping cart, free shipping progress bar, drawer
│   ├── index.html          # Hero showcase, category filters, featured drops, Qikink banner
│   ├── shop.html           # Full catalog archive with category filtering, search, and sorting
│   ├── product.html        # Product detail page, color/size customizer, Qikink specs
│   ├── checkout.html       # Dedicated checkout with compulsory fields & Guest support
│   ├── order-success.html  # Order confirmation, Qikink pipeline tracker, courier AWB
│   ├── account.html        # Customer profile, guest order lookup, past orders
│   └── admin.html          # Admin portal: Add T-Shirts, Categories, Orders, Qikink API Hub
└── README.md               # Documentation & setup guide
```
