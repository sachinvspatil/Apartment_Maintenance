import streamlit as st
import sqlite3
import bcrypt
import pandas as pd
from datetime import datetime

# ────────────────────────────────
# 📦 Database Setup
# ────────────────────────────────
def create_tables():
    conn = sqlite3.connect("residents.db")
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password BLOB,
            role TEXT DEFAULT 'user'  -- 'admin' or 'user'
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS maintenance (
            username TEXT,
            amount REAL,
            date TEXT
        )
    """)

    conn.commit()
    conn.close()

# ────────────────────────────────
# 📝 Register Page
# ────────────────────────────────
def show_register():
    st.subheader("📝 Register")
    new_user = st.text_input("Choose a username")
    new_pass = st.text_input("Choose a password", type='password')
    is_admin = st.checkbox("Register as Admin (check for admin)", value=False)
    register_btn = st.button("Register")

    if register_btn:
        if not new_user or not new_pass:
            st.warning("Please enter both username and password.")
            return

        conn = sqlite3.connect("residents.db")
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=?", (new_user,))
        if cur.fetchone():
            st.error("Username already exists.")
        else:
            hashed = bcrypt.hashpw(new_pass.encode(), bcrypt.gensalt())
            role = 'admin' if is_admin else 'user'
            cur.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (new_user, hashed, role))
            conn.commit()
            st.success("✅ Registration successful! You can now log in.")
            st.session_state.page = "login"
        conn.close()

# ────────────────────────────────
# 🔐 Login Page
# ────────────────────────────────
def show_login():
    st.subheader("🔐 Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type='password')
    login_btn = st.button("Login")

    if login_btn:
        conn = sqlite3.connect("residents.db")
        cur = conn.cursor()
        cur.execute("SELECT password, role FROM users WHERE username=?", (username,))
        data = cur.fetchone()
        conn.close()

        if data and bcrypt.checkpw(password.encode(), data[0]):
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.role = data[1]  # Store role (user/admin)
            st.success("✅ Logged in successfully!")
            st.rerun()  # force dashboard load
        else:
            st.error("❌ Invalid username or password.")

# ────────────────────────────────
# 💳 Dashboard after Login
# ────────────────────────────────
def show_dashboard():
    st.subheader(f"👋 Welcome, {st.session_state.username}")
    
    if st.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.page = "login"
        st.rerun()

    if st.session_state.role == "admin":
        show_admin_dashboard()
    else:
        show_user_dashboard()

# ────────────────────────────────
# 💳 Admin Dashboard
# ────────────────────────────────
def show_admin_dashboard():
    st.markdown("### Admin Panel")
    st.subheader("🔄 View All Users' Payments")

    conn = sqlite3.connect("residents.db")
    cur = conn.cursor()
    cur.execute("SELECT username, amount, date FROM maintenance ORDER BY date DESC")
    rows = cur.fetchall()
    conn.close()

    if rows:
        df = pd.DataFrame(rows, columns=["Username", "Amount", "Date"])
        st.write(df)
        
        # Export to CSV
        st.download_button(
            label="Download Payment Data as CSV",
            data=df.to_csv(index=False).encode(),
            file_name="payment_data.csv",
            mime="text/csv"
        )
    else:
        st.info("No payments recorded yet.")

# ────────────────────────────────
# 💳 User Dashboard
# ────────────────────────────────
def show_user_dashboard():
    st.markdown("### 💵 Add Maintenance Fee")
    amount = st.number_input("Enter amount", min_value=0.0, step=10.0)
    if st.button("Submit Payment"):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = sqlite3.connect("residents.db")
        cur = conn.cursor()
        cur.execute("INSERT INTO maintenance (username, amount, date) VALUES (?, ?, ?)",
                    (st.session_state.username, amount, now))
        conn.commit()
        conn.close()
        st.success("✅ Payment recorded.")

    st.markdown("---")
    st.markdown("### 📜 Your Payment History")
    conn = sqlite3.connect("residents.db")
    cur = conn.cursor()
    cur.execute("SELECT amount, date FROM maintenance WHERE username=? ORDER BY date DESC", (st.session_state.username,))
    rows = cur.fetchall()
    conn.close()
    if rows:
        for amt, date in rows:
            st.write(f"💰 ₹{amt} on {date}")
    else:
        st.info("No payments found.")

    # Monthly Total
    st.markdown("---")
    st.markdown("### 📅 Monthly Total")
    current_month = datetime.now().strftime("%Y-%m")
    conn = sqlite3.connect("residents.db")
    cur = conn.cursor()
    cur.execute("SELECT SUM(amount) FROM maintenance WHERE username=? AND date LIKE ?", (st.session_state.username, f"{current_month}%"))
    total = cur.fetchone()[0]
    conn.close()
    if total:
        st.write(f"Total amount for {current_month}: ₹{total}")
    else:
        st.info(f"No payments for {current_month}.")

# ────────────────────────────────
# 🚀 Main App Logic
# ────────────────────────────────
def main():
    st.set_page_config(page_title="Apartment Maintenance", page_icon="🏢")
    st.title("🏢 Apartment Maintenance Portal")
    create_tables()

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "page" not in st.session_state:
        st.session_state.page = "login"

    if st.session_state.logged_in:
        show_dashboard()
    elif st.session_state.page == "login":
        show_login()
        st.markdown("---")
        if st.button("Don't have an account? Register here."):
            st.session_state.page = "register"
    elif st.session_state.page == "register":
        show_register()
        st.markdown("---")
        if st.button("Already have an account? Login here."):
            st.session_state.page = "login"

# ────────────────────────────────
# ▶️ Run the App
# ────────────────────────────────
if __name__ == "__main__":
    main()
