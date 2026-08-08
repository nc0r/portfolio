# BarberFlow Telegram Bot

BarberFlow is a ready-to-customize Telegram bot for barber shops and small salons. Clients can check services, pick an available time, leave contact details, and receive reminders. Staff can manage slots and bookings from Telegram commands or the local FastAPI admin panel.

This public version is sanitized for GitHub: it includes `.env.example`, but no real bot token, database, logs, or virtual environment.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Fill `.env` with your Telegram bot token and admin ID.

## Run

Telegram bot:

```powershell
python bot.py
```

Admin panel:

```powershell
uvicorn web.app:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000`.

## Telegram Admin Commands

- `/admin` - show admin help.
- `/add_slot YYYY-MM-DD HH:MM` - add an appointment slot.
- `/delete_slot YYYY-MM-DD HH:MM` - delete a free slot.
- `/view YYYY-MM-DD` - view schedule and clients.
- `/stats` - show booking statistics.
