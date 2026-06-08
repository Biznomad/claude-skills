# Website Template Reference

Section-by-section HTML structure, CSS patterns, and JavaScript behaviors for the luxury e-commerce website.

## CSS Variables (Theming)

Define all colors, typography, and spacing via custom properties on `:root`. The design system generator populates these values.

```css
:root {
  --primary: #1a1a2e;
  --primary-light: #16213e;
  --secondary: #0f3460;
  --accent: #e94560;
  --accent-hover: #d63851;
  --text: #1a1a1a;
  --text-light: #6b7280;
  --text-inverse: #ffffff;
  --bg: #ffffff;
  --bg-alt: #f8f9fa;
  --bg-dark: #0a0a0a;
  --border: #e5e7eb;
  --glass: rgba(255, 255, 255, 0.08);
  --glass-border: rgba(255, 255, 255, 0.12);
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
  --shadow-md: 0 4px 12px rgba(0,0,0,0.1);
  --shadow-lg: 0 20px 60px rgba(0,0,0,0.15);
  --radius: 12px;
  --radius-sm: 8px;
  --font-heading: 'Playfair Display', serif;
  --font-body: 'Inter', sans-serif;
  --transition: 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
```

## Section Breakdown

### 1. Preloader

Full-screen overlay with brand logo or name that fades out after page load.

```html
<div id="preloader">
  <div class="preloader-content">
    <img src="logo.png" alt="Brand" class="preloader-logo">
    <div class="preloader-bar"><div class="preloader-fill"></div></div>
  </div>
</div>
```

CSS: fixed position, z-index 9999, fade-out animation after `window.onload`. Remove from DOM after animation completes.

### 2. Announcement Bar

Sliding ticker with 5+ messages. Infinite horizontal scroll animation.

```html
<div class="announcement-bar">
  <div class="announcement-track">
    <span>FREE SHIPPING ON ORDERS $75+</span>
    <span>NEW ARRIVALS JUST DROPPED</span>
    <span>PREMIUM QUALITY GUARANTEED</span>
    <span>EASY 30-DAY RETURNS</span>
    <span>SHOP NOW, PAY LATER</span>
    <!-- Duplicate set for seamless loop -->
  </div>
</div>
```

CSS: `overflow: hidden`, track uses `animation: scroll linear infinite`. Duplicate messages for seamless loop. Speed: ~30s for full cycle.

### 3. Navigation

Sticky glass-effect navbar. Transparent on hero, solid on scroll.

```html
<nav class="nav" id="mainNav">
  <div class="nav-container">
    <a href="#" class="nav-logo"><img src="logo.png" alt="Brand"></a>
    <ul class="nav-links">
      <li><a href="#collection">Shop</a></li>
      <li><a href="#story">Our Story</a></li>
      <li><a href="#reviews">Reviews</a></li>
      <li><a href="#contact">Contact</a></li>
    </ul>
    <div class="nav-actions">
      <button class="cart-btn" aria-label="Cart">
        <svg><!-- cart icon --></svg>
        <span class="cart-count">0</span>
      </button>
      <button class="mobile-toggle" aria-label="Menu">
        <span></span><span></span><span></span>
      </button>
    </div>
  </div>
</nav>
```

JS: Add `.scrolled` class on scroll > 50px. Toggle `.nav-open` for mobile menu. Glass effect via `backdrop-filter: blur(20px)`.

### 4. Hero Section

Full-viewport cinematic section with product image grid as background.

```html
<section class="hero" id="hero">
  <div class="hero-grid">
    <div class="hero-grid-item"><img src="product1.jpg" alt=""></div>
    <div class="hero-grid-item"><img src="product2.jpg" alt=""></div>
    <!-- 4-6 product images in a mosaic grid -->
  </div>
  <div class="hero-overlay"></div>
  <div class="hero-content">
    <p class="hero-subtitle">BRAND TAGLINE</p>
    <h1 class="hero-title">Headline Text</h1>
    <p class="hero-desc">Supporting description text.</p>
    <div class="hero-actions">
      <a href="#collection" class="btn btn-primary">Shop Collection</a>
      <a href="#story" class="btn btn-outline">Our Story</a>
    </div>
  </div>
</section>
```

CSS: `min-height: 100vh`, grid layout for background images, dark overlay gradient, content centered with `z-index: 2`. Subtle parallax on scroll via `transform: translateY()`.

### 5. Product Collection Grid

Responsive grid of product cards with hover interactions.

```html
<section class="collection" id="collection">
  <div class="section-header">
    <span class="section-label">COLLECTION</span>
    <h2>Shop Our Products</h2>
  </div>
  <div class="product-grid">
    <div class="product-card">
      <div class="product-image">
        <img src="product.jpg" alt="Product Name">
        <div class="product-overlay">
          <button class="quick-add">Quick Add</button>
        </div>
      </div>
      <div class="product-info">
        <h3>Product Name</h3>
        <div class="product-swatches">
          <span class="swatch" style="background:#1a1a2e" data-color="Navy"></span>
          <span class="swatch" style="background:#e94560" data-color="Rose"></span>
        </div>
        <div class="product-price">
          <span class="price">$49.99</span>
          <span class="price-compare">$64.99</span>
        </div>
      </div>
    </div>
  </div>
</section>
```

CSS: Grid `repeat(auto-fill, minmax(280px, 1fr))`, gap 24px. Card hover: image scale 1.05, overlay fade in. Swatches: 16px circles with border on active.

### 6. Product Detail (Mock PDP)

In-page or modal product detail with full e-commerce UI.

```html
<section class="product-detail" id="product">
  <div class="pdp-container">
    <div class="pdp-gallery">
      <div class="pdp-main-image"><img src="main.jpg" alt=""></div>
      <div class="pdp-thumbnails">
        <img src="thumb1.jpg" class="active" alt="">
        <img src="thumb2.jpg" alt="">
        <img src="thumb3.jpg" alt="">
      </div>
    </div>
    <div class="pdp-info">
      <span class="pdp-badge">BESTSELLER</span>
      <h1>Product Name</h1>
      <div class="pdp-rating"><!-- star SVGs --> (128 reviews)</div>
      <p class="pdp-price">$49.99 <span class="pdp-compare">$64.99</span></p>
      <div class="pdp-swatches">
        <label>Color:</label>
        <div class="swatch-group"><!-- color circles --></div>
      </div>
      <div class="pdp-sizes">
        <label>Size:</label>
        <div class="size-group">
          <button class="size-btn">XS</button>
          <button class="size-btn active">S</button>
          <button class="size-btn">M</button>
          <button class="size-btn">L</button>
          <button class="size-btn">XL</button>
        </div>
      </div>
      <div class="pdp-quantity">
        <button class="qty-btn minus">-</button>
        <input type="number" value="1" min="1">
        <button class="qty-btn plus">+</button>
      </div>
      <button class="btn btn-primary btn-full add-to-cart">Add to Cart</button>
      <div class="pdp-features">
        <div><svg><!-- icon --></svg> Free Shipping</div>
        <div><svg><!-- icon --></svg> Easy Returns</div>
        <div><svg><!-- icon --></svg> Premium Quality</div>
      </div>
    </div>
  </div>
</section>
```

JS: Thumbnail click swaps main image. Size/swatch buttons toggle `.active`. Quantity +/- buttons. Add-to-cart shows toast notification.

### 7. Brand Story

Editorial section with split layout.

```html
<section class="story" id="story">
  <div class="story-container">
    <div class="story-image">
      <img src="brand-story.jpg" alt="">
    </div>
    <div class="story-content">
      <span class="section-label">OUR STORY</span>
      <h2>Headline About the Brand</h2>
      <p>Brand narrative paragraph 1...</p>
      <p>Brand narrative paragraph 2...</p>
      <a href="#" class="btn btn-outline">Learn More</a>
    </div>
  </div>
</section>
```

CSS: Two-column grid, image with subtle parallax. On mobile, stacks vertically (image first).

### 8. Accessories Showcase

Secondary products in a horizontal scroll or smaller grid.

```html
<section class="accessories" id="accessories">
  <div class="section-header">
    <span class="section-label">ACCESSORIES</span>
    <h2>Complete Your Look</h2>
  </div>
  <div class="accessories-scroll">
    <div class="accessory-card">
      <img src="acc1.jpg" alt="">
      <h3>Accessory Name</h3>
      <p class="price">$19.99</p>
    </div>
    <!-- More cards -->
  </div>
</section>
```

CSS: Horizontal scroll with `overflow-x: auto`, snap points, hide scrollbar. Or grid on wider screens.

### 9. Trust Features

Icon grid showing brand promises.

```html
<section class="trust-features">
  <div class="trust-grid">
    <div class="trust-item">
      <svg><!-- shipping icon --></svg>
      <h3>Free Shipping</h3>
      <p>On orders over $75</p>
    </div>
    <div class="trust-item">
      <svg><!-- quality icon --></svg>
      <h3>Premium Quality</h3>
      <p>Medical-grade materials</p>
    </div>
    <div class="trust-item">
      <svg><!-- returns icon --></svg>
      <h3>Easy Returns</h3>
      <p>30-day return policy</p>
    </div>
    <div class="trust-item">
      <svg><!-- support icon --></svg>
      <h3>24/7 Support</h3>
      <p>Always here for you</p>
    </div>
  </div>
</section>
```

CSS: 4-column grid, centered text, icon 48px. On mobile: 2-column.

### 10. Testimonials

Auto-rotating carousel with star ratings.

```html
<section class="testimonials" id="reviews">
  <div class="section-header">
    <span class="section-label">REVIEWS</span>
    <h2>What Our Customers Say</h2>
  </div>
  <div class="testimonial-carousel">
    <div class="testimonial-track">
      <div class="testimonial-card">
        <div class="stars"><!-- 5 star SVGs --></div>
        <p class="testimonial-text">"Review text here..."</p>
        <div class="testimonial-author">
          <strong>Customer Name</strong>
          <span>Verified Buyer</span>
        </div>
      </div>
      <!-- More cards -->
    </div>
    <div class="testimonial-dots">
      <button class="dot active"></button>
      <button class="dot"></button>
      <button class="dot"></button>
    </div>
  </div>
</section>
```

JS: Auto-rotate every 5s. Dot navigation. Pause on hover. Swipe support on mobile via touch events.

### 11. Newsletter

Email capture with incentive offer.

```html
<section class="newsletter" id="contact">
  <div class="newsletter-container">
    <h2>Join the Family</h2>
    <p>Get 15% off your first order + exclusive drops.</p>
    <form class="newsletter-form">
      <input type="email" placeholder="Enter your email" required>
      <button type="submit" class="btn btn-primary">Subscribe</button>
    </form>
  </div>
</section>
```

CSS: Centered, max-width 600px, full-width input + button row. Dark background variant.

### 12. Footer

Full footer with links, social, payment icons, Biznomad credit.

```html
<footer class="footer">
  <div class="footer-container">
    <div class="footer-grid">
      <div class="footer-brand">
        <img src="logo.png" alt="Brand">
        <p>Brand description text.</p>
        <div class="social-links">
          <a href="#" aria-label="Instagram"><svg><!-- ig --></svg></a>
          <a href="#" aria-label="TikTok"><svg><!-- tiktok --></svg></a>
          <a href="#" aria-label="Facebook"><svg><!-- fb --></svg></a>
        </div>
      </div>
      <div class="footer-links">
        <h4>Shop</h4>
        <a href="#">All Products</a>
        <a href="#">New Arrivals</a>
        <a href="#">Sale</a>
      </div>
      <div class="footer-links">
        <h4>Company</h4>
        <a href="#">About Us</a>
        <a href="#">Contact</a>
        <a href="#">FAQ</a>
      </div>
      <div class="footer-links">
        <h4>Support</h4>
        <a href="#">Shipping</a>
        <a href="#">Returns</a>
        <a href="#">Size Guide</a>
      </div>
    </div>
    <div class="footer-bottom">
      <div class="payment-icons">
        <svg><!-- visa --></svg>
        <svg><!-- mastercard --></svg>
        <svg><!-- amex --></svg>
        <svg><!-- apple pay --></svg>
        <svg><!-- google pay --></svg>
      </div>
      <p>&copy; 2026 Brand Name. All rights reserved.</p>
      <p class="powered-by">Powered by <a href="https://biznomad.com">Biznomad</a></p>
    </div>
  </div>
</footer>
```

## JavaScript Patterns

### Scroll Reveal

```javascript
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('revealed');
      observer.unobserve(entry.target);
    }
  });
}, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });

document.querySelectorAll('.reveal').forEach(el => observer.observe(el));
```

Add `.reveal` class to elements. CSS: `.reveal { opacity: 0; transform: translateY(30px); transition: all 0.8s; }` and `.reveal.revealed { opacity: 1; transform: translateY(0); }`.

### Testimonial Slider

```javascript
let currentSlide = 0;
const slides = document.querySelectorAll('.testimonial-card');
const dots = document.querySelectorAll('.dot');

function goToSlide(n) {
  currentSlide = n;
  const track = document.querySelector('.testimonial-track');
  track.style.transform = `translateX(-${n * 100}%)`;
  dots.forEach((d, i) => d.classList.toggle('active', i === n));
}

setInterval(() => goToSlide((currentSlide + 1) % slides.length), 5000);
dots.forEach((dot, i) => dot.addEventListener('click', () => goToSlide(i)));
```

### Nav Scroll Effect

```javascript
window.addEventListener('scroll', () => {
  document.getElementById('mainNav').classList.toggle('scrolled', window.scrollY > 50);
});
```

### Preloader

```javascript
window.addEventListener('load', () => {
  const preloader = document.getElementById('preloader');
  preloader.style.opacity = '0';
  setTimeout(() => preloader.remove(), 500);
});
```

## Responsive Breakpoints

```css
/* Tablet landscape */
@media (max-width: 1024px) {
  .product-grid { grid-template-columns: repeat(3, 1fr); }
  .pdp-container { grid-template-columns: 1fr; }
  .footer-grid { grid-template-columns: repeat(2, 1fr); }
}

/* Tablet portrait */
@media (max-width: 768px) {
  .product-grid { grid-template-columns: repeat(2, 1fr); }
  .hero-title { font-size: 2.5rem; }
  .story-container { grid-template-columns: 1fr; }
  .trust-grid { grid-template-columns: repeat(2, 1fr); }
  .nav-links { display: none; } /* Show mobile menu */
}

/* Mobile */
@media (max-width: 480px) {
  .product-grid { grid-template-columns: 1fr; }
  .hero-title { font-size: 2rem; }
  .trust-grid { grid-template-columns: 1fr; }
  .footer-grid { grid-template-columns: 1fr; }
}
```

Always use `box-sizing: border-box` globally. Use `clamp()` for fluid typography: `font-size: clamp(2rem, 5vw, 4rem)`. Prefer `gap` over margins for grid/flex spacing.
