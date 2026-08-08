"""FastAPI administration panel for barber shop slots and bookings."""

import logging
import secrets
import sqlite3
import sys
from datetime import date as date_type, datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware


ROOT_DIR = Path(__file__).resolve().parents[1]
WEB_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import (  # noqa: E402
    ADMIN_ID,
    BUSINESS_NAME,
    PORTFOLIO_URL,
    PRICE_LIST,
    WEB_ADMIN_PASSWORD,
    WEB_COOKIE_SECURE,
    WEB_SECRET_KEY,
)
from database.db import get_db_connection, init_db  # noqa: E402


logger = logging.getLogger(__name__)
app = FastAPI(title="BarberFlow Admin Panel", version="1.0.0")
app.add_middleware(
    SessionMiddleware,
    secret_key=WEB_SECRET_KEY,
    session_cookie="barberflow_admin_session",
    same_site="strict",
    https_only=WEB_COOKIE_SECURE,
    max_age=8 * 60 * 60,
)
app.mount("/static", StaticFiles(directory=WEB_DIR / "static"), name="static")
templates = Jinja2Templates(directory=WEB_DIR / "templates")


class SlotCreate(BaseModel):
    date: str
    time: str


@app.on_event("startup")
def startup() -> None:
    init_db()
    if WEB_SECRET_KEY == "change-me-before-production":
        logger.warning("WEB_SECRET_KEY uses the development default")
    if not WEB_ADMIN_PASSWORD:
        logger.warning("WEB_ADMIN_PASSWORD is unset; ADMIN_ID is used as a legacy password")


def _expected_password() -> str:
    return WEB_ADMIN_PASSWORD or str(ADMIN_ID)


def _logged_in(request: Request) -> bool:
    return request.session.get("is_admin") is True


def _template_context(request: Request, **values):
    context = {
        "request": request,
        "business_name": BUSINESS_NAME,
        "portfolio_url": PORTFOLIO_URL,
        "price_list": PRICE_LIST,
    }
    context.update(values)
    return context


def _require_api_admin(request: Request) -> None:
    if not _logged_in(request):
        raise HTTPException(status_code=401, detail="Unauthorized")


def _validate_slot(value_date: str, value_time: str) -> tuple[str, str]:
    try:
        parsed = datetime.strptime(f"{value_date} {value_time}", "%Y-%m-%d %H:%M")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Use date YYYY-MM-DD and time HH:MM") from exc
    if parsed <= datetime.now():
        raise HTTPException(status_code=422, detail="Slot must be in the future")
    return parsed.strftime("%Y-%m-%d"), parsed.strftime("%H:%M")


@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    if _logged_in(request):
        return RedirectResponse("/dashboard", status_code=303)
    return templates.TemplateResponse("login.html", _template_context(request))


@app.post("/login")
async def login(request: Request, password: str = Form(...)):
    if secrets.compare_digest(password, _expected_password()):
        request.session.clear()
        request.session["is_admin"] = True
        return RedirectResponse("/dashboard", status_code=303)
    return templates.TemplateResponse("login.html", _template_context(request, error="Invalid password"), status_code=401)


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    if not _logged_in(request):
        return RedirectResponse("/", status_code=303)
    today = date_type.today().isoformat()
    with get_db_connection() as connection:
        stats = {
            "total_bookings": connection.execute("SELECT COUNT(*) FROM bookings").fetchone()[0],
            "active_bookings": connection.execute("SELECT COUNT(*) FROM bookings WHERE date >= ?", (today,)).fetchone()[0],
            "occupied_slots": connection.execute("SELECT COUNT(*) FROM slots WHERE is_booked = 1").fetchone()[0],
            "free_slots": connection.execute("SELECT COUNT(*) FROM slots WHERE is_booked = 0 AND date >= ?", (today,)).fetchone()[0],
        }
        recent = connection.execute("SELECT * FROM bookings WHERE date >= ? ORDER BY date, time LIMIT 10", (today,)).fetchall()
    return templates.TemplateResponse("dashboard.html", _template_context(request, stats=stats, recent_bookings=recent))


@app.get("/slots", response_class=HTMLResponse)
async def slots_page(request: Request, date: Optional[str] = None):
    if not _logged_in(request):
        return RedirectResponse("/", status_code=303)
    with get_db_connection() as connection:
        if date:
            slots = connection.execute(
                """
                SELECT s.*, b.name AS client_name, b.phone AS client_phone, b.service AS client_service
                FROM slots s LEFT JOIN bookings b ON s.date = b.date AND s.time = b.time
                WHERE s.date = ? ORDER BY s.time
                """,
                (date,),
            ).fetchall()
        else:
            slots = connection.execute(
                """
                SELECT s.*, b.name AS client_name, b.phone AS client_phone, b.service AS client_service
                FROM slots s LEFT JOIN bookings b ON s.date = b.date AND s.time = b.time
                WHERE s.date >= ? ORDER BY s.date, s.time LIMIT 200
                """,
                (date_type.today().isoformat(),),
            ).fetchall()
    return templates.TemplateResponse("slots.html", _template_context(request, slots=slots, selected_date=date or ""))


@app.post("/slots/add")
async def add_slot(slot: SlotCreate, request: Request):
    _require_api_admin(request)
    value_date, value_time = _validate_slot(slot.date, slot.time)
    try:
        with get_db_connection() as connection:
            connection.execute("INSERT INTO slots (date, time, is_booked) VALUES (?, ?, 0)", (value_date, value_time))
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="Slot already exists") from exc
    return {"success": True, "message": "Slot added successfully"}


@app.delete("/slots/{slot_id}")
async def delete_slot(slot_id: int, request: Request):
    _require_api_admin(request)
    with get_db_connection() as connection:
        slot = connection.execute("SELECT is_booked FROM slots WHERE id = ?", (slot_id,)).fetchone()
        if slot is None:
            raise HTTPException(status_code=404, detail="Slot not found")
        if slot["is_booked"]:
            raise HTTPException(status_code=409, detail="Cannot delete a booked slot")
        connection.execute("DELETE FROM slots WHERE id = ?", (slot_id,))
    return {"success": True, "message": "Slot deleted successfully"}


@app.get("/bookings", response_class=HTMLResponse)
async def bookings_page(request: Request, date: Optional[str] = None):
    if not _logged_in(request):
        return RedirectResponse("/", status_code=303)
    today = date_type.today().isoformat()
    with get_db_connection() as connection:
        if date:
            bookings = connection.execute("SELECT * FROM bookings WHERE date = ? ORDER BY time", (date,)).fetchall()
        else:
            bookings = connection.execute("SELECT * FROM bookings WHERE date >= ? ORDER BY date, time LIMIT 200", (today,)).fetchall()
        today_count = connection.execute("SELECT COUNT(*) FROM bookings WHERE date = ?", (today,)).fetchone()[0]
        upcoming_count = connection.execute("SELECT COUNT(*) FROM bookings WHERE date > ?", (today,)).fetchone()[0]
    return templates.TemplateResponse(
        "bookings.html",
        _template_context(
            request,
            bookings=bookings,
            selected_date=date or "",
            today_bookings_count=today_count,
            upcoming_bookings_count=upcoming_count,
        ),
    )


@app.delete("/bookings/{booking_id}")
async def delete_booking(booking_id: int, request: Request):
    _require_api_admin(request)
    with get_db_connection() as connection:
        connection.execute("BEGIN IMMEDIATE")
        booking = connection.execute("SELECT date, time FROM bookings WHERE id = ?", (booking_id,)).fetchone()
        if booking is None:
            raise HTTPException(status_code=404, detail="Booking not found")
        connection.execute("UPDATE slots SET is_booked = 0 WHERE date = ? AND time = ?", (booking["date"], booking["time"]))
        connection.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
    return {"success": True, "message": "Booking deleted successfully"}


@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=303)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
