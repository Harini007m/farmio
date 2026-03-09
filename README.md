# 🥛 Farmio — Farm-to-Door Milk Platform

A web application that directly connects **local dairy farmers** with **consumers** in their area. Farmers can list their daily milk availability, and consumers can browse nearby farms and place orders — all in one place.

---

## ✨ Features

### For Farmers
- **Dashboard** — View today's milk listings, total ordered quantity, remaining milk, and a summary of all recent orders.
- **Add Milk Listings** — Log morning and evening milk availability with price per litre, collection time, and delivery estimate.
- **Mark Milk as Externally Sold** — Record milk sold to third parties (e.g., tea shops, restaurants) to keep remaining quantity accurate.
- **Manage Products** — List dairy products (e.g., ghee, paneer, curd) with quantity and price.
- **Order Management** — View and update the status of both milk orders and product orders.

### For Consumers
- **Nearby Farmer Discovery** — Browse farmers within **7 km** of your location, sorted by distance (uses Haversine formula).
- **Real-time Availability** — See exactly how many litres are remaining for each farmer today, accounting for existing orders and external sales.
- **Place Orders** — Choose morning or evening delivery and specify how many litres you need.
- **Shop Dairy Products** — Browse and buy products listed by farmers.
- **Order History** — Track all your milk and product orders in one place.

---

## 🛠️ Tech Stack

| Layer      | Technology                        |
|------------|-----------------------------------|
| Backend    | Python · Flask                    |
| Database   | SQLite 3                          |
| Auth       | Werkzeug (password hashing)       |
| Frontend   | HTML · Jinja2 · CSS · JavaScript  |
| Distance   | Haversine formula (geolocation)   |

---

## 📁 Project Structure

```
farmio/                        # Repo root
├── app.py                     # Flask application — all routes and business logic
├── database.db                # SQLite database (auto-created on first run, git-ignored)
├── .gitignore                 # Python / Flask ignore rules
├── README.md
├── static/
│   ├── css/
│   │   └── style.css          # Global stylesheet
│   └── js/
│       └── script.js          # Frontend scripts
└── templates/
    ├── base.html              # Shared base layout
    ├── index.html             # Landing page
    ├── register.html          # Registration (farmer / consumer)
    ├── login.html             # Login page
    ├── farmer_dashboard.html  # Farmer home
    ├── add_milk.html          # Add milk listing form
    ├── consumer_dashboard.html # Consumer home (nearby farmers)
    ├── place_order.html       # Order placement
    ├── products.html          # Products listing
    └── orders.html            # Order history (shared by both roles)
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

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS / Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install flask werkzeug
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Open your browser** and visit `http://localhost:5000`

> The database (`database.db`) is created automatically on first run.

---

## 🗃️ Database Schema

| Table            | Description                                      |
|------------------|--------------------------------------------------|
| `users`          | All users (farmers & consumers) with coordinates |
| `farmers`        | Farmer profile, farm name, capacity, base price  |
| `milk_listings`  | Daily milk availability (morning + evening)      |
| `orders`         | Milk orders placed by consumers                  |
| `products`       | Dairy products listed by farmers                 |
| `product_orders` | Orders placed for dairy products                 |

---

## 🌍 Location & Distance

When registering, users grant access to their **GPS coordinates** (via browser geolocation). These are stored and used to:
- Show consumers only farmers within **7 km**, sorted nearest first.
- Let farmers and consumers see their location on their profile.

---

## 🔐 Authentication & Roles

- Passwords are hashed using **Werkzeug's** `generate_password_hash`.
- Two roles: `farmer` and `consumer` — each has separate dashboards and route guards.
- Session-based authentication with `@login_required`, `@farmer_required`, and `@consumer_required` decorators.

---

## 📋 Key Routes

| Route                                    | Role     | Description                       |
|------------------------------------------|----------|-----------------------------------|
| `/`                                      | Public   | Landing page with platform stats  |
| `/register`                              | Public   | Register as farmer or consumer    |
| `/login`                                 | Public   | Log in                            |
| `/farmer/dashboard`                      | Farmer   | Main farmer dashboard             |
| `/farmer/add-milk`                       | Farmer   | Add a milk listing                |
| `/farmer/mark-milk-used/<listing_id>`    | Farmer   | Record externally sold milk       |
| `/farmer/products`                       | Farmer   | Manage dairy products             |
| `/farmer/orders`                         | Farmer   | View and manage all orders        |
| `/consumer/dashboard`                    | Consumer | Browse nearby farmers             |
| `/consumer/order/<farmer_id>`            | Consumer | Place a milk order                |
| `/consumer/products`                     | Consumer | Browse and buy dairy products     |
| `/consumer/orders`                       | Consumer | View order history                |

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).
