# ---------------------------------------------------------------
# app.py: the "brain" of SkillSwap.
# This file runs the website: it shows pages, reads what users type,
# and saves things in our MongoDB database.
# ---------------------------------------------------------------


import os                                  # lets us read settings from the computer
from dotenv import load_dotenv             # reads our secret settings from the .env file
from pymongo import MongoClient            # lets Python talk to MongoDB
from flask import Flask, render_template, request, redirect, url_for, flash,session                                 
from werkzeug.security import generate_password_hash, check_password_hash  # scrambles a password so we never store the real one
from bson import ObjectId
from functools import wraps
from datetime import datetime              # to record when a request was made

# --- Load our secret settings from the .env file ---
# .env holds MONGO_URI (the database address and password) and SECRET_KEY.
# It is NOT uploaded to GitHub, so our passwords stay private.
load_dotenv()

# --- Connect to the database ---
client = MongoClient(os.getenv("MONGO_URI"))   # open the connection to MongoDB Atlas
db = client["skillswap"]                       # our database is called "skillswap"
users = db["users"]                            # "users" is a collection (like a table) inside it
skills = db["skills"]                          # NEW: one document per skill a person can teach or needs
help_requests = db["requests"]             # one document per "I need help with X" request
swap_sessions = db["sessions"]             # one document per accepted session
reports = db["reports"]                    # one document per report a person files

# --- Create the website itself ---
app = Flask(__name__)

# Flask needs a secret key to remember things about a visitor
# (like who is logged in) and to show flash messages.
app.secret_key = os.getenv("SECRET_KEY")

# Only emails ending with this can sign up.
COLLEGE_DOMAIN = "@heritageit.edu.in"

# The topics and languages people can choose from.
# We use fixed lists so "stack", "Stacks" and "stacks in c" never end up as different things.

TOPICS = ["Arrays", "Strings", "Pointers", "Linked lists", "Stacks", "Queues","Recursion", "Trees", "Sorting", "Searching"]
LANGUAGES = ["C", "C++", "Python", "Java"]


# ---------------------------------------------------------------
# PAGES (called "routes"). Each @app.route line says:
# "when someone visits this web address, run the function below it".
# ---------------------------------------------------------------

# Home page: visiting "/" just shows home.html
@app.route("/")
def home():
    return render_template("home.html")


# Login page: GET shows the form, POST checks the email and password.
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        found = users.find_one({"email": email})
        if found and check_password_hash(found["password_hash"], password):
            session["user_id"] = str(found["_id"])   # remember this person
            return redirect(url_for("profile"))

        flash("Wrong email or password.")
        return redirect(url_for("login"))
    return render_template("login.html")


# Sign-up page.
# GET  = the user just opened the page, so we show the empty form.
# POST = the user pressed the "Sign up" button, so we process what they typed.
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        # 1. Read what the user typed into the form.
        #    The names "name", "email", "password" must match the
        #    name="..." parts of the inputs in signup.html.
        name = request.form["name"].strip()            # .strip() removes extra spaces
        email = request.form["email"].strip().lower()  # .lower() so A@x.com and a@x.com count as the same
        password = request.form["password"]

        # 2. Only college emails are allowed.
        if not email.endswith(COLLEGE_DOMAIN):
            flash("Please use your college email.")    # message shown on the page
            return redirect(url_for("signup"))         # send them back to the form

        # 3. Stop people from signing up twice with the same email.
        if users.find_one({"email": email}):           # search the database for this email
            flash("This email is already registered.")
            return redirect(url_for("signup"))

        # 4. Everything is fine, so save the new user in the database.
        users.insert_one({
            "name": name,
            "email": email,
            "password_hash": generate_password_hash(password),  # scrambled password, never the real one
            "credits": 2,          # every new user starts with 2 free credits
            "rating_sum": 0,       # total stars received so far (used to work out the average later)
            "rating_count": 0,     # how many ratings received so far
            "available": True,     # True = free to help others right now
        })

        # 5. Account created, so send them to the login page.
        return redirect(url_for("login"))

    # If we reach here, the user only opened the page (GET), so show the form.
    return render_template("signup.html")


@app.route("/logout")
def logout():
    session.clear()          # forget who was logged in
    return redirect(url_for("home"))

# A "bouncer": put @login_required under a route to keep logged-out visitors out.
def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:               # nobody logged in?
            flash("Please log in first.")
            return redirect(url_for("login"))      # send them to the login page
        return view(*args, **kwargs)               # logged in, so show the page normally
    return wrapped

#-----------------------------------------------------------------------------------------------------------------------------#

# --- TEMPORARY STUBS: real logic comes in later steps ---
def skills_for(user_id, kind):
    found = skills.find({"user_id": user_id, "kind": kind})
    # The page wants a text "id", but MongoDB's _id is a special object, so we convert it.
    return [{"id": str(s["_id"]), "topic": s["topic"], "language": s["language"]} for s in found]

@app.route("/profile")
@login_required
def profile():
        return render_template("profile.html", teach_skills=skills_for(session["user_id"], "teach"), need_skills=skills_for(session["user_id"], "need"),topics=TOPICS, languages=LANGUAGES)

@app.route("/profile/skills/add", methods=["POST"])
@login_required
def add_skill():
    topic = request.form["topic"]
    language = request.form["language"]
    kind = request.form["kind"]            # "teach" or "need"

    # Only accept values from our own lists, never trust what the browser sends.
    if topic not in TOPICS or language not in LANGUAGES or kind not in ("teach", "need"):
        flash("Please choose a topic and a language.")
        return redirect(url_for("profile"))

    # Don't allow the same skill twice.
    already = skills.find_one({"user_id": session["user_id"], "topic": topic,
                               "language": language, "kind": kind})
    if already:
        flash("You already added that.")
        return redirect(url_for("profile"))

    skills.insert_one({
        "user_id": session["user_id"],     # who this skill belongs to
        "topic": topic,
        "language": language,
        "kind": kind,
    })
    return redirect(url_for("profile"))

@app.route("/profile/skills/<skill_id>/delete", methods=["POST"])
@login_required
def delete_skill(skill_id):
    # If someone types a garbage id in the URL, don't crash.
    if not ObjectId.is_valid(skill_id):
        flash("That skill doesn't exist.")
        return redirect(url_for("profile"))

    # Delete only if the skill's id matches AND it belongs to the logged-in user,
    # so nobody can delete another person's skill by changing the id.
    skills.delete_one({
        "_id": ObjectId(skill_id),
        "user_id": session["user_id"],
    })
    return redirect(url_for("profile"))

@app.route("/profile/availability", methods=["POST"])
@login_required
def toggle_availability():
    # Find the logged-in user.
    me = users.find_one({"_id": ObjectId(session["user_id"])})

    if me:
        # Flip the value: True becomes False, False becomes True.
        users.update_one(
            {"_id": me["_id"]},
            {"$set": {"available": not me["available"]}}
        )
    return redirect(url_for("profile"))

@app.route("/ask", methods=["GET", "POST"])
@login_required
def ask_help():
    my_id = session["user_id"]

    if request.method == "POST":
        topic = request.form["topic"]
        language = request.form["language"]

        # Only accept values from our own lists.
        if topic not in TOPICS or language not in LANGUAGES:
            flash("Please choose a topic and a language.")
            return redirect(url_for("ask_help"))

        # Learning costs 1 credit. Count requests that are still open
        # (waiting or accepted), so someone with 1 credit can't send 5 requests.
        me = users.find_one({"_id": ObjectId(my_id)})
        open_count = help_requests.count_documents({
            "learner_id": my_id,
            "status": {"$in": ["waiting", "accepted"]},
        })
        if not me or me["credits"] <= open_count:
            flash("You need a free credit to ask for help. Teach someone to earn one.")
            return redirect(url_for("ask_help"))

        # Don't allow the same open request twice.
        already = help_requests.find_one({
            "learner_id": my_id,
            "topic": topic,
            "language": language,
            "status": "waiting",
        })
        if already:
            flash("You already asked for that.")
            return redirect(url_for("ask_help"))

        help_requests.insert_one({
            "learner_id": my_id,           # who needs help
            "topic": topic,
            "language": language,
            "status": "waiting",           # waiting / accepted / declined / done
            "created_at": datetime.utcnow(),
        })
        flash("Request sent. Someone who teaches this will see it.")
        return redirect(url_for("ask_help"))

    # GET: show the form plus this person's own requests, newest first.
    mine = help_requests.find({"learner_id": my_id}).sort("created_at", -1)
    my_requests = [
        {"id": str(r["_id"]), "topic": r["topic"],
         "language": r["language"], "status": r["status"]}
        for r in mine
    ]
    return render_template("ask_help.html", topics=TOPICS, languages=LANGUAGES, my_requests=my_requests)


@app.route("/requests")
@login_required
def incoming_requests():
    my_id = session["user_id"]
    me = users.find_one({"_id": ObjectId(my_id)})

    requests_for_me = []

    # Only show requests if the person is marked available to help.
    if me and me["available"]:
        # The topic + language pairs this person can teach.
        my_teach = list(skills.find({"user_id": my_id, "kind": "teach"}))

        # $or needs at least one item, so skip the search if they teach nothing.
        if my_teach:
            matches = [{"topic": s["topic"], "language": s["language"]} for s in my_teach]

            found = help_requests.find({
                "status": "waiting",                # only requests nobody has answered yet
                "learner_id": {"$ne": my_id},       # never show someone their own request
                "$or": matches,                     # topic + language matches something I teach
            }).sort("created_at", 1)                # oldest first, so nobody waits forever

            for r in found:
                learner = users.find_one({"_id": ObjectId(r["learner_id"])})
                requests_for_me.append({
                    "id": str(r["_id"]),
                    "learner_name": learner["name"] if learner else "Unknown",
                    "topic": r["topic"],
                    "language": r["language"],
                })

    return render_template("requests.html", requests_for_me=requests_for_me)

def find_request_for_teacher(request_id, teacher_id):
    """Return the waiting request only if this person is allowed to answer it, otherwise None."""
    if not ObjectId.is_valid(request_id):
        return None

    req = help_requests.find_one({"_id": ObjectId(request_id), "status": "waiting"})
    if not req or req["learner_id"] == teacher_id:   # gone already, or it's their own request
        return None

    # They must actually teach this topic in this language.
    teaches_it = skills.find_one({
        "user_id": teacher_id, "kind": "teach",
        "topic": req["topic"], "language": req["language"],
    })
    return req if teaches_it else None


@app.route("/requests/<request_id>/accept", methods=["POST"])
@login_required
def accept_request(request_id):
    my_id = session["user_id"]
    req = find_request_for_teacher(request_id, my_id)
    if not req:
        flash("That request is no longer available.")
        return redirect(url_for("incoming_requests"))

    # Claim it. The filter includes status "waiting", so if two teachers click
    # at the same moment, only one of them gets modified_count == 1.
    claimed = help_requests.update_one(
        {"_id": req["_id"], "status": "waiting"},
        {"$set": {"status": "accepted"}},
    )
    if claimed.modified_count == 0:
        flash("Someone else just accepted that request.")
        return redirect(url_for("incoming_requests"))

    swap_sessions.insert_one({
        "request_id": str(req["_id"]),
        "learner_id": req["learner_id"],
        "teacher_id": my_id,
        "topic": req["topic"],
        "language": req["language"],
        "status": "active",            # active / done / reported
        "rated": False,
        "created_at": datetime.utcnow(),
    })
    flash("Accepted! You can see the details under Sessions.")
    return redirect(url_for("my_sessions"))


@app.route("/requests/<request_id>/decline", methods=["POST"])
@login_required
def decline_request(request_id):
    req = find_request_for_teacher(request_id, session["user_id"])
    if req:
        help_requests.update_one(
            {"_id": req["_id"], "status": "waiting"},
            {"$set": {"status": "declined"}},
        )
    return redirect(url_for("incoming_requests"))

@app.route("/sessions")
@login_required
def my_sessions():
    my_id = session["user_id"]

    # Every session where I am the learner or the teacher, newest first.
    found = swap_sessions.find({
        "$or": [{"learner_id": my_id}, {"teacher_id": my_id}]
    }).sort("created_at", -1)

    cards = []
    for s in found:
        i_am_teacher = (s["teacher_id"] == my_id)
        other_id = s["learner_id"] if i_am_teacher else s["teacher_id"]
        other = users.find_one({"_id": ObjectId(other_id)})

        # The server decides who sees contact details.
        # Only the two people in this session ever reach this line,
        # because the query above only returns sessions that include me.
        # Contact is sent only while the session is still active.
        contact = other["email"] if (other and s["status"] == "active") else None

        cards.append({
            "id": str(s["_id"]),
            # The template calls the teacher a "helper".
            "role": "helper" if i_am_teacher else "learner",
            "other_name": other["name"] if other else "Unknown",
            "topic": s["topic"],
            "language": s["language"],
            # The template calls an open session "accepted".
            "status": "accepted" if s["status"] == "active" else s["status"],
            "contact": contact,
            # The learner sees the "Mark as done" + rating form until they have rated.
            "can_rate": (not i_am_teacher) and (not s["rated"]) and s["status"] in ("active", "done"),
            "stars": s.get("stars"),
        })

    return render_template("sessions.html", my_sessions=cards)

@app.route("/sessions/<session_id>/done", methods=["POST"])
@login_required
def finish_session(session_id):
    my_id = session["user_id"]

    if not ObjectId.is_valid(session_id):
        flash("That session doesn't exist.")
        return redirect(url_for("my_sessions"))

    # Find the session, but only if I am one of the two people in it.
    s = swap_sessions.find_one({
        "_id": ObjectId(session_id),
        "$or": [{"learner_id": my_id}, {"teacher_id": my_id}],
    })
    if not s:
        flash("That session doesn't exist.")
        return redirect(url_for("my_sessions"))

    # Only the learner confirms. If the teacher could confirm,
    # they could give themselves a credit without teaching anything.
    if s["learner_id"] != my_id:
        flash("Only the learner can mark a session as done.")
        return redirect(url_for("my_sessions"))

    # PART 1: finish the session and move the credits (only once).
    # The filter includes status "active", so a double click can't pay twice.
    if s["status"] == "active":
        finished = swap_sessions.update_one(
            {"_id": s["_id"], "status": "active"},
            {"$set": {"status": "done"}},
        )
        if finished.modified_count == 1:
            users.update_one({"_id": ObjectId(s["learner_id"])}, {"$inc": {"credits": -1}})
            users.update_one({"_id": ObjectId(s["teacher_id"])}, {"$inc": {"credits": 1}})
            help_requests.update_one(
                {"_id": ObjectId(s["request_id"])},
                {"$set": {"status": "done"}},
            )
            flash("Session done. 1 credit moved to your teacher.")

    # PART 2: save a rating if the form sent one.
    stars_text = request.form.get("stars")
    if stars_text:
        try:
            stars = int(stars_text)
        except ValueError:
            stars = 0
        if stars < 1 or stars > 5:
            flash("Please pick between 1 and 5 stars.")
            return redirect(url_for("my_sessions"))

        comment = request.form.get("comment", "").strip()[:300]   # keep it short

        # Only rate a finished session, and only once.
        rated = swap_sessions.update_one(
            {"_id": s["_id"], "status": "done", "rated": False},
            {"$set": {"rated": True, "stars": stars, "comment": comment}},
        )
        if rated.modified_count == 1:
            users.update_one(
                {"_id": ObjectId(s["teacher_id"])},
                {"$inc": {"rating_sum": stars, "rating_count": 1}},
            )
            flash("Thanks for rating.")

    return redirect(url_for("my_sessions"))

@app.route("/sessions/<session_id>/report", methods=["POST"])
@login_required
def report_session(session_id):
    my_id = session["user_id"]

    if not ObjectId.is_valid(session_id):
        flash("That session doesn't exist.")
        return redirect(url_for("my_sessions"))

    # Find the session, but only if I am one of the two people in it.
    s = swap_sessions.find_one({
        "_id": ObjectId(session_id),
        "$or": [{"learner_id": my_id}, {"teacher_id": my_id}],
    })
    if not s:
        flash("That session doesn't exist.")
        return redirect(url_for("my_sessions"))

    # One report per person per session.
    already = reports.find_one({"session_id": str(s["_id"]), "reporter_id": my_id})
    if already:
        flash("You already reported this session.")
        return redirect(url_for("my_sessions"))

    # The person being reported is the other one in the session.
    other_id = s["learner_id"] if s["teacher_id"] == my_id else s["teacher_id"]

    reports.insert_one({
        "session_id": str(s["_id"]),
        "reporter_id": my_id,
        "reported_id": other_id,
        "created_at": datetime.utcnow(),
    })

    # If the session is still open, freeze it so no credits can move.
    # A finished session keeps its status, so its rating still shows.
    swap_sessions.update_one(
        {"_id": s["_id"], "status": "active"},
        {"$set": {"status": "reported"}},
    )

    flash("Thanks. Your report was sent to the SkillSwap team.")
    return redirect(url_for("my_sessions"))

# Runs before every page and adds a "user" variable to it,
# so templates can show the name, credits and rating in the navbar and profile.
@app.context_processor
def inject_user():
    user_id = session.get("user_id")          # who is logged in? (stored at login)
    if not user_id:
        return {}                             # nobody logged in, so no "user" variable
    u = users.find_one({"_id": ObjectId(user_id)})
    if not u:
        return {}
    count = u["rating_count"]
    avg = round(u["rating_sum"] / count, 1) if count else None   # average stars, or None if no ratings yet
    return {"user": {
        "name": u["name"],
        "email": u["email"],
        "credits": u["credits"],
        "avg_rating": avg,
        "available": u["available"],
    }}



# ---------------------------------------------------------------
# This starts the website when we run:  python app.py
# debug=True makes the page reload by itself when we change the code
# and shows helpful error messages. Turn it OFF before the real launch.
# ---------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)