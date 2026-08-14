import os
import time
from datetime import date, datetime, timezone
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pytz
import streamlit as st
import streamlit.components.v1 as components
from streamlit_geolocation import streamlit_geolocation

import base64
import streamlit as st

# ============================================================
# ✅ PAGE CONFIG (MUST BE CALLED ONLY ONCE AT THE VERY TOP)
# ============================================================

st.set_page_config(
    page_title="Attendance Management System",
    layout="wide"
)

# ============================================================
# ✅ UNIFIED CORPORATE DASHBOARD STYLING (CSS)
# ============================================================

st.markdown("""
<style>
    /* 1. Global Font & Main Container */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    
    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2.5rem;
        max-width: 1350px;
    }

    /* 2. Elevated Header Banner */
    .brand-banner {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
    }

    /* 3. Dashboard & KPI Metric Cards */
    .dashboard-card {
        background-color: #ffffff;
        border-radius: 18px;
        padding: 20px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.03);
        border: 1px solid #e5e7eb;
        margin-bottom: 20px;
    }

    .kpi-card {
        background-color: #ffffff;
        border-radius: 16px;
        padding: 16px 20px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02);
    }
    .kpi-title { font-size: 0.85rem; color: #6b7280; font-weight: 600; }
    .kpi-val { font-size: 1.6rem; font-weight: 700; color: #111827; margin: 4px 0; }
    .kpi-sub-green { font-size: 0.78rem; color: #10b981; font-weight: 600; }
    .kpi-sub-pink { font-size: 0.78rem; color: #ec4899; font-weight: 600; }

    /* 4. Streamlit Metric Component Overrides */
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 16px 20px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
        transition: all 0.3s ease;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-3px);
        border-color: rgba(99, 102, 241, 0.4);
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
    }
    div[data-testid="stMetricValue"] {
        font-weight: 700;
        font-size: 1.9rem;
    }

    /* 5. Employee List Status Indicators */
    .emp-item {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 6px 0;
        font-size: 0.88rem;
        font-weight: 500;
        color: #374151;
    }
    .dot-green { height: 10px; width: 10px; background-color: #10b981; border-radius: 50%; display: inline-block; }
    .dot-pink { height: 10px; width: 10px; background-color: #ec4899; border-radius: 50%; display: inline-block; }

    /* 6. Button Animations & Form Elements */
    .stButton > button {
        border-radius: 10px;
        font-weight: 600;
        letter-spacing: 0.3px;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 0.5rem 1.25rem;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.2);
    }
    .stTextInput > div > div > input, .stSelectbox > div > div {
        border-radius: 10px;
    }
    [data-testid="stDataFrame"] {
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        overflow: hidden;
    }
    hr {
        margin: 2rem 0;
        border-color: rgba(255, 255, 255, 0.08);
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# ✅ APP HEADER (THEME-SAFE CENTERED LOGO & BRAND)
# ============================================================

def get_image_base64(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode("utf-8")
    except Exception:
        return None

logo_b64 = get_image_base64("Logo white.png")

if logo_b64:
    st.markdown(
        f"""
        <div class="brand-banner">
            <img src="data:image/png;base64,{logo_b64}" style="max-width: 320px; height: auto; margin-bottom: 8px;">
            <h2 style="margin: 0; font-size: 1.6rem; color: #ffffff; font-weight: 700;">Lancers Risk Consulting</h2>
            <p style="margin: 4px 0 0 0; color: #94a3b8; font-size: 0.95rem;">Attendance Management System</p>
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    st.markdown("<h2 style='text-align: center;'>🛡️ Lancers Risk Consulting</h2>", unsafe_allow_html=True)
    st.markdown("<h5 style='text-align: center; color: #888;'>Attendance Management System</h5>", unsafe_allow_html=True)

st.divider()
# ============================================================
# ✅ APP STYLING (BACKGROUND + UI)
# ============================================================

from datetime import datetime, date, timezone
import pytz
import os
import time

# ✅ Auto refresh every 5 seconds
# if "last_refresh" not in st.session_state:
#     st.session_state["last_refresh"] = time.time()

# current_time = time.time()

# if current_time - st.session_state["last_refresh"] > 5:
#     st.session_state["last_refresh"] = current_time
#     st.rerun()

# ============================================================
# ✅ GOOGLE SHEET CONNECTION (FINAL STABLE VERSION)
# ============================================================

from oauth2client.service_account import ServiceAccountCredentials
import gspread


@st.cache_resource  # ✅ CRITICAL FIX (prevents API errors)
def connect_sheet():

    try:
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]

        # ✅ Load credentials
        creds_dict = st.secrets["gcp_service_account"]

        creds = ServiceAccountCredentials.from_json_keyfile_dict(
            creds_dict, scope
        )

        client = gspread.authorize(creds)

        # ✅ Open sheets (ONLY ONCE due to caching)
        sheet = client.open("AttendanceData").sheet1
        leave_sheet = client.open("AttendanceData").worksheet("Leave")

        return sheet, leave_sheet

    except Exception as e:
        st.error("❌ Google Sheet connection failed")
        st.error(str(e))  # optional debug
        st.stop()
# ============================================================
# ✅ IST TIME
# ============================================================

def get_ist():
    return pd.Timestamp.now(
        tz="Asia/Kolkata"
    ).tz_localize(None)

# ============================================================
# ✅ HOLIDAY LIST & WEEKEND HELPER (FIXED)
# ============================================================

HOLIDAY_LIST = {
    "01-01-2026": "New Year",
    "26-01-2026": "REPUBLIC DAY",
    "16-02-2026": "MAHA SHIVRATRI",
    "04-03-2026": "HOLI",
    "26-03-2026": "RAM NAVMI",
    "03-04-2026": "Good Friday",
    "28-08-2026": "RAKSHA BANDHAN",
    "04-09-2026": "JANMASHTAMI",
    "02-10-2026": "GANDHI JAYANTI",
    "20-10-2026": "DUSSEHRA",
    "24-11-2026": "GURU NANAK'S BIRTHDAY",
    "25-12-2026": "CHRISTMAS DAY",
}

def check_date_type(target_date):
    """Checks if a given date is a weekend (Saturday/Sunday) or a listed holiday."""
    # Saturday = 5, Sunday = 6
    is_weekend = target_date.weekday() in [5, 6]
    
    # ✅ Fixed to %d-%m-%Y (4-digit year) to match dictionary keys
    formatted_date = target_date.strftime("%d-%m-%Y")
    holiday_name = HOLIDAY_LIST.get(formatted_date)
    
    return is_weekend, holiday_name
# ============================================================
# ✅ LOAD ATTENDANCE (FINAL FIXED VERSION)
# ============================================================
@st.cache_data(ttl=2)
def load_attendance():
    df = pd.DataFrame()

    try:
        sheet, _ = connect_sheet()
        data = sheet.get_all_records()

        if not data:
            return pd.DataFrame(columns=[
                "Date", "Employee", "Login", "Logout", "Working Hours",
                "Status", "Type", "Login Latitude", "Login Longitude",
                "Logout Latitude", "Logout Longitude"
            ])

        df = pd.DataFrame(data)
        df.columns = df.columns.str.strip()

        if "Date" not in df.columns:
            st.error("❌ 'Date' column missing in sheet")
            return pd.DataFrame()

        # ✅ Formats date cleanly as DD-MM-YY (e.g., 13-08-26)
        df["Date"] = pd.to_datetime(
            df["Date"], dayfirst=True, format="mixed", errors="coerce"
        )
        df = df.dropna(subset=["Date"])
        df["Date"] = df["Date"].dt.strftime("%d-%m-%y")

        if "Employee" in df.columns:
            df["Employee"] = (
                df["Employee"]
                .astype(str)
                .str.strip()
                .str.upper()
            )

        return df

    except Exception as e:
        st.error(f"❌ Error loading attendance: {e}")
        return df
# ============================================================
# ✅ LOAD LEAVE (SAFE VERSION ✅ PLACE HERE)
# ============================================================
def load_leave():

    try:
        _, leave_sheet = connect_sheet()

        data = leave_sheet.get_all_records()

        if not data:
            return pd.DataFrame(columns=[
                "Employee",
                "Date",
                "Reason",
                "Status"
            ])

        df = pd.DataFrame(data)
        df.columns = df.columns.str.strip()

        if "Date" in df.columns:
            df["Date"] = pd.to_datetime(
                df["Date"], dayfirst=True, format="mixed", errors="coerce"
            ).dt.strftime("%d-%m-%y")

        # ✅ Normalize employee name
        if "Employee" in df.columns:
            df["Employee"] = (
                df["Employee"]
                .astype(str)
                .str.strip()
                .str.upper()
            )

        return df

    except Exception as e:
        st.error(f"❌ Error loading leave: {e}")
        return pd.DataFrame()

# ✅ ALWAYS LOAD FRESH DATA AFTER CALL
df = load_attendance()

# ============================================================
# ✅ SESSION STATE
# ============================================================
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "role" not in st.session_state:
    st.session_state["role"] = ""

if "employee" not in st.session_state:
    st.session_state["employee"] = ""

# ============================================================
# ✅ LOAD EMPLOYEE FILE
# ============================================================
try:
    df_emp = pd.read_excel("employees.xlsx")

except Exception as e:
    st.error(f"❌ employees.xlsx not found\n\n{e}")
    st.stop()

df_emp.columns = df_emp.columns.str.strip()

required_columns = ["Employee Name", "Password"]

for col in required_columns:
    if col not in df_emp.columns:
        st.error(f"❌ Missing column in employees.xlsx: {col}")
        st.stop()

# ============================================================
# ✅ USERS
# ============================================================
users = {
    "admin": {
        "password": "admin123",
        "role": "admin",
        "employee": "ADMIN"
    }
}

for _, row in df_emp.iterrows():

    username = str(row["Employee Name"]).split()[0].lower()

    users[username] = {
        "password": str(row["Password"]),
        "role": "employee",
        "employee": row["Employee Name"]
    }

# ============================================================
# ✅ LOGIN PAGE
# ============================================================

if not st.session_state["logged_in"]:

    st.title("🔐 Login")

    username = st.text_input(
        "Username",
        key="auth_login_user"
    )

    password = st.text_input(
        "Password",
        type="password",
        key="auth_login_pass"
    )

    if st.button(
        "🔑 Login",
        key="login_btn"
    ):

        if (
            username in users
            and users[username]["password"] == password
        ):

            st.session_state["logged_in"] = True
            st.session_state["role"] = users[username]["role"]
            st.session_state["employee"] = users[username]["employee"]

            st.rerun()

        else:

            st.error("❌ Invalid Credentials")

    st.stop()

# ============================================================
# ✅ LOGOUT
# ============================================================
if st.button("Logout", key="main_app_logout_btn"):

    st.session_state.clear()

    st.rerun()

role = st.session_state.get("role", "")

employee = st.session_state.get(
    "employee",
    ""
)

# ✅ ADD THIS
ADMIN_USERS = ["ADMIN"]

st.markdown(f"<h4 style='text-align: center;'>Welcome, {employee}</h4>", unsafe_allow_html=True)

# ✅ Show logged in user
col1, col2 = st.columns([6, 1])

with col1:
    st.success(f"✅ Logged in as: {employee}")

# ============================================================
# ✅ LOCATION INITIALIZATION + FETCH
# ============================================================

if "location" not in st.session_state:
    st.session_state["location"] = {}

location = streamlit_geolocation()

if location and location.get("latitude") and location.get("longitude"):
    st.session_state["location"] = {
        "lat": location["latitude"],
        "lon": location["longitude"]
    }

# ============================================================
# ✅ SINGLE SOURCE OF TRUTH FOR LOCATION
# ============================================================

def get_location_values():

    loc = st.session_state.get("location", {})

    lat = loc.get("lat") or "NA"
    lon = loc.get("lon") or "NA"

    return lat, lon

# ============================================================
# ✅ STEP 3: DISPLAY LOCATION
# ============================================================

# ✅ Get latest values FIRST (IMPORTANT ✅)
lat, lon = get_location_values()

st.write("📍 Current Location:")

st.write(f"Latitude: {lat}")
st.write(f"Longitude: {lon}")

# ============================================================
# ✅ GOOGLE MAPS LINK
# ============================================================

if lat != "NA" and lon != "NA":

    st.markdown(
        f"[🌍 Open in Google Maps](https://www.google.com/maps?q={lat},{lon})"
    )

    st.success("📍 Location captured successfully ✅")

else:

    st.warning("⚠ Please allow location access in your browser")

# ============================================================
# ✅ DATE SELECTION
# ============================================================
today = date.today()

if role == "employee":

    selected_date = st.date_input(
        "Attendance Date",
        today,
        today,
        today,
        key="emp_date_selector"
    )

else:

    selected_date = st.date_input(
        "Attendance Date",
        today,
        key="admin_date_selector"
    )

date_str = selected_date.strftime("%d-%m-%y")

# ============================================================
# ✅ ADMIN EMPLOYEE SELECTION
# ============================================================
if role == "admin":

    employee = st.selectbox(
        "Select Employee",
        sorted(df_emp["Employee Name"].unique()),
        key="employee_filter_admin"
    )

# ============================================================
# ✅ ATTENDANCE TYPE & AUTO-DETECTION FOR WO / HO
# ============================================================

is_wknd, holiday_name = check_date_type(selected_date)

# Determine default option based on date
options = [
    "Present WFO",
    "Present WFH",
    "Half Day",
    "Leave",
    "Week Off (WO)",
    "Holiday (HO)"
]

default_idx = 0

if holiday_name:
    default_idx = 5  # "Holiday (HO)"
    st.info(f"🎉 Selected date is an official holiday: **{holiday_name}**")
elif is_wknd:
    default_idx = 4  # "Week Off (WO)"
    st.info(f"🏖 Selected date falls on a Weekend (**{selected_date.strftime('%A')}**)")

attendance_type = st.selectbox(
    "Attendance Type",
    options,
    index=default_idx,
    key="attendance_type_selector"
)

# ============================================================
# ✅ ACTION BUTTONS
# ============================================================

col1, col2, col3 = st.columns(3)

# ============================================================
# ✅ LOGIN ATTENDANCE (FINAL CLEAN VERSION ✅)
# ============================================================

with col1:

    if st.button(
        "🔑 Login",
        key="login_att_action_btn"
    ):

        # ✅ CURRENT TIME
        login_time_str = get_ist().strftime("%H:%M:%S")

        # ✅ DATE
        date_str = selected_date.strftime("%d-%m-%y")

        # ✅ NORMALIZE EMPLOYEE
        employee_clean = str(employee).strip().upper()

        # ====================================================
        # ✅ CHECK APPROVED LEAVE
        # ====================================================

        leave_df = load_leave()

        approved_leave = leave_df[
            (
                leave_df["Employee"]
                .astype(str)
                .str.strip()
                .str.upper()
                == employee_clean
            ) &
            (
                leave_df["Date"]
                .astype(str)
                .str[:10]
                == date_str
            ) &
            (
                leave_df["Status"]
                .astype(str)
                .str.strip()
                .str.upper()
                == "APPROVED"
            )
        ]

        if not approved_leave.empty:

            if role != "admin":

                st.error(
                    "❌ Approved leave exists for today.\n"
                    "Attendance cannot be marked.\n"
                    "Please contact Admin if attendance is required."
                )

                st.stop()

            else:

                st.warning(
                    f"⚠ {employee} has an approved leave for {date_str}.\n"
                    "Admin override allowed."
                )

        # ✅ LOCATION
        lat, lon = get_location_values()

        if lat is None:
            lat = "NA"

        if lon is None:
            lon = "NA"

        # ✅ CONNECT SHEET
        sheet, _ = connect_sheet()

        # ✅ LOAD LATEST DATA
        st.cache_data.clear()

        df = load_attendance()

        # ✅ CLEAN DATA (SAFE)
        if df.empty:

            df = pd.DataFrame(
                columns=["Date", "Employee", "Logout"]
            )

        df.columns = df.columns.str.strip()

        if "Employee" in df.columns:

            df["Employee"] = (
                df["Employee"]
                .astype(str)
                .str.strip()
                .str.upper()
            )

        # ====================================================
        # ✅ PREVENT DUPLICATE LOGIN
        # ====================================================

        existing_today = df[
            (df["Date"] == date_str) &
            (df["Employee"] == employee_clean)
        ]

        if not existing_today.empty:

            last_logout = str(
                existing_today.iloc[-1]["Logout"]
            ).strip()

            if last_logout in ["", "nan", "None"]:

                st.warning(
                    "⚠ Already logged in today"
                )

                st.stop()

        # ====================================================
        # ✅ SAVE LOGIN (STEP 3 INTEGRATED HERE)
        # ====================================================

        # Determine status automatically based on selected Attendance Type
        if attendance_type == "Week Off (WO)":
            row_status = "WO"
        elif attendance_type == "Holiday (HO)":
            row_status = "HO"
        else:
            row_status = "In Progress"

        is_auto_closed = row_status in ["WO", "HO"]

        try:

            sheet.append_row([
                date_str,
                employee,
                login_time_str,
                login_time_str if is_auto_closed else "",        # Logout Time
                "00:00:00" if is_auto_closed else "",            # Working Hours
                row_status,                                       # Status ("WO", "HO", or "In Progress")
                attendance_type,
                lat,
                lon,
                lat if is_auto_closed else "",                   # Logout Latitude
                lon if is_auto_closed else ""                    # Logout Longitude
            ])

            st.success(
                f"✅ Attendance Recorded: {attendance_type} ({row_status})"
            )

        except Exception as e:

            st.error(
                f"❌ Login failed: {e}"
            )

            st.stop()

        # ✅ CLEAR CACHE
        try:
            st.cache_data.clear()
        except Exception:
            pass

        # ✅ REFRESH UI
        st.rerun()

with col2:
    if st.button(
        "🔴 Logout Attendance",
        key="logout_attendance_btn"
    ):

        lat, lon = get_location_values()

        sheet, _ = connect_sheet()

        # ✅ Always load fresh data
        st.cache_data.clear()

        df = load_attendance()

        df.columns = df.columns.str.strip()

        df["Date"] = pd.to_datetime(
            df["Date"],
            dayfirst=True, format="mixed", errors="coerce"
        ).dt.strftime("%d-%m-%y")

        # ✅ Normalize employee names
        employee_clean = str(employee).strip().upper()

        df["Employee"] = (
            df["Employee"]
            .astype(str)
            .str.strip()
            .str.upper()
        )

        today_date = selected_date.strftime("%d-%m-%y")

        user_today = df[
            (df["Date"] == today_date) &
            (df["Employee"] == employee_clean)
        ]

        if user_today.empty:
            st.warning("⚠ No login record found")
            st.stop()

        # ✅ Login record found
        last_index = user_today.index[-1]

        login_str = str(
            user_today.iloc[-1]["Login"]
        ).strip()

        login_time = pd.to_datetime(
            f"{today_date} {login_str}",
            errors="coerce"
        )

        logout_time = pd.to_datetime(
            get_ist(),
            errors="coerce"
        )

        if pd.isna(login_time):
            st.error("❌ Invalid login time")
            st.stop()

        if pd.isna(logout_time):
            st.error("❌ Invalid logout time")
            st.stop()

        existing_logout = str(
            user_today.iloc[-1]["Logout"]
        ).strip()

        if existing_logout not in ["", "nan", "None"]:
            st.warning("⚠ Logout already completed")
            st.stop()

        try:
            login_time = login_time.tz_localize(None)
        except Exception:
            pass

        try:
            logout_time = logout_time.tz_localize(None)
        except Exception:
            pass

        # ✅ Handle overnight shift
        if logout_time < login_time:
            logout_time += pd.Timedelta(days=1)

        time_diff = logout_time - login_time

        total_hours = time_diff.total_seconds() / 3600

        working_hours = str(time_diff).split(".")[0]

        if total_hours >= 8:
            status = "Full Day"
        elif total_hours >= 4:
            status = "Half Day"
        else:
            status = "Short Day"

        row_number = last_index + 2

        try:

            sheet.update_cell(
                row_number,
                4,
                logout_time.strftime("%H:%M:%S")
            )

            sheet.update_cell(
                row_number,
                5,
                working_hours
            )

            sheet.update_cell(
                row_number,
                6,
                status
            )

            sheet.update_cell(
                row_number,
                10,
                lat
            )

            sheet.update_cell(
                row_number,
                11,
                lon
            )

            st.cache_data.clear()

            st.success(
                f"""✅ Logout Recorded Successfully

📍 Location: {lat}, {lon}
⏱ Hours: {working_hours}
📌 Status: {status}
"""
            )

            st.rerun()

        except Exception as e:

            st.error(
                f"❌ Sheet update failed: {e}"
            )

            st.stop()
# ============================================================
# ✅ TODAY'S ATTENDANCE (IMPROVED & PRODUCTION READY)
# ============================================================

st.subheader("📋 Today's Attendance")

# ✅ Load attendance using cached data (TTL handles background updates)
df_today = load_attendance()

if df_today.empty:
    st.info("No attendance recorded today.")
else:
    df_today = df_today.copy()
    df_today.columns = df_today.columns.str.strip()

    # ✅ 1. Robust Date Normalization (handles DD/MM/YYYY, YYYY/MM/DD, YYYY-MM-DD)
    df_today["Date"] = pd.to_datetime(
        df_today["Date"],
        dayfirst=True,
        format="mixed",
        errors="coerce"
    ).dt.strftime("%d-%m-%y")

    # ✅ 2. Clean & Normalize Employee Column
    if "Employee" in df_today.columns:
        df_today["Employee"] = (
            df_today["Employee"]
            .astype(str)
            .str.strip()
            .str.upper()
        )

    # ✅ 3. Selected Date Normalization
    target_date_str = pd.to_datetime(selected_date).strftime("%d-%m-%y")

    # ✅ 4. Determine Active Logged-in User
    logged_user = st.session_state.get("employee", employee if 'employee' in locals() else "")
    employee_clean = str(logged_user).strip().upper()

    # ✅ 5. Role-based Filtering
    if role == "admin":
        # Admin sees all employee attendance for the target date
        today_data = df_today[df_today["Date"] == target_date_str]
    else:
        # Non-admin sees only their own attendance for the target date
        today_data = df_today[
            (df_today["Date"] == target_date_str) &
            (df_today["Employee"] == employee_clean)
        ]

    # ✅ 6. Render Data Frame
    if not today_data.empty:
        display_df = today_data.copy()

        # Format Login Time cleanly
        display_df["Login"] = pd.to_datetime(
            display_df["Login"], errors="coerce"
        ).dt.strftime("%H:%M:%S").fillna(display_df["Login"].astype(str))

        # Format Logout Time cleanly & handle Pending states
        display_df["Logout"] = pd.to_datetime(
            display_df["Logout"], errors="coerce"
        ).dt.strftime("%H:%M:%S")
        
        display_df["Logout"] = (
            display_df["Logout"]
            .replace(["nan", "None", "", "NaN"], None)
            .fillna("Pending")
        )

        # Fill blank values in working hours / status
        if "Working Hours" in display_df.columns:
            display_df["Working Hours"] = display_df["Working Hours"].replace(["", "nan", "None"], "-")
        if "Status" in display_df.columns:
            display_df["Status"] = display_df["Status"].replace(["", "nan", "None"], "In Progress")

        # Re-index for serial numbering
        display_df = display_df.reset_index(drop=True)
        display_df.insert(0, "S.No", range(1, len(display_df) + 1))

        # Define display column order safely
        column_order = [
            "S.No", "Employee", "Login", "Logout", "Working Hours",
            "Status", "Type", "Login Latitude", "Login Longitude",
            "Logout Latitude", "Logout Longitude"
        ]
        
        show_cols = [col for col in column_order if col in display_df.columns]

        st.dataframe(
            display_df[show_cols],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No attendance recorded for selected date.")

# ============================================================
# ✅ ADMIN CONTROLS
# ============================================================

st.divider()

if role == "admin":

    st.markdown("### ⚠️ Admin Controls")

    # ========================================================
    # ✅ CLEAR ATTENDANCE
    # ========================================================

    confirm_clear = st.checkbox(
        "Confirm Clear Attendance",
        key="confirm_clear_attendance"
    )

    if confirm_clear:

        if st.button(
            "🧹 Clear Attendance",
            key="clear_attendance_btn"
        ):

            try:

                sheet, _ = connect_sheet()

                sheet.clear()

                sheet.append_row([
                    "Date",
                    "Employee",
                    "Login",
                    "Logout",
                    "Working Hours",
                    "Status",
                    "Type",
                    "Login Latitude",
                    "Login Longitude",
                    "Logout Latitude",
                    "Logout Longitude"
                ])

                try:
                    st.cache_data.clear()
                except Exception:
                    pass

                st.success(
                    "✅ Attendance Cleared Successfully"
                )

                st.rerun()

            except Exception as e:
                st.error(
                    f"❌ Error clearing attendance: {e}"
                )

    # ========================================================
    # ✅ REMOVE DUPLICATE ENTRIES
    # ========================================================

    st.divider()

    if st.button(
        "🧹 Remove Duplicate Entries",
        key="remove_duplicates_btn"
    ):

        try:

            sheet, _ = connect_sheet()

            df = load_attendance()

            df.columns = df.columns.str.strip()

            if df.empty:

                st.warning(
                    "⚠ No data found in attendance sheet"
                )
                st.stop()

            df["Date"] = pd.to_datetime(
                df["Date"],
                dayfirst=True, format="mixed", errors="coerce"
            ).dt.strftime("%d-%m-%y")

            # Remove only truly identical rows
            df_clean = df.drop_duplicates()

            removed_count = len(df) - len(df_clean)

            sheet.clear()

            data_to_write = [
                df_clean.columns.tolist()
            ] + df_clean.values.tolist()

            sheet.update(
                "A1",
                data_to_write
            )

            try:
                st.cache_data.clear()
            except Exception:
                pass

            st.success(
                f"✅ Removed {removed_count} duplicate entries"
            )

            st.rerun()

        except Exception as e:

            st.error(
                f"❌ Error removing duplicates: {e}"
            )
# ============================================================
# ✅ LEAVE MANAGEMENT
# ============================================================
st.subheader("📩 Leave Management")

leave_df = load_leave()

employee_clean = str(employee).strip().upper()

# ============================================================
# ✅ EMPLOYEE LEAVE
# ============================================================
if role == "employee":

    colA, colB = st.columns(2)

    with colA:

        start_date = st.date_input(
            "Leave From",
            today,
            min_value=today,
            key="emp_leave_start_date"
        )

    with colB:

        end_date = st.date_input(
            "Leave To",
            start_date,
            min_value=start_date,
            key="emp_leave_end_date"
        )

    reason = st.text_input("Leave Reason", key="emp_leave_reason_input")

    if st.button("Submit Leave", key="submit_leave_request_btn"):

        if end_date < start_date:

            st.error("❌ Invalid Date Range")

        else:

            _, leave_sheet = connect_sheet()

            dates = pd.date_range(
                start=start_date,
                end=end_date
            )

            added = False

            for d in dates:

                d_str = d.strftime("%d-%m-%y")

                duplicate = leave_df[
                    (leave_df["Employee"] == employee_clean) &
                    (leave_df["Date"] == d_str)
                ]

                if duplicate.empty:

                    leave_sheet.append_row([
                        employee,
                        d_str,
                        reason,
                        "Pending"
                    ])

                    added = True

            st.cache_data.clear()

            if added:
                st.success("✅ Leave Submitted")
                st.rerun()

            else:
                st.warning("⚠ Leave Already Applied")

    st.subheader("My Leave Requests")

    leave_df = load_leave()

    st.dataframe(
        leave_df[leave_df["Employee"] == employee_clean]
    )

# ============================================================
# ✅ ADMIN LEAVE APPROVAL
# ============================================================
if role == "admin":

    st.subheader("📋 Pending Leave Requests")

    pending = leave_df[
        leave_df["Status"] == "Pending"
    ]

    if pending.empty:

        st.info("No Pending Requests")

    else:

        for i, row in pending.iterrows():

            st.write(
                f"{row['Employee']} | "
                f"{row['Date']} | "
                f"{row['Reason']}"
            )

            c1, c2 = st.columns(2)

            with c1:

                if st.button(f"Approve {i}", key=f"approve_leave_btn_{i}"):

                    _, leave_sheet = connect_sheet()

                    row_num = i + 2

                    leave_sheet.update_cell(
                        row_num,
                        4,
                        "Approved"
                    )

                    sheet, _ = connect_sheet()

                    sheet.append_row([
                        row["Date"],
                        row["Employee"],
                        "",
                        "",
                        "",
                        "Leave",
                        "Leave",
                        "",
                        "",
                        "",
                        ""
                    ])

                    st.cache_data.clear()

                    st.success("✅ Leave Approved")

                    st.rerun()

            with c2:

                if st.button(f"Reject {i}", key=f"reject_leave_btn_{i}"):

                    _, leave_sheet = connect_sheet()

                    row_num = i + 2

                    leave_sheet.update_cell(
                        row_num,
                        4,
                        "Rejected"
                    )

                    st.cache_data.clear()

                    st.warning("❌ Leave Rejected")

                    st.rerun()

# ============================================================
# ✅ ATTENDANCE RECORDS & DASHBOARD
# ============================================================
st.subheader("📋 Attendance Records")

df = load_attendance()

df.columns = df.columns.str.strip()

# ✅ ADD THIS
df["Month"] = pd.to_datetime(
    df["Date"],
    errors="coerce"
).dt.strftime("%Y-%m")

if not df.empty:

    # ========================================================
    # ADMIN FILTERS
    # ========================================================
    if role == "admin":

        f1, f2 = st.columns(2)

        with f1:

            emp_filter = st.selectbox(
                "Filter Employee",
                ["All"] +
                sorted(df["Employee"].dropna().unique()),
                key="admin_filter_emp_select"
            )

        with f2:

            date_filter = st.date_input(
                "Filter Date",
                None,
                key="admin_filter_date_input"
            )

        if emp_filter != "All":

            df = df[
                df["Employee"] == emp_filter
            ]

        if date_filter:

            df = df[
                df["Date"] ==
                date_filter.strftime("%d-%m-%y")
            ]

    # ========================================================
    # EMPLOYEE FILTER
    # ========================================================
    if role == "employee":

        employee_clean = str(employee).strip().upper()

        df = df[
            df["Employee"] == employee_clean
        ]

    # ========================================================
    # FORMAT TIME
    # ========================================================
    df["Login"] = pd.to_datetime(
        df["Login"],
        errors="coerce"
    ).dt.strftime("%H:%M:%S")

    df["Logout"] = pd.to_datetime(
        df["Logout"],
        errors="coerce"
    ).dt.strftime("%H:%M:%S")

# ✅ Fix column type issues (safe version)
if "Working Hours" in df.columns:
    df["Working Hours"] = df["Working Hours"].astype(str)

else:
    st.info("No attendance records found")

# ========================================================
# ✅ FILTERS
# ========================================================

col1_mflt, col2_mflt = st.columns(2)

# ✅ Month filter
with col1_mflt:
    month_list = sorted(df["Month"].dropna().unique(), reverse=True)

    if not month_list:
        st.info("No months available")
        st.stop()

    selected_month = st.selectbox(
        "📅 Select Month",
        month_list,
        key="month_filter_monthly"
    )

# ✅ Employee filter
with col2_mflt:
    employee_list = df["Employee"].dropna().astype(str).unique().tolist()
    employee_list = sorted(employee_list)
    employee_list = ["All"] + employee_list

    selected_employee = st.selectbox(
        "👤 Select Employee",
        employee_list,
        key="employee_filter_monthly_v2"
    )

# ========================================================
# ✅ APPLY FILTERS
# ========================================================

monthly_df = df[
    df["Month"] == selected_month
]

# ✅ Employee filter
if selected_employee != "All":

    monthly_df = monthly_df[
        monthly_df["Employee"] == selected_employee
    ]
monthly_df = monthly_df.copy()

# ✅ ✅ ADD YOUR FIXES HERE ✅
monthly_df["Date"] = pd.to_datetime(monthly_df["Date"]).dt.strftime("%d-%m-%y")
monthly_df["Logout"] = monthly_df["Logout"].replace("None", "Pending")

st.divider()

# ============================================================
# ✅ DASHBOARD SUMMARY (KPI CARDS)
# ============================================================

st.markdown("### 📊 Summary")

total_records = len(monthly_df)

unique_employees = (
    monthly_df["Employee"]
    .nunique()
)

full_days = len(
    monthly_df[
        monthly_df["Status"] == "Full Day"
    ]
)

half_days = len(
    monthly_df[
        monthly_df["Status"] == "Half Day"
    ]
)

short_days = len(
    monthly_df[
        monthly_df["Status"] == "Short Day"
    ]
)

col1_kpi, col2_kpi, col3_kpi, col4_kpi, col5_kpi = st.columns(5)

with col1_kpi:
    st.metric("📋 Total Records", total_records)

with col2_kpi:
    st.metric("👥 Employees", unique_employees)

with col3_kpi:
    st.metric("✅ Full Days", full_days)

with col4_kpi:
    st.metric("⏱ Half Days", half_days)

with col5_kpi:
    st.metric("⚠️ Short Days", short_days)

st.divider()

# ============================================================
# ✅ TABLE + DOWNLOAD (FIXED CALENDAR & DATE PARSING)
# ============================================================

if not monthly_df.empty:

    st.markdown("### 📅 Attendance Details")

    # ✅ Clean and standardize dates across the dataset (Fixes DD-MM vs MM-DD swap)
    monthly_df_clean = monthly_df.copy()
    
    monthly_df_clean["Date_Parsed"] = pd.to_datetime(
        monthly_df_clean["Date"], 
        dayfirst=True, 
        format="mixed", 
        errors="coerce"
    )

    # Clean out invalid NaT dates and format cleanly as YYYY-MM-DD
    monthly_df_clean = monthly_df_clean.dropna(subset=["Date_Parsed"])
    monthly_df_clean["Date"] = monthly_df_clean["Date_Parsed"].dt.strftime("%d-%m-%y")

    # Toggle between All Dates in Month or Specific Date
    col_cal1, col_cal2 = st.columns([1, 2])

    with col_cal1:
        filter_mode = st.radio(
            "Filter View",
            ["All Dates in Month", "Specific Date"],
            horizontal=True,
            key="details_date_filter_mode"
        )

    with col_cal2:
        if filter_mode == "Specific Date":
            # ✅ REMOVED min_value and max_value constraints so ALL past/previous dates are selectable
            selected_calendar_date = st.date_input(
                "📅 Select Date from Calendar",
                value=date.today(),
                key="attendance_details_calendar"
            )
            date_str_filter = selected_calendar_date.strftime("%d-%m-%y")
        else:
            date_str_filter = None

    # ✅ Filter data for table view
    if date_str_filter:
        display_df = monthly_df_clean[monthly_df_clean["Date"] == date_str_filter].copy()
    else:
        display_df = monthly_df_clean.copy()

    # Drop internal helper column
    if "Date_Parsed" in display_df.columns:
        display_df = display_df.drop(columns=["Date_Parsed"])

    # ✅ Render Table
    if not display_df.empty:
        st.dataframe(display_df, use_container_width=True, hide_index=True)

        st.divider()

        # ✅ Download Report
        file_suffix = date_str_filter if date_str_filter else selected_month
        st.download_button(
            label="⬇ Download Selected Report",
            data=display_df.to_csv(index=False).encode("utf-8"),
            file_name=f"attendance_report_{file_suffix}.csv",
            mime="text/csv",
            key="download_monthly_report_btn"
        )
    else:
        if date_str_filter:
            st.info(f"⚠ No attendance records found for {date_str_filter}")
        else:
            st.info("⚠ No attendance records found for selected month.")

else:
    st.info("⚠ No data available for selected month")

# ============================================================
# ✅ FULL DOWNLOAD (ALL DATA)
# ============================================================
if role == "admin":
    
    st.markdown("### 📥 Download Full Data")

st.download_button(
    label="📥 Download Full Attendance",
    data=df.to_csv(index=False).encode("utf-8"),
    file_name="attendance_full.csv",
    mime="text/csv",
    key="download_full_attendance"
)