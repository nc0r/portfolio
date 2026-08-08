# BarberFlow Bot Portfolio

This repository contains a buyer-facing portfolio page and a sanitized Telegram barber shop automation bot.

- `index.html` and `styles.css` are ready for GitHub Pages.
- `bot/` contains the downloadable Python bot project in the local prepared package.
- No real tokens, local databases, virtual environments, or logs are included.

## Run the bot locally

```powershell
cd bot
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python bot.py
```

## Run the admin panel

```powershell
cd bot
.\.venv\Scripts\activate
uvicorn web.app:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000`.
