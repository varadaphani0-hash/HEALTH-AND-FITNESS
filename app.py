import streamlit as st
import sqlite3
from datetime import datetime
import pandas as pd

# ---------------- DATABASE ----------------
def create_db():
    conn = sqlite3.connect("fitness.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        age INTEGER,
        height REAL,
        weight REAL,
        goal TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS logs (
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

# ---------------- FUNCTIONS ----------------
def register_user(name, age, height, weight, goal):
    conn = sqlite3.connect("fitness.db")
    c = conn.cursor()
    c.execute("INSERT INTO users (name,age,height,weight,goal) VALUES (?,?,?,?,?)",
              (name, age, height, weight, goal))
    conn.commit()
    conn.close()

def get_users():
    conn = sqlite3.connect("fitness.db")
    users = pd.read_sql("SELECT * FROM users", conn)
    conn.close()
    return users

def add_log(user_id, calories, protein, workout, weight):
    conn = sqlite3.connect("fitness.db")
    c = conn.cursor()
    date = datetime.now().strftime("%Y-%m-%d")
    c.execute("INSERT INTO logs (user_id,date,calories,protein,workout,weight) VALUES (?,?,?,?,?,?)",
              (user_id, date, calories, protein, workout, weight))
    conn.commit()
    conn.close()

def get_logs(user_id):
    conn = sqlite3.connect("fitness.db")
    df = pd.read_sql(f"SELECT * FROM logs WHERE user_id={user_id}", conn)
    conn.close()
    return df

def get_recommendations(weight, goal):
    if goal == "fat loss":
        return weight*30-300, weight*1.5
    else:
        return weight*30+300, weight*2.0

# ---------------- UI ----------------
st.title("🏋️ Fitness Data Management System")

menu = ["Register", "Add Log", "Analytics"]
choice = st.sidebar.selectbox("Menu", menu)

users = get_users()

# ---------------- REGISTER ----------------
if choice == "Register":
    st.subheader("Register User")

    name = st.text_input("Name")
    age = st.number_input("Age", 10, 100)
    height = st.number_input("Height (cm)")
    weight = st.number_input("Weight (kg)")
    goal = st.selectbox("Goal", ["fat loss", "muscle gain"])

    if st.button("Register"):
        register_user(name, age, height, weight, goal)
        st.success("User Registered")

# ---------------- ADD LOG ----------------
elif choice == "Add Log":
    st.subheader("Add Daily Log")

    if users.empty:
        st.warning("No users found")
    else:
        user = st.selectbox("Select User", users["name"])
        user_id = int(users[users["name"] == user]["id"].values[0])

        calories = st.number_input("Calories")
        protein = st.number_input("Protein")
        workout = st.selectbox("Workout", ["yes", "no"])
        weight = st.number_input("Current Weight")

        if st.button("Add Log"):
            add_log(user_id, calories, protein, workout, weight)
            st.success("Log Added")

# ---------------- ANALYTICS ----------------
elif choice == "Analytics":
    st.subheader("Analytics")

    if users.empty:
        st.warning("No users found")
    else:
        user = st.selectbox("Select User", users["name"])
        user_data = users[users["name"] == user]
        user_id = int(user_data["id"].values[0])
        weight = float(user_data["weight"].values[0])
        goal = user_data["goal"].values[0]

        logs = get_logs(user_id)

        if logs.empty:
            st.warning("No logs found")
        else:
            rec_cal, rec_pro = get_recommendations(weight, goal)

            st.write(f"Recommended Calories: {rec_cal:.0f}")
            st.write(f"Recommended Protein: {rec_pro:.0f}")

            st.line_chart(logs[["calories", "protein"]])

            avg_cal = logs["calories"].mean()
            avg_pro = logs["protein"].mean()

            st.write(f"Average Calories: {avg_cal:.0f}")
            st.write(f"Average Protein: {avg_pro:.0f}")

            if avg_pro < rec_pro * 0.85:
                st.error("Low protein intake")
            else:
                st.success("Protein on track")
