# 🥛 Farmio — Premium Farm-to-Door Milk Platform

A premium Hyperlocal Milk Supply Platform that directly connects **local dairy farmers**, **consumers**, and **delivery agents**. Farmio ensures pure, fresh milk and handcrafted dairy products reach your doorstep with complete transparency and real-time tracking.

---

## ✨ Features

### For Farmers
- **Strategic Dashboard** — Real-time analytics on milk listings, active subscription pipelines, and value-added product inventory.
- **Freshness Control** — Field-level tracking of **Collection Time** and **Delivery Windows** for every batch.
- **Batch Processing** — Convert surplus milk into high-value derivatives (Paneer, Ghee, Butter) to ensure zero waste.
- **Dynamic Order Management** — Integrated tracking for both instant milk orders and batch product deliveries.

### For Consumers
- **Proximity Discovery** — Smart matching with farmers within **7 km**, utilizing high-precision geolocation.
- **Fulfillment Transparency** — View exact milking times and delivery schedules before purchasing.
- **Milk Continuity Plans (Subscriptions)** — 21-day recurring delivery agreements for consistent, worry-free supply.
- **Categorized Archive** — Separate tracking for **Milk History** and **Product History** with live fulfillment journey maps.
- **Integrated Wallet** — Seamless, cashless transactions with a built-in virtual wallet.

### For Delivery Agents
- **Route Optimization Dashboard** — Interactive **Leaflet.js Maps** visualizing pickup (farm) and drop-off (consumer) locations.
- **Unified fulfillment** — Handle both fresh milk supply and value-added product deliveries in a single workflow.
- **Real-time Status Sync** — Instantly update order states (Preparing, Picked Up, Out for Delivery, Delivered) for consumers.

---

## 🎨 Design Aesthetic

Farmio features a **Premium Light Theme** visual identity, optimized for a professional and trustworthy farm-to-table experience.
- **Curated Palette** — High-contrast white backgrounds, slate typography, and **Soft Green (#22C55E)** accents.
- **Premium UI Components** — Shadow-rich cards, glassmorphic navigation, and micro-animated fulfillment timelines.
- **Modern Iconography** — Descriptive SVG icons for a clean, minimalist professional look.

---

## 🛠️ Tech Stack

| Layer      | Technology                                    |
|------------|-----------------------------------------------|
| Backend    | Python · Flask                                |
| Database   | SQLite 3                                      |
| Mapping    | Leaflet.js (OpenStreetMap)                    |
| Auth       | Werkzeug (password hashing)                   |
| Frontend   | HTML5 · CSS3 (Vanilla) · Bootstrap 5 · Jinja2 |
| Design     | Premium "Farm-Fresh" Soft Green System        |
| Logic      | JavaScript (ES6+)                             |

---

## 📁 Project Structure

```
farmio/                        # Repo root
├── app.py                     # Core Flask application & business logic
├── database.db                # SQLite database (auto-created)
├── reset_db.py                # Command to reset and re-initialize schema
├── static/
│   ├── css/
│   │   └── style.css          # Design system tokens & styles
│   └── js/
│       └── script.js          # Interactive frontend logic
└── templates/
    ├── base.html              # Shared layout & navigation
    ├── farmer_dashboard.html  # Farmer workspace with inventory tracking
    ├── consumer_dashboard.html # Hyperlocal discovery marketplace
    ├── delivery_dashboard.html # Map-integrated routing for agents
    ├── order_history.html     # Tabbed Categorized order archive
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
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install flask
   ```

4. **Launch Application**
   ```bash
   python app.py
   ```

### 🧹 Database Reset
To clear all data and reset the schema to the latest version:
```bash
python reset_db.py
```

---

## 🗃️ Database Schema Highlights

| Table            | Description                                              |
|------------------|----------------------------------------------------------|
| `users`          | Unified accounts (Farmer, Consumer, Delivery Partner)    |
| `milk_listings`  | Morning/Evening batches with collection/delivery windows |
| `delivery_tasks` | Integrated tracking for both milk and product deliveries |
| `product_orders` | Marketplace transaction records for derivatives          |
| `reviews`        | Consumer-to-Farmer feedback system                       |

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).
