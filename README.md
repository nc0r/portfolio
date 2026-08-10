# BarberFlow Bot Portfolio

This repository contains a buyer-facing portfolio page, a sanitized Telegram barber shop automation bot, and an additional UI/frontend demo case.

- `index.html` and `styles.css` are ready for GitHub Pages.
- `bot/` contains the downloadable Python bot project in the local prepared package.
- `interface-craft/` contains a static UI design and frontend layout demo.
- No real tokens, local databases, virtual environments, or logs are included.

## Interface Craft UI demo

`interface-craft/` is a separate one-page demonstration of visual UI design and frontend layout capabilities. It uses clean HTML5, responsive CSS3, CSS Grid, Flexbox, glassmorphism styling, neon accents, hover transitions, keyframe animations, and vanilla JavaScript.

After this branch is merged and GitHub Pages is published from `main`, open it here:

```text
https://nc0r.github.io/portfolio/interface-craft/
```

To preview it locally, open:

```text
interface-craft/index.html
```

No build step is required.

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
