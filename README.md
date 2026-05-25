# SoleVault 👟

SoleVault is a modern full-stack eCommerce web application built using Python Django. The platform is designed for seamless online shopping with secure authentication, product management, cart functionality, order tracking, and a powerful admin dashboard.

---

# 🚀 Features

## 👤 User Features

* User Registration & Login
* JWT / Session Authentication
* Browse Products by Categories
* Product Search & Filtering
* Product Detail Page
* Shopping Cart System
* Wishlist Functionality
* Secure Checkout
* Order Tracking
* User Profile Management
* Responsive UI Design

---

## 🛠️ Admin Features

* Admin Dashboard
* Product Management
* Category Management
* Order Management
* User Management
* Inventory Management
* Sales Analytics

---

# 🧰 Tech Stack

## Backend

* Python
* Django

## Frontend

* HTML5
* CSS3
* JavaScript

## Database

* PostgreSQL

## Authentication

* Django Authentication
* JWT Authentication

## Payment Integration

* Razorpay

---

# 📂 Project Structure

```bash id="yb1cde"
SoleVault/
│
├── core/                   # Main Django Project
├── products/               # Product App
├── users/                  # Authentication & Users
├── cart/                   # Cart Functionality
├── orders/                 # Orders & Checkout
├── templates/              # HTML Templates
├── static/                 # CSS, JS, Images
├── media/                  # Uploaded Files
├── requirements.txt
├── manage.py
└── README.md
```

---

# ⚙️ Installation

## 1️⃣ Clone the Repository

```bash id="5ylj52"
git clone https://github.com/yourusername/solevault.git
```

---

## 2️⃣ Navigate to Project Folder

```bash id="d0zzf0"
cd solevault
```

---

## 3️⃣ Create Virtual Environment

### Windows

```bash id="k9ngzy"
python -m venv venv
venv\Scripts\activate
```

### macOS/Linux

```bash id="sop20m"
python3 -m venv venv
source venv/bin/activate
```

---

## 4️⃣ Install Dependencies

```bash id="0g6rsy"
pip install -r requirements.txt
```

---

# 🔑 Environment Variables

Create a `.env` file in the root directory.

```env id="hzh9z0"
SECRET_KEY=your_secret_key
DEBUG=True

DATABASE_NAME=solevault
DATABASE_USER=postgres
DATABASE_PASSWORD=password
DATABASE_HOST=localhost
DATABASE_PORT=5432

RAZORPAY_KEY=your_key
RAZORPAY_SECRET=your_secret
```

---

# 🗄️ Run Migrations

```bash id="c8uvjv"
python manage.py makemigrations
python manage.py migrate
```

---

# 👤 Create Superuser

```bash id="gqrm1s"
python manage.py createsuperuser
```

---

# ▶️ Run the Server

```bash id="rt6d6x"
python manage.py runserver
```

Open in browser:

```bash id="0j83ii"
http://127.0.0.1:8000/
```

---

# 📸 Screenshots

## 🏠 Home Page

*Add screenshot here*

## 👟 Product Page

*Add screenshot here*

## 🛒 Cart Page

*Add screenshot here*

## 📦 Admin Dashboard

*Add screenshot here*

---

# 🔒 Security Features

* CSRF Protection
* Secure Authentication
* Password Hashing
* Protected Admin Routes
* Form Validation
* Secure Payment Gateway Integration

---

# 📈 Future Enhancements

* AI Product Recommendations
* Multi-Vendor Marketplace
* Dark Mode
* Real-Time Notifications
* Advanced Analytics Dashboard

---

# 🤝 Contributing

1. Fork the Repository

2. Create a Feature Branch

```bash id="hv5mna"
git checkout -b feature-name
```

3. Commit Changes

```bash id="lj0a0w"
git commit -m "Added new feature"
```

4. Push to Branch

```bash id="jlwmca"
git push origin feature-name
```

5. Open a Pull Request

---

# 📄 License

This project is licensed under the MIT License.

---

# 👨‍💻 Developer

Developed by Mohammed Aqif

---

# ⭐ Support

If you like this project, give it a ⭐ on GitHub!
