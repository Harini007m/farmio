# 🥛 Farmio — Premium Farm-to-Door Milk Platform

A premium web application that directly connects **local dairy farmers** with **consumers** in their area. Farmio streamlines the supply chain, ensuring pure, fresh milk reaches your doorstep while maximizing earnings for verified farmers.

---

## ✨ Features

### For Farmers
- **Strategic Dashboard** — Real-time analytics on milk listings, active subscription pipelines, and value-added product inventory.
- **Supply Chain Management** — Optimized morning/evening listing system with automated remaining quantity calculation.
- **Batch Processing** — Convert surplus milk into high-value derivatives (Paneer, Ghee, Butter) to ensure zero waste.
- **Dynamic Order Management** — Tracking system for both instant milk orders and batch product deliveries.

### For Consumers
- **Proximity Discovery** — Smart matching with farmers within **7 km**, utilizing high-precision geolocation.
- **Milk Continuity Plans (Subscriptions)** — 21-day recurring delivery agreements for consistent, worry-free supply.
- **Vacation Orchestration** — Pause deliveries instantly with integrated vacation mode for any duration.
- **Integrated Wallet** — Seamless, cashless transactions with a built-in virtual wallet and transaction history.
- **Marketplace Store** — Purchase artisanal dairy products directly from local farmers.

---

## 🎨 Design Aesthetic

Farmio features a **Premium Indigo & Slate** visual identity, designed for a professional and trustworthy user experience.
- **Sophisticated Palette** — Transition from "base green" to a curated Indigo (`#4665f0`) and Slate design system.
- **Modern Iconography** — Scalable SVG icons and abstract visuals for a clean, professional look.
- **Responsive Premium UI** — Mobile-first, glassmorphic navigation and shadow-rich components for a high-end feel.

---

## 🛠️ Tech Stack

| Layer      | Technology                        |
|------------|-----------------------------------|
| Backend    | Python · Flask                    |
| Database   | SQLite 3                          |
| Auth       | Werkzeug (password hashing)       |
| Frontend   | HTML5 · CSS3 (Vanilla) · Jinja2   |
| Design     | Premium Indigo Design System      |
| Logic      | JavaScript (ES6+)                 |

---

## 📁 Project Structure

```
farmio/                        # Repo root
├── app.py                     # Core Flask application & business logic
├── database.db                # SQLite database (auto-created)
├── static/
│   ├── css/
│   │   └── style.css          # Premium design system tokens & styles
│   └── js/
│       └── script.js          # Interactive frontend logic
└── templates/
    ├── base.html              # Shared layout & navigation
    ├── index.html             # Landing page with abstract visuals
    ├── farmer_dashboard.html  # Farmer workspace
    ├── consumer_dashboard.html # Marketplace discovery
    ├── subscribe.html         # Subscription configuration
    ├── subscriptions.html     # Contract management
    ├── wallet.html            # Financial management
    ├── vacation.html          # Delivery pause scheduling
    └── products.html          # Value-added derivatives store
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- pip

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Harini007m/farmio.git
   cd farmio
   ```

2. **Initialize Environment**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install flask
   ```

4. **Launch Application**
   ```bash
   python app.py
   ```

---

## 🗃️ Database Schema

| Table                 | Description                                      |
|-----------------------|--------------------------------------------------|
| `users`               | Unified user accounts with GPS coordinates       |
| `farmers`             | Verified farmer profiles and farm metadata       |
| `milk_listings`       | Morning/Evening availability batches             |
| `orders`              | Instant one-time milk purchase records           |
| `subscriptions`       | 21-day recurring delivery contracts              |
| `products`            | Value-added dairy batch listings                 |
| `product_orders`      | Marketplace transaction records                  |
| `wallet_transactions` | Comprehensive financial audit log                |
| `vacation_dates`      | User-scheduled delivery pause dates              |

---

## 📋 Strategic Routes

| Route                                  | Role     | Description                       |
|----------------------------------------|----------|-----------------------------------|
| `/`                                    | Public   | Landing page with platform stats  |
| `/consumer/dashboard`                  | Consumer | Proximity-based discovery         |
| `/consumer/subscribe/<id>`             | Consumer | Configure 21-day continuity plan  |
| `/consumer/subscriptions`              | Consumer | Manage active supply agreements   |
| `/consumer/wallet`                     | Consumer | Recharge & track balance          |
| `/consumer/vacation`                   | Consumer | Schedule delivery pauses          |
| `/farmer/dashboard`                    | Farmer   | Operation management center       |
| `/farmer/products`                     | Farmer   | Market derivative batches         |

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).
