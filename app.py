import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Fitness App", layout="wide")

# ---------------- DB ----------------
def connect():
    return sqlite3.connect("fitness.db")

def create_db():
    conn = connect()
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, age INT, height REAL, weight REAL, goal TEXT)""")

    c.execute("""CREATE TABLE IF NOT EXISTS logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INT, date TEXT, calories REAL,
        protein REAL, workout TEXT, weight REAL)""")

    conn.commit()
    conn.close()

create_db()

# ---------------- FUNCTIONS ----------------
def get_users():
    return pd.read_sql("SELECT * FROM users", connect())

def add_user(name, age, height, weight, goal):
    conn = connect()
    conn.execute("INSERT INTO users(name,age,height,weight,goal) VALUES(?,?,?,?,?)",
                 (name, age, height, weight, goal))
    conn.commit()
    conn.close()

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

# ---------------- UI ----------------
st.title("🔥 Fitness Intelligence Dashboard")

menu = st.sidebar.radio("Navigation", ["Dashboard","Register","Add Log","Analytics"])

users = get_users()

# ---------------- DASHBOARD ----------------
if menu == "Dashboard":
    st.subheader("Overview")

    if users.empty:
        st.warning("No users yet")
    else:
        user = st.selectbox("Select User", users["name"])
        data = users[users["name"]==user]
        uid = int(data["id"])
        weight = float(data["weight"])
        goal = data["goal"].values[0]

        logs = get_logs(uid)

        col1, col2, col3 = st.columns(3)

        rec_cal, rec_pro = get_rec(weight, goal)

        col1.metric("Target Calories", int(rec_cal))
        col2.metric("Target Protein", int(rec_pro))
        col3.metric("Logs Count", len(logs))

        if not logs.empty:
            st.line_chart(logs[["calories","protein"]])

# ---------------- REGISTER ----------------
elif menu == "Register":
    st.subheader("User Registration")

    name = st.text_input("Name")
    age = st.number_input("Age", 10, 100)
    height = st.number_input("Height")
    weight = st.number_input("Weight")
    goal = st.selectbox("Goal", ["fat loss","muscle gain"])

    if st.button("Register"):
        add_user(name, age, height, weight, goal)
        st.success("User Added")

# ---------------- ADD LOG ----------------
elif menu == "Add Log":
    st.subheader("Daily Tracking")

    if users.empty:
        st.warning("Add user first")
    else:
        user = st.selectbox("User", users["name"])
        uid = int(users[users["name"]==user]["id"])

        cal = st.number_input("Calories")
        pro = st.number_input("Protein")
        work = st.selectbox("Workout", ["yes","no"])
        wt = st.number_input("Weight")

        if st.button("Save Log"):
            add_log(uid, cal, pro, work, wt)
            st.success("Saved")

# ---------------- ANALYTICS ----------------
elif menu == "Analytics":
    st.subheader("Performance Analytics")

    if users.empty:
        st.warning("No users")
    else:
        user = st.selectbox("User", users["name"])
        data = users[users["name"]==user]
        uid = int(data["id"])
        weight = float(data["weight"])
        goal = data["goal"].values[0]

        logs = get_logs(uid)

        if logs.empty:
            st.warning("No logs")
        else:
            rec_cal, rec_pro = get_rec(weight, goal)

            avg_cal = logs["calories"].mean()
            avg_pro = logs["protein"].mean()

            st.write("### Averages")
            st.write(f"Calories: {avg_cal:.0f}")
            st.write(f"Protein: {avg_pro:.0f}")

            st.line_chart(logs["weight"])

            # INSIGHTS
            st.write("### Insights")

            if avg_pro < rec_pro*0.85:
                st.error("Low protein intake")
            else:
                st.success("Protein OK")

            workout_days = (logs["workout"]=="yes").sum()

            if workout_days < 3:
                st.warning("Low workout consistency")
            else:
                st.success("Workout consistent")
    
