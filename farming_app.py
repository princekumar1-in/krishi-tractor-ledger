import streamlit as st
import pandas as pd
import sqlite3
import hashlib
from datetime import datetime

# --- PRODUCTION STORAGE CORE ---
FARM_DB = "krishi_network_matrix_v2.db"

def init_farm_db():
    conn = sqlite3.connect(FARM_DB)
    c = conn.cursor()
    # Users Table
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (mobile TEXT PRIMARY KEY, name TEXT, password TEXT, role TEXT)''')
    # Virtual Accounts Table
    c.execute('''CREATE TABLE IF NOT EXISTS virtual_accounts 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  creator_mobile TEXT,
                  target_mobile TEXT,
                  target_name TEXT,
                  target_type TEXT)''')
    # Fixed Work Records Table with proper tracking
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

# Language Dictionary Setup
LANG_DICT = {
    "English": {
        "title": "🚜 Krishi & Tractor Network Ledger",
        "login_tab": "Login Account",
        "register_tab": "Create New Account",
        "signin_header": "🔑 Sign In",
        "reg_header": "📝 Registration",
        "mobile_label": "Mobile Number (10 Digit):",
        "password_label": "Password:",
        "name_label": "Full Name / Naam:",
        "login_btn": "LOGIN",
        "register_btn": "REGISTER NOW",
        "profile_title": "🌱 Profile Setup",
        "profile_sub": "Namaskar {}, select your profile setup:",
        "role_label": "Choose Profile Role:",
        "role_f": "Farmer (Manage Sowing/Farming Cost)",
        "role_t": "Tractor Owner (Manage Tractor Commercial Work)",
        "role_b": "Farmer + Tractor Owner (Manage Both Dynamically)",
        "save_enter_btn": "SAVE AND ENTER SYSTEM",
        "menu_opt1": "🗂️ Manage Accounts Directory & Entries",
        "menu_opt2": "👁️ Shared View Network Matrix",
        "dir_header": "📁 Your Accounts Directory (Khate)",
        "add_khata_exp": "➕ Add New Account Ledger (Naya Khata)",
        "acc_name": "Account Holder Name:",
        "acc_mob": "Account Holder Mobile Number:",
        "acc_type": "Account Type Role:",
        "create_node_btn": "CREATE ACCOUNT VIRTUAL NODE",
        "select_khata_label": "🎯 Choose Account to Add Entry:",
        "entry_form_title": "📝 Entry Log Form For: ",
        "work_date": "Work Date",
        "area_label": "Area (Total Bigha / Acre):",
        "rate_label": "Rate Per Unit (₹):",
        "paid_label": "Amount Received/Paid (₹):",
        "details_label": "Work Details / Notes:",
        "commit_btn": "COMMIT TRANSACTION TO THIS ACCOUNT",
        "personal_entries_title": "📊 Personal Entries in {}'s Ledger",
        "wipe_btn": "🗑️ Wipe Entry Record",
        "shared_title": "👁️ Shared Network Matrix View (Live Sync)",
        "shared_info": "🔒 Security Lock: Entries published by other users connected to your phone number are Read-Only.",
        "shared_empty": "No external users have logged any data linking to your mobile number yet.",
        "stat_total": "🌍 Network Total Cost",
        "stat_paid": "🟩 Network Settled Amount",
        "stat_due": "🟥 Network Due Calculation",
        "signout_btn": "🔒 SECURE TERMINAL SIGN OUT CONNECTION",
        "error_mob": "Please enter a valid 10-digit mobile number.",
        "error_fields": "All fields are required!",
        "error_self": "You cannot register your own mobile number here.",
        "toast_success": "Record logged and synced successfully!",
        "details_lbl": "Details:",
        "param_lbl": "Parameters:"
    },
    "Hindi": {
        "title": "🚜 कृषि और ट्रैक्टर नेटवर्क लेजर",
        "login_tab": "लॉगिन अकाउंट",
        "register_tab": "नया अकाउंट बनाएं",
        "signin_header": "🔑 साइन इन करें",
        "reg_header": "📝 नया रजिस्ट्रेशन",
        "mobile_label": "मोबाइल नंबर (10 अंक):",
        "password_label": "पासवर्ड:",
        "name_label": "आपका पूरा नाम:",
        "login_btn": "लॉगिन करें",
        "register_btn": "अकाउंट रजिस्टर करें",
        "profile_title": "🌱 प्रोफाइल सेटअप",
        "profile_sub": "नमस्कार {}, अपना प्रोफाइल सेटअप चुनें:",
        "role_label": "अपना काम/प्रोफाइल चुनें:",
        "role_f": "किसान (Farmer - सिर्फ खेती/बुवाई का हिसाब रखना है)",
        "role_t": "ट्रैक्टर मालिक (Tractor Owner - दूसरों का काम करने वाले)",
        "role_b": "किसान + ट्रैक्टर मालिक (Farmer + Tractor Owner - दोनों काम)",
        "save_enter_btn": "प्रोफाइल सेव करके ऐप में जाएं",
        "menu_opt1": "🗂️ खाते (Directory) और नई एंट्री डालें",
        "menu_opt2": "👁️ शेयर्ड नेटवर्क (दूसरों ने क्या एंट्री डाली)",
        "dir_header": "📁 आपके खाते (Ledger Directory)",
        "add_khata_exp": "➕ नया खाता जोड़ें (Create New Account)",
        "acc_name": "खाता धारक का नाम:",
        "acc_mob": "खाता धारक का मोबाइल नंबर:",
        "acc_type": "खाते का प्रकार (Role):",
        "create_node_btn": "नया खाता (Directory) सेव करें",
        "select_khata_label": "🎯 एंट्री करने के लिए खाता चुनें:",
        "entry_form_title": "📝 नया हिसाब फॉर्म किसके लिए: ",
        "work_date": "काम की तारीख",
        "area_label": "कुल जमीन (बीघा / एकड़):",
        "rate_label": "रेट प्रति बीघा (₹):",
        "paid_label": "एडवांस / दिया हुआ पैसा (₹):",
        "details_label": "काम की जानकारी (जैसे: नरमा बुवाई, गेहूं जुताई):",
        "commit_btn": "इस खाते में एंट्री पक्की (Save) करें",
        "personal_entries_title": "📊 {} के खाते में आपकी डाली गई एंट्रियां",
        "wipe_btn": "🗑️ एंट्री डिलीट करें",
        "shared_title": "👁️ शेयर्ड नेटवर्क मैट्रिक्स (लाइव सिंक व्यू)",
        "shared_info": "🔒 सुरक्षा लॉक: सामने वाले व्यक्ति ने जो एंट्री डाली है उसे आप सिर्फ देख सकते हैं, बदल नहीं सकते।",
        "shared_empty": "अभी तक किसी भी ट्रैक्टर मालिक या किसान ने आपके मोबाइल नंबर पर कोई लाइव एंट्री नहीं डाली है।",
        "stat_total": "🌍 नेटवर्क कुल काम लागत",
        "stat_paid": "🟩 नेटवर्क कुल चुकता राशि",
        "stat_due": "🟥 नेटवर्क कुल बाकी पैसा",
        "signout_btn": "🔒 अकाउंट लॉग आउट (Sign Out) करें",
        "error_mob": "कृपया सही 10 अंकों का मोबाइल नंबर डालें।",
        "error_fields": "सभी जानकारी भरना अनिवार्य है!",
        "error_self": "आप अपना खुद का नंबर यहाँ रजिस्टर नहीं कर सकते।",
        "toast_success": "रिकॉर्ड सफलतापूर्वक सेव और लिंक हो गया!",
        "details_lbl": "विवरण / नोट:",
        "param_lbl": "पैरामीटर:"
    }
}

# Persistent Language Selection Configuration
if "app_lang" not in st.session_state: st.session_state["app_lang"] = "English"

# --- GLOBAL LANGUAGE SELECTOR ON TOP ---
col_lang, _ = st.columns([1, 4])
with col_lang:
    st.session_state["app_lang"] = st.selectbox("🌐 Select Language / भाषा चुनें:", ["English", "Hindi"], index=0 if st.session_state["app_lang"] == "English" else 1)

L = LANG_DICT[st.session_state["app_lang"]]

if "farm_logged_in" not in st.session_state: st.session_state["farm_logged_in"] = False
if "user_mobile" not in st.session_state: st.session_state["user_mobile"] = ""
if "user_name" not in st.session_state: st.session_state["user_name"] = ""
if "user_role" not in st.session_state: st.session_state["user_role"] = "None"

# --- PHASE 1: AUTHENTICATION SYSTEM ---
if not st.session_state["farm_logged_in"]:
    st.title(L["title"])
    st.markdown("---")
    auth_choice = st.radio("Action:", [L["login_tab"], L["register_tab"]], horizontal=True)
    col1, _ = st.columns([1, 2])
    
    with col1:
        if auth_choice == L["login_tab"]:
            st.subheader(L["signin_header"])
            mobile_in = st.text_input(L["mobile_label"], max_chars=10, key="lin_mob").strip()
            pass_in = st.text_input(L["password_label"], type="password", key="lin_pwd")
            if st.button(L["login_btn"], use_container_width=True):
                if len(mobile_in) == 10 and mobile_in.isdigit():
                    user_data = login_user(mobile_in, pass_in)
                    if user_data:
                        st.session_state["farm_logged_in"] = True
                        st.session_state["user_mobile"] = mobile_in
                        st.session_state["user_name"] = user_data[0]
                        st.session_state["user_role"] = user_data[1]
                        st.rerun()
                    else: st.error("Wrong Username / Password!")
                else: st.error(L["error_mob"])
        elif auth_choice == L["register_tab"]:
            st.subheader(L["reg_header"])
            name_reg = st.text_input(L["name_label"], key="reg_nm").strip()
            mobile_reg = st.text_input(L["mobile_label"], max_chars=10, key="reg_mb").strip()
            pass_reg = st.text_input(L["password_label"], type="password", key="reg_pw")
            if st.button(L["register_btn"], use_container_width=True):
                if not name_reg or not mobile_reg or not pass_reg: st.error(L["error_fields"])
                elif len(mobile_reg) != 10 or not mobile_reg.isdigit(): st.error(L["error_mob"])
                else:
                    if register_user(mobile_reg, name_reg, pass_reg, "None"): st.success("Success! Please Login.")
                    else: st.error("Mobile Number Already Exists!")
    st.stop()

# --- PHASE 2: ROLE SELECTOR CONFIG ---
current_mobile = st.session_state["user_mobile"]
current_role = st.session_state["user_role"]

if current_role == "None":
    st.title(L["profile_title"])
    st.subheader(L["profile_sub"].format(st.session_state['user_name']))
    role_choice = st.selectbox(L["role_label"], [L["role_f"], L["role_t"], L["role_b"]])
    if st.button(L["save_enter_btn"], use_container_width=True, type="primary"):
        if role_choice == L["role_f"]: final_role = "Farmer"
        elif role_choice == L["role_t"]: final_role = "Tractor Owner"
        else: final_role = "Both"
        update_user_role(current_mobile, final_role)
        st.session_state["user_role"] = final_role
        st.rerun()
    st.stop()

# --- PHASE 3: MAIN APP NETWORKING ---
st.title(f"{L['title']} [Mode: {st.session_state['user_role'].upper()}]")
st.markdown(f"Active Session: **{st.session_state['user_name']} ({current_mobile})**")
st.markdown("---")

menu = st.radio("Menu Operations:", [L["menu_opt1"], L["menu_opt2"]], horizontal=True)

if menu == L["menu_opt1"]:
    st.subheader(L["dir_header"])
    
    # Section A: Create Virtual Account
    with st.expander(L["add_khata_exp"]):
        v_name = st.text_input(L["acc_name"]).strip().title()
        v_mob = st.text_input(L["acc_mob"], max_chars=10).strip()
        
        if st.session_state["user_role"] == "Farmer": target_type_assigned = "Tractor"
        elif st.session_state["user_role"] == "Tractor Owner": target_type_assigned = "Farmer"
        else: target_type_assigned = st.selectbox(L["acc_type"], ["Farmer", "Tractor"])
        
        if st.button(L["create_node_btn"], use_container_width=True):
            if not v_name or len(v_mob) != 10 or not v_mob.isdigit(): st.error(L["error_fields"] + " " + L["error_mob"])
            elif v_mob == current_mobile: st.error(L["error_self"])
            else:
                create_virtual_account(current_mobile, v_mob, v_name, target_type_assigned)
                st.success("Account Node Linked Successfully!")
                st.rerun()

    # Section B: Fetch Directory
    conn = sqlite3.connect(FARM_DB)
    v_df = pd.read_sql_query("SELECT target_mobile, target_name, target_type FROM virtual_accounts WHERE creator_mobile=?", conn, params=(current_mobile,))
    conn.close()

    if v_df.empty:
        st.info("No accounts in directory yet. Please add one above.")
    else:
        directory_options = [f"{row['target_name']} ({row['target_mobile']}) - [{row['target_type']}]" for index, row in v_df.iterrows()]
        selected_account = st.selectbox(L["select_khata_label"], directory_options)
        
        target_active_mobile = selected_account.split("(")[1].split(")")[0]
        target_active_name = selected_account.split(" - ")[0]
        target_active_type = "Farmer" if "[Farmer]" in selected_account else "Tractor"

        st.markdown("---")
        st.markdown(f"#### {L['entry_form_title']} **{target_active_name}**")
        with st.form("entry_form_krishi", clear_on_submit=True):
            col_left, col_right = st.columns(2)
            with col_left:
                date_w = st.date_input(L["work_date"], datetime.now())
                bigha = st.number_input(L["area_label"], min_value=0.1, step=0.5)
                rate = st.number_input(L["rate_label"], min_value=1.0, step=50.0)
            with col_right:
                paid = st.number_input(L["paid_label"], min_value=0.0, step=100.0)
                notes = st.text_area(L["details_label"])
            
            submit_entry = st.form_submit_button(L["commit_btn"], use_container_width=True)

        if submit_entry:
            # FIXED BI-DIRECTIONAL ASSIGNMENT FOR SHARING SYSTEM
            if st.session_state["user_role"] == "Farmer" or (st.session_state["user_role"] == "Both" and target_active_type == "Tractor"):
                f_num, o_num = current_mobile, target_active_mobile
            else: 
                f_num, o_num = target_active_mobile, current_mobile
                
            total_cost = bigha * rate
            status = "Paid" if paid >= total_cost else "Pending"
            
            conn = sqlite3.connect(FARM_DB)
            c = conn.cursor()
            c.execute('''INSERT INTO work_records (created_by_mobile, farmer_mobile, owner_mobile, date, area_bigha, rate_per_bigha, total_amount, paid_amount, status, notes)
                         VALUES (?,?,?,?,?,?,?,?,?,?)''', (current_mobile, f_num, o_num, str(date_w), bigha, rate, total_cost, paid, status, notes))
            conn.commit()
            conn.close()
            st.toast(L["toast_success"], icon="✅")
            st.rerun()

        # Section C: Display Entries
        st.markdown(f"#### {L['personal_entries_title'].format(target_active_name)}")
        conn = sqlite3.connect(FARM_DB)
        entries_df = pd.read_sql_query("SELECT id, date, area_bigha, rate_per_bigha, total_amount, paid_amount, status, notes FROM work_records WHERE created_by_mobile=? AND (farmer_mobile=? OR owner_mobile=?)", 
                                        conn, params=(current_mobile, target_active_mobile, target_active_mobile))
        conn.close()

        if entries_df.empty:
            st.info("No records inside this account.")
        else:
            for index, r in entries_df.sort_values(by="date", ascending=False).iterrows():
                with st.expander(f"🗓️ {r['date']} | Total: ₹{r['total_amount']:,} | Paid: ₹{r['paid_amount']:,} | [{r['status']}]"):
                    st.write(f"📝 **{L['details_lbl']}** {r['notes']}")
                    st.write(f"🚜 {L['param_lbl']} {r['area_bigha']} Bigha @ ₹{r['rate_per_bigha']}/Unit")
                    if st.button(L["wipe_btn"], key=f"del_krishi_{r['id']}", type="primary"):
                        delete_farm_transaction(r['id'])
                        st.toast("Wiped!")
                        st.rerun()

elif menu == L["menu_opt2"]:
    st.subheader(L["shared_title"])
    st.info(L["shared_info"])
    
    conn = sqlite3.connect(FARM_DB)
    # FIXED DATABASE MATRIX QUERY TO TARGET CORRESPONDING REGISTERED PHONENUMBER VIA BI-DIRECTIONAL LEADER LINKS
    shared_df = pd.read_sql_query('''SELECT date, area_bigha, rate_per_bigha, total_amount, paid_amount, status, notes, created_by_mobile 
                                     FROM work_records 
                                     WHERE created_by_mobile != ? AND (farmer_mobile = ? OR owner_mobile = ?)''', 
                                  conn, params=(current_mobile, current_mobile, current_mobile))
    conn.close()

    if shared_df.empty:
        st.info(L["shared_empty"])
    else:
        s_work = shared_df["total_amount"].sum()
        s_paid = shared_df["paid_amount"].sum()
        s_due = s_work - s_paid
        
        col_s1, col_s2, col_s3 = st.columns(3)
        col_s1.metric(L["stat_total"], f"₹{s_work:,}")
        col_s2.metric(L["stat_paid"], f"₹{s_paid:,}")
        col_s3.metric(L["stat_due"], f"₹{s_due:,}")
        
        st.markdown("---")
        for index, row in shared_df.sort_values(by="date", ascending=False).iterrows():
            with st.expander(f"📥 Entry by User ({row['created_by_mobile']}) | Date: {row['date']} | Amount: ₹{row['total_amount']:,} | Status: [{row['status']}]"):
                st.markdown(f"**🌾 {L['details_lbl']}** {row['notes']}")
                st.markdown(f"**📊 {L['param_lbl']}** {row['area_bigha']} Bigha @ ₹{row['rate_per_bigha']}/Unit")
                st.markdown("<span style='color: #4A90E2; font-size: 0.85em;'>🔒 Secure Live Sync (Read-Only)</span>", unsafe_allow_html=True)

st.markdown("---")
if st.button(L["signout_btn"], type="primary", use_container_width=True):
    st.session_state["farm_logged_in"] = False
    st.rerun()
