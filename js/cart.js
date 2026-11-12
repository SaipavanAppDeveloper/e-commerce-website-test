/**
 * AURA APPAREL - SHOPPING CART & SLIDE DRAWER SYSTEM
 */

const CART_KEY = 'aura_pod_cart';
const FREE_SHIPPING_LIMIT = 999;

function getCart() {
  try {
    return JSON.parse(localStorage.getItem(CART_KEY)) || [];
  } catch (e) {
    return [];
  }
}

function saveCart(cart) {
  localStorage.setItem(CART_KEY, JSON.stringify(cart));
  updateCartBadge();
  renderCartDrawer();
}

function addToCart(product, size = 'L', color = 'Black', quantity = 1) {
  const cart = getCart();
  const existingIndex = cart.findIndex(
    item => item.product_id === product.id && item.size === size && item.color === color
  );

  const img = (product.images && product.images.length > 0) 
    ? product.images[0] 
    : 'https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=600';

  if (existingIndex > -1) {
    cart[existingIndex].quantity += quantity;
  } else {
    cart.push({
      product_id: product.id,
      title: product.title,
      price: product.price,
      compare_price: product.compare_price,
      image: img,
      size: size,
      color: color,
      quantity: quantity,
      qikink_sku: product.qikink_sku || `TS-RN-${color.toUpperCase().slice(0,3)}-${size}`
    });
  }

  saveCart(cart);
  showToast(`Added "${product.title}" (${size} / ${color}) to your bag`, 'success');
  openCart();
}

function removeFromCart(index) {
  const cart = getCart();
  cart.splice(index, 1);
  saveCart(cart);
}

function updateQuantity(index, delta) {
  const cart = getCart();
  if (!cart[index]) return;
  cart[index].quantity += delta;
  if (cart[index].quantity <= 0) {
    cart.splice(index, 1);
  }
  saveCart(cart);
}

function clearCart() {
  localStorage.removeItem(CART_KEY);
  updateCartBadge();
  renderCartDrawer();
}

function getCartSubtotal() {
  const cart = getCart();
  return cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
}

function updateCartBadge() {
  const cart = getCart();
  const totalCount = cart.reduce((sum, item) => sum + item.quantity, 0);
  const badges = document.querySelectorAll('.cart-count');
  badges.forEach(b => {
    b.textContent = totalCount;
    b.style.display = totalCount > 0 ? 'flex' : 'none';
  });
}

function openCart() {
  const overlay = document.getElementById('cart-drawer-overlay');
  const drawer = document.getElementById('cart-drawer');
  if (overlay && drawer) {
    renderCartDrawer();
    overlay.classList.add('active');
    drawer.classList.add('active');
    document.body.style.overflow = 'hidden';
  }
}

function closeCart() {
  const overlay = document.getElementById('cart-drawer-overlay');
  const drawer = document.getElementById('cart-drawer');
  if (overlay && drawer) {
    overlay.classList.remove('active');
    drawer.classList.remove('active');
    document.body.style.overflow = '';
  }
}

function renderCartDrawer() {
  const itemsContainer = document.getElementById('drawer-items-list');
  const subtotalEl = document.getElementById('drawer-subtotal-val');
  const totalEl = document.getElementById('drawer-total-val');
  const progressText = document.getElementById('free-shipping-text');
  const progressFill = document.getElementById('free-shipping-bar-fill');
  
  if (!itemsContainer) return;

  const cart = getCart();
  const subtotal = getCartSubtotal();

  // Progress Bar for Free Shipping
  if (progressText && progressFill) {
    if (subtotal >= FREE_SHIPPING_LIMIT) {
      progressText.innerHTML = `🎉 <strong>Congratulations!</strong> You unlocked <strong>FREE Standard Delivery</strong> across India.`;
      progressFill.style.width = '100%';
    } else {
      const remaining = FREE_SHIPPING_LIMIT - subtotal;
      const pct = Math.min(100, Math.round((subtotal / FREE_SHIPPING_LIMIT) * 100));
      progressText.innerHTML = `Add <strong>${formatINR(remaining)}</strong> more to get <strong>FREE Priority Delivery</strong>`;
      progressFill.style.width = `${pct}%`;
    }
  }

  if (cart.length === 0) {
    itemsContainer.innerHTML = `
      <div style="text-align: center; padding: 60px 20px; color: var(--text-muted);">
        <div style="font-size: 3rem; margin-bottom: 12px; opacity: 0.6;">🛍️</div>
        <h4 style="color: var(--text-primary); margin-bottom: 6px;">Your bag is empty</h4>
        <p style="font-size: 0.85rem; margin-bottom: 24px;">Discover our heavyweight streetwear drops & limited anime editions.</p>
        <a href="/shop" onclick="closeCart()" class="btn btn-sm btn-primary">Browse T-Shirts</a>
      </div>
    `;
    if (subtotalEl) subtotalEl.textContent = formatINR(0);
    if (totalEl) totalEl.textContent = formatINR(0);
    return;
  }

  itemsContainer.innerHTML = cart.map((item, idx) => `
    <div class="cart-item">
      <img src="${item.image}" alt="${item.title}" class="cart-item-img">
      <div class="cart-item-info">
        <h4>${item.title}</h4>
        <div class="cart-item-meta">
          Size: <strong>${item.size}</strong> &bull; Color: <strong>${item.color}</strong>
        </div>
        <div style="display: flex; align-items: center; justify-content: space-between; margin-top: 6px;">
          <div class="qty-control">
            <button class="qty-btn" onclick="updateQuantity(${idx}, -1)">−</button>
            <span class="qty-value">${item.quantity}</span>
            <button class="qty-btn" onclick="updateQuantity(${idx}, 1)">+</button>
          </div>
          <span style="font-weight: 700; color: var(--text-primary);">${formatINR(item.price * item.quantity)}</span>
        </div>
      </div>
      <div>
        <button onclick="removeFromCart(${idx})" title="Remove item" style="background: none; border: none; color: var(--text-muted); cursor: pointer; font-size: 1.1rem; padding: 4px;">
          ✕
        </button>
      </div>
    </div>
  `).join('');

  if (subtotalEl) subtotalEl.textContent = formatINR(subtotal);
  if (totalEl) totalEl.textContent = formatINR(subtotal);
}

// Attach drawer DOM components dynamically if missing on pages
function ensureDrawerDOM() {
  if (document.getElementById('cart-drawer')) return;

  const html = `
    <div id="cart-drawer-overlay" class="cart-drawer-overlay" onclick="closeCart()"></div>
    <div id="cart-drawer" class="cart-drawer">
      <div class="drawer-header">
        <div style="display: flex; align-items: center; gap: 8px;">
          <h3 style="font-size: 1.25rem;">Shopping Bag</h3>
          <span class="badge badge-primary"><span class="cart-count">0</span> ITEMS</span>
        </div>
        <button onclick="closeCart()" class="icon-btn" style="width: 36px; height: 36px;">✕</button>
      </div>

      <div class="free-shipping-progress">
        <div id="free-shipping-text" style="color: var(--text-secondary);"></div>
        <div class="progress-bar-track">
          <div id="free-shipping-bar-fill" class="progress-bar-fill" style="width: 0%;"></div>
        </div>
      </div>

      <div id="drawer-items-list" class="drawer-items"></div>

      <div class="drawer-footer">
        <div class="drawer-summary-row">
          <span>Subtotal</span>
          <span id="drawer-subtotal-val" style="font-weight: 700; color: var(--text-primary);">₹0</span>
        </div>
        <div class="drawer-summary-row" style="font-size: 0.8rem;">
          <span>Pan-India Priority Dispatch</span>
          <span style="color: var(--accent-emerald);">Calculated at Checkout</span>
        </div>
        <div class="drawer-summary-row" style="border-top: 1px solid var(--border-subtle); padding-top: 12px;">
          <span style="font-weight: 700;">Estimated Total</span>
          <span id="drawer-total-val" class="drawer-summary-total">₹0</span>
        </div>
        
        <a href="/checkout" class="btn btn-primary btn-block btn-lg" style="gap: 8px;">
          <span>Proceed to Checkout</span>
          <span>→</span>
        </a>

        <div style="text-align: center; font-size: 0.78rem; color: var(--text-muted); display: flex; align-items: center; justify-content: center; gap: 10px;">
          <span>🔒 256-Bit SSL Secure</span>
          <span>•</span>
          <span>⚡ Guest Checkout Available</span>
        </div>
      </div>
    </div>
  `;

  document.body.insertAdjacentHTML('beforeend', html);
}

document.addEventListener('DOMContentLoaded', () => {
  ensureDrawerDOM();
  updateCartBadge();
  renderCartDrawer();
});
