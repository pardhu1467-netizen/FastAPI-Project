# 💪 BeFit Gym Management API (FastAPI)

A fully functional Gym Management Backend System built using **FastAPI**.  
This project demonstrates REST API design, validation, filtering, sorting, pagination, and multi-step workflows.

---

## 🚀 Features

### 🏋️ Plans Management
- View all gym plans
- Get plan by ID
- Add new plans
- Update plan details
- Delete plans (with validation)
- Plan summary (cheapest, expensive, features)

---

### 👥 Membership System
- Enroll members with validation
- Discount logic (6 months → 10%, 12 months → 20%)
- Referral discount (extra 5%)
- EMI processing fee handling
- Freeze & Reactivate memberships

---

### 📚 Class Booking System
- Book fitness classes
- Cancel bookings
- Validate active membership before booking

---

### 🔍 Advanced Features
- Search plans (by name / classes / trainer)
- Filter plans (price, duration, features)
- Sort plans (price, name, duration)
- Pagination (plans & memberships)
- Combined browsing endpoint

---

## 🛠️ Tech Stack

- **Python 3**
- **FastAPI**
- **Pydantic**
- **Uvicorn**

---

## 📂 Project Structure


main.py
README.md
requirements.txt


---

## ▶️ How to Run

### 1️⃣ Install dependencies
```bash
pip install -r requirements.txt
```
### 2️⃣ Run server
uvicorn main:app --reload
### 3️⃣ Open in browser
Swagger UI: http://127.0.0.1:8000/docs
Redoc: http://127.0.0.1:8000/redoc

# 📌 Sample API Endpoints
Home
GET /
Plans
GET /plans
GET /plans/{plan_id}
GET /plans/summary
POST /plans
PUT /plans/{plan_id}
DELETE /plans/{plan_id}
Memberships
GET /memberships
POST /memberships
PUT /memberships/{id}/freeze
PUT /memberships/{id}/reactivate
Classes
POST /classes/book
GET /classes/bookings
DELETE /classes/cancel/{booking_id}
Advanced
GET /plans/search
GET /plans/filter
GET /plans/sort
GET /plans/page
GET /plans/browse

# 🧪 Validation Highlights
Minimum name length enforced
Phone number length validation
Duplicate plan prevention
Cannot delete plan with active members
Membership required for class booking

#💡 Key Learning Outcomes
REST API design
Request validation using Pydantic
Business logic implementation
Query parameters handling
Clean and scalable backend structure
