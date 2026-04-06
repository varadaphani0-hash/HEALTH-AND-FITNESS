import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import plotly.express as px

st.set_page_config(page_title="Health & Fitness", layout="wide")

# ---------- STYLE ----------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(to right, #0f2027, #203a43, #2c5364);
    color: white;
}
.card {
    padding: 20px;
    border-radius: 15px;
    background-color: rgba(255,255,255,0.05);
    box-shadow: 0px 4px 20px rgba(0,0,0,0.3);
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

# ---------- DB ----------
def connect():
    return sqlite3.connect("fitness.db", check_same_thread=False)

def create_db():
    conn = connect()
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        age INTEGER,
        height REAL,
        weight REAL,
        goal TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        date TEXT,
        calories REAL,
        protein REAL,
        workout TEXT,
        weight REAL
    )""")

    conn.commit()
    conn.close()

create_db()

# ---------- AUTH ----------
def register_user(u,p,a,h,w,g):
    try:
        conn = connect()
        conn.execute("INSERT INTO users(username,password,age,height,weight,goal) VALUES(?,?,?,?,?,?)",
                     (u.strip(),p.strip(),a,h,w,g))
        conn.commit()
        return True
    except:
        return False

def login_user(u,p):
    df = pd.read_sql("SELECT * FROM users", connect())
    return df[(df["username"].str.strip()==u.strip()) &
              (df["password"].str.strip()==p.strip())]

# ---------- LOGIC ----------
def add_log(uid,cal,pro,work,wt):
    conn = connect()
    conn.execute("INSERT INTO logs(user_id,date,calories,protein,workout,weight) VALUES(?,?,?,?,?,?)",
                 (uid, datetime.now().strftime("%Y-%m-%d"), cal, pro, work, wt))
    conn.commit()

def get_logs(uid):
    return pd.read_sql(f"SELECT * FROM logs WHERE user_id={uid}", connect())

def get_rec(weight,goal):
    if goal=="fat loss":
        return weight*30-300, weight*1.5
    return weight*30+300, weight*2

# ---------- SESSION ----------
if "user" not in st.session_state:
    st.session_state.user = None

# ---------- LOGIN ----------
if st.session_state.user is None:

    st.image("logo.png", width=120)
    st.markdown("<h1 style='text-align:center;'>Health & Fitness System</h1>", unsafe_allow_html=True)
    st.markdown("---")

    opt = st.radio("", ["Login","Register"])

    if opt=="Login":
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")

        if st.button("Login"):
            user = login_user(u,p)
            if not user.empty:
                st.session_state.user = user.iloc[0]
                st.rerun()
            else:
                st.error("Invalid credentials")

    else:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        age = st.number_input("Age")
        h = st.number_input("Height")
        w = st.number_input("Weight")
        g = st.selectbox("Goal", ["fat loss","muscle gain"])

        if st.button("Register"):
            if register_user(u,p,age,h,w,g):
                st.success("Registered. Now login.")
            else:
                st.error("Username exists")

# ---------- MAIN ----------
else:
    user = st.session_state.user
    uid = int(user["id"])
    weight = float(user["weight"])
    goal = user["goal"]

    st.sidebar.image("logo.png", width=100)
    st.sidebar.title(f"👤 {user['username']}")
    menu = st.sidebar.radio("Menu", ["Dashboard","Add Log","Analytics","Logout"])

    if menu=="Logout":
        st.session_state.user=None
        st.rerun()

    logs = get_logs(uid)

    # ---------- DASHBOARD ----------
    if menu=="Dashboard":
        st.title("📊 Dashboard")

        rec_cal, rec_pro = get_rec(weight, goal)

        col1,col2,col3 = st.columns(3)

        col1.markdown(f"<div class='card'><h3>Calories Target</h3><h2>{int(rec_cal)}</h2></div>", unsafe_allow_html=True)
        col2.markdown(f"<div class='card'><h3>Protein Target</h3><h2>{int(rec_pro)}</h2></div>", unsafe_allow_html=True)
        col3.markdown(f"<div class='card'><h3>Total Logs</h3><h2>{len(logs)}</h2></div>", unsafe_allow_html=True)

        if not logs.empty:
            st.markdown("### 📈 Progress")
            fig = px.line(logs, x="date", y=["calories","protein"], markers=True)
            fig.update_layout(template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)

    # ---------- ADD LOG ----------
    elif menu=="Add Log":
        st.title("➕ Add Daily Log")

        cal = st.number_input("Calories")
        pro = st.number_input("Protein")
        work = st.selectbox("Workout", ["yes","no"])
        wt = st.number_input("Weight")

        if st.button("Save"):
            add_log(uid,cal,pro,work,wt)
            st.success("Saved")

    # ---------- ANALYTICS ----------
    elif menu=="Analytics":
        st.title("📊 Analytics")

        if logs.empty:
            st.warning("No data")
        else:
            rec_cal, rec_pro = get_rec(weight, goal)

            recent = logs.tail(7)

            avg_cal = recent["calories"].mean()
            avg_pro = recent["protein"].mean()
            weight_change = recent["weight"].iloc[-1] - recent["weight"].iloc[0]

            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.subheader("Weekly Summary")
            st.write(f"🔥 Calories Avg: {avg_cal:.0f}")
            st.write(f"💪 Protein Avg: {avg_pro:.0f}")
            st.write(f"⚖️ Weight Change: {weight_change:.2f} kg")
            st.markdown("</div>", unsafe_allow_html=True)

            fig = px.bar(logs, x="date", y="weight")
            fig.update_layout(template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)

            # INSIGHTS
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.subheader("Insights")

            if avg_pro < rec_pro*0.85:
                st.error("⚠️ Low protein intake")

            workout_days = (recent["workout"]=="yes").sum()
            if workout_days < 3:
                st.warning("⚠️ Low workout consistency")

            if abs(weight_change) < 0.2:
                st.info("ℹ️ No significant weight change")

            if avg_pro >= rec_pro*0.85 and workout_days >= 3:
                st.success("✅ Good progress")

            st.markdown("</div>", unsafe_allow_html=True)

            # TABLE
            st.subheader("📋 Recent Logs")
            st.dataframe(logs.tail(10), use_container_width=True)
