import os
from datetime import date
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from psycopg2.extras import RealDictCursor
from pydantic import BaseModel
import requests

app = FastAPI(title="Hotel Booking & Catalog API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_HOST = os.getenv("DB_HOST", "db")
DB_NAME = os.getenv("DB_NAME", "hotel_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASSWORD", "secretpassword")
WEB_SERVICE_URL = os.getenv("WEB_SERVICE_URL", "http://web-service:5000")

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        cursor_factory=RealDictCursor
    )

class HotelCreate(BaseModel):
    name: str
    city: str
    stars: int = 4
    price_standard: float
    price_deluxe: float
    price_suite: float
    description: str
    image_url: Optional[str] = "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=600&q=80"

class EstimateRequest(BaseModel):
    hotel_id: int
    room_type: str
    check_in: date
    check_out: date

class BookingCreate(BaseModel):
    hotel_id: int
    guest_name: str
    room_type: str
    check_in: date
    check_out: date

@app.get("/api/hotels")
def get_hotels():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM hotels ORDER BY id ASC;")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

@app.post("/api/hotels")
def create_hotel(hotel: HotelCreate):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO hotels (name, city, stars, price_standard, price_deluxe, price_suite, description, image_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING *;
            """,
            (hotel.name, hotel.city, hotel.stars, hotel.price_standard, hotel.price_deluxe, hotel.price_suite, hotel.description, hotel.image_url)
        )
        new_hotel = cur.fetchone()
        conn.commit()
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail=f"Ошибка добавления отеля: {str(e)}")
    cur.close()
    conn.close()
    return new_hotel

@app.delete("/api/hotels/{hotel_id}")
def delete_hotel(hotel_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM hotels WHERE id = %s RETURNING id;", (hotel_id,))
    deleted = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    if not deleted:
        raise HTTPException(status_code=404, detail="Отель не найден")
    return {"status": "ok", "deleted_id": hotel_id}

@app.get("/api/bookings")
def get_bookings():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM bookings ORDER BY id DESC;")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

@app.delete("/api/bookings/{booking_id}")
def delete_booking(booking_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM bookings WHERE id = %s RETURNING id;", (booking_id,))
    deleted = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    if not deleted:
        raise HTTPException(status_code=404, detail="Бронирование не найдено")
    return {"status": "ok", "deleted_id": booking_id}

@app.get("/api/stats")
def get_stats():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS total_count, COALESCE(SUM(total_price), 0) AS total_revenue, COALESCE(AVG(total_price), 0) AS avg_price FROM bookings;")
    stats = cur.fetchone()
    cur.close()
    conn.close()
    return {
        "total_count": int(stats["total_count"]),
        "total_revenue": float(stats["total_revenue"]),
        "avg_price": round(float(stats["avg_price"]), 2)
    }

@app.post("/api/estimate")
def estimate_cost(req: EstimateRequest):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM hotels WHERE id = %s;", (req.hotel_id,))
    hotel = cur.fetchone()
    cur.close()
    conn.close()
    if not hotel:
        raise HTTPException(status_code=404, detail="Отель не найден")

    room_field = f"price_{req.room_type.lower()}"
    if room_field not in hotel or hotel[room_field] is None:
        raise HTTPException(status_code=400, detail="Неверная категория номера")

    price_per_night = float(hotel[room_field])

    try:
        resp = requests.post(
            f"{WEB_SERVICE_URL}/calculate",
            json={
                "check_in": str(req.check_in),
                "check_out": str(req.check_out),
                "base_price_per_night": price_per_night
            },
            timeout=5
        )
        if resp.status_code != 200:
            detail_msg = resp.text
            try:
                detail_msg = resp.json().get("detail", detail_msg)
            except Exception:
                pass
            raise HTTPException(status_code=resp.status_code, detail=detail_msg)
        calc_data = resp.json()
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="Web-сервис расчета цен недоступен")

    return {
        "hotel_name": hotel["name"],
        "room_type": req.room_type,
        "nights": calc_data["nights"],
        "rate_per_night": calc_data["rate_per_night"],
        "total_price": calc_data["total_price"]
    }

@app.post("/api/bookings")
def create_booking(booking: BookingCreate):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM hotels WHERE id = %s;", (booking.hotel_id,))
    hotel = cur.fetchone()
    if not hotel:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Отель не найден")

    room_field = f"price_{booking.room_type.lower()}"
    if room_field not in hotel or hotel[room_field] is None:
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Неверная категория номера")

    price_per_night = float(hotel[room_field])

    try:
        resp = requests.post(
            f"{WEB_SERVICE_URL}/calculate",
            json={
                "check_in": str(booking.check_in),
                "check_out": str(booking.check_out),
                "base_price_per_night": price_per_night
            },
            timeout=5
        )
        if resp.status_code != 200:
            detail_msg = resp.text
            try:
                detail_msg = resp.json().get("detail", detail_msg)
            except Exception:
                pass
            cur.close()
            conn.close()
            raise HTTPException(status_code=resp.status_code, detail=detail_msg)
        calc_data = resp.json()
    except requests.RequestException:
        cur.close()
        conn.close()
        raise HTTPException(status_code=503, detail="Web-сервис расчета цен недоступен")

    total_price = calc_data["total_price"]

    try:
        cur.execute(
            """
            INSERT INTO bookings (hotel_id, hotel_name, guest_name, room_type, check_in, check_out, total_price)
            VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING *;
            """,
            (hotel["id"], hotel["name"], booking.guest_name, booking.room_type, booking.check_in, booking.check_out, total_price)
        )
        new_record = cur.fetchone()
        conn.commit()
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail=f"Ошибка сохранения: {str(e)}")

    cur.close()
    conn.close()
    return new_record
