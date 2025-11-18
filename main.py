import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime

from database import db, create_document, get_documents
from schemas import Menuitem, Service, Order, Orderitem, Customer
from bson import ObjectId

app = FastAPI(title="Bbrother Cafe API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def serialize_value(v):
    if isinstance(v, ObjectId):
        return str(v)
    if isinstance(v, datetime):
        return v.isoformat()
    if isinstance(v, list):
        return [serialize_value(x) for x in v]
    if isinstance(v, dict):
        return {k: serialize_value(val) for k, val in v.items()}
    return v


def serialize_doc(doc: dict):
    if not doc:
        return doc
    doc = {**doc}
    if "_id" in doc:
        doc["id"] = str(doc.pop("_id"))
    return serialize_value(doc)


@app.get("/")
def read_root():
    return {"message": "Bbrother Cafe backend is running"}


@app.get("/api/health")
def health():
    return {"ok": True}


# ----------------------- MENU -----------------------
@app.get("/api/menu")
def get_menu():
    try:
        items = get_documents("menuitem")
        return [serialize_doc(i) for i in items]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/menu", status_code=201)
def create_menu_item(item: Menuitem):
    try:
        new_id = create_document("menuitem", item)
        doc = db["menuitem"].find_one({"_id": ObjectId(new_id)})
        return serialize_doc(doc)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --------------------- SERVICES ---------------------
@app.get("/api/services")
def get_services():
    try:
        items = get_documents("service")
        return [serialize_doc(i) for i in items]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/services", status_code=201)
def create_service(svc: Service):
    try:
        new_id = create_document("service", svc)
        doc = db["service"].find_one({"_id": ObjectId(new_id)})
        return serialize_doc(doc)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------- ORDERS ----------------------
class CreateOrderRequest(BaseModel):
    items: List[Orderitem]
    customer: Customer
    table_number: Optional[str] = None


@app.post("/api/orders", status_code=201)
def create_order(payload: CreateOrderRequest):
    try:
        # Recalculate total from database to prevent tampering
        total = 0.0
        for it in payload.items:
            try:
                mid = ObjectId(it.menu_item_id)
            except Exception:
                raise HTTPException(status_code=400, detail=f"Invalid menu_item_id: {it.menu_item_id}")
            menu_doc = db["menuitem"].find_one({"_id": mid})
            if not menu_doc:
                raise HTTPException(status_code=404, detail=f"Menu item not found: {it.menu_item_id}")
            price = float(menu_doc.get("price", it.unit_price))
            total += price * int(it.quantity)

        order_doc = Order(
            items=payload.items,
            customer=payload.customer,
            total_amount=round(total, 2),
            table_number=payload.table_number,
        )
        new_id = create_document("order", order_doc)
        created = db["order"].find_one({"_id": ObjectId(new_id)})
        return serialize_doc(created)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/orders")
def list_orders(limit: int = 20):
    try:
        docs = get_documents("order")
        docs = sorted(docs, key=lambda d: d.get("created_at"), reverse=True)
        if limit:
            docs = docs[:limit]
        return [serialize_doc(d) for d in docs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
