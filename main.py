from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

app = FastAPI()

# -------------------- DATA --------------------

plans = [
    {"id": 1, "name": "Basic", "duration_months": 1, "price": 1000, "includes_classes": False, "includes_trainer": False},
    {"id": 2, "name": "Standard", "duration_months": 3, "price": 2500, "includes_classes": True, "includes_trainer": False},
    {"id": 3, "name": "Premium", "duration_months": 6, "price": 4500, "includes_classes": True, "includes_trainer": True},
    {"id": 4, "name": "Elite", "duration_months": 12, "price": 8000, "includes_classes": True, "includes_trainer": True},
    {"id": 5, "name": "Pro", "duration_months": 9, "price": 6000, "includes_classes": True, "includes_trainer": False},
]

memberships = []
membership_counter = 1

bookings = []
booking_counter = 1

# -------------------- HOME --------------------

@app.get("/")
def home():
    return {"message": "Welcome to BeFit Gym"}

# -------------------- PLANS --------------------

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
        "cheapest": cheapest,
        "expensive": expensive
    }


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


@app.get("/plans/search")
def search_plans(keyword: str):
    keyword = keyword.lower()
    result = [
        p for p in plans
        if keyword in p["name"].lower()
        or (keyword == "classes" and p["includes_classes"])
        or (keyword == "trainer" and p["includes_trainer"])
    ]
    return {"results": result, "total": len(result)}


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
        "data": plans[start:end]
    }


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

    if sort_by not in ["price", "name", "duration_months"]:
        raise HTTPException(status_code=400, detail="Invalid sort field")

    if order not in ["asc", "desc"]:
        raise HTTPException(status_code=400, detail="Invalid order")

    result = sorted(result, key=lambda x: x[sort_by], reverse=(order == "desc"))

    start = (page - 1) * limit
    end = start + limit
    total_pages = (len(result) + limit - 1) // limit

    return {
        "total": len(result),
        "page": page,
        "total_pages": total_pages,
        "data": result[start:end]
    }


# ✅ KEEP THIS LAST (IMPORTANT)
@app.get("/plans/{plan_id}")
def get_plan(plan_id: int):
    for p in plans:
        if p["id"] == plan_id:
            return p
    raise HTTPException(status_code=404, detail="Plan not found")


# -------------------- MEMBERSHIPS --------------------

@app.get("/memberships")
def get_memberships():
    return {"memberships": memberships, "total": len(memberships)}


class EnrollRequest(BaseModel):
    member_name: str = Field(..., min_length=2)
    plan_id: int = Field(..., gt=0)
    phone: str = Field(..., min_length=10)
    start_month: str = Field(..., min_length=3)
    payment_mode: str = "cash"
    referral_code: str = ""


def find_plan(plan_id):
    for p in plans:
        if p["id"] == plan_id:
            return p
    return None


def calculate_fee(price, duration, payment_mode, referral):
    discount = 0

    if duration >= 12:
        discount += 20
    elif duration >= 6:
        discount += 10

    if referral:
        discount += 5

    final_price = price * (1 - discount / 100)
    processing = 200 if payment_mode == "emi" else 0

    return int(final_price + processing), discount, processing


@app.post("/memberships", status_code=201)
def create_membership(data: EnrollRequest):
    global membership_counter

    plan = find_plan(data.plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    total, discount, processing = calculate_fee(
        plan["price"], plan["duration_months"], data.payment_mode, data.referral_code
    )

    m = {
        "membership_id": membership_counter,
        "member_name": data.member_name,
        "plan_name": plan["name"],
        "duration": plan["duration_months"],
        "total_fee": total,
        "monthly_cost": total // plan["duration_months"],
        "discount_percent": discount,
        "processing_fee": processing,
        "status": "active"
    }

    memberships.append(m)
    membership_counter += 1
    return m


@app.get("/memberships/search")
def m_search(name: str):
    return [m for m in memberships if name.lower() in m["member_name"].lower()]


@app.get("/memberships/sort")
def m_sort(sort_by: str = "total_fee"):
    if sort_by not in ["total_fee", "duration"]:
        raise HTTPException(status_code=400, detail="Invalid sort field")
    return sorted(memberships, key=lambda x: x.get(sort_by, 0))


@app.get("/memberships/page")
def m_page(page: int = 1, limit: int = 2):
    start = (page - 1) * limit
    end = start + limit
    total_pages = (len(memberships) + limit - 1) // limit

    return {
        "page": page,
        "total_pages": total_pages,
        "data": memberships[start:end]
    }


# -------------------- BOOKINGS --------------------

class Booking(BaseModel):
    member_name: str
    class_name: str
    class_date: str


@app.post("/classes/book")
def book(data: Booking):
    global booking_counter

    valid = any(m["member_name"] == data.member_name and m["status"] == "active" for m in memberships)

    if not valid:
        raise HTTPException(status_code=400, detail="No active membership")

    b = {"booking_id": booking_counter, **data.dict()}
    bookings.append(b)
    booking_counter += 1
    return b


@app.get("/classes/bookings")
def get_bookings():
    return bookings


@app.delete("/classes/cancel/{bid}")
def cancel(bid: int):
    for b in bookings:
        if b["booking_id"] == bid:
            bookings.remove(b)
            return {"message": "Cancelled"}
    raise HTTPException(status_code=404, detail="Not found")


@app.put("/memberships/{mid}/freeze")
def freeze(mid: int):
    for m in memberships:
        if m["membership_id"] == mid:
            m["status"] = "frozen"
            return m
    raise HTTPException(status_code=404, detail="Not found")


@app.put("/memberships/{mid}/reactivate")
def reactivate(mid: int):
    for m in memberships:
        if m["membership_id"] == mid:
            m["status"] = "active"
            return m
    raise HTTPException(status_code=404, detail="Not found")
