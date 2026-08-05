# 🛍️ Outfitters-Style E-Commerce Platform — Product Requirements Document (PRD)

> **Project**: StyleHub E-Commerce  
> **Stack**: Django 5.x · Jinja2 Templates · PostgreSQL · Django REST Framework (optional APIs)  
> **Inspired by**: Outfitters Pakistan  
> **Date**: July 2026

---

## 1. 🎯 Project Overview

A full-featured fashion e-commerce platform inspired by Outfitters — offering clothing, accessories, and lifestyle products. The platform will support browsing, filtering, cart management, secure checkout, order tracking, and an admin panel for store management.

### Goals
- Build a production-ready Django e-commerce site
- Use Jinja2 for fast, flexible templating
- PostgreSQL as the primary database
- Django REST Framework for cart/wishlist/order APIs (AJAX-friendly)
- Mobile-responsive, premium UI with modern aesthetics

---

## 2. 🧱 Technology Stack

| Layer | Technology |
|-------|-----------|
| Backend Framework | Django 5.x |
| Templating Engine | Jinja2 (via `django-jinja`) |
| Database | PostgreSQL 16 |
| ORM | Django ORM |
| REST APIs | Django REST Framework (DRF) |
| Authentication | Django AllAuth |
| Image Handling | Pillow + Cloudinary (or local media) |
| Payments | Stripe / JazzCash (pluggable) |
| Search | Django-filter + PostgreSQL Full-Text Search |
| Caching | Redis (session + cart caching) |
| Task Queue | Celery + Redis (order emails, notifications) |
| Static Files | WhiteNoise (dev) / AWS S3 (prod) |
| Deployment | Gunicorn + Nginx + Docker |
| Environment Config | python-decouple / .env |

---

## 3. 📁 Complete File & Folder Structure

```
stylehub/                          ← Project root
│
├── manage.py
├── requirements.txt
├── .env                           ← Secrets (DB, keys)
├── .env.example
├── docker-compose.yml
├── Dockerfile
├── README.md
│
├── config/                        ← Django project config
│   ├── __init__.py
│   ├── settings/
│   │   ├── base.py               ← Shared settings
│   │   ├── development.py        ← Dev overrides
│   │   └── production.py         ← Prod overrides
│   ├── urls.py                   ← Root URL config
│   ├── wsgi.py
│   └── asgi.py
│
├── apps/                          ← All Django apps
│   │
│   ├── core/                      ← Shared utilities
│   │   ├── models.py             ← Abstract base models (timestamps)
│   │   ├── mixins.py
│   │   ├── utils.py
│   │   └── context_processors.py ← Global Jinja2 context
│   │
│   ├── accounts/                  ← User auth & profiles
│   │   ├── models.py             ← CustomUser, Address
│   │   ├── views.py
│   │   ├── forms.py
│   │   ├── urls.py
│   │   ├── serializers.py
│   │   └── signals.py
│   │
│   ├── catalog/                   ← Products & Categories
│   │   ├── models.py             ← Category, Product, ProductImage, ProductVariant
│   │   ├── views.py              ← List, Detail, Search, Filter
│   │   ├── filters.py            ← django-filter FilterSets
│   │   ├── urls.py
│   │   ├── serializers.py        ← DRF serializers
│   │   └── admin.py
│   │
│   ├── cart/                      ← Shopping cart (session + DB)
│   │   ├── models.py             ← Cart, CartItem
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── serializers.py        ← DRF for AJAX cart ops
│   │   └── cart_manager.py       ← Cart logic class
│   │
│   ├── orders/                    ← Order management
│   │   ├── models.py             ← Order, OrderItem, OrderStatus
│   │   ├── views.py              ← Checkout, confirmation, history
│   │   ├── urls.py
│   │   ├── serializers.py
│   │   └── signals.py            ← Send email on order placed
│   │
│   ├── payments/                  ← Payment gateway integration
│   │   ├── models.py             ← Payment, Transaction
│   │   ├── views.py              ← Stripe/JazzCash webhooks
│   │   ├── urls.py
│   │   └── gateway.py            ← Pluggable gateway interface
│   │
│   ├── wishlist/                  ← Saved items
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── serializers.py
│   │
│   ├── reviews/                   ← Product reviews & ratings
│   │   ├── models.py             ← Review, Rating
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── serializers.py
│   │
│   ├── promotions/                ← Coupons, discounts, sales
│   │   ├── models.py             ← Coupon, DiscountRule, Sale
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── validators.py
│   │
│   └── notifications/             ← Email & in-app notifications
│       ├── models.py
│       ├── tasks.py              ← Celery tasks
│       └── emails.py             ← Email templates
│
├── templates/                     ← Jinja2 templates (global)
│   ├── jinja2/                   ← Jinja2 root
│   │   ├── base.html             ← Master layout
│   │   ├── partials/
│   │   │   ├── _navbar.html
│   │   │   ├── _footer.html
│   │   │   ├── _sidebar.html
│   │   │   ├── _product_card.html
│   │   │   ├── _cart_sidebar.html
│   │   │   ├── _breadcrumb.html
│   │   │   └── _messages.html
│   │   ├── accounts/
│   │   │   ├── login.html
│   │   │   ├── register.html
│   │   │   ├── profile.html
│   │   │   └── addresses.html
│   │   ├── catalog/
│   │   │   ├── home.html
│   │   │   ├── product_list.html
│   │   │   ├── product_detail.html
│   │   │   ├── category.html
│   │   │   └── search_results.html
│   │   ├── cart/
│   │   │   └── cart.html
│   │   ├── orders/
│   │   │   ├── checkout.html
│   │   │   ├── order_confirm.html
│   │   │   └── order_history.html
│   │   ├── wishlist/
│   │   │   └── wishlist.html
│   │   └── errors/
│   │       ├── 404.html
│   │       └── 500.html
│
├── static/                        ← Static assets
│   ├── css/
│   │   ├── main.css              ← Global styles
│   │   ├── variables.css         ← CSS custom properties
│   │   ├── components/
│   │   │   ├── navbar.css
│   │   │   ├── product-card.css
│   │   │   ├── cart.css
│   │   │   ├── checkout.css
│   │   │   └── buttons.css
│   │   └── pages/
│   │       ├── home.css
│   │       ├── product-list.css
│   │       └── product-detail.css
│   ├── js/
│   │   ├── main.js               ← Global JS
│   │   ├── cart.js               ← AJAX cart operations
│   │   ├── wishlist.js           ← AJAX wishlist
│   │   ├── product.js            ← Variant selection, gallery
│   │   ├── filters.js            ← Filter sidebar JS
│   │   └── checkout.js           ← Payment form handling
│   └── images/
│       └── logo.svg
│
└── media/                         ← Uploaded product images (dev)
```

---

## 4. 🗄️ Database Schema (Key Models)

### `accounts` App
```
CustomUser
- id, email (unique), username, first_name, last_name
- phone_number, date_of_birth, avatar
- is_active, is_staff, date_joined

Address
- user (FK → CustomUser)
- label (Home/Work/Other)
- street, city, province, postal_code, country
- is_default
```

### `catalog` App
```
Category
- name, slug, parent (self-FK), image, description
- is_active, display_order

Product
- name, slug, sku, description, category (FK)
- base_price, sale_price, is_on_sale
- brand, gender (Men/Women/Unisex/Kids)
- is_active, is_featured, created_at

ProductImage
- product (FK), image, alt_text, is_primary, display_order

ProductVariant
- product (FK), size, color, color_hex
- stock_quantity, additional_price
- sku_suffix

Tag  (M2M with Product)
- name, slug
```

### `cart` App
```
Cart
- user (FK, nullable), session_key
- created_at, updated_at

CartItem
- cart (FK), variant (FK → ProductVariant)
- quantity, added_at
```

### `orders` App
```
Order
- user (FK), order_number (auto-generated)
- status (pending/confirmed/shipped/delivered/cancelled)
- shipping_address (JSON), billing_address (JSON)
- subtotal, discount_amount, shipping_cost, total
- payment_method, payment_status
- notes, created_at, updated_at

OrderItem
- order (FK), variant (FK)
- product_name, size, color  ← snapshot at time of order
- quantity, unit_price, total_price

OrderStatusHistory
- order (FK), status, note, changed_at, changed_by
```

### `payments` App
```
Payment
- order (FK), gateway (stripe/jazzcash)
- transaction_id, amount, currency
- status (pending/success/failed/refunded)
- gateway_response (JSONField), created_at
```

### `promotions` App
```
Coupon
- code, discount_type (percent/fixed)
- discount_value, min_order_amount
- usage_limit, used_count
- valid_from, valid_until, is_active

ProductSale
- product (FK), discount_percent
- start_date, end_date
```

### `reviews` App
```
Review
- product (FK), user (FK)
- rating (1-5), title, body
- is_approved, created_at
```

---

## 5. 🌐 URL Structure

```
/                              → Home page
/products/                     → All products
/products/<slug>/              → Product detail
/category/<slug>/              → Category page
/search/                       → Search results
/cart/                         → Cart page
/cart/add/                     → API: Add to cart (POST)
/cart/update/                  → API: Update qty (PATCH)
/cart/remove/                  → API: Remove item (DELETE)
/wishlist/                     → Wishlist page
/wishlist/toggle/              → API: Toggle wishlist
/checkout/                     → Checkout
/checkout/apply-coupon/        → API: Apply coupon
/orders/                       → Order history
/orders/<order_number>/        → Order detail
/accounts/login/               → Login
/accounts/register/            → Register
/accounts/profile/             → User profile
/accounts/addresses/           → Manage addresses
/api/v1/products/              → DRF product listing
/api/v1/cart/                  → DRF cart endpoints
/admin/                        → Django admin panel
```

---

## 6. 🎨 Frontend Design System

### Design Tokens (CSS Variables)
```css
--color-primary: #1a1a2e;       /* Deep navy */
--color-accent: #e94560;        /* Vibrant red-pink */
--color-accent-2: #f5a623;      /* Gold */
--color-surface: #16213e;       /* Dark surface */
--color-bg: #0f3460;            /* Background */
--color-text: #eaeaea;
--color-muted: #a0a0b0;
--font-heading: 'Outfit', sans-serif;
--font-body: 'Inter', sans-serif;
--radius-card: 12px;
--shadow-card: 0 8px 32px rgba(0,0,0,0.3);
--transition-smooth: all 0.3s cubic-bezier(0.4,0,0.2,1);
```

### Key UI Components
- **Sticky mega-menu navbar** with category dropdowns
- **Product cards** with hover zoom, quick-add button, wishlist icon
- **Slide-out cart drawer** (AJAX, no page reload)
- **Filter sidebar** with price range slider, color swatches, size chips
- **Product image gallery** with zoom + thumbnail strip
- **Size/color variant selector** with live stock feedback
- **Checkout stepper** (Address → Payment → Confirm)
- **Toast notifications** for cart/wishlist actions
- **Skeleton loaders** for async content

---

## 7. 🔌 Django REST Framework API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/products/` | Product list with filters |
| GET | `/api/v1/products/<slug>/` | Product detail |
| GET | `/api/v1/cart/` | Get current cart |
| POST | `/api/v1/cart/items/` | Add item to cart |
| PATCH | `/api/v1/cart/items/<id>/` | Update quantity |
| DELETE | `/api/v1/cart/items/<id>/` | Remove item |
| GET/POST | `/api/v1/wishlist/` | Get/toggle wishlist |
| POST | `/api/v1/orders/` | Place order |
| GET | `/api/v1/orders/<id>/` | Order detail |
| POST | `/api/v1/coupons/validate/` | Validate coupon code |

---

## 8. 📦 Phase-wise Implementation Plan

---

### 🟢 PHASE 1 — Foundation & Setup (Week 1-2)

**Goal**: Get the project skeleton running with auth and basic product display.

#### Tasks:
- [ ] Initialize Django project with modular settings (`base`, `dev`, `prod`)
- [ ] Configure PostgreSQL connection via `.env`
- [ ] Install and configure **Jinja2** (`django-jinja`) as template backend
- [ ] Set up `apps/` directory structure
- [ ] Create **`core`** app with abstract base models (timestamps)
- [ ] Create **`accounts`** app:
  - CustomUser model (email-based auth)
  - Login, Register, Logout views
  - User profile + address management
  - Jinja2 templates for all auth pages
- [ ] Create **`catalog`** app (read-only):
  - Category, Product, ProductImage, ProductVariant models
  - Admin panel registration with inline images/variants
  - Home page (featured products)
  - Category listing page
  - Basic product detail page
- [ ] Static file setup (CSS variables, base layout, navbar, footer)
- [ ] Set up Django admin with custom branding

**Deliverable**: Working site with auth + product browsing (no cart yet)

---

### 🟡 PHASE 2 — Shopping Experience (Week 3-4)

**Goal**: Full product browsing + cart + wishlist functionality.

#### Tasks:
- [ ] **Product List Page**:
  - Pagination
  - Filter by category, gender, size, color, price range
  - Sort by (newest, price low-high, popular)
  - Django-filter integration
- [ ] **Product Detail Page**:
  - Image gallery with thumbnails + zoom
  - Variant selector (size, color) with stock indication
  - Related products section
  - Breadcrumb navigation
- [ ] **Search**:
  - Full-text search (PostgreSQL `SearchVector`)
  - Search suggestions (AJAX)
- [ ] **`cart`** app:
  - Cart model (session-based for guests, DB for logged-in users)
  - Cart manager class
  - DRF API endpoints for add/update/remove
  - Slide-out cart drawer (AJAX + Jinja2 partial)
  - Cart page (full view)
  - Guest ↔ user cart merge on login
- [ ] **`wishlist`** app:
  - Toggle wishlist via AJAX
  - Wishlist page
- [ ] **`reviews`** app:
  - Submit review form (logged-in only)
  - Display star ratings on product page
- [ ] CSS components: product cards, filter sidebar, cart drawer, gallery

**Deliverable**: Full shopping UX — browse → add to cart → wishlist

---

### 🟠 PHASE 3 — Checkout & Orders (Week 5-6)

**Goal**: Complete the purchase flow end-to-end.

#### Tasks:
- [ ] **`promotions`** app:
  - Coupon model + validation logic
  - Apply coupon at checkout (AJAX)
  - Sale badge on product cards
- [ ] **Checkout Flow**:
  - Step 1: Shipping address (select saved or enter new)
  - Step 2: Order summary + coupon
  - Step 3: Payment method selection
  - Step 4: Confirmation page
- [ ] **`orders`** app:
  - Order creation from cart
  - Order number generation (e.g., `SH-2026-00001`)
  - Order status model + history
  - Order history page (my orders)
  - Order detail page with status timeline
- [ ] **`payments`** app:
  - Payment model
  - Cash on Delivery (COD) support
  - Stripe integration (card payments)
  - Payment webhook handler
- [ ] **`notifications`** app:
  - Celery task for order confirmation email
  - HTML email templates
- [ ] Inventory management:
  - Stock decrement on order placement
  - Out-of-stock handling in cart/checkout

**Deliverable**: Complete purchase flow — cart → checkout → payment → confirmation

---

### 🔵 PHASE 4 — Admin, CMS & Advanced Features (Week 7-8)

**Goal**: Rich admin experience + advanced user features.

#### Tasks:
- [ ] **Enhanced Django Admin**:
  - Custom admin dashboard with stats
  - Product admin with inline image/variant management
  - Order admin with status update actions
  - Bulk product operations (activate/deactivate)
  - Export orders to CSV
- [ ] **Product Management**:
  - `django-import-export` for bulk product import/export
  - Product tagging system
  - Featured collections / banners management
- [ ] **Homepage CMS**:
  - Hero banner management via admin
  - Featured categories section
  - "New Arrivals" and "On Sale" dynamic sections
- [ ] **User Dashboard**:
  - Profile settings page
  - Change password
  - Address book management
  - Order history with filters
  - Return/refund request form
- [ ] **SEO & Performance**:
  - Meta tags for all pages (Jinja2 blocks)
  - `sitemap.xml` generation
  - `robots.txt`
  - Product schema markup (JSON-LD)
  - Image lazy loading
  - Django query optimization (select_related, prefetch_related)
- [ ] Redis caching for:
  - Home page product lists
  - Category trees
  - Frequently viewed products

**Deliverable**: Full admin control + polished user dashboard + SEO-ready

---

### 🟣 PHASE 5 — Polish, Testing & Deployment (Week 9-10)

**Goal**: Production-ready, tested, and deployed.

#### Tasks:
- [ ] **Testing**:
  - Unit tests for models (pytest-django)
  - View tests for all key flows
  - API endpoint tests (DRF test client)
  - Cart logic tests
- [ ] **Security**:
  - CSRF protection on all forms
  - Rate limiting on login/register (django-ratelimit)
  - Input sanitization
  - Secure password validators
  - HTTPS enforcement
  - Django security checklist (`manage.py check --deploy`)
- [ ] **Performance**:
  - Whitenoise for static files
  - Database index review
  - Django Debug Toolbar removed for prod
- [ ] **Deployment**:
  - Docker + docker-compose setup
  - Nginx reverse proxy config
  - Gunicorn WSGI server
  - PostgreSQL in Docker / hosted (e.g., Supabase, Neon)
  - Environment variable management
  - CI/CD pipeline (GitHub Actions)
  - Static/media to AWS S3 or Cloudinary
- [ ] **Final QA**:
  - Cross-browser testing
  - Mobile responsiveness audit
  - Payment flow end-to-end test
  - Performance audit (Lighthouse)

**Deliverable**: Production-deployed, secure, performant e-commerce site

---

## 9. 📦 Python Requirements

```txt
# Core
django>=5.0
psycopg2-binary          # PostgreSQL driver
django-jinja             # Jinja2 integration
python-decouple          # .env management
Pillow                   # Image processing

# Auth
django-allauth           # Social + email auth

# REST API
djangorestframework
djangorestframework-simplejwt

# Filtering & Search
django-filter

# Payments
stripe

# Task Queue
celery
redis
django-celery-beat

# Caching
django-redis

# Admin Enhancements
django-import-export
django-admin-rangefilter

# Static Files
whitenoise

# Dev Tools
django-debug-toolbar
pytest-django
factory-boy

# Production
gunicorn
```

---

## 10. 🗺️ Phase Summary Table

| Phase | Focus | Duration | Key Output |
|-------|-------|----------|------------|
| 1 | Foundation + Auth + Products (browse only) | 2 weeks | Browsable product catalog |
| 2 | Cart + Wishlist + Search + Filters | 2 weeks | Full shopping experience |
| 3 | Checkout + Orders + Payments | 2 weeks | Complete purchase flow |
| 4 | Admin + CMS + Dashboard + SEO | 2 weeks | Admin control + user dashboard |
| 5 | Testing + Security + Deployment | 2 weeks | Live production site |

**Total Estimated Duration**: ~10 weeks (solo developer)  
**Total Estimated Duration**: ~5-6 weeks (2-person team)

---

## 11. 📌 Open Questions / Decisions Needed

> [!IMPORTANT]
> **Payment Gateway**: Stripe (international) vs JazzCash/EasyPaisa (Pakistan local)? Both supported in Phase 3 but one should be primary.

> [!IMPORTANT]
> **Image Hosting**: Local `/media/` (development) vs Cloudinary vs AWS S3 (production)? Cloudinary is easiest to set up.

> [!NOTE]
> **Social Login**: Should Phase 1 include Google/Facebook login via django-allauth, or just email/password first?

> [!NOTE]
> **Multi-vendor**: Is this a single-vendor store (like Outfitters) or multi-vendor marketplace? This PRD assumes single-vendor.

> [!NOTE]
> **Mobile App**: DRF APIs are included if you later want a React Native or Flutter mobile app companion.
