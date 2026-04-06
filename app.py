import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import plotly.express as px

st.set_page_config(page_title="Fitness Pro", layout="wide")

# ---------------- DATABASE ----------------
def connect():
    return sqlite3.connect("fitness.db", check_same_thread=False)

def create_db():
    conn = connect()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        age INTEGER,
        height REAL,
        weight REAL,
        goal TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        date TEXT,
        calories REAL,
        protein REAL,
        workout TEXT,
        weight REAL
    )
    """)

    conn.commit()
    conn.close()

create_db()

# ---------------- AUTH ----------------
def register_user(username, password, age, height, weight, goal):
    conn = connect()
    try:
        conn.execute(
            "INSERT INTO users(username,password,age,height,weight,goal) VALUES(?,?,?,?,?,?)",
            (username.strip(), password.strip(), age, height, weight, goal)
        )
        conn.commit()
        return True
    except Exception as e:
        return False

def login_user(username, password):
    conn = connect()
    df = pd.read_sql("SELECT * FROM users", conn)
    conn.close()

    user = df[
        (df["username"].str.strip() == username.strip()) &
        (df["password"].str.strip() == password.strip())
    ]

    return user

# ---------------- LOGIC ----------------
def add_log(uid, cal, pro, work, wt):
    conn = connect()
    date = datetime.now().strftime("%Y-%m-%d")

    conn.execute(
        "INSERT INTO logs(user_id,date,calories,protein,workout,weight) VALUES(?,?,?,?,?,?)",
        (uid, date, cal, pro, work, wt)
    )
    conn.commit()
    conn.close()

def get_logs(uid):
    return pd.read_sql(f"SELECT * FROM logs WHERE user_id={uid}", connect())

def get_rec(weight, goal):
    if goal == "fat loss":
        return weight*30-300, weight*1.5
    return weight*30+300, weight*2

# ---------------- SESSION ----------------
if "user" not in st.session_state:
    st.session_state.user = None

# ---------------- LOGIN PAGE ----------------
if st.session_state.user is None:
    st.title("🔐 Login / Register")

    option = st.radio("", ["Login", "Register"])

    if option == "Login":
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")

        if st.button("Login"):
            user = login_user(u, p)
            if not user.empty:
                st.session_state.user = user.iloc[0]
                st.success("Login successful")
                st.rerun()
            else:
                st.error("Invalid credentials")

    else:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        age = st.number_input("Age")
        height = st.number_input("Height")
        weight = st.number_input("Weight")
        goal = st.selectbox("Goal", ["fat loss", "muscle gain"])

        if st.button("Register"):
            if register_user(u, p, age, height, weight, goal):
                st.success("Registered. Now login.")
            else:
                st.error("Username already exists")

# ---------------- MAIN APP ----------------
else:
    user = st.session_state.user
    uid = int(user["id"])
    weight = float(user["weight"])
    goal = user["goal"]

    st.sidebar.title(f"👋 {user['username']}")
    menu = st.sidebar.radio("Menu", ["Dashboard", "Add Log", "Analytics", "Logout"])

    if menu == "Logout":
        st.session_state.user = None
        st.rerun()

    # DASHBOARD
    if menu == "Dashboard":
        st.title("🔥 Dashboard")

        logs = get_logs(uid)
        rec_cal, rec_pro = get_rec(weight, goal)

        col1, col2, col3 = st.columns(3)
        col1.metric("Calories Target", int(rec_cal))
        col2.metric("Protein Target", int(rec_pro))
        col3.metric("Logs", len(logs))

        if not logs.empty:
            fig = px.line(logs, x="date", y=["calories", "protein"])
            st.plotly_chart(fig, use_container_width=True)

    # ADD LOG
    elif menu == "Add Log":
        st.title("📥 Add Daily Log")

        cal = st.number_input("Calories")
        pro = st.number_input("Protein")
        work = st.selectbox("Workout", ["yes", "no"])
        wt = st.number_input("Weight")

        if st.button("Save"):
            add_log(uid, cal, pro, work, wt)
            st.success("Saved")

    # ANALYTICS
    elif menu == "Analytics":
        st.title("📊 Analytics")

        logs = get_logs(uid)

        if logs.empty:
            st.warning("No data yet")
        else:
            rec_cal, rec_pro = get_rec(weight, goal)

            avg_cal = logs["calories"].mean()
            avg_pro = logs["protein"].mean()

            st.write(f"Average Calories: {avg_cal:.0f}")
            st.write(f"Average Protein: {avg_pro:.0f}")

            fig = px.bar(logs, x="date", y="weight")
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("Insights")

            if avg_pro < rec_pro * 0.85:
                st.error("Low protein intake")
            else:
                st.success("Protein on track")

            workout_days = (logs["workout"] == "yes").sum()

            if workout_days < 3:
                st.warning("Workout consistency low")
            else:
                st.success("Workout consistent")
