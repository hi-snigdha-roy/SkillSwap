# SkillSwap

A student stuck on one concept gets matched with a classmate who knows it, for a free 20–30 minute session.

**The credit rule:** teach one concept = earn 1 credit. Learning costs 1 credit. New users start with 2 credits.

- Repo: https://github.com/hi-snigdha-roy/SkillSwap
- Stack: Flask (Python) + MongoDB Atlas, with plain HTML / CSS / JavaScript
- Branch we work on: `main`
- Last updated: 24 Oct 2026

---

## Status at a glance

| Part | State |
|---|---|
| Frontend (8 pages, CSS, JS) | ✅ Done |
| Backend routes | ✅ All 15 written (13 added in this round + `home`, `signup`) |
| Manual testing of every route | ⬜ Use the checklist in section 6 and tick it off |
| Cleanup before launch | ⬜ See section 7 |

---

## 1. Get it running on your machine

You need Python 3.10 or newer and a MongoDB Atlas connection string.

```
git clone https://github.com/hi-snigdha-roy/SkillSwap.git
cd SkillSwap
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

On Mac or Linux the activate line is `source venv/bin/activate` instead.
On Windows PowerShell, use `.\venv\Scripts\Activate.ps1`. If PowerShell says scripts are disabled, run `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned` once.

### Make your `.env` file

Copy `.env.example` to `.env`, then fill in two values:

```
MONGO_URI=your-mongodb-atlas-connection-string
SECRET_KEY=any-long-random-string-you-invent
```

> ⚠️ **Change needed:** `.env.example` must list **both** `MONGO_URI` and `SECRET_KEY`. `app.py` reads both, and without `SECRET_KEY` logging in and flash messages will not work. If your copy of `.env.example` only lists `MONGO_URI`, add the second line and commit it.

**Never commit `.env`.** It holds the database password. `.gitignore` already blocks it, so leave that alone.

### Check the database connection

```
python test_db.py
```

If it prints `{'ok': 1.0}` you are connected.

---

## 2. Two ways to run the app

### A. The real app (use this for backend work)

```
python app.py
```

Opens on http://127.0.0.1:5000. All pages now work with real data.

### B. The frontend preview (optional now)

`frontend_preview.py` shows all 8 pages with fake data and does not touch the database.

```
python frontend_preview.py
```

Opens on http://127.0.0.1:5001. Add `?logged_out=1` for the visitor navbar, or `?empty=1` for the "nothing here yet" messages.

Now that the real app works, this is only useful for checking a design change quickly. See section 7 for when to delete it.

---

## 3. What is done ✅

### The whole frontend

Every page is built, commented and tested. Nobody needs to touch HTML or CSS to use the backend.

| File | What it is |
|---|---|
| `templates/base.html` | The shared frame: navbar, flash messages, footer |
| `templates/home.html` | Landing page: the idea, 4 steps, the credit rule |
| `templates/signup.html` | Sign-up form with a show/hide password button |
| `templates/login.html` | Log-in form with a show/hide password button |
| `templates/profile.html` | Credits, rating, availability switch, the two skill lists |
| `templates/ask_help.html` | Ask-for-help form plus your requests and their status |
| `templates/requests.html` | People asking you to teach, with Accept / Decline |
| `templates/sessions.html` | Session cards, contact details, star rating, Report |
| `static/css/style.css` | All the styling. Colours are CSS variables at the top |
| `static/js/main.js` | Password toggle, mobile menu, flash fade, star widget, "are you sure?" prompts |

### The whole backend

| Route function | URL | What it does |
|---|---|---|
| `home` | `GET /` | Landing page |
| `signup` | `GET/POST /signup` | Checks the college email, refuses duplicates, hashes the password, gives 2 starting credits |
| `login` | `GET/POST /login` | Checks the password hash, stores the user id in the session |
| `logout` | `GET /logout` | Clears the session |
| `profile` | `GET /profile` | Shows credits, rating, availability and both skill lists |
| `add_skill` | `POST /profile/skills/add` | Adds a teach or need skill. Only accepts values from `TOPICS` and `LANGUAGES`. Blocks duplicates |
| `delete_skill` | `POST /profile/skills/<skill_id>/delete` | Deletes a skill, only if it belongs to the logged-in user |
| `toggle_availability` | `POST /profile/availability` | Flips available / unavailable |
| `ask_help` | `GET/POST /ask` | Creates a help request. Blocks a request if the learner has no free credit, or already has the same request waiting |
| `incoming_requests` | `GET /requests` | Shows waiting requests that match a topic + language the user teaches. Hidden when the user is unavailable. Never shows your own requests |
| `accept_request` | `POST /requests/<request_id>/accept` | Claims the request and creates a session |
| `decline_request` | `POST /requests/<request_id>/decline` | Marks the request declined |
| `my_sessions` | `GET /sessions` | Shows every session the user is part of, with contact details only when allowed |
| `finish_session` | `POST /sessions/<session_id>/done` | Learner marks the session done (and rates it in the same click). Moves the credit |
| `report_session` | `POST /sessions/<session_id>/report` | Files a report. Freezes an open session so no credit moves |

Also done: `login_required` (keeps logged-out visitors out of a page), `skills_for` (helper used by the profile page), `find_request_for_teacher` (the safety check shared by Accept and Decline), and `inject_user` (gives every page the `user` variable).

---

## 4. How a swap works, start to finish

1. **Learner** goes to *Ask for help*, picks a topic and language. A request is saved with status `waiting`.
2. **A teacher** who has a matching *teach* skill, and is marked available, sees it under *Requests*. They click **Accept** or **Decline**.
3. **Accept** changes the request to `accepted` and creates a session with status `active`. Both people now see each other's email on the *Sessions* page.
4. They meet for 20–30 minutes.
5. The **learner** opens *Sessions*, picks 1–5 stars and clicks **Mark as done**. The session becomes `done`, the learner pays 1 credit, the teacher earns 1 credit, and the teacher's rating is updated.
6. Either person can click **Report** at any time. An open session becomes `reported` and no credit can move.

Credits only move in step 5, and only the learner can trigger it. If the teacher could, they could pay themselves without teaching anything.

---

## 5. The database

Five collections in the `skillswap` database. All five are created automatically the first time something is saved to them.

| Collection | One document is… | Main fields |
|---|---|---|
| `users` | one person | `name`, `email`, `password_hash`, `credits`, `rating_sum`, `rating_count`, `available` |
| `skills` | one skill a person can teach or needs | `user_id`, `topic`, `language`, `kind` (`teach` or `need`) |
| `requests` | one "I need help with X" request | `learner_id`, `topic`, `language`, `status` (`waiting` / `accepted` / `declined` / `done`), `created_at` |
| `sessions` | one accepted session | `request_id`, `learner_id`, `teacher_id`, `topic`, `language`, `status` (`active` / `done` / `reported`), `rated`, `stars`, `comment`, `created_at` |
| `reports` | one report | `session_id`, `reporter_id`, `reported_id`, `created_at` |

In `app.py` the request collection is called `help_requests` and the session collection is called `swap_sessions`. This avoids clashing with Flask's own `request` and `session`.

---

## 6. What each page expects from the backend

This is the contract between `app.py` and the templates. `mock_data.py` holds an example of every one of these.

Every page may receive `user`. Leave it out and the visitor is treated as logged out:

```python
user = {"name": str, "email": str, "credits": int,
        "avg_rating": float or None, "available": True or False}
```

| Page | Route function | Also needs |
|---|---|---|
| `home.html` | `home` | nothing |
| `signup.html` | `signup` | nothing. Form sends `name`, `email`, `password` |
| `login.html` | `login` | nothing. Form sends `email`, `password` |
| `profile.html` | `profile` | `teach_skills`, `need_skills` (lists of `{id, topic, language}`); `topics`, `languages` (lists of strings) |
| `ask_help.html` | `ask_help` | `topics`, `languages`; `my_requests` (list of `{id, topic, language, status}`). Form sends `topic`, `language` |
| `requests.html` | `incoming_requests` | `requests_for_me` (list of `{id, learner_name, topic, language}`) |
| `sessions.html` | `my_sessions` | `my_sessions` (list of `{id, role, other_name, topic, language, status, contact, can_rate, stars}`). Rating form sends `stars` (1–5) and `comment` |

### Changes to the contract (read this)

While wiring up the backend, the real templates showed that a few words differ from what the database stores. The backend translates them in `my_sessions`:

| Field | Database stores | Page receives |
|---|---|---|
| `role` | `teacher` / `learner` | `helper` / `learner` |
| `status` | `active` / `done` / `reported` | `accepted` / `done` / `reported` |
| `can_rate` | n/a | `True` for the learner until a rating is saved, while the session is `active` or `done` |

> ⚠️ **Changes needed in the frontend files:**
> 1. **`templates/sessions.html` header comment** still says status is `"accepted" or "done"`. Update it to `"accepted", "done" or "reported"`. Also update the Forms line: the rating form posts to `finish_session` and its button is **Mark as done**, so marking done and rating happen in one click.
> 2. **`static/css/style.css`** needs a `.badge--reported` rule so the "reported" badge is styled. Copy one of the existing `.badge--...` rules and change the colour.
> 3. **`mock_data.py`** can stay until it is deleted (section 7). Its `status` values do not include `reported`, so do not rely on it for that case.

---

## 7. What is left to do ❌

### Test every route (do this first)

You need **two accounts**, because you never see your own requests. Use a normal window for account A and a private window for account B. Both need a `@heritageit.edu.in` email.

- [ ] Sign up, log in, log out
- [ ] Add a teach skill and a need skill. Adding the same one twice is refused
- [ ] Delete a skill. It disappears
- [ ] Toggle availability. The switch flips, and an unavailable teacher sees an empty *Requests* page
- [ ] B asks for help with something A teaches. The same request twice is refused
- [ ] With 2 credits, B can send 2 open requests but not a third
- [ ] A sees B's request, clicks **Accept**. Both see a session with each other's email
- [ ] A different request: A clicks **Decline**. B sees `declined`
- [ ] B marks the session done with 4 stars. B loses 1 credit, A gains 1, the card shows ★★★★☆, A's profile rating becomes 4.0
- [ ] Reloading does not move credits a second time
- [ ] A (the teacher) cannot mark a session done
- [ ] **Report** on an open session: it becomes `reported`, the email disappears, no rating form
- [ ] **Report** twice from the same person: refused the second time
- [ ] Visiting any page while logged out sends you to the login page

### Cleanup before launch

- [ ] Add `SECRET_KEY` to `.env.example` (see section 1)
- [ ] Add `@login_required` to every route that needs it. Check that all 11 routes added in this round have it
- [ ] Remove the `# --- TEMPORARY STUBS ---` comment in `app.py`. It no longer applies
- [ ] Update `sessions.html` and `style.css` (see section 6)
- [ ] Delete `mock_data.py` and `frontend_preview.py`
- [ ] Change `app.run(debug=True)` to `debug=False`. Debug mode shows error details to visitors
- [ ] Never commit `.env`

---

## 8. Known limitations

These are fine for a college prototype. Each one is a clear next step if the project grows.

1. **A decline hides the request from everyone.** If two teachers match and the first one declines, the second never sees it. A fix would be to remember who declined and hide the request only from them.
2. **No database transactions.** Finishing a session makes four separate updates. If the app crashed in the middle, credits could end up wrong. The `status` checks stop double payment, but not a crash. Atlas supports transactions if you need this.
3. **No CSRF protection.** The POST routes do not check a hidden token, so another website could in theory trick a logged-in user's browser into submitting one of these forms. A hand-made token stored in the session would fix it without any library.
4. **No password rules.** Signup accepts any password length.
5. **Reports have no reason and no admin screen.** A report only records who reported whom and when. Review them in Atlas under the `reports` collection.
6. **Bad ids in `accept` and `decline`.** These are handled, but only by the shared helper, so keep using `find_request_for_teacher` if you add similar routes.
7. **`datetime.utcnow()` is deprecated** in newer Python versions. It works fine. A later change to `datetime.now(timezone.utc)` is optional.

---

## 9. The security rules (unchanged, still apply)

**Contact details:** on the sessions page, contact details are only written into the page when the backend actually sends `contact`. They are never hidden with CSS, because hidden HTML can still be read by anyone who views the page source. Send `contact=None` for anyone who should not see it. The server decides who sees what.

**Who owns what:** every route that changes data checks that the logged-in person is allowed to. For example, `delete_skill` filters by both the skill id and the user id, and `my_sessions` only returns sessions that include the logged-in person.

---

## 10. House rules for this project

Please keep to these so the code stays readable for everyone.

- **No frameworks or libraries on the frontend.** Plain HTML, CSS and JavaScript only. No React, Tailwind, Bootstrap, jQuery, npm, and no CDN links. System fonts only.
- **Every action is a normal form POST followed by a redirect.** No `fetch`, no AJAX, no JSON APIs.
- **Use `url_for()` for every link and form action**, never a hand-typed path. Use `url_for('static', filename='...')` for CSS, JS and images.
- **Keep the route function names exactly as listed above.** The templates call them by name, so renaming one breaks the pages.
- **Every template starts with a `{# ... #}` comment** saying its URL, its route function, the variables it expects and the forms it submits. Keep that up to date when you change something.
- **Comment in plain language.** Assume the reader is new to this.
- **Never commit `.env`.**