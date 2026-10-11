# SkillSwap

A student stuck on one concept gets matched with a classmate who knows it, for a
free 20–30 minute session.

**The credit rule:** teach one concept = earn 1 credit. Learning costs 1 credit.
New users start with 2 credits.

- **Repo:** https://github.com/hi-snigdha-roy/SkillSwap
- **Stack:** Flask (Python) + MongoDB Atlas, with plain HTML / CSS / JavaScript
- **Branch we work on:** `main`

---

## 1. Get it running on your machine

You need Python 3.10 or newer and a MongoDB Atlas connection string.

```bash
git clone https://github.com/snigdha19-here/SkillSwap.git
cd SkillSwap
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

> On Mac or Linux the activate line is `source venv/bin/activate` instead.

### Make your `.env` file

Copy `.env.example` to `.env`, then fill in **two** values:

```
MONGO_URI=your-mongodb-atlas-connection-string
SECRET_KEY=any-long-random-string-you-invent
```

⚠️ `.env.example` currently only lists `MONGO_URI`, but `app.py` also reads
`SECRET_KEY`. Without it, logging in and flash messages will not work. Add both.

**Never commit `.env`.** It holds the database password. `.gitignore` already
blocks it — leave that alone.

### Check the database connection

```bash
python test_db.py
```

If it prints `{'ok': 1.0}` you are connected.

---

## 2. Two ways to run the app

### A. The real app — use this for backend work

```bash
python app.py
```

Opens on http://127.0.0.1:5000. Only the pages whose routes exist will work
(see the checklist in section 4).

### B. The frontend preview — use this to see every page

The design is finished but most backend routes are not, so this throwaway app
shows all 8 pages filled with fake data. It does **not** touch the database and
does **not** import `app.py`.

```bash
python frontend_preview.py
```

Opens on http://127.0.0.1:5001. Two tricks you can add to any address:

| Add to the URL | What it shows |
|---|---|
| `?logged_out=1` | the navbar as a visitor who is not logged in sees it |
| `?empty=1` | the friendly "nothing here yet" messages |

Example: http://127.0.0.1:5001/sessions?empty=1

---

## 3. What is already done ✅

### The whole frontend

Every page is built, commented and tested. Nobody needs to touch HTML or CSS to
finish the backend.

| File | What it is |
|---|---|
| `templates/base.html` | The shared frame: navbar, flash messages, footer. Every other page sits inside it. |
| `templates/home.html` | Landing page: the idea, 4 steps, the credit rule |
| `templates/signup.html` | Sign-up form with a show/hide password button |
| `templates/login.html` | Log-in form with a show/hide password button |
| `templates/profile.html` | Credits, rating, availability switch, the two skill lists |
| `templates/ask_help.html` | Ask-for-help form plus your requests and their status |
| `templates/requests.html` | People asking you to teach, with Accept / Decline |
| `templates/sessions.html` | Session cards, contact details, star rating, Report |
| `static/css/style.css` | All the styling. Colours are CSS variables at the top. |
| `static/js/main.js` | Password toggle, mobile menu, flash fade, star widget, "are you sure?" prompts |

Checked and working: all 8 pages, both phone and desktop layouts, every form
posts to the right address with the right field names, and the colour contrast
meets the WCAG AA guideline.

### Two backend routes

- `home` — GET `/` ✅
- `signup` — GET and POST `/signup` ✅ (checks the college email, refuses
  duplicates, hashes the password, gives 2 starting credits)

---

## 4. What is left to do ❌

13 routes. Tick them off as you go.

### Step 1 — Log in and log out (do this first)

Nothing else can be tested until someone can actually log in.

- [ ] `login` — add `methods=["GET", "POST"]`, check the password with
      `check_password_hash`, store the user's id in Flask's `session`
- [ ] `logout` — GET `/logout`, clear the session

### Step 2 — Stub the other routes before step 1 goes live

**Read this or you will lose an hour.** The navbar shows Profile / Ask for help /
Requests / Sessions links as soon as a page receives a `user` variable. Jinja
builds those links with `url_for('profile')` and friends, and it raises
`BuildError` for any route that does not exist yet.

Right now nothing breaks, because no page receives `user`. The moment login
works, every page will break at once unless these routes exist — even as empty
functions that just render their template.

So: create all 13 functions below with the correct names first, then fill them in.

### Step 3 — Profile

- [ ] `profile` — GET `/profile`
- [ ] `add_skill` — POST `/profile/skills/add`
- [ ] `delete_skill` — POST `/profile/skills/<skill_id>/delete`
- [ ] `toggle_availability` — POST `/profile/availability`

### Step 4 — Asking for help

- [ ] `ask_help` — GET and POST `/ask`

### Step 5 — Incoming requests

- [ ] `incoming_requests` — GET `/requests`
- [ ] `accept_request` — POST `/requests/<request_id>/accept`
- [ ] `decline_request` — POST `/requests/<request_id>/decline`

### Step 6 — Sessions

- [ ] `my_sessions` — GET `/sessions`
- [ ] `finish_session` — POST `/sessions/<session_id>/done`
- [ ] `report_session` — POST `/sessions/<session_id>/report`

### Database collections still to create

Only `users` exists so far. The pages assume three more: **skills**,
**requests** and **sessions**.

---

## 5. What each page expects from the backend

This is the contract. Send these exact names and shapes to `render_template()`
and the pages work with no changes.

**`mock_data.py` holds a real example of every single one of these, with
comments.** When in doubt, open that file — it is the spec.

Every page may receive `user`. Leave it out and the visitor is treated as
logged out:

```python
user = {"name": str, "email": str, "credits": int,
        "avg_rating": float or None, "available": True or False}
```

| Page | Route function | Also needs |
|---|---|---|
| `home.html` | `home` | nothing |
| `signup.html` | `signup` | nothing · form sends `name`, `email`, `password` |
| `login.html` | `login` | nothing · form sends `email`, `password` |
| `profile.html` | `profile` | `teach_skills`, `need_skills` — lists of `{id, topic, language}`; `topics`, `languages` — lists of strings |
| `ask_help.html` | `ask_help` | `topics`, `languages`; `my_requests` — list of `{id, topic, language, status}` where status is `waiting` / `accepted` / `declined` / `done` · form sends `topic`, `language` |
| `requests.html` | `incoming_requests` | `requests_for_me` — list of `{id, learner_name, topic, language}` |
| `sessions.html` | `my_sessions` | `my_sessions` — list of `{id, role, other_name, topic, language, status, contact, can_rate, stars}` · rating form sends `stars` (1–5) and `comment` |

### The one security rule

On the sessions page, **contact details are only written into the page when the
backend actually sends `contact`.** They are never hidden with CSS, because
hidden HTML can still be read by anyone who views the page source.

Send `contact=None` for anyone who should not see it. The server decides who
sees what.

---

## 6. House rules for this project

Please keep to these so the code stays readable for everyone.

1. **No frameworks or libraries.** Plain HTML, CSS and JavaScript only. No React,
   Tailwind, Bootstrap, jQuery, npm, and no CDN links. System fonts only.
2. **Every action is a normal form POST followed by a redirect.** No `fetch`, no
   AJAX, no JSON APIs.
3. **Use `url_for()` for every link and form action**, never a hand-typed path.
   Use `url_for('static', filename='...')` for CSS, JS and images.
4. **Keep the route function names exactly as listed above** — the templates call
   them by name, so renaming one breaks the pages.
5. **Every template starts with a `{# ... #}` comment** saying its URL, its route
   function, the variables it expects and the forms it submits. Keep that up to
   date when you change something.
6. **Comment in plain language.** Assume the reader is new to this.
7. **Never commit `.env`.**

---

## 7. Temporary files — delete these later

These two exist only so the pages can be looked at before the backend is
finished. Once `app.py` serves all the pages with real data, delete both:

- `mock_data.py`
- `frontend_preview.py`

Until then, keep them — `mock_data.py` doubles as the spec for section 5.
