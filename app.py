from flask import Flask, render_template, request, redirect, session
from flask_socketio import SocketIO, join_room, send
import sqlite3
import requests
import os

app = Flask(__name__)
app.secret_key = "secret123"
socketio = SocketIO(app, async_mode="eventlet")

def init_db():
    conn = sqlite3.connect("db.sqlite3")
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS maps(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT
    )
    """)
    conn.commit()
    conn.close()

init_db()

def get_avatar(username):
    try:
        r = requests.post(
            "https://users.roblox.com/v1/usernames/users",
            json={"usernames":[username]}
        )
        uid = r.json()["data"][0]["id"]

        img = requests.get(
            f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={uid}&size=150x150&format=Png"
        ).json()

        return img["data"][0]["imageUrl"]
    except:
        return ""

@app.route("/")
def index():
    conn = sqlite3.connect("db.sqlite3")
    maps = conn.execute("SELECT * FROM maps").fetchall()
    conn.close()
    return render_template("index.html", maps=maps)

@app.route("/join", methods=["POST"])
def join():
    session["user"] = request.form["username"]
    session["avatar"] = get_avatar(session["user"])
    session["room"] = f"map_{request.form['map']}"
    return redirect("/chat")

@app.route("/chat")
def chat():
    if "user" not in session:
        return redirect("/")
    return render_template("chat.html",
                           user=session["user"],
                           avatar=session["avatar"])

@app.route("/admin", methods=["GET","POST"])
def admin():
    if request.method == "POST":
        conn = sqlite3.connect("db.sqlite3")
        conn.execute("INSERT INTO maps(name) VALUES(?)",[request.form["name"]])
        conn.commit()
        conn.close()

    conn = sqlite3.connect("db.sqlite3")
    maps = conn.execute("SELECT * FROM maps").fetchall()
    conn.close()
    return render_template("admin.html", maps=maps)

@socketio.on("join")
def on_join():
    join_room(session["room"])
    send("👋 joined", to=session["room"])

@socketio.on("msg")
def handle_msg(msg):
    send(msg, to=session["room"])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port)
