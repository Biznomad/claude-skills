# Dashboard Template Reference

HTML structure patterns, interactive JavaScript, and styling for the dark-mode Biznomad client dashboard.

## CSS Variables (Dark Theme)

```css
:root {
  --bg: #0a0a0f;
  --bg-card: #12121a;
  --bg-sidebar: #0d0d14;
  --bg-hover: #1a1a25;
  --border: #1e1e2e;
  --border-light: #2a2a3a;
  --text: #e4e4e7;
  --text-muted: #71717a;
  --text-heading: #fafafa;
  --accent: #6366f1;
  --accent-hover: #818cf8;
  --success: #22c55e;
  --warning: #f59e0b;
  --danger: #ef4444;
  --gradient-accent: linear-gradient(135deg, #6366f1, #8b5cf6);
  --gradient-card: linear-gradient(145deg, #12121a, #1a1a25);
  --glass: rgba(255, 255, 255, 0.03);
  --glass-border: rgba(255, 255, 255, 0.06);
  --shadow: 0 4px 24px rgba(0, 0, 0, 0.4);
  --radius: 16px;
  --radius-sm: 10px;
  --font-heading: 'Inter', sans-serif;
  --font-body: 'Inter', sans-serif;
  --sidebar-width: 260px;
  --topbar-height: 0px;
}
```

## Password Gate

Full-screen overlay that blocks access until correct password is entered.

```html
<div id="passwordGate" class="password-gate">
  <div class="gate-content">
    <img src="biznomad-logo.jpg" alt="Biznomad" class="gate-logo">
    <h1>Client Dashboard</h1>
    <p>Enter your access code to continue.</p>
    <form id="gateForm">
      <input type="password" id="gatePassword" placeholder="Access Code" autocomplete="off">
      <button type="submit" class="btn btn-accent">Enter Dashboard</button>
    </form>
    <p id="gateError" class="gate-error" hidden>Invalid access code. Try again.</p>
  </div>
</div>
```

JavaScript pattern:

```javascript
const HASH = 'SHA256_HASH_HERE';

document.getElementById('gateForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const pw = document.getElementById('gatePassword').value;
  const encoded = new TextEncoder().encode(pw);
  const hashBuffer = await crypto.subtle.digest('SHA-256', encoded);
  const hashHex = Array.from(new Uint8Array(hashBuffer))
    .map(b => b.toString(16).padStart(2, '0')).join('');
  if (hashHex === HASH) {
    sessionStorage.setItem('dashboard_auth', 'true');
    document.getElementById('passwordGate').remove();
    document.getElementById('dashboard').style.display = 'flex';
  } else {
    document.getElementById('gateError').hidden = false;
  }
});

// Auto-login if session exists
if (sessionStorage.getItem('dashboard_auth') === 'true') {
  document.getElementById('passwordGate').remove();
  document.getElementById('dashboard').style.display = 'flex';
}
```

## Sidebar Navigation

```html
<aside class="sidebar" id="sidebar">
  <div class="sidebar-header">
    <img src="biznomad-logo.jpg" alt="Biznomad" class="sidebar-logo">
    <span class="sidebar-brand">Biznomad</span>
  </div>
  <nav class="sidebar-nav">
    <a href="#overview" class="nav-item active">
      <svg><!-- dashboard icon --></svg> Overview
    </a>
    <a href="#packages" class="nav-item">
      <svg><!-- package icon --></svg> Website Packages
    </a>
    <a href="#maintenance" class="nav-item">
      <svg><!-- wrench icon --></svg> Maintenance
    </a>
    <a href="#marketing" class="nav-item">
      <svg><!-- megaphone icon --></svg> Marketing
    </a>
    <a href="#platform" class="nav-item">
      <svg><!-- grid icon --></svg> Platform
    </a>
    <a href="#addons" class="nav-item">
      <svg><!-- plus icon --></svg> Add-Ons
    </a>
  </nav>
  <div class="sidebar-footer">
    <a href="sms:+15551234567" class="btn btn-outline btn-sm">Message Us</a>
    <a href="https://calendly.com/biznomad" class="btn btn-accent btn-sm">Schedule Call</a>
  </div>
</aside>
```

CSS: Fixed left sidebar, `width: var(--sidebar-width)`. On mobile: off-screen left, slides in with `.sidebar-open` class. Content area gets `margin-left: var(--sidebar-width)`.

## Mobile Hamburger Menu

```html
<header class="mobile-header">
  <button class="hamburger" id="hamburger" aria-label="Menu">
    <span></span><span></span><span></span>
  </button>
  <span class="mobile-title">Dashboard</span>
</header>
```

```javascript
const hamburger = document.getElementById('hamburger');
const sidebar = document.getElementById('sidebar');
const overlay = document.getElementById('overlay');

hamburger.addEventListener('click', () => {
  sidebar.classList.toggle('sidebar-open');
  overlay.classList.toggle('visible');
  hamburger.classList.toggle('active');
});

overlay.addEventListener('click', () => {
  sidebar.classList.remove('sidebar-open');
  overlay.classList.remove('visible');
  hamburger.classList.remove('active');
});
```

## Website Preview Banner

```html
<section class="preview-banner" id="overview">
  <div class="preview-content">
    <div class="preview-info">
      <span class="status-badge live">LIVE</span>
      <h2>Your Website</h2>
      <p>brand-name.netlify.app</p>
    </div>
    <a href="https://brand-name.netlify.app" target="_blank" class="btn btn-accent">
      Visit Site <svg><!-- external link icon --></svg>
    </a>
  </div>
</section>
```

## Stats Row

```html
<div class="stats-row">
  <div class="stat-card">
    <div class="stat-icon success"><svg><!-- check --></svg></div>
    <div class="stat-info">
      <span class="stat-value">Active</span>
      <span class="stat-label">Project Status</span>
    </div>
  </div>
  <div class="stat-card">
    <div class="stat-icon success"><svg><!-- globe --></svg></div>
    <div class="stat-info">
      <span class="stat-value">Live</span>
      <span class="stat-label">Website Status</span>
    </div>
  </div>
  <div class="stat-card">
    <div class="stat-icon accent"><svg><!-- bolt --></svg></div>
    <div class="stat-info">
      <span class="stat-value">3-7 Days</span>
      <span class="stat-label">Speed to Launch</span>
    </div>
  </div>
  <div class="stat-card">
    <div class="stat-icon" id="packagesCount"><svg><!-- box --></svg></div>
    <div class="stat-info">
      <span class="stat-value" id="selectedCount">0</span>
      <span class="stat-label">Packages Selected</span>
    </div>
  </div>
  <div class="stat-card">
    <div class="stat-icon warning"><svg><!-- dollar --></svg></div>
    <div class="stat-info">
      <span class="stat-value" id="totalInvestment">$0</span>
      <span class="stat-label">Investment</span>
    </div>
  </div>
</div>
```

CSS: Flex row, wrap, gap 16px. Each card: `flex: 1 1 180px`, dark card background, border, padding 20px.

## Package Card Pattern

Used for Website, Maintenance, and Marketing packages.

```html
<div class="package-card" data-price="2500" data-name="Starter Website">
  <div class="package-header">
    <span class="package-badge">MOST POPULAR</span>
    <h3>Starter</h3>
    <div class="package-price">
      <span class="price-amount">$2,500</span>
      <span class="price-period">one-time</span>
    </div>
    <p class="package-delivery">5-Day Delivery</p>
  </div>
  <ul class="package-features">
    <li><svg><!-- check --></svg> Feature one</li>
    <li><svg><!-- check --></svg> Feature two</li>
    <li><svg><!-- check --></svg> Feature three</li>
  </ul>
  <button class="btn btn-select" onclick="togglePackage(this)">Select Package</button>
</div>
```

CSS: Cards in a grid `repeat(auto-fit, minmax(260px, 1fr))`. Selected state: accent border, glow shadow. Badge positioned absolute top-right.

## Maintenance Card Pattern

```html
<div class="maintenance-card" data-price="750" data-name="90-Day Maintenance">
  <div class="maintenance-header">
    <h3>90 Days</h3>
    <div class="maintenance-price">$750</div>
  </div>
  <ul class="maintenance-features">
    <li><svg><!-- check --></svg> Unlimited revisions</li>
    <li><svg><!-- check --></svg> Priority support</li>
    <li><svg><!-- check --></svg> Monthly analytics report</li>
  </ul>
  <button class="btn btn-select" onclick="togglePackage(this)">Select Plan</button>
</div>
```

## Biznomad Platform Features Grid

```html
<section id="platform" class="platform-section">
  <div class="section-header">
    <span class="free-badge">FREE WITH ANY MARKETING PACKAGE</span>
    <h2>Biznomad Platform</h2>
    <p>Everything you need to run your business — included at no extra cost.</p>
  </div>
  <div class="platform-grid">
    <div class="platform-card">
      <div class="platform-icon"><svg><!-- users --></svg></div>
      <h3>CRM</h3>
      <p>Customer relationship management</p>
      <span class="replaces">Replaces: HubSpot ($800/mo)</span>
    </div>
    <div class="platform-card">
      <div class="platform-icon"><svg><!-- zap --></svg></div>
      <h3>Automations</h3>
      <p>Workflow & email automation</p>
      <span class="replaces">Replaces: ActiveCampaign ($500/mo)</span>
    </div>
    <div class="platform-card">
      <div class="platform-icon"><svg><!-- funnel --></svg></div>
      <h3>Funnels</h3>
      <p>Sales funnels & landing pages</p>
      <span class="replaces">Replaces: ClickFunnels ($297/mo)</span>
    </div>
    <div class="platform-card">
      <div class="platform-icon"><svg><!-- calendar --></svg></div>
      <h3>Booking</h3>
      <p>Appointment scheduling</p>
      <span class="replaces">Replaces: Calendly ($240/mo)</span>
    </div>
    <div class="platform-card">
      <div class="platform-icon"><svg><!-- star --></svg></div>
      <h3>Reputation</h3>
      <p>Review management & monitoring</p>
      <span class="replaces">Replaces: Birdeye ($350/mo)</span>
    </div>
    <div class="platform-card">
      <div class="platform-icon"><svg><!-- inbox --></svg></div>
      <h3>Unified Inbox</h3>
      <p>All messages in one place</p>
      <span class="replaces">Replaces: Intercom ($600/mo)</span>
    </div>
  </div>
</section>
```

CSS: 3-column grid, cards with icon top, gradient border on hover. "Replaces" text in muted color with strikethrough price.

## Trust Banner

```html
<div class="trust-banner">
  <div class="trust-content">
    <div class="payment-icons">
      <svg><!-- visa --></svg>
      <svg><!-- mastercard --></svg>
      <svg><!-- amex --></svg>
      <svg><!-- stripe --></svg>
      <svg><!-- paypal --></svg>
    </div>
    <p>Secure payments. 100% satisfaction guaranteed. Cancel anytime.</p>
  </div>
</div>
```

## Interactive Package Selection JS

```javascript
const selectedPackages = new Map();

function togglePackage(btn) {
  const card = btn.closest('[data-price]');
  const name = card.dataset.name;
  const price = parseInt(card.dataset.price);

  if (selectedPackages.has(name)) {
    selectedPackages.delete(name);
    card.classList.remove('selected');
    btn.textContent = btn.dataset.selectText || 'Select Package';
    showToast(`Removed: ${name}`, 'warning');
  } else {
    selectedPackages.set(name, price);
    card.classList.add('selected');
    btn.textContent = 'Selected';
    showToast(`Added: ${name} — $${price.toLocaleString()}`, 'success');
  }

  updateTotals();
}

function updateTotals() {
  let total = 0;
  selectedPackages.forEach(price => total += price);
  document.getElementById('totalInvestment').textContent = `$${total.toLocaleString()}`;
  document.getElementById('selectedCount').textContent = selectedPackages.size;
}

function showToast(message, type = 'success') {
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  document.getElementById('toastContainer').appendChild(toast);
  requestAnimationFrame(() => toast.classList.add('show'));
  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}
```

## Toast Container

```html
<div id="toastContainer" class="toast-container"></div>
```

```css
.toast-container {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.toast {
  padding: 12px 20px;
  border-radius: var(--radius-sm);
  color: #fff;
  font-size: 14px;
  transform: translateX(120%);
  transition: transform 0.3s ease;
}
.toast.show { transform: translateX(0); }
.toast-success { background: var(--success); }
.toast-warning { background: var(--warning); color: #000; }
```

## Sidebar Active Link Tracking

```javascript
const sections = document.querySelectorAll('section[id]');
const navItems = document.querySelectorAll('.nav-item');

const sectionObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      navItems.forEach(item => {
        item.classList.toggle('active', item.getAttribute('href') === `#${entry.target.id}`);
      });
    }
  });
}, { threshold: 0.3 });

sections.forEach(section => sectionObserver.observe(section));
```

## Responsive Layout

```css
/* Desktop */
.dashboard { display: flex; min-height: 100vh; }
.sidebar { width: var(--sidebar-width); position: fixed; height: 100vh; overflow-y: auto; }
.main-content { margin-left: var(--sidebar-width); flex: 1; padding: 32px; }

/* Tablet */
@media (max-width: 1024px) {
  .sidebar { transform: translateX(-100%); z-index: 100; }
  .sidebar.sidebar-open { transform: translateX(0); }
  .main-content { margin-left: 0; }
  .mobile-header { display: flex; }
  .stats-row { flex-wrap: wrap; }
  .stat-card { flex: 1 1 calc(50% - 8px); }
}

/* Mobile */
@media (max-width: 480px) {
  .main-content { padding: 16px; }
  .stat-card { flex: 1 1 100%; }
  .package-card, .maintenance-card { min-width: 100%; }
  .platform-grid { grid-template-columns: 1fr; }
}
```

All `section[id]` elements should have `scroll-margin-top: 80px` to account for any fixed headers when navigating via sidebar links.
