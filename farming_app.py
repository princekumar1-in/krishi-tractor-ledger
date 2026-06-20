import streamlit as st
import pandas as pd
import sqlite3
import hashlib
from datetime import datetime

# --- FARMING STORAGE CORE ---
FARM_DB = "krishi_secure_ledger_v1.db"

def init_farm_db():
    conn = sqlite3.connect(FARM_DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (mobile TEXT PRIMARY KEY, name TEXT, password TEXT, role TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS work_records 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  farmer_mobile TEXT, 
                  owner_mobile TEXT, 
                  date TEXT, 
                  area_bigha REAL, 
                  rate_per_bigha REAL, 
                  total_amount REAL, 
                  paid_amount REAL, 
                  status TEXT, 
                  notes TEXT)''')
    conn.commit()
    conn.close()

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def register_user(mobile, name, password, role):
    conn = sqlite3.connect(FARM_DB)
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users VALUES (?,?,?,?)', (mobile, name, make_hashes(password), role))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def login_user(mobile, password):
    conn = sqlite3.connect(FARM_DB)
    c = conn.cursor()
    c.execute('SELECT name, role FROM users WHERE mobile = ? AND password = ?', (mobile, make_hashes(password)))
    data = c.fetchone()
    conn.close()
    return data

def update_user_role(mobile, role):
    conn = sqlite3.connect(FARM_DB)
    c = conn.cursor()
    c.execute('UPDATE users SET role = ? WHERE mobile = ?', (role, mobile))
    conn.commit()
    conn.close()

def update_farm_transaction(t_id, bigha, rate, paid, status, notes):
    conn = sqlite3.connect(FARM_DB)
    c = conn.cursor()
    total = bigha * rate
    c.execute('''UPDATE work_records 
                 SET area_bigha=?, rate_per_bigha=?, total_amount=?, paid_amount=?, status=?, notes=? 
                 WHERE id=?''', (bigha, rate, total, paid, status, notes, t_id))
    conn.commit()
    conn.close()

def delete_farm_transaction(t_id):
    conn = sqlite3.connect(FARM_DB)
    c = conn.cursor()
    c.execute('DELETE FROM work_records WHERE id = ?', (t_id,))
    conn.commit()
    conn.close()

init_farm_db()

# --- STREAMLIT CONFIGURATION ---
st.set_page_config(page_title="Krishi Tractor Ledger", layout="wide", page_icon="🚜")

# --- MOBILE COMPATIBILITY LAYER & CLEAN UI ---
st.markdown("""
    <style>
    header, footer, .stDecoration, [data-testid="stStatusWidget"] { visibility: hidden !important; display: none !important; }
    #MainMenu, .stAppDeployDropdown { display: none !important; }
    [data-testid="stViewerBadge"] { display: none !important; }
    html, body, .stApp { 
        overscroll-behavior-y: contain !important; 
        -webkit-overflow-scrolling: touch !important;
    }
    </style>
""", unsafe_allow_html=True)

if "farm_logged_in" not in st.session_state: st.session_state["farm_logged_in"] = False
if "user_mobile" not in st.session_state: st.session_state["user_mobile"] = ""
if "user_name" not in st.session_state: st.session_state["user_name"] = ""
if "user_role" not in st.session_state: st.session_state["user_role"] = "None"

# --- PHASE 1: AUTHENTICATION ---
if not st.session_state["farm_logged_in"]:
    st.title("🚜 कृषि और ट्रैक्टर हिसाब लेजर")
    st.markdown("---")
    auth_choice = st.radio("Select Action:", ["Login Account", "Create New Account"], horizontal=True)
    
    col1, _ = st.columns([1, 2])
    with col1:
        if auth_choice == "Login Account":
            st.subheader("🔑 Sign In")
            mobile_in = st.text_input("Mobile Number (10 Digit):", max_chars=10).strip()
            pass_in = st.text_input("Password:", type="password")
            
            if st.button("LOGIN", use_container_width=True):
                if len(mobile_in) == 10 and mobile_in.isdigit():
                    user_data = login_user(mobile_in, pass_in)
                    if user_data:
                        st.session_state["farm_logged_in"] = True
                        st.session_state["user_mobile"] = mobile_in
                        st.session_state["user_name"] = user_data[0]
                        st.session_state["user_role"] = user_data[1]
                        st.rerun()
                    else: st.error("Galat Mobile Number ya Password!")
                else: st.error("Kripya sahi 10-digit mobile number daalein.")
                
        elif auth_choice == "Create New Account":
            st.subheader("📝 Registration")
            name_reg = st.text_input("Apna Naam (Full Name):").strip()
            mobile_reg = st.text_input("Mobile Number:", max_chars=10).strip()
            pass_reg = st.text_input("Strong Password:", type="password")
            
            if st.button("REGISTER NOW", use_container_width=True):
                if not name_reg or not mobile_reg or not pass_reg:
                    st.error("Saari fields bharna zaroori hai!")
                elif len(mobile_reg) != 10 or not mobile_reg.isdigit():
                    st.error("Mobile number 10 digits ka hona chahiye.")
                else:
                    if register_user(mobile_reg, name_reg, pass_reg, "None"):
                        st.success("Account Ban Gaya! Ab Login Karein.")
                    else: st.error("Ye Mobile Number pehle se registered hai!")
    st.stop()

# --- PHASE 2: FIRST TIME PROFILE SETUP ---
current_mobile = st.session_state["user_mobile"]
current_role = st.session_state["user_role"]

if current_role == "None":
    st.title("🌱 Select Your Profile Setup")
    st.markdown("---")
    st.subheader(f"Namaskar {st.session_state['user_name']}, aap app kaise chalana chahte hain?")
    
    role_choice = st.selectbox("Apna Profile Chunein:", [
        "Farmer (Kisan - Jameen Par Kaam Karwaya Hai)",
        "Tractor Owner (Mera Tractor Kaam Karta Hai)",
        "Farmer + Tractor Owner (Dono Kaam Manage Karne Hain)"
    ])
    
    if st.button("SAVE AND ENTER APP", use_container_width=True, type="primary"):
        final_role = "Farmer" if "Farmer (" in role_choice else "Tractor Owner" if "Tractor Owner" in role_choice else "Both"
        update_user_role(current_mobile, final_role)
        st.session_state["user_role"] = final_role
        st.rerun()
    st.stop()

# --- PHASE 3: MAIN MANAGEMENT SYSTEM ---
st.title(f"🚜 KRISHI MATRIX: {st.session_state['user_role'].upper()} MODE")
st.markdown(f"User: **{st.session_state['user_name']} ({current_mobile})**")
st.markdown("---")

app_mode = st.radio("Menu Operations:", ["📊 View System Ledger Records", "📝 Log New Farming Work"], horizontal=True)

if app_mode == "📝 Log New Farming Work":
    st.subheader("📝 Entry Form Management")
    with st.form("work_form", clear_on_submit=True):
        f_col, o_col = st.columns(2)
        with f_col:
            if st.session_state["user_role"] == "Farmer":
                farmer_num = current_mobile
                st.text_input("Farmer Mobile:", value=farmer_num, disabled=True)
                owner_num = st.text_input("Tractor Owner Mobile Number:").strip()
            elif st.session_state["user_role"] == "Tractor Owner":
                owner_num = current_mobile
                st.text_input("Tractor Owner Mobile:", value=owner_num, disabled=True)
                farmer_num = st.text_input("Farmer Mobile Number:").strip()
            else:
                work_type = st.selectbox("Kaam Kis Khet Ka Hai?", ["Apni Khud Ki Jameen", "Doosre Kisan Ki Jameen"])
                if work_type == "Apni Khud Ki Jameen":
                    farmer_num, owner_num = current_mobile, current_mobile
                else:
                    owner_num = current_mobile
                    farmer_num = st.text_input("Farmer Mobile Number:").strip()

        with o_col:
            date_work = st.date_input("Work Date", datetime.now())
            bigha = st.number_input("Total Bigha Area:", min_value=0.1, step=0.5)
            rate = st.number_input("Rate Per Bigha (₹):", min_value=1.0, step=50.0)
            paid = st.number_input("Advance Paid Amount (₹):", min_value=0.0, step=100.0)
            notes = st.text_area("Details (e.g., Papaya Buvai, Narma Jutai, Rotavator)")

        submit_work = st.form_submit_button("COMMIT SECURE RECORD ENTRY", use_container_width=True)

    if submit_work:
        if not farmer_num or not owner_num or len(farmer_num) != 10 or len(owner_num) != 10:
            st.error("Kripya dono valid 10-digit mobile number enter karein.")
        else:
            total_cost = bigha * rate
            status = "Paid" if paid >= total_cost else "Pending"
            conn = sqlite3.connect(FARM_DB)
            c = conn.cursor()
            c.execute('''INSERT INTO work_records (farmer_mobile, owner_mobile, date, area_bigha, rate_per_bigha, total_amount, paid_amount, status, notes)
                         VALUES (?,?,?,?,?,?,?,?,?)''', (farmer_num, owner_num, str(date_work), bigha, rate, total_cost, paid, status, notes))
            conn.commit()
            conn.close()
            st.toast("Record successfully link ho gaya!", icon="✅")

elif app_mode == "📊 View System Ledger Records":
    conn = sqlite3.connect(FARM_DB)
    if st.session_state["user_role"] == "Farmer":
        query = "SELECT * FROM work_records WHERE farmer_mobile = ?"
        df = pd.read_sql_query(query, conn, params=(current_mobile,))
    elif st.session_state["user_role"] == "Tractor Owner":
        query = "SELECT * FROM work_records WHERE owner_mobile = ?"
        df = pd.read_sql_query(query, conn, params=(current_mobile,))
    else:
        query = "SELECT * FROM work_records WHERE farmer_mobile = ? OR owner_mobile = ?"
        df = pd.read_sql_query(query, conn, params=(current_mobile, current_mobile))
    conn.close()

    if df.empty:
        st.info("Abhi tak koi accounting work record data nahi mila.")
    else:
        t_work = df["total_amount"].sum()
        t_paid = df["paid_amount"].sum()
        t_due = t_work - t_paid

        st.markdown("### ⚙️ Financial Metrics Matrix")
        s1, s2, s3 = st.columns(3)
        s1.metric("💰 Total Cost Logged", f"₹{t_work:,}")
        s2.metric("🟩 Paid / Settled", f"₹{t_paid:,}")
        s3.metric("🟥 Net Balance Due", f"₹{t_due:,}")

        st.markdown("---")
        st.subheader("📝 Live Statement Logs")
        
        for index, row in df.sort_values(by="date", ascending=False).iterrows():
            card_title = f"🗓️ {row['date']} | Bigha: {row['area_bigha']} | Total: ₹{row['total_amount']:,} | Status: [{row['status']}]"
            with st.expander(card_title):
                st.markdown(f"**🌾 Description Notes:** {row['notes']}")
                st.markdown(f"**📱 Connected Parameters:** Farmer ({row['farmer_mobile']}) ⇆ Owner ({row['owner_mobile']})")
                
                # Inline Edit / Delete Controllers
                st.markdown("---")
                e_col, d_col = st.columns(2)
                with e_col:
                    if st.button("✏️ Edit Entry", key=f"f_ed_{row['id']}", use_container_width=True):
                        st.session_state[f"farm_edit_show_{row['id']}"] = True
                with d_col:
                    if st.button("🗑️ Wipe Entry", key=f"f_del_{row['id']}", type="primary", use_container_width=True):
                        delete_farm_transaction(row['id'])
                        st.toast("Wiped!")
                        st.rerun()
                
                if f"farm_edit_show_{row['id']}" in st.session_state and st.session_state[f"farm_edit_show_{row['id']}"]:
                    st.markdown("##### ✏️ Update Values Matrix")
                    new_bigha = st.number_input("Change Bigha:", value=float(row['area_bigha']), key=f"eb_{row['id']}")
                    new_rate = st.number_input("Change Rate:", value=float(row['rate_per_bigha']), key=f"er_{row['id']}")
                    new_paid = st.number_input("Change Paid:", value=float(row['paid_amount']), key=f"ep_{row['id']}")
                    new_notes = st.text_area("Change Note:", value=row['notes'], key=f"en_{row['id']}")
                    
                    c_save, c_drop = st.columns(2)
                    with c_save:
                        if st.button("Commit Node Update", key=f"sb_v_{row['id']}", use_container_width=True):
                            new_status = "Paid" if new_paid >= (new_bigha * new_rate) else "Pending"
                            update_farm_transaction(row['id'], new_bigha, new_rate, new_paid, new_status, new_notes)
                            st.session_state[f"farm_edit_show_{row['id']}"] = False
                            st.rerun()
                    with c_drop:
                        if st.button("Drop Context", key=f"dr_v_{row['id']}", use_container_width=True):
                            st.session_state[f"farm_edit_show_{row['id']}"] = False
                            st.rerun()

st.markdown("---")
if st.button("🔒 SECURE TERMINAL SIGN OUT CONNECTION", type="primary", use_container_width=True):
    st.session_state["farm_logged_in"] = False
    st.rerun()
      
