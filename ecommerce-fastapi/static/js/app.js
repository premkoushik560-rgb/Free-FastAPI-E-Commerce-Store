const API = "/api/v1";
const page = document.querySelector("#page");
const authDialog = document.querySelector("#auth-dialog");
const toastRegion = document.querySelector("#toast-region");
const currency = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" });
const state = {
  user: null,
  categories: [],
  guestCart: readGuestCart(),
  authMode: "login",
  adminTab: "dashboard",
};

function readGuestCart() {
  try {
    const saved = JSON.parse(localStorage.getItem("northstar-guest-cart") || "[]");
    return Array.isArray(saved) ? saved.filter((row) => Number(row.product_id) > 0 && Number(row.quantity) > 0) : [];
  } catch {
    return [];
  }
}

function saveGuestCart() {
  localStorage.setItem("northstar-guest-cart", JSON.stringify(state.guestCart));
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[char]);
}

function money(value) {
  return currency.format(Number(value || 0));
}

async function api(path, options = {}) {
  const headers = new Headers(options.headers || {});
  const request = { ...options, headers, credentials: "same-origin" };
  if (options.body && typeof options.body !== "string") {
    headers.set("Content-Type", "application/json");
    request.body = JSON.stringify(options.body);
  }
  const response = await fetch(`${API}${path}`, request);
  if (response.status === 204) return null;
  const type = response.headers.get("content-type") || "";
  const body = type.includes("application/json") ? await response.json() : await response.text();
  if (!response.ok) {
    const detail = typeof body === "object" ? body.detail : body;
    throw new Error(Array.isArray(detail) ? detail.map((item) => item.msg).join(", ") : detail || `Request failed (${response.status}).`);
  }
  return body;
}

function notify(message, isError = false) {
  const toast = document.createElement("div");
  toast.className = `toast${isError ? " error" : ""}`;
  toast.textContent = message;
  toastRegion.append(toast);
  window.setTimeout(() => toast.remove(), 3400);
}

function loading() {
  page.innerHTML = '<div class="initial-loader"><span class="loader"></span><span>Just a moment…</span></div>';
}

function pathParts() {
  const raw = location.hash.startsWith("#") ? location.hash.slice(1) : "/";
  const [pathname, query = ""] = raw.split("?");
  return { pathname: pathname || "/", params: new URLSearchParams(query) };
}

function navigate(path) {
  location.hash = path;
}

function getCategoryName(id) {
  return state.categories.find((category) => category.id === Number(id))?.name || "Collection";
}

function productCard(product, index = 0) {
  const label = product.stock === 0 ? "Sold out" : product.stock <= 5 ? "Almost gone" : "";
  return `
    <article class="product-card" style="animation-delay:${Math.min(index * 45, 270)}ms">
      <a class="product-art" href="#/product/${product.id}" aria-label="View ${escapeHtml(product.title)}">
        <img src="${escapeHtml(product.image_url)}" alt="${escapeHtml(product.title)}" loading="lazy" />
        ${label ? `<span class="product-badge">${escapeHtml(label)}</span>` : ""}
      </a>
      <div class="product-info">
        <div><h3><a href="#/product/${product.id}">${escapeHtml(product.title)}</a></h3><span class="product-category">${escapeHtml(product.category?.name || getCategoryName(product.category_id))}</span></div>
        <span class="product-price">${money(product.price)}</span>
      </div>
      <button class="quick-add" type="button" data-add-product="${product.id}" aria-label="Add ${escapeHtml(product.title)} to bag" ${product.stock === 0 ? "disabled" : ""}>+</button>
    </article>`;
}

function icon(name) {
  const icons = {
    spark: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2.8 13.8 9l6.2 3-6.2 2.7L12 21l-2-6.3L3.8 12 10 9l2-6.2Z"></path></svg>',
    return: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h12a4 4 0 1 1 0 8H8"></path><path d="m8 11-4 4 4 4"></path></svg>',
    leaf: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 4c-8 0-14 3-14 10a5 5 0 0 0 5 5c7 0 9-7 9-15Z"></path><path d="M4 21c3-5 6-8 12-11"></path></svg>',
    arrow: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 12h15M13 5l7 7-7 7"></path></svg>',
  };
  return icons[name] || "";
}

async function ensureBaseData() {
  if (!state.categories.length) state.categories = await api("/categories");
}

async function renderRoute() {
  loading();
  try {
    await ensureBaseData();
    const { pathname, params } = pathParts();
    if (pathname === "/" || pathname === "") return await renderHome();
    if (pathname === "/products") return await renderProducts(params);
    if (pathname.startsWith("/product/")) return await renderProduct(pathname.split("/")[2]);
    if (pathname === "/cart") return await renderCart();
    if (pathname === "/checkout") return await renderCheckout();
    if (pathname === "/account") return await renderAccount();
    if (pathname === "/orders") return await renderOrders();
    if (pathname.startsWith("/order/")) return await renderOrder(pathname.split("/")[2]);
    if (pathname === "/admin") return await renderAdmin();
    return renderNotFound();
  } catch (error) {
    page.innerHTML = `<section class="content-page"><div class="empty-state"><div class="empty-mark">!</div><h2>We couldn’t load that.</h2><p>${escapeHtml(error.message || "Please try again.")}</p><button class="button button-dark" type="button" data-retry>Try again <span aria-hidden="true">→</span></button></div></section>`;
  }
  updateCartCount();
}

async function renderHome() {
  const [featured] = await Promise.all([
    api("/products?page=1&page_size=8&sort=featured"),
  ]);
  page.innerHTML = `
    <div class="fade-in">
      <section class="home-hero">
        <div class="hero-copy">
          <span class="eyebrow">OBJECTS FOR ORDINARY DAYS</span>
          <h1>Useful things.<br /><em>Chosen well.</em></h1>
          <p>A considered collection of everyday essentials, made to earn their place and stay awhile.</p>
          <div class="hero-actions"><a class="button button-dark" href="#/products">Shop the collection <span aria-hidden="true">→</span></a><a class="text-link" href="#/products">Find your corner</a></div>
        </div>
        <div class="hero-image">
          <img src="/static/images/hero.svg" alt="Illustration of useful everyday objects arranged in a calm, sunlit space" />
          <span class="hero-index">Nº 01 — THE EVERYDAY EDIT</span>
          <span class="hero-stamp">Thoughtful<br />by nature</span>
        </div>
      </section>
      <section class="promise-strip" aria-label="Our shop promises">
        <div class="promise-item">${icon("spark")}<span>Useful, not just pretty</span></div>
        <div class="promise-item">${icon("leaf")}<span>Made to be used for years</span></div>
        <div class="promise-item">${icon("return")}<span>Easy, no-pressure shopping</span></div>
      </section>
      <section class="section" id="categories">
        <div class="section-heading"><div><span class="section-eyebrow">FIND YOUR CORNER</span><h2>Good things, grouped.</h2></div><p>Start with what you need today. There’s no wrong place to begin.</p></div>
        <div class="category-grid">${state.categories.map((category, index) => `
          <a class="category-tile" href="#/products?category_id=${category.id}">
            <span class="category-number">0${index + 1} / COLLECTION</span>
            <span class="category-name">${escapeHtml(category.name)}</span><span class="category-arrow" aria-hidden="true">↗</span>
          </a>`).join("")}</div>
      </section>
      <section class="section featured-section">
        <div class="section-heading"><div><span class="section-eyebrow">THE SHORTLIST</span><h2>Quietly excellent.</h2></div><p>The pieces people reach for again and again.</p></div>
        <div class="product-grid">${featured.items.map(productCard).join("")}</div>
        <div class="featured-more"><a class="button button-outline" href="#/products">See everything <span aria-hidden="true">→</span></a></div>
      </section>
      <section class="editorial-band">
        <div class="editorial-art"><img src="/static/images/studio.svg" alt="A carefully arranged collection of desk and studio tools" loading="lazy" /></div>
        <div class="editorial-copy"><span class="section-eyebrow">A SMALLER, BETTER EDIT</span><h2>Keep the things that make the day.</h2><p>We look for good materials, thoughtful details, and objects that feel better with use. Less clutter. More keepers.</p><a class="text-link" href="#/products">Browse all the good stuff&nbsp; →</a></div>
      </section>
    </div>`;
  updateCartCount();
}

async function renderProducts(params) {
  const search = params.get("q") || "";
  const categoryId = params.get("category_id") || "";
  const sort = params.get("sort") || "featured";
  const currentPage = Math.max(1, Number(params.get("page") || 1));
  const query = new URLSearchParams({ page: String(currentPage), page_size: "12", sort });
  if (search) query.set("q", search);
  if (categoryId) query.set("category_id", categoryId);
  const result = await api(`/products?${query}`);
  const category = state.categories.find((item) => item.id === Number(categoryId));
  page.innerHTML = `
    <section class="listing-page fade-in">
      <div class="breadcrumb"><a href="#/">Home</a> &nbsp; / &nbsp; <span>${escapeHtml(category?.name || "Shop all")}</span></div>
      <div class="listing-title-row"><div><span class="section-eyebrow">THE NORTHSTAR COLLECTION</span><h1>${escapeHtml(category?.name || "Shop all")}</h1></div><p>${result.total} considered ${result.total === 1 ? "object" : "objects"}</p></div>
      <form class="filter-bar" id="product-filters">
        <div class="search-wrap"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="10.8" cy="10.8" r="6.7"></circle><path d="m16 16 4.5 4.5"></path></svg><input class="filter-control" type="search" name="q" value="${escapeHtml(search)}" placeholder="Search the collection" aria-label="Search products" /></div>
        <select class="filter-control" name="category_id" aria-label="Filter by category">
          <option value="">Every collection</option>${state.categories.map((item) => `<option value="${item.id}" ${String(item.id) === categoryId ? "selected" : ""}>${escapeHtml(item.name)}</option>`).join("")}
        </select>
        <select class="filter-control" name="sort" aria-label="Sort products">
          <option value="featured" ${sort === "featured" ? "selected" : ""}>Sort: Featured</option>
          <option value="price_asc" ${sort === "price_asc" ? "selected" : ""}>Price: Low to high</option>
          <option value="price_desc" ${sort === "price_desc" ? "selected" : ""}>Price: High to low</option>
          <option value="newest" ${sort === "newest" ? "selected" : ""}>Newest first</option>
          <option value="name" ${sort === "name" ? "selected" : ""}>Name: A to Z</option>
        </select>
      </form>
      <div class="result-line">${search ? `Showing results for “${escapeHtml(search)}”` : "A little something for the everyday."}</div>
      ${result.items.length ? `<div class="product-grid">${result.items.map(productCard).join("")}</div>` : `<div class="empty-state"><div class="empty-mark">?</div><h2>No objects found.</h2><p>Try a different search or clear the filters.</p><a class="button button-outline" href="#/products">Clear filters</a></div>`}
      ${result.pages > 1 ? `<div class="pagination"><button class="button button-outline button-small" type="button" data-page="${currentPage - 1}" ${currentPage <= 1 ? "disabled" : ""}>← Previous</button><span class="page-number">Page ${result.page} of ${result.pages}</span><button class="button button-outline button-small" type="button" data-page="${currentPage + 1}" ${currentPage >= result.pages ? "disabled" : ""}>Next →</button></div>` : ""}
    </section>`;
  const filterForm = document.querySelector("#product-filters");
  filterForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const values = new FormData(filterForm);
    const next = new URLSearchParams();
    for (const key of ["q", "category_id", "sort"]) {
      const value = String(values.get(key) || "");
      if (value && !(key === "sort" && value === "featured")) next.set(key, value);
    }
    navigate(`/products${next.size ? `?${next}` : ""}`);
  });
  filterForm.elements.category_id.addEventListener("change", () => filterForm.requestSubmit());
  filterForm.elements.sort.addEventListener("change", () => filterForm.requestSubmit());
  updateCartCount();
}

async function renderProduct(id) {
  const product = await api(`/products/${encodeURIComponent(id)}`);
  const available = product.stock > 0;
  page.innerHTML = `
    <section class="product-detail fade-in">
      <div class="breadcrumb"><a href="#/">Home</a> &nbsp; / &nbsp; <a href="#/products">Shop</a> &nbsp; / &nbsp; <span>${escapeHtml(product.title)}</span></div>
      <div class="detail-grid">
        <div class="detail-image"><img src="${escapeHtml(product.image_url)}" alt="${escapeHtml(product.title)}" /></div>
        <div class="detail-copy">
          <span class="section-eyebrow">${escapeHtml(product.category.name)}</span>
          <h1>${escapeHtml(product.title)}</h1><div class="detail-price">${money(product.price)}</div>
          <hr class="detail-rule" />
          <p class="detail-description">${escapeHtml(product.description)}</p>
          <div class="stock-line"><span class="stock-dot ${product.stock <= 5 ? "low" : ""}"></span>${available ? (product.stock <= 5 ? `Only ${product.stock} left in stock` : "In stock, ready to go") : "Currently out of stock"}</div>
          <div class="detail-actions">
            <input class="quantity-input" id="detail-quantity" type="number" min="1" max="${Math.max(1, product.stock)}" value="1" aria-label="Quantity" ${available ? "" : "disabled"} />
            <button class="button button-dark button-wide" type="button" data-detail-add="${product.id}" ${available ? "" : "disabled"}>${available ? "Add to bag" : "Sold out"} <span aria-hidden="true">→</span></button>
          </div>
          <div class="detail-notes"><span>${icon("leaf")} Thoughtful materials, made for everyday use</span><span>${icon("return")} Simulated checkout — no payment details collected</span></div>
        </div>
      </div>
    </section>`;
  updateCartCount();
}

async function getCartItems() {
  if (state.user) {
    const cart = await api("/cart");
    return { items: cart.items.map((row) => ({ ...row, line_total: row.line_total, cart_id: row.id })), subtotal: cart.subtotal, count: cart.count, guest: false };
  }
  const items = await Promise.all(state.guestCart.map(async (row) => {
    try {
      const product = await api(`/products/${row.product_id}`);
      return { id: row.product_id, cart_id: row.product_id, product, quantity: row.quantity, line_total: Number(product.price) * row.quantity };
    } catch {
      return null;
    }
  }));
  const validItems = items.filter(Boolean);
  return {
    items: validItems,
    subtotal: validItems.reduce((sum, row) => sum + Number(row.line_total), 0),
    count: validItems.reduce((sum, row) => sum + row.quantity, 0),
    guest: true,
  };
}

function cartSummary(cart, checkout = false) {
  return `<aside class="summary-box">
    <h2>Order summary</h2>
    <div class="summary-row"><span>Subtotal (${cart.count} ${cart.count === 1 ? "item" : "items"})</span><span>${money(cart.subtotal)}</span></div>
    <div class="summary-row"><span>Shipping</span><span>Calculated at dispatch</span></div>
    <div class="summary-row summary-total"><span>Total</span><span>${money(cart.subtotal)}</span></div>
    <p class="summary-small">This demonstration does not charge you or collect payment card details.</p>
    ${checkout ? "" : `<button class="button button-dark button-wide" type="button" data-checkout>Continue to checkout <span aria-hidden="true">→</span></button>`}
  </aside>`;
}

async function renderCart() {
  const cart = await getCartItems();
  if (!cart.items.length) {
    page.innerHTML = `<section class="content-page"><div class="content-header"><div><span class="section-eyebrow">YOUR BAG</span><h1 class="page-title">A little room<br />for something good.</h1></div></div><div class="empty-state"><div class="empty-mark">+</div><h2>Your bag is taking a breather.</h2><p>Find something useful for the everyday.</p><a class="button button-dark" href="#/products">Explore the collection <span aria-hidden="true">→</span></a></div></section>`;
    updateCartCount();
    return;
  }
  page.innerHTML = `
    <section class="content-page fade-in">
      <div class="content-header"><div><span class="section-eyebrow">YOUR BAG</span><h1 class="page-title">Good choices.</h1></div><p>${cart.count} ${cart.count === 1 ? "item" : "items"} tucked away</p></div>
      <div class="cart-layout">
        <div class="cart-items">${cart.items.map((row) => `
          <article class="cart-row">
            <a href="#/product/${row.product.id}"><img src="${escapeHtml(row.product.image_url)}" alt="${escapeHtml(row.product.title)}" /></a>
            <div><h3><a href="#/product/${row.product.id}">${escapeHtml(row.product.title)}</a></h3><span class="muted">${escapeHtml(row.product.category.name)} · ${money(row.product.price)}</span>
              <div class="cart-item-actions"><label class="sr-only" for="cart-qty-${row.cart_id}">Quantity for ${escapeHtml(row.product.title)}</label><select class="cart-qty" id="cart-qty-${row.cart_id}" data-cart-quantity="${row.cart_id}">${Array.from({ length: Math.min(10, row.product.stock || 10) }, (_, i) => `<option value="${i + 1}" ${row.quantity === i + 1 ? "selected" : ""}>${i + 1}</option>`).join("")}</select>
              <button class="remove-link" type="button" data-remove-cart="${row.cart_id}">Remove</button></div></div>
            <span class="cart-line-price">${money(row.line_total)}</span>
          </article>`).join("")}
          <p class="form-note">${cart.guest ? "Your bag is saved in this browser. Sign in at checkout to sync it with your account." : "Your bag is saved to your account."}</p>
        </div>
        ${cartSummary(cart)}
      </div>
    </section>`;
  updateCartCount();
}

async function renderCheckout() {
  const cart = await getCartItems();
  if (!cart.items.length) {
    page.innerHTML = `<section class="content-page"><div class="empty-state"><div class="empty-mark">+</div><h2>Your bag is empty.</h2><p>Add something to your bag before checking out.</p><a class="button button-dark" href="#/products">Shop the collection <span aria-hidden="true">→</span></a></div></section>`;
    return;
  }
  if (!state.user) {
    page.innerHTML = `<section class="content-page"><div class="empty-state"><div class="empty-mark">↗</div><h2>One quick sign-in first.</h2><p>Create an account or sign in to place your demonstration order.</p><button class="button button-dark" type="button" data-open-auth>Create account or sign in <span aria-hidden="true">→</span></button></div></section>`;
    return;
  }
  page.innerHTML = `
    <section class="content-page fade-in">
      <div class="breadcrumb"><a href="#/cart">Your bag</a> &nbsp; / &nbsp; <span>Checkout</span></div>
      <div class="content-header"><div><span class="section-eyebrow">ALMOST THERE</span><h1 class="page-title">Make it yours.</h1></div><p>Signed in as ${escapeHtml(state.user.email)}</p></div>
      <div class="checkout-layout">
        <form class="checkout-card" id="checkout-form">
          <section class="checkout-section"><h2>Where should it go?</h2>
            <div class="stack-form">
              <label class="form-field">Full name<input name="shipping_name" autocomplete="name" value="${escapeHtml(state.user.name)}" required minlength="2" maxlength="120" /></label>
              <label class="form-field">Street address<input name="shipping_address" autocomplete="street-address" required minlength="5" maxlength="240" /></label>
              <div class="form-grid"><label class="form-field">City<input name="shipping_city" autocomplete="address-level2" required minlength="2" maxlength="100" /></label><label class="form-field">Postal code<input name="shipping_postal_code" autocomplete="postal-code" required minlength="2" maxlength="24" /></label></div>
              <label class="form-field">Country<input name="shipping_country" autocomplete="country-name" required minlength="2" maxlength="80" /></label>
            </div>
          </section>
          <section class="checkout-section"><h2>Payment demonstration</h2><span class="simulated-label">Simulated · No real payment</span>
            <div class="payment-demo">
              <label class="payment-option"><input type="radio" name="payment_result" value="success" checked /><span><strong>Test a successful order</strong><small>Creates an order and reduces sample stock. No payment details are needed.</small></span></label>
              <label class="payment-option"><input type="radio" name="payment_result" value="failure" /><span><strong>Test a declined payment</strong><small>Shows a failed order while keeping items in your bag.</small></span></label>
            </div>
            <p class="form-error" id="checkout-error" role="alert"></p>
            <button class="button button-dark button-wide" type="submit" id="checkout-submit">Place demonstration order <span aria-hidden="true">→</span></button>
          </section>
        </form>
        ${cartSummary(cart, true)}
      </div>
    </section>`;
  updateCartCount();
}

async function renderAccount() {
  if (!state.user) {
    page.innerHTML = `<section class="content-page"><div class="empty-state"><div class="empty-mark">↗</div><h2>Your account, all in one place.</h2><p>Sign in to see your profile and recent orders.</p><button class="button button-dark" type="button" data-open-auth>Create account or sign in <span aria-hidden="true">→</span></button></div></section>`;
    return;
  }
  const orders = await api("/orders");
  page.innerHTML = `
    <section class="content-page fade-in">
      <div class="content-header"><div><span class="section-eyebrow">YOUR NORTHSTAR ACCOUNT</span><h1 class="page-title">Hello, ${escapeHtml(state.user.name.split(" ")[0])}.</h1></div><button class="button button-outline button-small" type="button" data-logout>Sign out</button></div>
      <div class="account-card"><div><h2>${escapeHtml(state.user.name)}</h2><p>${escapeHtml(state.user.email)} · ${state.user.role === "admin" ? "Administrator" : "Customer account"}</p></div><span class="account-initials">${escapeHtml(state.user.name.split(/\s+/).map((part) => part[0]).join("").slice(0, 2).toUpperCase())}</span></div>
      <div class="content-header"><div><span class="section-eyebrow">KEPT IN ONE PLACE</span><h2 class="page-title" style="font-size:38px">Your orders</h2></div><a class="text-link" href="#/orders">View order history →</a></div>
      ${orders.length ? orders.slice(0, 3).map(orderCard).join("") : `<div class="empty-state"><h2>No orders yet.</h2><p>Your next useful thing is just around the corner.</p><a class="button button-outline" href="#/products">Browse the collection</a></div>`}
    </section>`;
}

function orderCard(order) {
  const firstNames = order.items.slice(0, 2).map((item) => item.product_title).join(", ");
  const date = new Date(order.created_at).toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
  return `<a class="order-card" href="#/order/${order.id}">
    <div class="order-card-header"><div><span class="order-id">Order Nº ${String(order.id).padStart(4, "0")}</span><span class="order-date">${escapeHtml(date)}</span></div><span class="status-pill ${order.payment_status === "failed" ? "failed" : ""}">${escapeHtml(order.status.replaceAll("_", " "))}</span></div>
    <div class="order-items-preview"><span>${escapeHtml(firstNames || "No line items")}${order.items.length > 2 ? ` + ${order.items.length - 2} more` : ""}</span><span class="order-total">${money(order.total)}</span></div>
  </a>`;
}

async function renderOrders() {
  if (!state.user) {
    page.innerHTML = `<section class="content-page"><div class="empty-state"><div class="empty-mark">↗</div><h2>Orders, neatly kept.</h2><p>Sign in to see your order history.</p><button class="button button-dark" type="button" data-open-auth>Sign in <span aria-hidden="true">→</span></button></div></section>`;
    return;
  }
  const orders = await api("/orders");
  page.innerHTML = `<section class="content-page fade-in"><div class="content-header"><div><span class="section-eyebrow">YOUR NORTHSTAR ACCOUNT</span><h1 class="page-title">Order history.</h1></div><a class="text-link" href="#/account">Back to account →</a></div>
    ${orders.length ? orders.map(orderCard).join("") : `<div class="empty-state"><h2>No orders yet.</h2><p>Good things are waiting in the collection.</p><a class="button button-outline" href="#/products">Browse the collection</a></div>`}
  </section>`;
}

async function renderOrder(id) {
  if (!state.user) {
    page.innerHTML = `<section class="content-page"><div class="empty-state"><h2>Sign in to see this order.</h2><button class="button button-dark" type="button" data-open-auth>Sign in <span aria-hidden="true">→</span></button></div></section>`;
    return;
  }
  const order = await api(`/orders/${encodeURIComponent(id)}`);
  const failed = order.payment_status === "failed";
  page.innerHTML = `
    <section class="content-page fade-in">
      <div class="breadcrumb"><a href="#/orders">Order history</a> &nbsp; / &nbsp; <span>Order Nº ${String(order.id).padStart(4, "0")}</span></div>
      <div class="content-header"><div><span class="section-eyebrow">${failed ? "PAYMENT NOT COMPLETED" : "THANKS FOR YOUR ORDER"}</span><h1 class="page-title">${failed ? "Not quite yet." : "Nicely done."}</h1></div><span class="status-pill ${failed ? "failed" : ""}">${escapeHtml(order.status.replaceAll("_", " "))}</span></div>
      <div class="checkout-layout"><div>
        <div class="order-card"><div class="order-id">Order Nº ${String(order.id).padStart(4, "0")}</div><span class="order-date">${new Date(order.created_at).toLocaleString()}</span>
          ${order.items.map((item) => `<div class="order-items-preview"><span>${escapeHtml(item.product_title)} × ${item.quantity}</span><span class="order-total">${money(Number(item.unit_price) * item.quantity)}</span></div>`).join("")}
          <div class="summary-row summary-total"><span>Total</span><span>${money(order.total)}</span></div>
        </div>
        ${failed ? `<div class="form-note">This is a simulated declined payment. Nothing was charged and your cart is still saved. <a class="text-link" href="#/cart">Return to your bag</a>.</div>` : `<p class="form-note">Your demonstration order is confirmed. No money changed hands.</p>`}
      </div>
      <aside class="summary-box"><h2>Shipping to</h2><p class="form-note">${escapeHtml(order.shipping_name)}<br />${escapeHtml(order.shipping_address)}<br />${escapeHtml(order.shipping_city)}, ${escapeHtml(order.shipping_postal_code)}<br />${escapeHtml(order.shipping_country)}</p><a class="text-link" href="#/orders">All orders →</a></aside>
      </div>
    </section>`;
}

function adminTabs() {
  return `<nav class="admin-tabs" aria-label="Admin sections">
    ${[["dashboard", "Overview"], ["products", "Products"], ["categories", "Categories"], ["orders", "Orders"]].map(([value, label]) => `<button type="button" class="admin-tab ${state.adminTab === value ? "active" : ""}" data-admin-tab="${value}">${label}</button>`).join("")}
  </nav>`;
}

async function renderAdmin() {
  if (!state.user) {
    page.innerHTML = `<section class="content-page"><div class="empty-state"><h2>Administrator sign-in required.</h2><p>Sign in with an administrator account to manage the store.</p><button class="button button-dark" type="button" data-open-auth>Sign in <span aria-hidden="true">→</span></button></div></section>`;
    return;
  }
  if (state.user.role !== "admin") {
    page.innerHTML = `<section class="content-page"><div class="empty-state"><h2>This area is for store administrators.</h2><p>Your customer account cannot manage products or orders.</p><a class="button button-outline" href="#/account">Back to your account</a></div></section>`;
    return;
  }
  let panel = "";
  if (state.adminTab === "dashboard") panel = await adminDashboard();
  if (state.adminTab === "products") panel = await adminProducts();
  if (state.adminTab === "categories") panel = await adminCategories();
  if (state.adminTab === "orders") panel = await adminOrders();
  page.innerHTML = `<section class="content-page fade-in"><div class="content-header"><div><span class="section-eyebrow">STORE MANAGEMENT</span><h1 class="page-title">The back room.</h1></div><a class="text-link" href="#/account">Your account →</a></div><div class="admin-layout">${adminTabs()}<div class="admin-panel">${panel}</div></div></section>`;
}

async function adminDashboard() {
  const dashboard = await api("/admin/dashboard");
  return `<div class="metric-grid">
    ${[["Products", dashboard.product_count], ["Orders", dashboard.order_count], ["Customers", dashboard.customer_count], ["Paid revenue", money(dashboard.paid_revenue)]].map(([label, value]) => `<div class="metric-card"><div class="metric-label">${label}</div><div class="metric-value">${value}</div></div>`).join("")}
    </div>
    <div class="admin-product-heading"><h3>Recent orders</h3><button class="button button-outline button-small" type="button" data-admin-tab="orders">All orders →</button></div>
    ${dashboard.recent_orders.length ? `<div class="admin-table-wrap"><table class="admin-table"><thead><tr><th>Order</th><th>Status</th><th>Items</th><th>Total</th></tr></thead><tbody>${dashboard.recent_orders.map((order) => `<tr><td> Nº ${String(order.id).padStart(4, "0")}</td><td><span class="status-pill ${order.payment_status === "failed" ? "failed" : ""}">${escapeHtml(order.status.replaceAll("_", " "))}</span></td><td>${order.items.reduce((sum, item) => sum + item.quantity, 0)}</td><td>${money(order.total)}</td></tr>`).join("")}</tbody></table></div>` : `<div class="admin-empty">Orders will appear here after a customer checks out.</div>`}
    <p class="form-note" style="margin-top:15px">${dashboard.low_stock_count} product${dashboard.low_stock_count === 1 ? "" : "s"} with five or fewer in stock · ${dashboard.category_count} categories</p>`;
}

async function adminProducts() {
  const result = await api("/products?page_size=48&sort=name");
  return `<div class="admin-form-box"><h3>Add a product</h3>
    <form class="stack-form" id="admin-product-form">
      <div class="form-grid"><label class="form-field">Product name<input name="title" required minlength="2" maxlength="140" /></label><label class="form-field">Slug<input name="slug" required pattern="[a-z0-9]+(?:-[a-z0-9]+)*" placeholder="short-product-name" /></label></div>
      <label class="form-field">Description<textarea name="description" required minlength="8" maxlength="5000"></textarea></label>
      <div class="form-grid"><label class="form-field">Price (USD)<input name="price" type="number" min="0.01" step="0.01" required /></label><label class="form-field">Stock<input name="stock" type="number" min="0" step="1" required /></label></div>
      <div class="form-grid"><label class="form-field">Category<select name="category_id" required>${state.categories.map((category) => `<option value="${category.id}">${escapeHtml(category.name)}</option>`).join("")}</select></label><label class="form-field">Image path<input name="image_url" value="/static/images/objects.svg" maxlength="500" /></label></div>
      <p class="form-error" id="admin-product-error" role="alert"></p>
      <button class="button button-dark button-small" type="submit">Add product <span aria-hidden="true">→</span></button>
    </form></div>
    <div class="admin-product-heading"><h3>Products <span class="product-category">(${result.total})</span></h3></div>
    <div class="admin-table-wrap"><table class="admin-table"><thead><tr><th>Product</th><th>Category</th><th>Price</th><th>Stock</th><th>Actions</th></tr></thead><tbody>
    ${result.items.map((product) => `<tr><td><strong>${escapeHtml(product.title)}</strong><br /><span class="product-category">${escapeHtml(product.slug)}</span></td><td>${escapeHtml(product.category.name)}</td><td>${money(product.price)}</td><td>${product.stock}</td><td><div class="table-actions"><button class="button button-outline button-small" type="button" data-edit-product="${product.id}">Edit</button><button class="button button-outline button-small" type="button" data-delete-product="${product.id}">Delete</button></div></td></tr>`).join("")}
    </tbody></table></div>
    <div class="admin-form-box hidden" id="edit-product-box"><h3>Edit product</h3><form class="stack-form" id="admin-edit-form"><input name="id" type="hidden" /><div class="form-grid"><label class="form-field">Product name<input name="title" required minlength="2" maxlength="140" /></label><label class="form-field">Slug<input name="slug" required pattern="[a-z0-9]+(?:-[a-z0-9]+)*" /></label></div><label class="form-field">Description<textarea name="description" required minlength="8" maxlength="5000"></textarea></label><div class="form-grid"><label class="form-field">Price (USD)<input name="price" type="number" min="0.01" step="0.01" required /></label><label class="form-field">Stock<input name="stock" type="number" min="0" step="1" required /></label></div><label class="form-field">Category<select name="category_id">${state.categories.map((category) => `<option value="${category.id}">${escapeHtml(category.name)}</option>`).join("")}</select></label><label class="form-field">Image path<input name="image_url" maxlength="500" /></label><p class="form-error" id="admin-edit-error" role="alert"></p><div class="table-actions"><button class="button button-dark button-small" type="submit">Save changes</button><button class="button button-outline button-small" type="button" data-cancel-edit>Cancel</button></div></form></div>`;
}

async function adminCategories() {
  await ensureBaseData();
  return `<div class="admin-form-box"><h3>Add a category</h3><form class="stack-form" id="admin-category-form">
    <div class="form-grid"><label class="form-field">Category name<input name="name" required minlength="2" maxlength="80" /></label><label class="form-field">Slug<input name="slug" required pattern="[a-z0-9]+(?:-[a-z0-9]+)*" placeholder="category-name" /></label></div>
    <label class="form-field">Short description<input name="description" maxlength="240" /></label>
    <p class="form-error" id="admin-category-error" role="alert"></p><button class="button button-dark button-small" type="submit">Create category <span aria-hidden="true">→</span></button>
  </form></div>
  <div class="admin-product-heading"><h3>Current categories</h3></div><div class="admin-table-wrap"><table class="admin-table"><thead><tr><th>Name</th><th>Slug</th><th>Description</th><th>Products</th></tr></thead><tbody>
  ${state.categories.map((category) => `<tr><td><strong>${escapeHtml(category.name)}</strong></td><td>${escapeHtml(category.slug)}</td><td>${escapeHtml(category.description)}</td><td><a class="text-link" href="#/products?category_id=${category.id}">Browse →</a></td></tr>`).join("")}
  </tbody></table></div>`;
}

async function adminOrders() {
  const orders = await api("/admin/orders");
  return `<div class="admin-product-heading"><h3>All orders <span class="product-category">(${orders.length})</span></h3></div>
    ${orders.length ? `<div class="admin-table-wrap"><table class="admin-table"><thead><tr><th>Order</th><th>Payment</th><th>Status</th><th>Total</th><th>Update status</th></tr></thead><tbody>
    ${orders.map((order) => `<tr><td><strong>Nº ${String(order.id).padStart(4, "0")}</strong><br /><span class="product-category">${escapeHtml(order.shipping_name)}</span></td><td>${escapeHtml(order.payment_status)}</td><td><span class="status-pill ${order.payment_status === "failed" ? "failed" : ""}">${escapeHtml(order.status.replaceAll("_", " "))}</span></td><td>${money(order.total)}</td><td>${order.payment_status === "paid" ? `<div class="table-actions"><select class="inline-select" data-order-status="${order.id}"><option value="processing" ${order.status === "processing" ? "selected" : ""}>Processing</option><option value="shipped" ${order.status === "shipped" ? "selected" : ""}>Shipped</option><option value="delivered" ${order.status === "delivered" ? "selected" : ""}>Delivered</option><option value="cancelled" ${order.status === "cancelled" ? "selected" : ""}>Cancelled</option></select><button class="button button-outline button-small" type="button" data-save-status="${order.id}">Save</button></div>` : "—"}</td></tr>`).join("")}
    </tbody></table></div>` : `<div class="admin-empty">No orders to manage yet.</div>`}`;
}

function renderNotFound() {
  page.innerHTML = `<section class="content-page"><div class="empty-state"><div class="empty-mark">?</div><h2>That page has wandered off.</h2><p>Let’s find our way back to the useful things.</p><a class="button button-dark" href="#/">Go home <span aria-hidden="true">→</span></a></div></section>`;
}

async function updateCartCount() {
  let count = state.guestCart.reduce((sum, row) => sum + Number(row.quantity), 0);
  if (state.user) {
    try {
      count = (await api("/cart")).count;
    } catch {
      count = 0;
    }
  }
  const badge = document.querySelector("#cart-count");
  if (badge) badge.textContent = String(count);
}

async function addProduct(productId, quantity = 1) {
  const product = await api(`/products/${productId}`);
  if (product.stock < quantity) throw new Error(`Only ${product.stock} of this item are currently in stock.`);
  if (state.user) {
    await api("/cart/items", { method: "POST", body: { product_id: product.id, quantity } });
  } else {
    const existing = state.guestCart.find((row) => row.product_id === product.id);
    const nextQuantity = quantity + (existing?.quantity || 0);
    if (nextQuantity > product.stock) throw new Error(`Only ${product.stock} of this item are currently in stock.`);
    if (existing) existing.quantity = nextQuantity;
    else state.guestCart.push({ product_id: product.id, quantity });
    saveGuestCart();
  }
  await updateCartCount();
  notify("Added to your bag.");
}

async function syncGuestCart() {
  const leftover = [];
  for (const row of state.guestCart) {
    try {
      await api("/cart/items", { method: "POST", body: row });
    } catch (error) {
      leftover.push(row);
      notify(error.message, true);
    }
  }
  state.guestCart = leftover;
  saveGuestCart();
  await updateCartCount();
}

function setAuthMode(mode) {
  state.authMode = mode;
  const register = mode === "register";
  document.querySelector("#auth-title").textContent = register ? "A good place to start." : "Welcome back.";
  document.querySelector("#auth-copy").textContent = register ? "Create an account to save your cart and keep your orders together." : "Sign in to keep your cart and see your orders.";
  document.querySelector("#name-field").classList.toggle("hidden", !register);
  document.querySelector("#name-field input").required = register;
  document.querySelector("#auth-form [name=password]").autocomplete = register ? "new-password" : "current-password";
  document.querySelector("#auth-submit").innerHTML = `${register ? "Create account" : "Sign in"} <span aria-hidden="true">→</span>`;
  document.querySelectorAll(".auth-mode").forEach((button) => button.classList.toggle("active", button.dataset.authMode === mode));
  document.querySelector("#auth-error").textContent = "";
}

function openAuth(mode = "login") {
  setAuthMode(mode);
  if (!authDialog.open) authDialog.showModal();
}

document.addEventListener("click", async (event) => {
  const target = event.target.closest("button, a");
  if (!target) return;
  if (target.matches(".account-trigger")) {
    if (state.user) navigate("/account");
    else openAuth("login");
  }
  if (target.matches(".mobile-menu-button")) {
    const open = target.getAttribute("aria-expanded") !== "true";
    target.setAttribute("aria-expanded", String(open));
    document.querySelector("#mobile-nav").classList.toggle("open", open);
  }
  if (target.closest("#mobile-nav a")) {
    document.querySelector("#mobile-nav").classList.remove("open");
    document.querySelector(".mobile-menu-button").setAttribute("aria-expanded", "false");
  }
  if (target.matches("[data-open-auth]")) openAuth("login");
  if (target.matches("[data-retry]")) renderRoute();
  if (target.dataset.addProduct) {
    target.disabled = true;
    try { await addProduct(Number(target.dataset.addProduct)); } catch (error) { notify(error.message, true); } finally { target.disabled = false; }
  }
  if (target.dataset.detailAdd) {
    const quantity = Math.max(1, Number(document.querySelector("#detail-quantity").value || 1));
    target.disabled = true;
    try { await addProduct(Number(target.dataset.detailAdd), quantity); } catch (error) { notify(error.message, true); } finally { target.disabled = false; }
  }
  if (target.hasAttribute("data-checkout")) {
    if (!state.user) openAuth("login");
    else navigate("/checkout");
  }
  if (target.dataset.removeCart) {
    try {
      if (state.user) await api(`/cart/items/${target.dataset.removeCart}`, { method: "DELETE" });
      else {
        state.guestCart = state.guestCart.filter((row) => row.product_id !== Number(target.dataset.removeCart));
        saveGuestCart();
      }
      notify("Removed from your bag.");
      await renderRoute();
    } catch (error) { notify(error.message, true); }
  }
  if (target.dataset.page) {
    const { params } = pathParts();
    params.set("page", target.dataset.page);
    navigate(`/products?${params}`);
  }
  if (target.dataset.authMode) setAuthMode(target.dataset.authMode);
  if (target.matches(".dialog-close")) authDialog.close();
  if (target.hasAttribute("data-logout")) {
    try { await api("/auth/logout", { method: "POST" }); } catch { /* local user state is cleared regardless */ }
    state.user = null;
    notify("You’re signed out.");
    navigate("/");
    await updateCartCount();
  }
  if (target.dataset.adminTab) {
    state.adminTab = target.dataset.adminTab;
    await renderAdmin();
  }
  if (target.dataset.deleteProduct) {
    if (!window.confirm("Delete this product? It will be removed from the catalog and any active carts.")) return;
    try {
      await api(`/products/${target.dataset.deleteProduct}`, { method: "DELETE" });
      notify("Product deleted.");
      await renderAdmin();
    } catch (error) { notify(error.message, true); }
  }
  if (target.dataset.editProduct) {
    try {
      const product = await api(`/products/${target.dataset.editProduct}`);
      const box = document.querySelector("#edit-product-box");
      const form = document.querySelector("#admin-edit-form");
      form.elements.id.value = product.id;
      for (const key of ["title", "slug", "description", "price", "stock", "category_id", "image_url"]) form.elements[key].value = product[key];
      box.classList.remove("hidden");
      box.scrollIntoView({ behavior: "smooth", block: "start" });
    } catch (error) { notify(error.message, true); }
  }
  if (target.hasAttribute("data-cancel-edit")) document.querySelector("#edit-product-box").classList.add("hidden");
  if (target.dataset.saveStatus) {
    const select = document.querySelector(`[data-order-status="${target.dataset.saveStatus}"]`);
    target.disabled = true;
    try {
      await api(`/admin/orders/${target.dataset.saveStatus}/status`, { method: "PATCH", body: { status: select.value } });
      notify("Order status updated.");
      await renderAdmin();
    } catch (error) { notify(error.message, true); target.disabled = false; }
  }
});

document.addEventListener("change", async (event) => {
  const select = event.target.closest("[data-cart-quantity]");
  if (!select) return;
  const itemId = Number(select.dataset.cartQuantity);
  const quantity = Number(select.value);
  try {
    if (state.user) await api(`/cart/items/${itemId}`, { method: "PATCH", body: { quantity } });
    else {
      const item = state.guestCart.find((row) => row.product_id === itemId);
      const product = await api(`/products/${itemId}`);
      if (quantity > product.stock) throw new Error(`Only ${product.stock} of this item are currently in stock.`);
      if (item) item.quantity = quantity;
      saveGuestCart();
    }
    notify("Bag updated.");
    await renderRoute();
  } catch (error) { notify(error.message, true); await renderRoute(); }
});

document.addEventListener("submit", async (event) => {
  if (event.target.matches("#auth-form")) {
    event.preventDefault();
    const form = event.target;
    const errorLine = document.querySelector("#auth-error");
    const values = new FormData(form);
    const payload = { email: String(values.get("email")).trim().toLowerCase(), password: String(values.get("password")) };
    const register = state.authMode === "register";
    if (register) payload.name = String(values.get("name")).trim();
    const button = document.querySelector("#auth-submit");
    button.disabled = true;
    errorLine.textContent = "";
    try {
      state.user = await api(register ? "/auth/register" : "/auth/login", { method: "POST", body: payload });
      authDialog.close();
      form.reset();
      await syncGuestCart();
      notify(register ? "Your account is ready." : "Welcome back.");
      await renderRoute();
    } catch (error) { errorLine.textContent = error.message; } finally { button.disabled = false; }
  }
  if (event.target.matches("#checkout-form")) {
    event.preventDefault();
    const form = event.target;
    const button = document.querySelector("#checkout-submit");
    const errorLine = document.querySelector("#checkout-error");
    const values = new FormData(form);
    const payload = Object.fromEntries(values.entries());
    button.disabled = true;
    errorLine.textContent = "";
    try {
      const order = await api("/orders", { method: "POST", body: payload });
      notify(order.payment_status === "paid" ? "Your demonstration order is confirmed." : "The simulated payment was declined.", order.payment_status !== "paid");
      await updateCartCount();
      navigate(`/order/${order.id}`);
    } catch (error) { errorLine.textContent = error.message; } finally { button.disabled = false; }
  }
  if (event.target.matches("#admin-product-form")) {
    event.preventDefault();
    const form = event.target;
    const errorLine = document.querySelector("#admin-product-error");
    const values = Object.fromEntries(new FormData(form).entries());
    values.price = Number(values.price);
    values.stock = Number(values.stock);
    values.category_id = Number(values.category_id);
    const button = form.querySelector('button[type="submit"]');
    button.disabled = true;
    try {
      await api("/products", { method: "POST", body: values });
      notify("Product added to the catalog.");
      await renderAdmin();
    } catch (error) { errorLine.textContent = error.message; } finally { button.disabled = false; }
  }
  if (event.target.matches("#admin-edit-form")) {
    event.preventDefault();
    const form = event.target;
    const values = Object.fromEntries(new FormData(form).entries());
    const id = values.id;
    delete values.id;
    values.price = Number(values.price);
    values.stock = Number(values.stock);
    values.category_id = Number(values.category_id);
    const button = form.querySelector('button[type="submit"]');
    button.disabled = true;
    try {
      await api(`/products/${id}`, { method: "PUT", body: values });
      notify("Product details saved.");
      await renderAdmin();
    } catch (error) { document.querySelector("#admin-edit-error").textContent = error.message; } finally { button.disabled = false; }
  }
  if (event.target.matches("#admin-category-form")) {
    event.preventDefault();
    const form = event.target;
    const values = Object.fromEntries(new FormData(form).entries());
    const button = form.querySelector('button[type="submit"]');
    button.disabled = true;
    try {
      await api("/categories", { method: "POST", body: values });
      state.categories = await api("/categories");
      notify("Category created.");
      await renderAdmin();
    } catch (error) { document.querySelector("#admin-category-error").textContent = error.message; } finally { button.disabled = false; }
  }
});

window.addEventListener("hashchange", () => {
  document.querySelector("#mobile-nav").classList.remove("open");
  document.querySelector(".mobile-menu-button").setAttribute("aria-expanded", "false");
  renderRoute();
});

async function bootstrap() {
  try {
    await ensureBaseData();
    try { state.user = await api("/auth/me"); } catch { state.user = null; }
    await updateCartCount();
    await renderRoute();
  } catch (error) {
    page.innerHTML = `<section class="content-page"><div class="empty-state"><h2>The shop is having a moment.</h2><p>${escapeHtml(error.message)}</p><button class="button button-dark" type="button" data-retry>Try again <span aria-hidden="true">→</span></button></div></section>`;
  }
}

bootstrap();
