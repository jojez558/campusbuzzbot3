# 🎓 CampusBuzz Kenya — Telegram Bot

> **Your #1 student hub for WhatsApp groups across Kenyan universities 🇰🇪**  
> Connecting students smarter. Built for speed, scale, and premium UX.

---

## ✨ Features

| Feature | Status |
|---|---|
| Force-Join channel gate | ✅ |
| 60+ universities seeded | ✅ |
| All 47 counties indexed | ✅ |
| Paginated browsing | ✅ |
| Smart multi-type search | ✅ |
| Group submission + admin review | ✅ |
| Favorites / saved groups | ✅ |
| Report system | ✅ |
| XP + badges + leaderboard | ✅ |
| Referral system | ✅ |
| Daily check-in rewards | ✅ |
| Admin broadcast | ✅ |
| Admin analytics dashboard | ✅ |
| Auto ban / spam protection | ✅ |
| Rate limiting | ✅ |
| Link health monitoring | ✅ |
| QR code generation | ✅ |
| Auto-expiring links | ✅ |
| Trending computation | ✅ |
| Scheduled tasks | ✅ |
| Webhook + polling modes | ✅ |
| Docker + Docker Compose | ✅ |
| Alembic migrations | ✅ |

---

## 🏗 Project Structure

```
campusbuzz/
├── main.py                   # Bot entry point
├── config.py                 # Settings (pydantic-settings)
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── alembic.ini
├── .env.example
│
├── database/
│   ├── models.py             # All SQLAlchemy models
│   ├── connection.py         # Async engine + session
│   └── seed.py               # 47 counties + 60+ universities
│
├── handlers/
│   ├── start.py              # /start, welcome, force-join verify
│   ├── menu.py               # /menu, main navigation
│   ├── universities.py       # Browse → category → groups
│   ├── search.py             # FSM multi-type search
│   ├── submit_group.py       # 6-step FSM group submission
│   ├── report.py             # Report flow
│   ├── profile.py            # XP, badges, referrals
│   ├── favorites.py          # Save / unsave groups
│   ├── admin.py              # Full admin panel
│   └── _categories.py        # Freshers, Jobs, Materials, Events…
│
├── keyboards/
│   └── welcome.py            # ALL inline keyboard layouts
│
├── middlewares/
│   ├── force_join.py         # Channel membership gate
│   ├── rate_limit.py         # Per-user token bucket
│   └── anti_spam.py          # Duplicate + suspicious link detection
│
└── utils/
    ├── link_monitor.py       # Async WhatsApp link health checks
    ├── qr_generator.py       # Branded QR code images
    └── scheduler.py          # Trending, stats, expiry tasks
```

---

## 🚀 Quick Start (Local Development)

### 1. Prerequisites
- Python 3.12+
- PostgreSQL 14+
- Redis 7+

### 2. Clone & setup

```bash
git clone https://github.com/youruser/campusbuzz-ke.git
cd campusbuzz-ke

python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
nano .env                      # Fill in BOT_TOKEN, ADMIN_ID, DATABASE_URL
```

### 4. Set up database

```bash
# Create DB
createdb campusbuzz

# Run bot (auto-creates tables + seeds data on first run)
python main.py
```

### 5. Run the bot

```bash
python main.py
```

---

## 🐳 Docker Deployment (Recommended)

### One-command startup

```bash
cp .env.example .env
# Edit .env with your BOT_TOKEN and ADMIN_ID

docker compose up -d --build
```

This starts:
- 🤖 **Bot** — the Telegram bot
- 🐘 **PostgreSQL 16** — database
- ⚡ **Redis 7** — FSM + caching

### View logs

```bash
docker compose logs -f bot
```

### Stop

```bash
docker compose down
```

---

## ☁️ Production Deployment

### Railway (Easiest)

1. Push code to GitHub
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Add PostgreSQL and Redis plugins
4. Set environment variables from `.env.example`
5. Railway auto-detects `Dockerfile` and deploys

### Render

1. Create a Web Service from your GitHub repo
2. Set Build Command: `pip install -r requirements.txt`
3. Set Start Command: `python main.py`
4. Add environment variables
5. Add PostgreSQL and Redis add-ons

### VPS (Ubuntu)

```bash
# Install Docker
curl -fsSL https://get.docker.com | sh

# Clone and run
git clone <repo>
cd campusbuzz-ke
cp .env.example .env && nano .env
docker compose up -d --build

# Set up NGINX reverse proxy for webhook mode
# Point your domain to port 8080
```

---

## ⚙️ Webhook vs Polling

| Mode | When to use |
|------|-------------|
| **Long Polling** (default) | Development, testing |
| **Webhook** | Production (faster, lower resource usage) |

To enable webhook, set in `.env`:
```
WEBHOOK_URL=https://yourdomain.com
PORT=8080
```

---

## 🛡 Admin Commands

Send `/admin` to the bot from your admin account.

| Action | How |
|---|---|
| Review pending groups | Admin panel → Pending Groups |
| Approve / Reject | Tap Approve ✅ or Reject ❌ |
| Broadcast to all users | Admin panel → Broadcast |
| Ban a user | Admin panel → Ban User → enter Telegram ID |
| View analytics | Admin panel → Analytics |
| Mark trending groups | Admin panel → Set Trending |

---

## 📊 Database Schema Overview

```
counties          → 47 Kenyan counties
universities      → 60+ institutions (public/private/TVET)
faculties         → Faculties per university
departments       → Departments per faculty
users             → Bot users (XP, badges, referrals)
whatsapp_groups   → The core group directory
favorites         → User ↔ group many-to-many
reports           → Abuse reports
broadcasts        → Broadcast history
activity_logs     → User action audit trail
bot_stats         → Daily analytics snapshots
```

---

## 💰 Monetization Options

1. **Sponsored Groups** — Set `is_sponsored=True` on a group; it appears at the top of listings. Charge per week/month.
2. **Premium Verified Placement** — Charge universities/societies for ✅ verified badge + priority placement.
3. **Promoted Categories** — Sell banner-style "pinned" entries in Jobs, Events sections.
4. **Campus Ambassador Program** — Top referrers earn real rewards (M-Pesa) funded by ad revenue.

Enable with `ENABLE_MONETIZATION=true` in `.env`.

---

## 🔒 Security Checklist

- [x] Rate limiting (5 msgs / 10s per user)
- [x] Anti-spam (duplicate & keyword detection)
- [x] Force-join gate blocks unverified users
- [x] Admin panel restricted by Telegram ID (not username)
- [x] WhatsApp links validated by regex before saving
- [x] Non-root Docker user
- [x] No secrets in code (all from .env)
- [x] Automatic link expiry detection

---

## 📞 Support

Built by **@DevMwaura**  
Official channel: **@CampusBuzz**

---

*Powered by CampusBuzz Kenya 🇰🇪 — Connecting Kenyan students smarter.*
