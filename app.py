import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import plotly.express as px

st.set_page_config(page_title="Fitness Pro", layout="wide")

# ---------- DB ----------
def connect():
    return sqlite3.connect("fitness.db")

def create_db():
    conn = connect()
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        age INT, height REAL, weight REAL, goal TEXT)""")

    c.execute("""CREATE TABLE IF NOT EXISTS logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INT, date TEXT, calories REAL,
        protein REAL, workout TEXT, weight REAL)""")

    conn.commit()
    conn.close()

create_db()

# ---------- AUTH ----------
def register(username, password, age, height, weight, goal):
    conn = connect()
    try:
        conn.execute("INSERT INTO users(username,password,age,height,weight,goal) VALUES(?,?,?,?,?,?)",
                     (username, password, age, height, weight, goal))
        conn.commit()
    except:
        return False
    return True

def login(username, password):
    df = pd.read_sql("SELECT * FROM users", connect())
    user = df[(df["username"]==username) & (df["password"]==password)]
    return user

# ---------- LOGIC ----------
def add_log(uid, cal, pro, work, wt):
    conn = connect()
    date = datetime.now().strftime("%Y-%m-%d")
    conn.execute("INSERT INTO logs(user_id,date,calories,protein,workout,weight) VALUES(?,?,?,?,?,?)",
                 (uid, date, cal, pro, work, wt))
    conn.commit()
    conn.close()

def get_logs(uid):
    return pd.read_sql(f"SELECT * FROM logs WHERE user_id={uid}", connect())

def get_rec(weight, goal):
    if goal == "fat loss":
        return weight*30-300, weight*1.5
    return weight*30+300, weight*2

# ---------- UI THEME ----------
st.markdown("""
<style>
body {background-color: #0e1117; color: white;}
.stButton>button {background: #00d4aa; color: black;}
</style>
""", unsafe_allow_html=True)

# ---------- SESSION ----------
if "user" not in st.session_state:
    st.session_state.user = None

# ---------- LOGIN PAGE ----------
if st.session_state.user is None:
    st.title("🔐 Login / Register")

    menu = st.radio("", ["Login", "Register"])

    if menu == "Login":
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")

        if st.button("Login"):
            user = login(u, p)
            if not user.empty:
                st.session_state.user = user.iloc[0]
                st.success("Logged in")
                st.rerun()
            else:
                st.error("Invalid credentials")

    else:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        age = st.number_input("Age")
        height = st.number_input("Height")
        weight = st.number_input("Weight")
        goal = st.selectbox("Goal", ["fat loss","muscle gain"])

        if st.button("Register"):
            if register(u, p, age, height, weight, goal):
                st.success("Registered. Now login.")
            else:
                st.error("Username exists")

# ---------- MAIN APP ----------
else:
    user = st.session_state.user
    uid = int(user["id"])
    weight = float(user["weight"])
    goal = user["goal"]

    st.sidebar.title(f"👋 {user['username']}")
    menu = st.sidebar.radio("Menu", ["Dashboard","Add Log","Analytics","Logout"])

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
        col3.metric("Total Logs", len(logs))

        if not logs.empty:
            fig = px.line(logs, x="date", y=["calories","protein"], title="Progress")
            st.plotly_chart(fig, use_container_width=True)

    # ADD LOG
    elif menu == "Add Log":
        st.title("📥 Add Daily Data")

        cal = st.number_input("Calories")
        pro = st.number_input("Protein")
        work = st.selectbox("Workout", ["yes","no"])
        wt = st.number_input("Weight")

        if st.button("Save"):
            add_log(uid, cal, pro, work, wt)
            st.success("Saved")

    # ANALYTICS
    elif menu == "Analytics":
        st.title("📊 Analytics")

        logs = get_logs(uid)

        if logs.empty:
            st.warning("No data")
        else:
            rec_cal, rec_pro = get_rec(weight, goal)

            avg_cal = logs["calories"].mean()
            avg_pro = logs["protein"].mean()

            st.write(f"Avg Calories: {avg_cal:.0f}")
            st.write(f"Avg Protein: {avg_pro:.0f}")

            fig = px.bar(logs, x="date", y="weight", title="Weight Trend")
            st.plotly_chart(fig, use_container_width=True)

            # INSIGHTS
            st.subheader("Insights")

            if avg_pro < rec_pro*0.85:
                st.error("Low protein intake")
            else:
                st.success("Protein on track")

            workout_days = (logs["workout"]=="yes").sum()

            if workout_days < 3:
                st.warning("Workout consistency low")
            else:
                st.success("Workout consistent")
