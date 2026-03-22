from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, Field
from typing import List, Optional

app = FastAPI()

# -------------------- DAY 1 --------------------

@app.get("/")
def home():
    return {"message": "Welcome to IronFit Gym"}


# Plans Data
plans = [
    {"id": 1, "name": "Basic", "duration_months": 1, "price": 1000, "includes_classes": False, "includes_trainer": False},
    {"id": 2, "name": "Standard", "duration_months": 3, "price": 2500, "includes_classes": True, "includes_trainer": False},
    {"id": 3, "name": "Premium", "duration_months": 6, "price": 4500, "includes_classes": True, "includes_trainer": True},
    {"id": 4, "name": "Elite", "duration_months": 12, "price": 8000, "includes_classes": True, "includes_trainer": True},
    {"id": 5, "name": "Pro", "duration_months": 9, "price": 6000, "includes_classes": True, "includes_trainer": False},
]


@app.get("/plans")
def get_plans():
    prices = [p["price"] for p in plans]
    return {
        "plans": plans,
        "total": len(plans),
        "min_price": min(prices),
        "max_price": max(prices)
    }


@app.get("/plans/summary")
def plans_summary():
    cheapest = min(plans, key=lambda x: x["price"])
    expensive = max(plans, key=lambda x: x["price"])

    return {
        "total_plans": len(plans),
        "includes_classes": sum(1 for p in plans if p["includes_classes"]),
        "includes_trainer": sum(1 for p in plans if p["includes_trainer"]),
        "cheapest": {"name": cheapest["name"], "price": cheapest["price"]},
        "expensive": {"name": expensive["name"], "price": expensive["price"]}
    }


@app.get("/plans/{plan_id}")
def get_plan(plan_id: int):
    for plan in plans:
        if plan["id"] == plan_id:
            return plan
    raise HTTPException(status_code=404, detail="Plan not found")


# Memberships
memberships = []
membership_counter = 1


@app.get("/memberships")
def get_memberships():
    return {"memberships": memberships, "total": len(memberships)}


# -------------------- DAY 2 & 3 --------------------

class EnrollRequest(BaseModel):
    member_name: str = Field(..., min_length=2)
    plan_id: int = Field(..., gt=0)
    phone: str = Field(..., min_length=10)
    start_month: str = Field(..., min_length=3)
    payment_mode: str = "cash"
    referral_code: str = ""


def find_plan(plan_id: int):
    for plan in plans:
        if plan["id"] == plan_id:
            return plan
    return None


def calculate_membership_fee(price, duration, payment_mode, referral_code):
    discount = 0

    if duration >= 12:
        discount += 20
    elif duration >= 6:
        discount += 10

    if referral_code:
        discount += 5

    discounted_price = price * (1 - discount / 100)

    processing_fee = 200 if payment_mode == "emi" else 0

    total = discounted_price + processing_fee

    return {
        "base_price": price,
        "discount_percent": discount,
        "processing_fee": processing_fee,
        "total_fee": int(total)
    }


@app.post("/memberships", status_code=201)
def create_membership(data: EnrollRequest):
    global membership_counter

    plan = find_plan(data.plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    fee_details = calculate_membership_fee(
        plan["price"],
        plan["duration_months"],
        data.payment_mode,
        data.referral_code
    )

    membership = {
        "membership_id": membership_counter,
        "member_name": data.member_name,
        "plan_name": plan["name"],
        "duration": plan["duration_months"],
        "monthly_cost": fee_details["total_fee"] // plan["duration_months"],
        "total_fee": fee_details["total_fee"],
        "status": "active",
        "discount_breakdown": fee_details
    }

    memberships.append(membership)
    membership_counter += 1

    return membership


@app.get("/plans/filter")
def filter_plans(
    max_price: Optional[int] = None,
    max_duration: Optional[int] = None,
    includes_classes: Optional[bool] = None,
    includes_trainer: Optional[bool] = None
):
    result = plans

    if max_price is not None:
        result = [p for p in result if p["price"] <= max_price]

    if max_duration is not None:
        result = [p for p in result if p["duration_months"] <= max_duration]

    if includes_classes is not None:
        result = [p for p in result if p["includes_classes"] == includes_classes]

    if includes_trainer is not None:
        result = [p for p in result if p["includes_trainer"] == includes_trainer]

    return {"plans": result, "total": len(result)}


# -------------------- DAY 4 --------------------

class NewPlan(BaseModel):
    name: str = Field(..., min_length=2)
    duration_months: int = Field(..., gt=0)
    price: int = Field(..., gt=0)
    includes_classes: bool = False
    includes_trainer: bool = False


@app.post("/plans", status_code=201)
def add_plan(plan: NewPlan):
    for p in plans:
        if p["name"].lower() == plan.name.lower():
            raise HTTPException(status_code=400, detail="Plan already exists")

    new_plan = {
        "id": len(plans) + 1,
        **plan.dict()
    }
    plans.append(new_plan)
    return new_plan


@app.put("/plans/{plan_id}")
def update_plan(
    plan_id: int,
    price: Optional[int] = None,
    includes_classes: Optional[bool] = None,
    includes_trainer: Optional[bool] = None
):
    plan = find_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    if price is not None:
        plan["price"] = price
    if includes_classes is not None:
        plan["includes_classes"] = includes_classes
    if includes_trainer is not None:
        plan["includes_trainer"] = includes_trainer

    return plan


@app.delete("/plans/{plan_id}")
def delete_plan(plan_id: int):
    plan = find_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    for m in memberships:
        if m["plan_name"] == plan["name"] and m["status"] == "active":
            raise HTTPException(status_code=400, detail="Active memberships exist")

    plans.remove(plan)
    return {"message": "Plan deleted"}


# -------------------- DAY 5 --------------------

class Booking(BaseModel):
    member_name: str
    class_name: str
    class_date: str


class_bookings = []
class_counter = 1


@app.post("/classes/book")
def book_class(data: Booking):
    global class_counter

    valid_member = any(
        m["member_name"] == data.member_name and m["status"] == "active"
        for m in memberships
    )

    if not valid_member:
        raise HTTPException(status_code=400, detail="No active membership")

    booking = {
        "booking_id": class_counter,
        **data.dict()
    }

    class_bookings.append(booking)
    class_counter += 1

    return booking


@app.get("/classes/bookings")
def get_bookings():
    return {"bookings": class_bookings}


@app.delete("/classes/cancel/{booking_id}")
def cancel_booking(booking_id: int):
    for b in class_bookings:
        if b["booking_id"] == booking_id:
            class_bookings.remove(b)
            return {"message": "Booking cancelled"}

    raise HTTPException(status_code=404, detail="Booking not found")


@app.put("/memberships/{membership_id}/freeze")
def freeze_membership(membership_id: int):
    for m in memberships:
        if m["membership_id"] == membership_id:
            m["status"] = "frozen"
            return m
    raise HTTPException(status_code=404, detail="Membership not found")


@app.put("/memberships/{membership_id}/reactivate")
def reactivate_membership(membership_id: int):
    for m in memberships:
        if m["membership_id"] == membership_id:
            m["status"] = "active"
            return m
    raise HTTPException(status_code=404, detail="Membership not found")


# -------------------- DAY 6 --------------------

@app.get("/plans/search")
def search_plans(keyword: str):
    keyword = keyword.lower()

    result = [
        p for p in plans
        if keyword in p["name"].lower()
        or (keyword == "classes" and p["includes_classes"])
        or (keyword == "trainer" and p["includes_trainer"])
    ]

    return {"results": result, "total_found": len(result)}


@app.get("/plans/sort")
def sort_plans(sort_by: str = "price"):
    if sort_by not in ["price", "name", "duration_months"]:
        raise HTTPException(status_code=400, detail="Invalid sort field")

    return sorted(plans, key=lambda x: x[sort_by])


@app.get("/plans/page")
def paginate_plans(page: int = 1, limit: int = 2):
    start = (page - 1) * limit
    end = start + limit

    total_pages = (len(plans) + limit - 1) // limit

    return {
        "page": page,
        "total_pages": total_pages,
        "plans": plans[start:end]
    }


@app.get("/memberships/search")
def search_members(name: str):
    result = [m for m in memberships if name.lower() in m["member_name"].lower()]
    return {"results": result}


@app.get("/memberships/sort")
def sort_members(sort_by: str = "total_fee"):
    return sorted(memberships, key=lambda x: x.get(sort_by, 0))


@app.get("/memberships/page")
def paginate_members(page: int = 1, limit: int = 2):
    start = (page - 1) * limit
    end = start + limit
    return memberships[start:end]


@app.get("/plans/browse")
def browse_plans(
    keyword: Optional[str] = None,
    includes_classes: Optional[bool] = None,
    includes_trainer: Optional[bool] = None,
    sort_by: str = "price",
    order: str = "asc",
    page: int = 1,
    limit: int = 2
):
    result = plans

    if keyword:
        result = [p for p in result if keyword.lower() in p["name"].lower()]

    if includes_classes is not None:
        result = [p for p in result if p["includes_classes"] == includes_classes]

    if includes_trainer is not None:
        result = [p for p in result if p["includes_trainer"] == includes_trainer]

    reverse = True if order == "desc" else False
    result = sorted(result, key=lambda x: x[sort_by], reverse=reverse)

    start = (page - 1) * limit
    end = start + limit

    return {
        "total": len(result),
        "page": page,
        "results": result[start:end]
    }