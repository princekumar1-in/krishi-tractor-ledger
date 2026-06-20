import streamlit as st
import pandas as pd
import sqlite3
import hashlib
from datetime import datetime

# --- PRODUCTION STORAGE CORE ---
FARM_DB = "krishi_network_matrix_v1.db"

def init_farm_db():
    conn = sqlite3.connect(FARM_DB)
    c = conn.cursor()
    # Main App Authentication Users Table
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (mobile TEXT PRIMARY KEY, name TEXT, password TEXT, role TEXT)''')
    
    # Virtual Accounts Directory (Who created whose account ledger via mobile)
    c.execute('''CREATE TABLE IF NOT EXISTS virtual_accounts 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  creator_mobile TEXT,
                  target_mobile TEXT,
                  target_name TEXT,
                  target_type TEXT)''') # 'Farmer' or 'Tractor'
    
    # Unified Transaction & Work Records Ledger Table
    c.execute('''CREATE TABLE IF NOT EXISTS work_records 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  created_by_mobile TEXT,
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
    except sqlite3.IntegrityError: return False
    finally: conn.close()

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

def create_virtual_account(creator, target_mob, target_name, target_type):
    conn = sqlite3.connect(FARM_DB)
    c = conn.cursor()
    c.execute('SELECT 1 FROM virtual_accounts WHERE creator_mobile=? AND target_mobile=?', (creator, target_mob))
    if not c.fetchone():
        c.execute('INSERT INTO virtual_accounts (creator_mobile, target_mobile, target_name, target_type) VALUES (?,?,?,?)',
                  (creator, target_mob, target_name, target_type))
        conn.commit()
    conn.close()

def delete_farm_transaction(t_id):
    conn = sqlite3.connect(FARM_DB)
    c = conn.cursor()
    c.execute('DELETE FROM work_records WHERE id = ?', (t_id,))
    conn.commit()
    conn.close()

init_farm_db()

# --- STREAMLIT MASTER CONFIG ---
st.set_page_config(page_title="Krishi Network Ledger", layout="wide", page_icon="🚜")

st.markdown("""
    <style>
    header, footer, .stDecoration, [data-testid="stStatusWidget"] { visibility: hidden !important; display: none !important; }
    #MainMenu, .stAppDeployDropdown { display: none !important; }
    [data-testid="stViewerBadge"] { display: none !important; }
    html, body, .stApp { overscroll-behavior-y: contain !important; -webkit-overflow-scrolling: touch !important; }
    </style>
""", unsafe_allow_html=True)

if "farm_logged_in" not in st.session_state: st.session_state["farm_logged_in"] = False
if "user_mobile" not in st.session_state: st.session_state["user_mobile"] = ""
if "user_name" not in st.session_state: st.session_state["user_name"] = ""
if "user_role" not in st.session_state: st.session_state["user_role"] = "None"

# --- PHASE 1: AUTHENTICATION SYSTEM ---
if not st.session_state["farm_logged_in"]:
    st.title("🚜 कृषि और ट्रैक्टर नेटवर्क लेजर")
    st.markdown("---")
    auth_choice = st.radio("Action:", ["Login Account", "Create New Account"], horizontal=True)
    col1, _ = st.columns([1, 2])
    with col1:
        if auth_choice == "Login Account":
            st.subheader("🔑 Sign In")
            mobile_in = st.text_input("Mobile Number:", max_chars=10).strip()
            pass_in = st.text_input("Password:", type="password")
            if st.button("LOGIN", use_container_width=True):
                if len(mobile_in) == 10 and mobile_in.isdigit():
                    user_data = login_user(mobile_in, pass_in)
                    if user_data:
                        st.session_state["farm_logged_in"] = True
                        st.session_state["user_mobile"] = mobile_in
                        st.session_state["user_name"] = user_data[0]
                        st.session_state["user_role"] = user_data[1]
                        st.text("Loading Session...")
                        st.rerun()
                    else: st.error("Galat credentials!")
                else: st.error("Sahi 10-digit number daalein.")
        elif auth_choice == "Create New Account":
            st.subheader("📝 Registration")
            name_reg = st.text_input("Naam (Full Name):").strip()
            mobile_reg = st.text_input("Mobile Number:", max_chars=10).strip()
            pass_reg = st.text_input("Password:", type="password")
            if st.button("REGISTER NOW", use_container_width=True):
                if not name_reg or not mobile_reg or not pass_reg: st.error("Saari fields bharein!")
                elif len(mobile_reg) != 10 or not mobile_reg.isdigit(): st.error("Sahi 10-digit number daalein.")
                else:
                    if register_user(mobile_reg, name_reg, pass_reg, "None"): st.success("Account Ready! Login karein.")
                    else: st.error("Mobile Number pehle se registered hai!")
    st.stop()

# --- PHASE 2: ROLE SELECTOR CONFIG ---
current_mobile = st.session_state["user_mobile"]
current_role = st.session_state["user_role"]

if current_role == "None":
    st.title("🌱 Profile Setup")
    st.subheader(f"Namaskar {st.session_state['user_name']}, aapka profile setup:")
    role_choice = st.selectbox("Apna Profile Chunein:", [
        "Farmer (Kisan - Jameen Buvai Ka Hisab)",
        "Tractor Owner (Tractor Se Kaam Karne Wale)",
        "Farmer + Tractor Owner (Dono Kaam Manage Karne Wale)"
    ])
    if st.button("SAVE AND ENTER SYSTEM", use_container_width=True, type="primary"):
        final_role = "Farmer" if "Farmer (" in role_choice else "Tractor Owner" if "Tractor Owner" in role_choice else "Both"
        update_user_role(current_mobile, final_role)
        st.session_state["user_role"] = final_role
        st.rerun()
    st.stop()

# --- PHASE 3: MAIN APP NETWORKING ---
st.title(f"🚜 KRISHI MATRIX Ledger [Mode: {st.session_state['user_role'].upper()}]")
st.markdown(f"User Active: **{st.session_state['user_name']} ({current_mobile})**")
st.markdown("---")

menu = st.radio("Navigate Node Operations:", ["🗂️ Manage Accounts Directory & Entries", "👁️ Shared View Network Matrix"], horizontal=True)

if menu == "🗂️ Manage Accounts Directory & Entries":
    st.subheader("📁 Apne Khate (Ledger Directory)")
    
    # Section A: Create New Virtual Sub-Account Node
    with st.expander("➕ Naya Khata Add Karein (Create New Sub-Ledger Account)"):
        v_name = st.text_input("Account Holder Name / Naam:").strip().title()
        v_mob = st.text_input("Account Holder Mobile Number:", max_chars=10).strip()
        if st.session_state["user_role"] == "Farmer": target_type_assigned = "Tractor"
        elif st.session_state["user_role"] == "Tractor Owner": target_type_assigned = "Farmer"
        else: target_type_assigned = st.selectbox("Khate Ka Type Kya Hai?", ["Farmer", "Tractor"])
        
        if st.button("CREATE ACCOUNT VIRTUAL NODE", use_container_width=True):
            if not v_name or len(v_mob) != 10 or not v_mob.isdigit(): st.error("Sahi Naam aur 10-digit number daalna zaroori hai.")
            elif v_mob == current_mobile: st.error("Aap apna khud ka number yahan register nahi kar sakte.")
            else:
                create_virtual_account(current_mobile, v_mob, v_name, target_type_assigned)
                st.success(f"{v_name} Ka Khata Matrix Safaltapoorvak Add Ho Gaya!")
                st.preload = True
                st.rerun()

    # Section B: Fetch All Created Accounts Directory
    conn = sqlite3.connect(FARM_DB)
    v_df = pd.read_sql_query("SELECT target_mobile, target_name, target_type FROM virtual_accounts WHERE creator_mobile=?", conn, params=(current_mobile,))
    conn.close()

    if v_df.empty:
        st.info("Aapki directory mein abhi tak koi khata nahi hai. Kripya upar click karke pehla khata add karein!")
    else:
        # Create selectbox directory
        directory_options = [f"{row['target_name']} ({row['target_mobile']}) - [{row['target_type']}]" for index, row in v_df.iterrows()]
        selected_account = st.selectbox("🎯 entry Karne Ke Liye Khata (Account) Chunein:", directory_options)
        
        # Extract target mobile parameters safely
        target_active_mobile = selected_account.split("(")[1].split(")")[0]
        target_active_name = selected_account.split(" - ")[0]
        target_active_type = "Farmer" if "[Farmer]" in selected_account else "Tractor"

        st.markdown("---")
        # Log entry for the selected virtual account
        st.markdown(f"#### 📝 Entry Log Node Form For: **{target_active_name}**")
        with st.form("entry_form_krishi", clear_on_submit=True):
            col_left, col_right = st.columns(2)
            with col_left:
                date_w = st.date_input("Work Date", datetime.now())
                bigha = st.number_input("Area (Total Bigha / Acre):", min_value=0.1, step=0.5)
                rate = st.number_input("Rate Per Unit (₹):", min_value=1.0, step=50.0)
            with col_right:
                paid = st.number_input("Amount Received/Paid Ledger (₹):", min_value=0.0, step=100.0)
                notes = st.text_area("Work Details (e.g., Gehun Buvai, Narma Harrow Work)")
            
            submit_entry = st.form_submit_button("COMMIT TRANSACTION TO THIS ACCOUNT", use_container_width=True)

        if submit_entry:
            # Map dynamic relation values based on roles
            if st.session_state["user_role"] == "Farmer" or (st.session_state["user_role"] == "Both" and target_active_type == "Tractor"):
                f_num, o_num = current_mobile, target_active_mobile
            else: f_num, o_num = target_active_mobile, current_mobile
                
            total_cost = bigha * rate
            status = "Paid" if paid >= total_cost else "Pending"
            
            conn = sqlite3.connect(FARM_DB)
            c = conn.cursor()
            c.execute('''INSERT INTO work_records (created_by_mobile, farmer_mobile, owner_mobile, date, area_bigha, rate_per_bigha, total_amount, paid_amount, status, notes)
                         VALUES (?,?,?,?,?,?,?,?,?,?)''', (current_mobile, f_num, o_num, str(date_w), bigha, rate, total_cost, paid, status, notes))
            conn.commit()
            conn.close()
            st.toast("Record Logged successfully!", icon="✅")
            st.rerun()

        # Section C: Display Entries created inside this specific account
        st.markdown(f"#### 📊 Personal Entries in {target_active_name}'s Ledger")
        conn = sqlite3.connect(FARM_DB)
        entries_df = pd.read_sql_query("SELECT id, date, area_bigha, rate_per_bigha, total_amount, paid_amount, status, notes FROM work_records WHERE created_by_mobile=? AND (farmer_mobile=? OR owner_mobile=?)", 
                                        conn, params=(current_mobile, target_active_mobile, target_active_mobile))
        conn.close()

        if entries_df.empty:
            st.info("Is khate mein abhi koi entry nahi hai.")
        else:
            for index, r in entries_df.sort_values(by="date", ascending=False).iterrows():
                with st.expander(f"🗓️ Date: {r['date']} | Total: ₹{r['total_amount']:,} | Received/Paid: ₹{r['paid_amount']:,} | [{r['status']}]"):
                    st.write(f"📝 **Details:** {r['notes']}")
                    st.write(f"🚜 Parameters: {r['area_bigha']} Bigha @ ₹{r['rate_per_bigha']}/Bigha")
                    if st.button("🗑️ Wipe Entry Record", key=f"del_krishi_{r['id']}", type="primary"):
                        delete_farm_transaction(r['id'])
                        st.toast("Entry Wiped!")
                        st.rerun()

elif menu == "👁️ Shared View Network Matrix":
    st.subheader("👁️ Saamne Waale Ne Kya Entries Daali Hain? (Network Cross-View)")
    st.info("Security Lock Control Active: Aap yahan par doosro ka data sirf dekh paayenge (Read-Only), use edit ya mita nahi sakte.")
    
    conn = sqlite3.connect(FARM_DB)
    # Fetch entries created by OTHER USERS that target current user's phone number
    shared_df = pd.read_sql_query('''SELECT date, area_bigha, rate_per_bigha, total_amount, paid_amount, status, notes, created_by_mobile 
                                     FROM work_records 
                                     WHERE created_by_mobile != ? AND (farmer_mobile = ? OR owner_mobile = ?)''', 
                                  conn, params=(current_mobile, current_mobile, current_mobile))
    conn.close()

    if shared_df.empty:
        st.info("Abhi tak kisi anya tractor maalik ya kisan ne aapke mobile number par koi entry network par publish nahi ki hai.")
    else:
        # Display Shared view stats
        s_work = shared_df["total_amount"].sum()
        s_paid = shared_df["paid_amount"].sum()
        s_due = s_work - s_paid
        
        col_s1, col_s2, col_s3 = st.columns(3)
        col_s1.metric("🌍 Network Total Work Cost", f"₹{s_work:,}")
        col_s2.metric("🟩 Network Settled Amount", f"₹{s_paid:,}")
        col_s3.metric("🟥 Network Due Calculation", f"₹{s_due:,}")
        
        st.markdown("---")
        for index, row in shared_df.sort_values(by="date", ascending=False).iterrows():
            with st.expander(f"📥 Entry by Node ({row['created_by_mobile']}) | Date: {row['date']} | Amount: ₹{row['total_amount']:,} | Status: [{row['status']}]"):
                st.markdown(f"**🌾 Logged Details Note:** {row['notes']}")
                st.markdown(f"**📊 Analytics Frame:** {row['area_bigha']} Bigha across ₹{row['rate_per_bigha']}/Bigha rate standard.")
                st.markdown("<span style='color: #4A90E2; font-size: 0.85em;'>🔒 Security Guardrail: Read-Only System Synced</span>", unsafe_allow_html=True)

st.markdown("---")
if st.button("🔒 SECURE TERMINAL SIGN OUT CONNECTION", type="primary", use_container_width=True):
    st.session_state["farm_logged_in"] = False
    st.rerun()
