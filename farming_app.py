import streamlit as st
import pandas as pd
import sqlite3
import hashlib
import os
from datetime import datetime

# --- PRODUCTION STORAGE CORE ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FARM_DB = os.path.join(BASE_DIR, "krishi_matrix_ultimate_v4.db")

def init_farm_db():
    conn = sqlite3.connect(FARM_DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (mobile TEXT PRIMARY KEY, name TEXT, password TEXT, role TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS virtual_accounts 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  creator_mobile TEXT,
                  target_mobile TEXT,
                  target_name TEXT,
                  target_type TEXT,
                  UNIQUE(creator_mobile, target_mobile))''')
    c.execute('''CREATE TABLE IF NOT EXISTS work_records 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  created_by_mobile TEXT,
                  farmer_mobile TEXT, 
                  owner_mobile TEXT, 
                  date TEXT, 
                  entry_mode TEXT,
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
    try:
        c.execute('INSERT INTO virtual_accounts (creator_mobile, target_mobile, target_name, target_type) VALUES (?,?,?,?)',
                  (creator, target_mob, target_name, target_type))
        conn.commit()
        return True
    except sqlite3.IntegrityError: return False
    finally: conn.close()

def update_virtual_account(v_id, new_name, new_mob):
    conn = sqlite3.connect(FARM_DB)
    c = conn.cursor()
    try:
        c.execute('UPDATE virtual_accounts SET target_name=?, target_mobile=? WHERE id=?', (new_name, new_mob, v_id))
        conn.commit()
        return True
    except sqlite3.IntegrityError: return False
    finally: conn.close()

def delete_virtual_account(v_id, creator_mob, target_mob):
    conn = sqlite3.connect(FARM_DB)
    c = conn.cursor()
    c.execute('DELETE FROM virtual_accounts WHERE id = ?', (v_id,))
    c.execute('DELETE FROM work_records WHERE created_by_mobile=? AND (farmer_mobile=? OR owner_mobile=?)', (creator_mob, target_mob, target_mob))
    conn.commit()
    conn.close()

def update_farm_transaction(t_id, bigha, rate, paid, status, notes, entry_mode):
    conn = sqlite3.connect(FARM_DB)
    c = conn.cursor()
    total = bigha * rate
    c.execute('''UPDATE work_records 
                 SET area_bigha=?, rate_per_bigha=?, total_amount=?, paid_amount=?, status=?, notes=?, entry_mode=? 
                 WHERE id=?''', (bigha, rate, total, paid, status, notes, entry_mode, t_id))
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

LANG_DICT = {
    "English": {
        "title": "🚜 Krishi & Tractor Network Ledger",
        "login_tab": "Login Account", "register_tab": "Create New Account",
        "signin_header": "🔑 Sign In", "reg_header": "📝 Registration",
        "mobile_label": "Mobile Number (10 Digit):", "password_label": "Password:", "name_label": "Full Name / Naam:",
        "login_btn": "LOGIN", "register_btn": "REGISTER NOW",
        "profile_title": "🌱 Profile Setup", "profile_sub": "Namaskar {}, select your profile setup:",
        "role_label": "Choose Profile Role:",
        "role_f": "Farmer (Manage Sowing/Farming Cost)", "role_t": "Tractor Owner (Manage Tractor Commercial Work)", "role_b": "Farmer + Tractor Owner",
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
        "error_mob": "Please enter a valid 10-digit mobile number.", "error_fields": "All fields are required!",
        "error_self": "You cannot register your own mobile number here.", "toast_success": "Record logged successfully!",
        "details_lbl": "Details:", "param_lbl": "Parameters:"
    },
    "Hindi": {
        "title": "🚜 कृषि और ट्रैक्टर लेजर सिस्टम",
        "login_tab": "लॉगिन अकाउंट", "register_tab": "नया अकाउंट बनाएं",
        "signin_header": "🔑 साइन इन करें", "reg_header": "📝 नया रजिस्ट्रेशन",
        "mobile_label": "मोबाइल नंबर (10 अंक):", "password_label": "पासवर्ड:", "name_label": "आपका पूरा नाम:",
        "login_btn": "लॉगिन करें", "register_btn": "अकाउंट रजिस्टर करें",
        "profile_title": "🌱 प्रोफाइल सेटअप", "profile_sub": "नमस्कार {}, अपना प्रोफाइल सेटअप चुनें:",
        "role_label": "अपना काम/प्रोफाइल चुनें:",
        "role_f": "किसान (Farmer)", "role_t": "ट्रैक्टर मालिक (Tractor Owner)", "role_b": "किसान + ट्रैक्टर मालिक",
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
        "error_mob": "कृपया सही 10 अंकों का mobile number डालें।", "error_fields": "सभी जानकारी भरना अनिवार्य है!",
        "error_self": "आप अपना खुद का नंबर यहाँ रजिस्टर नहीं कर सकते।", "toast_success": "रिकॉर्ड सफलतापूर्वक सेव हो गया!",
        "details_lbl": "विवरण / नोट:", "param_lbl": "पैरामीटर:"
    }
}

if "app_lang" not in st.session_state: st.session_state["app_lang"] = "English"
if "selected_entry_id" not in st.session_state: st.session_state["selected_entry_id"] = None

col_lang, _ = st.columns([1, 4])
with col_lang:
    st.session_state["app_lang"] = st.selectbox("🌐 Language / भाषा:", ["English", "Hindi"], index=0 if st.session_state["app_lang"] == "English" else 1)

L = LANG_DICT[st.session_state["app_lang"]]

if "farm_logged_in" not in st.session_state: st.session_state["farm_logged_in"] = False
if "user_mobile" not in st.session_state: st.session_state["user_mobile"] = ""
if "user_name" not in st.session_state: st.session_state["user_name"] = ""
if "user_role" not in st.session_state: st.session_state["user_role"] = "None"

# --- PHASE 1: AUTH SYSTEM ---
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
                    else: st.error("Account with this mobile number already exists!")
    st.stop()

current_mobile = st.session_state["user_mobile"]
current_role = st.session_state["user_role"]

if current_role == "None":
    st.title(L["profile_title"])
    st.subheader(L["profile_sub"].format(st.session_state['user_name']))
    role_choice = st.selectbox(L["role_label"], [L["role_f"], L["role_t"], L["role_b"]])
    if st.button(L["save_enter_btn"], use_container_width=True, type="primary"):
        final_role = "Farmer" if role_choice == L["role_f"] else "Tractor Owner" if role_choice == L["role_t"] else "Both"
        update_user_role(current_mobile, final_role)
        st.session_state["user_role"] = final_role
        st.rerun()
    st.stop()

# ----------------------------------------------------
#            DYNAMIC DUAL PAGE VIEW MANAGER
# ----------------------------------------------------
if st.session_state["selected_entry_id"] is not None:
    # Dedicated Sub-Page Mode for Entry Inspection Node
    t_id = st.session_state["selected_entry_id"]
    conn = sqlite3.connect(FARM_DB)
    c = conn.cursor()
    c.execute("SELECT * FROM work_records WHERE id=?", (t_id,))
    row = c.fetchone()
    conn.close()

    if not row:
        st.error("Entry record parameters missing.")
        if st.button("⬅️ Back to Main Screen", type="secondary"):
            st.session_state["selected_entry_id"] = None
            st.rerun()
    else:
        st.title("📄 Detailed Transaction Node System")
        st.markdown(f"**Record Core Identity Token:** `NODE-RE-00{row[0]}`")
        st.markdown("---")

        # Visual Grid representation separating receipt architecture
        box1, box2 = st.columns(2)
        with box1:
            st.info(f"📅 **Date:** {row[4]}\n\n📋 **Category Type:** {row[5]}")
            if row[5] == "Work Entry":
                st.success(f"📐 **Area Covered:** {row[6]} Bigha\n\n💰 **Rate Standard:** ₹{row[7]}/Unit")
        with box2:
            st.warning(f"💵 **Calculated Total Cost:** ₹{row[8]:,}\n\n🟩 **Amount Logged Settled:** ₹{row[9]:,}\n\n📝 **Notes Description:** {row[11]}")

        st.markdown("---")
        
        # Check permissions to show edit panels exclusively to creator nodes
        if row[1] == current_mobile:
            st.subheader("🛠️ Operations Update Control Matrix")
            ch_bigha = st.number_input("Change Bigha Configuration Parameters:", value=float(row[6]), key=f"chb_{row[0]}")
            ch_rate = st.number_input("Change Rate Configuration Parameters:", value=float(row[7]), key=f"chr_{row[0]}")
            ch_paid = st.number_input("Change Settled Ledger Balance Parameters:", value=float(row[9]), key=f"chp_{row[0]}")
            ch_notes = st.text_area("Change Entry Specific Descriptions:", value=row[11], key=f"chn_{row[0]}")

            col_sub1, col_sub2 = st.columns(2)
            with col_sub1:
                if st.button("💾 Commit Permanent Save Node Updates", use_container_width=True, type="primary"):
                    ch_tot = ch_bigha * ch_rate
                    ch_status = "Paid" if row[5] == "Payment Entry" or ch_paid >= ch_tot else "Pending"
                    update_farm_transaction(row[0], ch_bigha, ch_rate, ch_paid, ch_status, ch_notes, row[5])
                    st.session_state["selected_entry_id"] = None
                    st.toast("Changes Saved Successfully!")
                    st.rerun()
            with col_sub2:
                if st.button("🗑️ Wipe Record From Network Grid Permanently", type="primary", use_container_width=True):
                    delete_farm_transaction(row[0])
                    st.session_state["selected_entry_id"] = None
                    st.toast("Record Wiped!")
                    st.rerun()
        else:
            st.info("🔒 Secure Node Protection: This record belongs to another active user. Shared views are read-only framework meshes.")

        st.markdown("---")
        if st.button("⬅️ Drop Context and Return Home", use_container_width=True):
            st.session_state["selected_entry_id"] = None
            st.rerun()
    st.stop()

# --- PHASE 3: CORE APPLICATION INTERFACE ---
# Global DB Directory Fetch for Dynamic UI Verification
conn = sqlite3.connect(FARM_DB)
v_df = pd.read_sql_query("SELECT id, target_mobile, target_name, target_type FROM virtual_accounts WHERE creator_mobile=?", conn, params=(current_mobile,))
conn.close()

if st.session_state["user_role"] == "Farmer":
    # ----------------------------------------------------
    #                  FARMER INTERFACE DESIGN
    # ----------------------------------------------------
    f_menu = st.radio(
        "Select Operation Option / विकल्प चुनें:",
        [
            "📊 Option 1: Apne Khet Ka Hisab Kitab (Personal Records View)",
            "👁️ Option 2: Tractor Owners Matrix (Saamne wale ka input data)",
            "📝 Option 3: Manage Directory & Log New Entries"
        ],
        horizontal=True
    )

    if f_menu.startswith("📊 Option 1"):
        st.subheader("📊 खेती बाड़ी रिकॉर्ड विवरण (Read-Only Matrix)")
        conn = sqlite3.connect(FARM_DB)
        df_self = pd.read_sql_query("SELECT * FROM work_records WHERE created_by_mobile=?", conn, params=(current_mobile,))
        conn.close()

        if df_self.empty:
            st.info("Aapne abhi tak koi entry data feed nahi kiya hai.")
        else:
            distinct_owners = df_self["owner_mobile"].unique()
            filter_owner = st.selectbox("Filter by Tractor Owner Ledger (Alag se hisab dekhein):", ["All Owners / Sabhi Ka Combo"] + list(distinct_owners))
            
            if filter_owner != "All Owners / Sabhi Ka Combo":
                df_filtered = df_self[df_self["owner_mobile"] == filter_owner]
            else: df_filtered = df_self

            t_cost = df_filtered["total_amount"].sum()
            t_paid = df_filtered["paid_amount"].sum()
            
            col_m1, col_m2, col_m3 = st.columns(3)
            col_m1.metric("💰 Total cost Logged (कुल खर्चा)", f"₹{t_cost:,}")
            col_m2.metric("🟩 Total Paid Outflow (भुगतान)", f"₹{t_paid:,}")
            col_m3.metric("🟥 Remaining Due Balance (शेष बकाया)", f"₹{(t_cost - t_paid):,}")

            st.markdown("---")
            st.subheader("🗂️ Available Records Node List (Click to open full page)")
            for i, r in df_filtered.sort_values(by="date", ascending=False).iterrows():
                if st.button(f"📄 Date: {r['date']} | Mode: {r['entry_mode']} | Net Cost: ₹{r['total_amount']:,} | Owner: {r['owner_mobile']} ➡️", key=f"rec_self_{r['id']}", use_container_width=True):
                    st.session_state["selected_entry_id"] = r['id']
                    st.rerun()

    elif f_menu.startswith("👁️ Option 2"):
        st.subheader("👁️ Tractor Owners Shared Grid Logs")
        st.info("🔒 Security Layer: Saamne wale tractor maalik ne aapka number daal kar jo entries ki hain, wo yahan bina badlaav ke dikhengi.")

        conn = sqlite3.connect(FARM_DB)
        df_shared = pd.read_sql_query("SELECT * FROM work_records WHERE created_by_mobile != ? AND farmer_mobile = ?", conn, params=(current_mobile, current_mobile))
        conn.close()

        if df_shared.empty:
            st.info("Kisi bhi external tractor maalik ne aapke mobile number par koi data publish nahi kiya hai.")
        else:
            active_publishers = df_shared["created_by_mobile"].unique()
            selected_pub = st.selectbox("Chunein kis Tractor Owner ka live data track karna hai:", active_publishers)
            
            df_pub_filtered = df_shared[df_shared["created_by_mobile"] == selected_pub]
            
            s_cost = df_pub_filtered["total_amount"].sum()
            s_paid = df_pub_filtered["paid_amount"].sum()
            
            col_st1, col_st2 = st.columns(2)
            col_st1.metric("🌍 Tractor Logged Cost (सामने वाले का काम)", f"₹{s_cost:,}")
            col_st2.metric("🟩 Tractor Claimed Received (सामने वाले के अनुसार मिला पैसा)", f"₹{s_paid:,}")
            
            st.markdown("---")
            st.subheader("🗂️ Network Records Node List (Click to view full page)")
            for i, r in df_pub_filtered.sort_values(by="date", ascending=False).iterrows():
                if st.button(f"📥 Shared Entry: {r['date']} | Mode: {r['entry_mode']} | Total Value: ₹{r['total_amount']:,} ➡️", key=f"rec_sh_{r['id']}", use_container_width=True):
                    st.session_state["selected_entry_id"] = r['id']
                    st.rerun()

    elif f_menu.startswith("📝 Option 3"):
        st.subheader("📝 Accounts Directory Setup & Log Factory")
        
        with st.expander("➕ Add New Tractor Owner to Directory (Naya Khata kholin)"):
            v_name = st.text_input("Tractor Owner Name:").strip().title()
            v_mob = st.text_input("Tractor Owner Mobile Number:", max_chars=10).strip()
            if st.button("Link New Tractor Owner Node", use_container_width=True):
                if not v_name or len(v_mob) != 10 or not v_mob.isdigit(): st.error(L["error_fields"])
                elif v_mob == current_mobile: st.error(L["error_self"])
                else:
                    if create_virtual_account(current_mobile, v_mob, v_name, "Tractor"):
                        st.success("Tractor Owner Added to Directory node!")
                        st.rerun()
                    else: st.error("Account already exists in directory node! Clear or delete old one first.")

        if v_df.empty:
            st.info("Aapki directory khaali hai. Kripya upar jaakar naya account node add karein.")
        else:
            st.markdown("---")
            st.markdown("### ⚙️ Directory Node Management")
            acc_options = [f"{r['target_name']} ({r['target_mobile']})" for i, r in v_df.iterrows()]
            selected_node = st.selectbox("Select Tractor Account Node:", acc_options, key="farm_node_sel")
            
            t_v_mob = selected_node.split("(")[1].split(")")[0]
            matched_row = v_df[v_df["target_mobile"] == t_v_mob].iloc[0]
            
            e_name = st.text_input("Modify Selected Name:", value=matched_row["target_name"], key=f"ed_n_{matched_row['id']}")
            e_mob = st.text_input("Modify Selected Mobile:", value=matched_row["target_mobile"], max_chars=10, key=f"ed_m_{matched_row['id']}")
            
            col_db1, col_db2 = st.columns(2)
            with col_db1:
                if st.button("🔄 Update Directory Profile Data", use_container_width=True):
                    if not e_name or len(e_mob) != 10: st.error("Valid fields required.")
                    else:
                        if update_virtual_account(matched_row["id"], e_name.title(), e_mob):
                            st.toast("Directory Updated Successfully!")
                            st.rerun()
                        else: st.error("Mobile number collision configuration error.")
            with col_db2:
                if st.button("🗑️ Wipe Out This Entire Directory Account", type="primary", use_container_width=True):
                    delete_virtual_account(matched_row["id"], current_mobile, t_v_mob)
                    st.toast("Account and entries deleted permanently!")
                    st.rerun()

            st.markdown("---")
            st.markdown(f"### 📝 Post Transaction Log Node for: **{matched_row['target_name']}**")
            entry_type = st.radio("Choose Entry Mode Variant:", ["Tractor Work Entry (काम का हिसाब)", "Payment Ledger Entry (लेन-देन का हिसाब)"], horizontal=True)

            with st.form("farmer_post_form", clear_on_submit=True):
                d_input = st.date_input("Date", datetime.now())
                if entry_type.startswith("Tractor Work"):
                    b_input = st.number_input("Total Bigha Area:", min_value=0.1, step=0.5)
                    r_input = st.number_input("Rate Per Bigha (₹):", min_value=1.0, step=50.0)
                    p_input = 0.0
                else:
                    b_input, r_input = 0.0, 0.0
                    p_input = st.number_input("Paid Amount (INR ₹):", min_value=1.0, step=100.0)
                
                n_input = st.text_area("Entry Description Notes (नरमा बुवाई, रोटावेटर, एडवांस भुगतान)")
                submit_f = st.form_submit_button("SAVE RECORD PERMANENTLY")

            if submit_f:
                tot_amt = b_input * r_input
                mode_tag = "Work Entry" if entry_type.startswith("Tractor Work") else "Payment Entry"
                stat_tag = "Paid" if mode_tag == "Payment Entry" or p_input >= tot_amt else "Pending"
                
                conn = sqlite3.connect(FARM_DB)
                c = conn.cursor()
                c.execute('''INSERT INTO work_records (created_by_mobile, farmer_mobile, owner_mobile, date, entry_mode, area_bigha, rate_per_bigha, total_amount, paid_amount, status, notes)
                             VALUES (?,?,?,?,?,?,?,?,?,?,?)''', (current_mobile, current_mobile, t_v_mob, str(d_input), mode_tag, b_input, r_input, tot_amt, p_input, stat_tag, n_input))
                conn.commit()
                conn.close()
                st.toast(L["toast_success"], icon="✅")
                st.rerun()

            st.markdown(f"#### Your Created Logs in {matched_row['target_name']}'s Khata (Click to open full sub-page)")
            conn = sqlite3.connect(FARM_DB)
            df_entries = pd.read_sql_query("SELECT * FROM work_records WHERE created_by_mobile=? AND owner_mobile=?", conn, params=(current_mobile, t_v_mob))
            conn.close()

            if df_entries.empty: st.info("No logs generated under this registry node context yet.")
            else:
                for idx, row in df_entries.sort_values(by="date", ascending=False).iterrows():
                    if st.button(f"⚙️ Log Variant: {row['date']} | Type: {row['entry_mode']} | Net Value: ₹{row['total_amount'] if row['total_amount'] > 0 else row['paid_amount']:,} ➡️", key=f"f_sub_page_click_{row['id']}", use_container_width=True):
                        st.session_state["selected_entry_id"] = row['id']
                        st.rerun()

else:
    # ----------------------------------------------------
    #            TRACTOR OWNER / BOTH INTERFACE DESIGN
    # ----------------------------------------------------
    st.subheader(L["menu_opt1"])
    with st.expander(L["add_khata_exp"]):
        v_name = st.text_input(L["acc_name"]).strip().title()
        v_mob = st.text_input(L["acc_mob"], max_chars=10).strip()
        if st.button(L["create_node_btn"], use_container_width=True):
            if not v_name or len(v_mob) != 10 or not v_mob.isdigit(): st.error(L["error_fields"])
            elif v_mob == current_mobile: st.error(L["error_self"])
            else:
                if create_virtual_account(current_mobile, v_mob, v_name, "Farmer"):
                    st.success("Success!")
                    st.rerun()
                else: st.error("Account identity replication blocked.")

    if v_df.empty:
        st.info("No accounts inside directory database mesh matrix setup frame yet.")
    else:
        with st.expander("🛠️ Edit / Delete Account Khata Directory"):
            acc_select_modify = st.selectbox("Select Account Node To Alter:", [f"{r['target_name']} ({r['target_mobile']})" for i, r in v_df.iterrows()], key="mod_acc_sel_trac")
            target_v_mob = acc_select_modify.split("(")[1].split(")")[0]
            matched_row = v_df[v_df["target_mobile"] == target_v_mob].iloc[0]
            
            edit_acc_name = st.text_input("Modify Account Name:", value=matched_row["target_name"], key=f"en_a_t_{matched_row['id']}")
            edit_acc_mob = st.text_input("Modify Mobile Number:", value=matched_row["target_mobile"], max_chars=10, key=f"em_a_t_{matched_row['id']}")
            
            col_ac1, col_ac2 = st.columns(2)
            with col_ac1:
                if st.button("Update Account Data", use_container_width=True, key=f"up_ac_btn_t_{matched_row['id']}"):
                    if not edit_acc_name or len(edit_acc_mob) != 10: st.error(L["error_fields"])
                    else:
                        update_virtual_account(matched_row["id"], edit_acc_name.title(), edit_acc_mob)
                        st.toast("Account Directory Updated!")
                        st.rerun()
            with col_ac2:
                if st.button("🗑️ Delete Account Completely", type="primary", use_container_width=True, key=f"del_ac_btn_t_{matched_row['id']}"):
                    delete_virtual_account(matched_row["id"], current_mobile, target_v_mob)
                    st.toast("Account and its records wiped permanently!")
                    st.rerun()

        st.markdown("---")
        directory_options = [f"{row['target_name']} ({row['target_mobile']}) - [{row['target_type']}]" for index, row in v_df.iterrows()]
        selected_account = st.selectbox(L["select_khata_label"], directory_options)
        
        target_active_mobile = selected_account.split("(")[1].split(")")[0]
        target_active_name = selected_account.split(" - ")[0]

        st.markdown(f"#### {L['entry_form_title']} **{target_active_name}**")
        with st.form("entry_form_krishi_trac", clear_on_submit=True):
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
            total_cost = bigha * rate
            status = "Paid" if paid >= total_cost else "Pending"
            
            conn = sqlite3.connect(FARM_DB)
            c = conn.cursor()
            c.execute('''INSERT INTO work_records (created_by_mobile, farmer_mobile, owner_mobile, date, entry_mode, area_bigha, rate_per_bigha, total_amount, paid_amount, status, notes)
                         VALUES (?,?,?,?,?,?,?,?,?,?,?)''', (current_mobile, target_active_mobile, current_mobile, str(date_w), "Work Entry", bigha, rate, total_cost, paid, status, notes))
            conn.commit()
            conn.close()
            st.toast(L["toast_success"], icon="✅")
            st.rerun()

        st.markdown(f"#### {L['personal_entries_title'].format(target_active_name)} (Click to view full page)")
        conn = sqlite3.connect(FARM_DB)
        entries_df = pd.read_sql_query("SELECT * FROM work_records WHERE created_by_mobile=? AND farmer_mobile=?", 
                                        conn, params=(current_mobile, target_active_mobile))
        conn.close()

        if entries_df.empty:
            st.info("No records inside this account.")
        else:
            for index, r in entries_df.sort_values(by="date", ascending=False).iterrows():
                if st.button(f"🚜 Log Statement: {r['date']} | Total: ₹{r['total_amount']:,} | Received: ₹{r['paid_amount']:,} ➡️", key=f"t_sub_page_click_{r['id']}", use_container_width=True):
                    st.session_state["selected_entry_id"] = r['id']
                    st.rerun()

    # Shared Network Matrix rendering logic block for Tractor Profiles
    st.markdown("---")
    st.subheader(L["shared_title"])
    conn = sqlite3.connect(FARM_DB)
    shared_df = pd.read_sql_query("SELECT * FROM work_records WHERE created_by_mobile != ? AND owner_mobile = ?", conn, params=(current_mobile, current_mobile))
    conn.close()

    if shared_df.empty: st.info(L["shared_empty"])
    else:
        for idx, row in shared_df.sort_values(by="date", ascending=False).iterrows():
            if st.button(f"📥 Synced Kisan Node Entry ({row['created_by_mobile']}) | Date: {row['date']} | Net Total: ₹{row['total_amount'] if row['total_amount'] > 0 else row['paid_amount']:,} ➡️", key=f"sh_trac_click_{row['id']}", use_container_width=True):
                st.session_state["selected_entry_id"] = row['id']
                st.rerun()

st.markdown("---")
if st.button(L["signout_btn"], type="primary", use_container_width=True):
    st.session_state["farm_logged_in"] = False
    st.rerun()
