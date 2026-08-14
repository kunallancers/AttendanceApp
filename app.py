""" 
Lancers Risk Consulting - Attendance Management & Workforce Analytics
Corporate Enterprise SaaS UI integrated with the existing AttendanceData Google Sheet.

Preserved core functionality:
- employees.xlsx authentication
- Google Sheets AttendanceData / Leave integration
- Employee/Admin roles
- GPS capture
- Login / Logout attendance
- Leave application and approval
- Attendance records
- Admin clear / duplicate cleanup
- CSV exports
- Corporate dashboard inspired by the supplied design
"""

import os
import base64
import html
from datetime import date, datetime, time, timedelta

import gspread
import pandas as pd
import plotly.graph_objects as go
import pytz
import streamlit as st
import textwrap
from oauth2client.service_account import ServiceAccountCredentials
from streamlit_geolocation import streamlit_geolocation


# ============================================================
# 1. PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Lancers HRMS | Attendance Management",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

IST = pytz.timezone("Asia/Kolkata")

ATTENDANCE_HEADERS = [
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
    "Logout Longitude",
]

LEAVE_HEADERS = ["Employee", "Date", "Reason", "Status"]


# ============================================================
# 2. CORPORATE CSS
# ============================================================

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont,
                 'Segoe UI', Roboto, sans-serif;
}

.stApp {
    background: #F5F7FB;
}

.main .block-container {
    padding-top: 1rem;
    padding-bottom: 2.5rem;
    max-width: 1500px;
}

section[data-testid="stSidebar"] {
    background: #FFFFFF;
    border-right: 1px solid #E2E8F0;
}

section[data-testid="stSidebar"] > div {
    padding-top: 1rem;
}

.saas-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 18px;
    padding: 18px 20px;
    box-shadow: 0 4px 20px -4px rgba(15, 23, 42, 0.05);
    margin-bottom: 16px;
}

.header-card {
    background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
    border-radius: 18px;
    padding: 18px 24px;
    margin-bottom: 20px;
    box-shadow: 0 10px 28px -8px rgba(15, 23, 42, 0.35);
    color: white;
}

.header-title {
    color: #FFFFFF;
    font-size: 1.35rem;
    font-weight: 800;
    margin: 0;
}

.header-subtitle {
    color: #94A3B8;
    font-size: 0.78rem;
    margin-top: 3px;
}

.header-user {
    color: #FFFFFF;
    font-size: 0.9rem;
    font-weight: 700;
    text-align: right;
}

.header-date {
    color: #38BDF8;
    font-size: 0.72rem;
    font-weight: 600;
    text-align: right;
    margin-top: 3px;
}

.kpi-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 15px;
    padding: 15px 17px;
    min-height: 112px;
    box-shadow: 0 3px 12px rgba(15, 23, 42, 0.035);
}

.kpi-title {
    color: #64748B;
    font-size: 0.73rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.45px;
}

.kpi-value {
    color: #0F172A;
    font-size: 1.65rem;
    line-height: 1.15;
    font-weight: 800;
    margin: 6px 0 5px 0;
}

.kpi-positive { color: #10B981; }
.kpi-warning { color: #F59E0B; }
.kpi-danger { color: #EC4899; }
.kpi-info { color: #2563EB; }

.kpi-sub {
    color: #94A3B8;
    font-size: 0.7rem;
    font-weight: 600;
}

.emp-item {
    display: flex;
    align-items: center;
    gap: 9px;
    padding: 7px 9px;
    border-radius: 9px;
    margin-bottom: 3px;
    background: #F8FAFC;
    border: 1px solid #F1F5F9;
    color: #334155;
    font-size: 0.76rem;
    font-weight: 600;
}

.emp-item:hover {
    background: #F1F5F9;
}

.status-dot {
    height: 9px;
    width: 9px;
    min-width: 9px;
    border-radius: 50%;
    display: inline-block;
}

.dot-green { background: #10B981; }
.dot-pink { background: #EC4899; }
.dot-blue { background: #3B82F6; }

.small-muted {
    color: #94A3B8;
    font-size: 0.74rem;
}

.section-title {
    color: #0F172A;
    font-size: 1.05rem;
    font-weight: 800;
    margin: 5px 0 12px 0;
}

div[data-testid="stDataFrame"] {
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    overflow: hidden;
}

.stButton > button {
    border-radius: 10px;
    font-weight: 700;
    border: 1px solid #CBD5E1;
    transition: all .2s ease;
}

.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 5px 15px rgba(15, 23, 42, .10);
}

.stTextInput input,
.stSelectbox [data-baseweb="select"],
.stDateInput input {
    border-radius: 10px !important;
}

div[data-testid="stMetric"] {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 14px;
    padding: 12px 16px;
}

hr {
    border-color: #E2E8F0;
}

.login-wrap {
    max-width: 460px;
    margin: 7vh auto 0 auto;
}

.login-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 22px;
    padding: 32px;
    box-shadow: 0 20px 45px rgba(15, 23, 42, .10);
}

.login-brand {
    text-align: center;
    color: #0F172A;
    font-size: 1.45rem;
    font-weight: 800;
}

.login-sub {
    text-align: center;
    color: #64748B;
    font-size: .82rem;
    margin-bottom: 20px;
}
</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# 3. COMMON HELPERS
# ============================================================

def norm_name(value):
    return str(value).strip().upper()


def clean_text(value, fallback=""):
    if value is None:
        return fallback
    text = str(value).strip()
    if text.lower() in {"nan", "none", "nat"}:
        return fallback
    return text


def html_text(value):
    return html.escape(clean_text(value))


def get_ist():
    return pd.Timestamp.now(tz="Asia/Kolkata").tz_localize(None)


def date_key(value):
    parsed = pd.to_datetime(value, dayfirst=True, format="mixed", errors="coerce")
    if pd.isna(parsed):
        return ""
    return parsed.strftime("%d-%m-%y")


def time_to_seconds(value):
    try:
        parsed = pd.to_datetime(str(value).strip(), format="%H:%M:%S", errors="coerce")
        if pd.isna(parsed):
            return None
        return parsed.hour * 3600 + parsed.minute * 60 + parsed.second
    except Exception:
        return None


def working_hours_to_decimal(value):
    text = clean_text(value, "0")
    try:
        if ":" in text:
            parts = text.split(":")
            return float(parts[0]) + float(parts[1]) / 60 + (
                float(parts[2]) / 3600 if len(parts) > 2 else 0
            )
        return float(text)
    except Exception:
        return 0.0


def calculate_duration_str(login_time_str, logout_time_str):
    try:
        t_in = pd.to_datetime(str(login_time_str), format="%H:%M:%S", errors="coerce")
        t_out = pd.to_datetime(str(logout_time_str), format="%H:%M:%S", errors="coerce")
        if pd.isna(t_in) or pd.isna(t_out):
            return "00:00:00", 0.0
        delta = t_out - t_in
        if delta.total_seconds() < 0:
            delta += pd.Timedelta(days=1)
        seconds = max(0, int(delta.total_seconds()))
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        return f"{h:02d}:{m:02d}:{s:02d}", round(seconds / 3600, 2)
    except Exception:
        return "00:00:00", 0.0


def determine_attendance_status(total_hours_dec):
    if total_hours_dec >= 8:
        return "Full Day"
    if total_hours_dec >= 4:
        return "Half Day"
    if total_hours_dec > 0:
        return "Short Day"
    return "In Progress"


def get_lateness_category(login_time_str):
    seconds = time_to_seconds(login_time_str)
    if seconds is None:
        return "On Time"
    if seconds < 9 * 3600 + 15 * 60:
        return "Early"
    if seconds <= 9 * 3600 + 35 * 60:
        return "On Time"
    return "Late"


def check_date_type(target_date):
    holiday_list = {
        "01-01-2026": "New Year's Day",
        "26-01-2026": "Republic Day",
        "16-02-2026": "Maha Shivratri",
        "04-03-2026": "Holi",
        "26-03-2026": "Ram Navami",
        "03-04-2026": "Good Friday",
        "28-08-2026": "Raksha Bandhan",
        "04-09-2026": "Janmashtami",
        "02-10-2026": "Gandhi Jayanti",
        "20-10-2026": "Dussehra",
        "24-11-2026": "Guru Nanak Jayanti",
        "25-12-2026": "Christmas Day",
    }
    is_weekend = target_date.weekday() in [5, 6]
    return is_weekend, holiday_list.get(target_date.strftime("%d-%m-%Y"))


def clear_data_cache():
    try:
        st.cache_data.clear()
    except Exception:
        pass


# ============================================================
# 4. GOOGLE SHEETS CONNECTION
# ============================================================

@st.cache_resource
def connect_sheet():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]

    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)

        workbook_name = st.secrets.get("SHEET_NAME", "AttendanceData")
        workbook = client.open(workbook_name)
        sheet = workbook.sheet1

        try:
            leave_sheet = workbook.worksheet("Leave")
        except Exception:
            leave_sheet = workbook.add_worksheet(title="Leave", rows=1000, cols=4)
            leave_sheet.append_row(LEAVE_HEADERS)

        return sheet, leave_sheet

    except Exception as exc:
        st.error("❌ Google Sheet connection failed.")
        st.error(str(exc))
        st.stop()


# ============================================================
# 5. EMPLOYEE MASTER / AUTHENTICATION
# ============================================================

@st.cache_data(ttl=300)
def load_employee_master():
    try:
        if not os.path.exists("employees.xlsx"):
            st.error("❌ employees.xlsx not found in the application folder.")
            st.stop()

        df = pd.read_excel("employees.xlsx")
        df.columns = df.columns.astype(str).str.strip()

        required = ["Employee Name", "Password"]
        missing = [c for c in required if c not in df.columns]

        if missing:
            st.error(f"❌ Missing columns in employees.xlsx: {', '.join(missing)}")
            st.stop()

        df["Employee Name"] = df["Employee Name"].astype(str).str.strip()
        return df

    except Exception as exc:
        st.error(f"❌ Unable to load employees.xlsx: {exc}")
        st.stop()


def build_users(df_emp):
    users = {
        "admin": {
            "password": "admin123",
            "role": "admin",
            "employee": "ADMIN",
        }
    }

    for _, row in df_emp.iterrows():
        employee_name = clean_text(row.get("Employee Name"))
        if not employee_name:
            continue

        username = employee_name.split()[0].lower()

        users[username] = {
            "password": clean_text(row.get("Password")),
            "role": "employee",
            "employee": employee_name,
        }

    return users


# ============================================================
# 6. ATTENDANCE / LEAVE DATA
# ============================================================

@st.cache_data(ttl=2)
def load_attendance():
    try:
        sheet, _ = connect_sheet()
        data = sheet.get_all_records()

        if not data:
            return pd.DataFrame(columns=ATTENDANCE_HEADERS)

        df = pd.DataFrame(data)
        df.columns = df.columns.astype(str).str.strip()

        for col in ATTENDANCE_HEADERS:
            if col not in df.columns:
                df[col] = ""

        df = df[ATTENDANCE_HEADERS].copy()
        df["Date"] = df["Date"].apply(date_key)
        df["Employee"] = df["Employee"].apply(norm_name)

        return df

    except Exception as exc:
        st.error(f"❌ Error loading attendance: {exc}")
        return pd.DataFrame(columns=ATTENDANCE_HEADERS)


@st.cache_data(ttl=5)
def load_leave():
    try:
        _, leave_sheet = connect_sheet()
        data = leave_sheet.get_all_records()

        if not data:
            return pd.DataFrame(columns=LEAVE_HEADERS)

        df = pd.DataFrame(data)
        df.columns = df.columns.astype(str).str.strip()

        for col in LEAVE_HEADERS:
            if col not in df.columns:
                df[col] = ""

        df = df[LEAVE_HEADERS].copy()
        df["Employee"] = df["Employee"].apply(norm_name)
        df["Date"] = df["Date"].apply(date_key)

        return df

    except Exception as exc:
        st.error(f"❌ Error loading leave records: {exc}")
        return pd.DataFrame(columns=LEAVE_HEADERS)


def save_attendance_dataframe(df):
    sheet, _ = connect_sheet()
    data = df.copy()

    for col in ATTENDANCE_HEADERS:
        if col not in data.columns:
            data[col] = ""

    data = data[ATTENDANCE_HEADERS].fillna("")
    values = [ATTENDANCE_HEADERS] + data.astype(str).values.tolist()

    sheet.clear()
    sheet.update("A1", values)
    clear_data_cache()


# ============================================================
# 7. LOCATION
# ============================================================

def get_location_values():
    location = st.session_state.get("location", {})
    return location.get("lat", "NA"), location.get("lon", "NA")


def capture_location():
    if "location" not in st.session_state:
        st.session_state["location"] = {}

    try:
        location = streamlit_geolocation()

        if (
            location
            and location.get("latitude") is not None
            and location.get("longitude") is not None
        ):
            st.session_state["location"] = {
                "lat": location["latitude"],
                "lon": location["longitude"],
            }
    except Exception:
        pass

    return get_location_values()


# ============================================================
# EXECUTIVE HEADER
# ============================================================

def render_brand_header(current_user, user_role):
    now_ist = get_ist()
    current_hour = now_ist.hour

    if current_hour < 12:
        greeting = "Good Morning"
    elif current_hour < 17:
        greeting = "Good Afternoon"
    else:
        greeting = "Good Evening"

    formatted_date = now_ist.strftime("%A, %d %B %Y")
    user_display_name = str(current_user).strip().title()
    user_role_display = str(user_role).strip().title()

    header_html = textwrap.dedent(f"""
<div style="
    display:flex;
    justify-content:space-between;
    align-items:center;
    background:linear-gradient(135deg,#0F172A 0%,#1E293B 100%);
    padding:16px 24px;
    border-radius:14px;
    border:1px solid rgba(255,255,255,0.08);
    box-shadow:0 4px 20px rgba(0,0,0,0.15);
    margin-bottom:20px;
">
    <div>
        <div style="
            color:#FFFFFF;
            font-size:1.25rem;
            font-weight:700;
        ">
            Lancers Risk Consulting
        </div>

        <div style="
            color:#94A3B8;
            font-size:0.82rem;
            margin-top:2px;
        ">
            Enterprise Attendance & Workforce Analytics
        </div>
    </div>

    <div style="text-align:right;">
        <div style="
            color:#FFFFFF;
            font-weight:700;
            font-size:0.95rem;
        ">
            {greeting}, {user_display_name} 👋
        </div>

        <div style="
            color:#94A3B8;
            font-size:0.78rem;
            margin-top:4px;
        ">
            {formatted_date} · Role:

            <span style="
                color:#7DD3FC;
                font-weight:600;
                background:rgba(56,189,248,0.15);
                padding:3px 8px;
                border-radius:6px;
            ">
                {user_role_display}
            </span>
        </div>
    </div>
</div>
""")

    st.markdown(
        header_html,
        unsafe_allow_html=True
    )


def render_login_page():
    logo = get_logo_base64()

    logo_html = (
        f'<img src="data:image/png;base64,{logo}" '
        f'style="max-height:58px;width:auto;">'
        if logo
        else '<div style="font-size:3rem;">🛡️</div>'
    )

    st.markdown(
        f"""
        <div class="login-wrap">
            <div class="login-card">
                <div style="text-align:center;">{logo_html}</div>
                <div class="login-brand">Lancers Risk Consulting</div>
                <div class="login-sub">
                    Attendance Management & Workforce Analytics
                </div>
        """,
        unsafe_allow_html=True,
    )

    username = st.text_input(
        "Username",
        key="auth_login_user",
        placeholder="Enter username",
    )

    password = st.text_input(
        "Password",
        type="password",
        key="auth_login_pass",
        placeholder="Enter password",
    )

    if st.button(
        "🔐 Sign In",
        key="login_btn",
        type="primary",
        use_container_width=True,
    ):
        username_clean = username.lower().strip()

        if username_clean in st.session_state["users"]:
            account = st.session_state["users"][username_clean]

            if account["password"] == password:
                st.session_state["logged_in"] = True
                st.session_state["role"] = account["role"]
                st.session_state["employee"] = account["employee"]
                st.rerun()

        st.error("❌ Invalid username or password.")

# ============================================================
# ✅ EXECUTIVE HEADER BANNER (FIXED)
# ============================================================

st.markdown("""
<div style="
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
    padding: 16px 24px;
    border-radius: 14px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
    margin-bottom: 20px;
">
    <!-- Left Side: Brand Title & Subtitle -->
    <div>
        <h3 style="
            margin: 0;
            color: #FFFFFF;
            font-size: 1.25rem;
            font-weight: 700;
        ">
            Lancers Risk Consulting
        </h3>
        <p style="
            margin: 2px 0 0 0;
            color: #94A3B8;
            font-size: 0.82rem;
        ">
            Enterprise Attendance & Workforce Analytics
        </p>
    </div>

    <!-- Right Side: User Greeting, Date & Role Badge -->
    <div style="text-align: right;">
        <div style="
            color: #FFFFFF;
            font-weight: 700;
            font-size: 0.95rem;
        ">
            Good Afternoon, Admin 👋
        </div>
        <div style="
            color: #94A3B8;
            font-size: 0.78rem;
            margin-top: 2px;
        ">
            Friday, 14 August 2026 · Role:
            <span style="
                color: #7DD3FC;
                font-weight: 600;
                background: rgba(56, 189, 248, 0.15);
                padding: 2px 8px;
                border-radius: 6px;
            ">
                Admin
            </span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# ============================================================
# 9. SIDEBAR
# ============================================================

def render_sidebar():
    role = st.session_state["role"]

    with st.sidebar:
        st.markdown("## 🛡️ Lancers")
        st.caption("Attendance Management System")
        st.divider()

        pages = [
            "📊 Dashboard",
            "⏱️ Clock In / Out",
            "📋 Attendance Records",
            "👤 Employee Profile",
            "🏖️ Leave Management",
            "📈 Analytics",
            "📑 Reports & Export",
        ]

        if role == "admin":
            pages += [
                "🏢 Department Analysis",
                "📍 Location Tracker",
                "⚙️ Admin Control Panel",
            ]

        current = st.session_state.get("page", pages[0])

        if current not in pages:
            current = pages[0]

        page = st.radio(
            "Navigation",
            pages,
            index=pages.index(current),
            label_visibility="collapsed",
            key="main_navigation",
        )

        st.session_state["page"] = page

        st.divider()

        st.markdown(
            f"""
            <div class="small-muted">LOGGED-IN USER</div>
            <div style="font-weight:800;color:#0F172A;margin-top:4px;">
                {html_text(st.session_state["employee"])}
            </div>
            <div class="small-muted">
                {html_text(role.title())}
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button(
            "🚪 Logout",
            key="main_app_logout_btn",
            use_container_width=True,
        ):
            st.session_state.clear()
            st.rerun()


# ============================================================
# 10. DATA HELPERS FOR DASHBOARD
# ============================================================

def prepare_attendance(df_att):
    df = df_att.copy()

    for col in ATTENDANCE_HEADERS:
        if col not in df.columns:
            df[col] = ""

    if df.empty:
        df["Date_dt"] = pd.Series(dtype="datetime64[ns]")
        return df

    df["Date_dt"] = pd.to_datetime(
        df["Date"],
        dayfirst=True,
        format="mixed",
        errors="coerce",
    )

    df["Employee"] = df["Employee"].apply(norm_name)
    df["Status"] = df["Status"].apply(
        lambda x: clean_text(x, "In Progress")
    )
    df["Type"] = df["Type"].apply(
        lambda x: clean_text(x, "WFO")
    )

    return df


def get_employee_names(df_emp, df_att):
    if not df_emp.empty and "Employee Name" in df_emp.columns:
        names = (
            df_emp["Employee Name"]
            .dropna()
            .astype(str)
            .str.strip()
            .tolist()
        )
    elif not df_att.empty:
        names = (
            df_att["Employee"]
            .dropna()
            .astype(str)
            .tolist()
        )
    else:
        names = []

    return sorted(set(names), key=str.lower)


def approved_leave_employees(df_leave, target_date):
    if df_leave.empty:
        return set()

    target = target_date.strftime("%d-%m-%y")

    return set(
        df_leave.loc[
            (df_leave["Date"] == target)
            & (
                df_leave["Status"]
                .astype(str)
                .str.strip()
                .str.upper()
                == "APPROVED"
            ),
            "Employee",
        ]
        .astype(str)
        .map(norm_name)
    )


def day_frame(df_att, target_date):
    if df_att.empty:
        return df_att.copy()

    target = target_date.strftime("%d-%m-%y")
    return df_att[df_att["Date"] == target].copy()

def parse_duration_to_hours(val):
    """
    Safely converts strings ('08:30:00', '08:30', '4.5'), timedeltas,
    or numeric values into float hours. Returns 0.0 on invalid inputs.
    """
    if pd.isna(val) or val in ["", "-", "None", "nan", "NaN", None]:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, timedelta):
        return val.total_seconds() / 3600.0
    
    val_str = str(val).strip()
    # Handle "HH:MM:SS" or "HH:MM" format
    if ":" in val_str:
        parts = val_str.split(":")
        try:
            hrs = float(parts[0])
            mins = float(parts[1]) if len(parts) > 1 else 0.0
            secs = float(parts[2]) if len(parts) > 2 else 0.0
            return hrs + (mins / 60.0) + (secs / 3600.0)
        except (ValueError, IndexError):
            return 0.0
    
    # Handle direct numeric strings like "8.5"
    try:
        return float(val_str)
    except ValueError:
        return 0.0

def weekly_metrics(df, selected_date):
    """
    Calculates 7-day Monday-to-Sunday metrics safely.
    Returns datetime objects in week_days to support .strftime() calls downstream.
    """
    if df is None or df.empty:
        start_of_week = selected_date - timedelta(days=selected_date.weekday())
        week_days_dt = [start_of_week + timedelta(days=i) for i in range(7)]
        return week_days_dt, [0.0] * 7, [0] * 7

    df_copy = df.copy()
    df_copy["Date_dt"] = pd.to_datetime(
        df_copy["Date"], dayfirst=True, format="mixed", errors="coerce"
    )

    if "Working Hours" in df_copy.columns:
        df_copy["Hours_Numeric"] = df_copy["Working Hours"].apply(parse_duration_to_hours)
    else:
        df_copy["Hours_Numeric"] = 0.0

    start_of_week = selected_date - timedelta(days=selected_date.weekday())
    week_days_dt = [start_of_week + timedelta(days=i) for i in range(7)]

    actual_hours = []
    attendance_count = []

    for day_dt in week_days_dt:
        d_str = day_dt.strftime("%d-%m-%y")
        day_slice = df_copy[df_copy["Date_dt"].dt.strftime("%d-%m-%y") == d_str]

        if not day_slice.empty:
            day_total_hrs = round(float(day_slice["Hours_Numeric"].sum()), 2)
            day_att_count = int(len(day_slice))
        else:
            day_total_hrs = 0.0
            day_att_count = 0

        actual_hours.append(day_total_hrs)
        attendance_count.append(day_att_count)

    # ✅ Returns datetime objects in week_days_dt
    return week_days_dt, actual_hours, attendance_count

# ============================================================
# 11. CHART / KPI HELPERS
# ============================================================

def chart_base(fig, height=220):
    fig.update_layout(
        height=height,
        margin=dict(
            l=8,
            r=8,
            t=18,
            b=8,
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(
            family="Plus Jakarta Sans",
            color="#64748B",
        ),
        showlegend=False,
    )

    return fig


def render_kpi_card(
    container,
    title,
    value,
    subtitle="",
    value_class="",
):
    container.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">
                {html_text(title)}
            </div>

            <div class="kpi-value {value_class}">
                {html_text(value)}
            </div>

            <div class="kpi-sub">
                {html_text(subtitle)}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# 12. MAIN CORPORATE DASHBOARD
# ============================================================

def render_dashboard(df_emp, df_att, df_leave):
    st.markdown("### 📊 Workforce Dashboard")

    f1, f2, f3 = st.columns([1.6, 1.2, 1.2])

    with f1:
        period = st.selectbox(
            "Analysis Period",
            [
                "Today",
                "This Week",
                "This Month",
                "Previous Month",
                "Custom Date",
            ],
            key="dashboard_period",
        )

    with f2:
        if period == "Custom Date":
            selected_date = st.date_input(
                "Select Date",
                value=datetime.now(IST).date(),
                key="dashboard_custom_date",
            )
        else:
            selected_date = datetime.now(IST).date()

    with f3:
        weekend, holiday = check_date_type(selected_date)

        if holiday:
            st.info(f"🎉 {holiday}")
        elif weekend:
            st.info("⛱️ Weekend")

    df = prepare_attendance(df_att)

    employees = get_employee_names(
        df_emp,
        df,
    )

    total_headcount = len(employees)

    df_day = day_frame(
        df,
        selected_date,
    )

    present_set = (
        set(df_day["Employee"].unique())
        if not df_day.empty
        else set()
    )

    leave_set = approved_leave_employees(
        df_leave,
        selected_date,
    )

    present_today = len(present_set)

    leave_today = len(
        leave_set - present_set
    )

    weekend, holiday = check_date_type(
        selected_date
    )

    if weekend or holiday:
        absent_today = 0
    else:
        absent_today = max(
            0,
            total_headcount
            - present_today
            - leave_today,
        )

    wfh_today = (
        int(
            df_day["Type"]
            .astype(str)
            .str.contains(
                "WFH",
                case=False,
                na=False,
            )
            .sum()
        )
        if not df_day.empty
        else 0
    )

    wfo_today = (
        int(
            df_day["Type"]
            .astype(str)
            .str.contains(
                "WFO",
                case=False,
                na=False,
            )
            .sum()
        )
        if not df_day.empty
        else 0
    )

    early_cnt = 0
    ontime_cnt = 0
    late_cnt = 0

    if not df_day.empty:
        for login in df_day["Login"].dropna():
            category = get_lateness_category(
                login
            )

            if category == "Early":
                early_cnt += 1
            elif category == "Late":
                late_cnt += 1
            else:
                ontime_cnt += 1

    attendance_pct = (
        round(
            (present_today / total_headcount) * 100,
            1,
        )
        if total_headcount
        else 0
    )

    total_hours_day = (
        round(
            df_day["Working Hours"]
            .map(working_hours_to_decimal)
            .sum(),
            1,
        )
        if not df_day.empty
        else 0.0
    )

    # --------------------------------------------------------
    # KPI CARDS
    # --------------------------------------------------------

    k1, k2, k3, k4, k5, k6 = st.columns(6)

    render_kpi_card(
        k1,
        "Total Employees",
        str(total_headcount),
        "Active employee master",
    )

    render_kpi_card(
        k2,
        "Present Today",
        str(present_today),
        f"{attendance_pct}% attendance",
        "kpi-positive",
    )

    render_kpi_card(
        k3,
        "Absent",
        str(absent_today),
        "Excluding approved leave",
        "kpi-danger",
    )

    render_kpi_card(
        k4,
        "WFH / WFO",
        f"{wfh_today} / {wfo_today}",
        "Work location",
        "kpi-info",
    )

    render_kpi_card(
        k5,
        "Late Arrivals",
        str(late_cnt),
        "After 09:35 AM",
        "kpi-warning",
    )

    render_kpi_card(
        k6,
        "Hours Logged",
        f"{total_hours_day:.1f}",
        "Selected day",
        "kpi-positive",
    )

    st.markdown(
        "<div style='height:10px'></div>",
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # REFERENCE-STYLE GRID
    # --------------------------------------------------------

    left, right = st.columns(
        [1, 3.2],
        gap="medium",
    )

    with left:
        st.markdown(
            '<div class="saas-card">',
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div style="
                display:flex;
                justify-content:space-between;
                align-items:center;
                margin-bottom:8px;
            ">
                <div class="section-title"
                     style="margin:0;">
                    Employees
                </div>

                <div style="
                    font-weight:800;
                    color:#10B981;
                ">
                    {present_today}
                    <span style="
                        color:#94A3B8;
                        font-size:.75rem;
                    ">
                        / {total_headcount}
                    </span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        search = st.text_input(
            "Search employee",
            placeholder="Search name...",
            label_visibility="collapsed",
            key="dashboard_employee_search",
        )

        filtered = [
            employee
            for employee in employees
            if (
                not search
                or search.lower()
                in employee.lower()
            )
        ]

        for employee_name in filtered[:80]:
            employee_norm = norm_name(
                employee_name
            )

            if employee_norm in present_set:
                dot = "dot-green"
                status = "Present"
            elif employee_norm in leave_set:
                dot = "dot-blue"
                status = "Leave"
            else:
                dot = "dot-pink"
                status = "Absent"

            st.markdown(
                f"""
                <div class="emp-item"
                     title="{status}">
                    <span class="status-dot {dot}"></span>
                    <span>
                        {html_text(
                            employee_name.title()
                        )}
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        if len(filtered) > 80:
            st.caption(
                f"Showing first 80 of {len(filtered)} employees."
            )

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )

    with right:
        week_days, actual_hours, attendance_count = weekly_metrics(
            df,
            selected_date,
        )

        labels = [
            d.strftime("%a")[0]
            for d in week_days
        ]

        # ----------------------------------------------------
        # TOP CHARTS
        # ----------------------------------------------------

        c1, c2 = st.columns(2)

        with c1:
            st.markdown(
                '<div class="saas-card">',
                unsafe_allow_html=True,
            )

            week_total = sum(
                actual_hours
            )

            target_hours = (
                total_headcount * 8 * 5
            )

            st.markdown(
                f"""
                <div style="
                    display:flex;
                    justify-content:space-between;
                    align-items:center;
                ">
                    <div>
                        <div class="section-title"
                             style="margin:0;">
                            Total Productive Hours
                        </div>

                        <div class="small-muted">
                            Current week total
                        </div>
                    </div>

                    <div style="
                        font-size:1.25rem;
                        font-weight:800;
                        color:#10B981;
                    ">
                        {week_total:.1f}

                        <span style="
                            font-size:.75rem;
                            color:#94A3B8;
                        ">
                            / {target_hours} hrs
                        </span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            fig = go.Figure()

            fig.add_trace(
                go.Bar(
                    x=labels,
                    y=actual_hours,
                    marker_color="#F5B914",
                    width=0.42,
                    hovertemplate=(
                        "%{x}: %{y:.1f} hrs"
                        "<extra></extra>"
                    ),
                )
            )

            fig.update_xaxes(
                showgrid=False,
                zeroline=False,
            )

            fig.update_yaxes(
                showgrid=True,
                gridcolor="#EEF2F7",
                zeroline=False,
            )

            chart_base(fig, 235)

            st.plotly_chart(
                fig,
                use_container_width=True,
                config={
                    "displayModeBar": False
                },
            )

            st.markdown(
                "</div>",
                unsafe_allow_html=True,
            )

        with c2:
            st.markdown(
                '<div class="saas-card">',
                unsafe_allow_html=True,
            )

            st.markdown(
                f"""
                <div style="
                    display:flex;
                    justify-content:space-between;
                    align-items:center;
                ">
                    <div>
                        <div class="section-title"
                             style="margin:0;">
                            Total Attendance
                        </div>

                        <div class="small-muted">
                            Daily headcount · current week
                        </div>
                    </div>

                    <div style="
                        font-size:1.25rem;
                        font-weight:800;
                        color:#10B981;
                    ">
                        {present_today}

                        <span style="
                            font-size:.75rem;
                            color:#94A3B8;
                        ">
                            today
                        </span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            fig = go.Figure()

            fig.add_trace(
                go.Scatter(
                    x=labels,
                    y=attendance_count,
                    mode="lines+markers",
                    line=dict(
                        color="#F5B914",
                        width=3,
                    ),
                    marker=dict(
                        size=7,
                        color="#F5B914",
                    ),
                    hovertemplate=(
                        "%{x}: %{y} employees"
                        "<extra></extra>"
                    ),
                )
            )

            fig.update_xaxes(
                showgrid=False,
                zeroline=False,
            )

            fig.update_yaxes(
                showgrid=True,
                gridcolor="#EEF2F7",
                zeroline=False,
            )

            chart_base(fig, 235)

            st.plotly_chart(
                fig,
                use_container_width=True,
                config={
                    "displayModeBar": False
                },
            )

            st.markdown(
                "</div>",
                unsafe_allow_html=True,
            )

        # ----------------------------------------------------
        # SECOND ROW
        # ----------------------------------------------------

        r2c1, r2c2, r2c3 = st.columns(
            [1.15, 1.15, 1.6]
        )

        with r2c1:
            st.markdown(
                '<div class="saas-card">',
                unsafe_allow_html=True,
            )

            st.markdown(
                '<div class="section-title">Lateness</div>',
                unsafe_allow_html=True,
            )

            fig = go.Figure(
                go.Bar(
                    x=[
                        early_cnt,
                        ontime_cnt,
                        late_cnt,
                    ],
                    y=[
                        "Early",
                        "On-time",
                        "Late",
                    ],
                    orientation="h",
                    marker_color=[
                        "#F5B914",
                        "#10B981",
                        "#EC4899",
                    ],
                    text=[
                        early_cnt,
                        ontime_cnt,
                        late_cnt,
                    ],
                    textposition="outside",
                    hovertemplate=(
                        "%{y}: %{x}"
                        "<extra></extra>"
                    ),
                )
            )

            fig.update_xaxes(
                showgrid=False,
                zeroline=False,
            )

            fig.update_yaxes(
                showgrid=False,
                zeroline=False,
            )

            chart_base(fig, 205)

            st.plotly_chart(
                fig,
                use_container_width=True,
                config={
                    "displayModeBar": False
                },
            )

            st.markdown(
                "</div>",
                unsafe_allow_html=True,
            )

        with r2c2:
            st.markdown(
                '<div class="saas-card">',
                unsafe_allow_html=True,
            )

            st.markdown(
                '<div class="section-title">Attendance Status</div>',
                unsafe_allow_html=True,
            )

            status_map = {
                "Present": present_today,
                "Absent": absent_today,
                "Leave": leave_today,
                "WFH": wfh_today,
                "WFO": wfo_today,
            }

            status_map = {
                key: value
                for key, value
                in status_map.items()
                if value > 0
            }

            if not status_map:
                status_map = {
                    "No Data": 1
                }

            fig = go.Figure(
                data=[
                    go.Pie(
                        labels=list(
                            status_map.keys()
                        ),
                        values=list(
                            status_map.values()
                        ),
                        hole=0.62,
                        textinfo="none",
                        marker=dict(
                            colors=[
                                "#10B981",
                                "#EC4899",
                                "#8B5CF6",
                                "#3B82F6",
                                "#22C55E",
                                "#E5E7EB",
                            ]
                        ),
                    )
                ]
            )

            fig.add_annotation(
                text=(
                    f"<b>{present_today}</b>"
                    "<br>"
                    "<span style='font-size:11px'>"
                    "Present"
                    "</span>"
                ),
                showarrow=False,
            )

            chart_base(fig, 205)

            st.plotly_chart(
                fig,
                use_container_width=True,
                config={
                    "displayModeBar": False
                },
            )

            st.markdown(
                "</div>",
                unsafe_allow_html=True,
            )

        with r2c3:
            m1, m2 = st.columns(2)

            pending = (
                int(
                    (
                        df_day["Status"]
                        .astype(str)
                        .str.upper()
                        == "IN PROGRESS"
                    ).sum()
                )
                if not df_day.empty
                else 0
            )

            cumulative_hours = (
                round(
                    df["Working Hours"]
                    .map(
                        working_hours_to_decimal
                    )
                    .sum(),
                    1,
                )
                if not df.empty
                else 0
            )

            render_kpi_card(
                m1,
                "Total Hours",
                f"{cumulative_hours:.1f}",
                "Cumulative logged hours",
                "kpi-positive",
            )

            render_kpi_card(
                m2,
                "Active Attendance",
                f"{present_today}/{total_headcount}",
                "Present today",
                "kpi-positive",
            )

            st.markdown(
                "<div style='height:10px'></div>",
                unsafe_allow_html=True,
            )

            render_kpi_card(
                m1,
                "Employees Late",
                str(late_cnt),
                "After 09:35 AM",
                "kpi-danger",
            )

            render_kpi_card(
                m2,
                "Pending Clock-Outs",
                str(pending),
                "Still in progress",
                "kpi-warning",
            )

    # --------------------------------------------------------
    # TODAY'S ACTIVITY
    # --------------------------------------------------------

    st.markdown(
        "### 🕘 Today's Attendance Activity"
    )

    if df_day.empty:
        st.info(
            "No attendance records for the selected date."
        )
    else:
        activity = df_day.copy()
        activity.insert(
            0,
            "S.No",
            range(1, len(activity) + 1),
        )

        cols = [
            c
            for c in [
                "S.No",
                "Employee",
                "Login",
                "Logout",
                "Working Hours",
                "Status",
                "Type",
            ]
            if c in activity.columns
        ]

        st.dataframe(
            activity[cols],
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# 13. CLOCK IN / OUT
# ============================================================

def render_clock_in_out(df_att):
    st.markdown(
        "### ⏱️ Daily Attendance Punch"
    )

    user = norm_name(
        st.session_state["employee"]
    )

    today = datetime.now(IST).date()
    today_str = today.strftime("%d-%m-%y")

    df = prepare_attendance(df_att)

    user_today = (
        df[
            (df["Date"] == today_str)
            & (df["Employee"] == user)
        ]
        if not df.empty
        else pd.DataFrame()
    )

    c1, c2 = st.columns(
        [1.6, 1]
    )

    with c1:
        st.markdown(
            f"""
            <div class="saas-card">
                <div class="section-title">
                    Employee Punch Terminal
                </div>

                <div class="small-muted">
                    Employee:
                    <b>
                        {html_text(
                            st.session_state["employee"]
                        )}
                    </b>
                    &nbsp; · &nbsp;
                    Date:
                    <b>{today_str}</b>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        work_mode = st.selectbox(
            "Attendance Type",
            [
                "Present WFO",
                "Present WFH",
                "Client Site Visit",
            ],
            key="clock_work_mode",
        )

        lat, lon = capture_location()

        loc1, loc2 = st.columns(2)

        with loc1:
            st.metric(
                "Latitude",
                clean_text(lat, "NA"),
            )

        with loc2:
            st.metric(
                "Longitude",
                clean_text(lon, "NA"),
            )

        if lat != "NA" and lon != "NA":
            st.success(
                "📍 Location captured successfully."
            )

            st.markdown(
                f"[🌍 Open current location in Google Maps]"
                f"(https://www.google.com/maps?q={lat},{lon})"
            )
        else:
            st.warning(
                "Please allow location access in your browser "
                "if GPS capture is required."
            )

        # ----------------------------------------------------
        # CLOCK IN
        # ----------------------------------------------------

        if user_today.empty:
            if st.button(
                "🚀 Punch Clock-In Now",
                key="punch_clock_in",
                type="primary",
                use_container_width=True,
            ):
                sheet, _ = connect_sheet()

                clear_data_cache()

                fresh = prepare_attendance(
                    load_attendance()
                )

                duplicate = (
                    fresh[
                        (fresh["Date"] == today_str)
                        & (fresh["Employee"] == user)
                    ]
                    if not fresh.empty
                    else pd.DataFrame()
                )

                if not duplicate.empty:
                    last_logout = clean_text(
                        duplicate.iloc[-1]["Logout"]
                    )

                    if not last_logout:
                        st.warning(
                            "⚠ You are already clocked in today."
                        )
                        st.stop()

                try:
                    sheet.append_row(
                        [
                            today_str,
                            user,
                            get_ist().strftime(
                                "%H:%M:%S"
                            ),
                            "",
                            "",
                            "In Progress",
                            work_mode,
                            lat,
                            lon,
                            "",
                            "",
                        ]
                    )

                    clear_data_cache()

                    st.success(
                        "✅ Clock-In recorded successfully."
                    )

                    st.rerun()

                except Exception as exc:
                    st.error(
                        f"❌ Clock-In failed: {exc}"
                    )

        # ----------------------------------------------------
        # CLOCK OUT
        # ----------------------------------------------------

        else:
            row = user_today.iloc[-1]

            login = clean_text(
                row["Login"]
            )

            logout = clean_text(
                row["Logout"]
            )

            if not logout:
                st.warning(
                    f"⏳ You are clocked in since "
                    f"**{login}**."
                )

                if st.button(
                    "🛑 Punch Clock-Out Now",
                    key="punch_clock_out",
                    type="primary",
                    use_container_width=True,
                ):
                    sheet, _ = connect_sheet()

                    clear_data_cache()

                    fresh = prepare_attendance(
                        load_attendance()
                    )

                    matches = (
                        fresh[
                            (fresh["Date"] == today_str)
                            & (fresh["Employee"] == user)
                        ]
                        if not fresh.empty
                        else pd.DataFrame()
                    )

                    if matches.empty:
                        st.error(
                            "❌ Active login record not found."
                        )
                        st.stop()

                    idx = matches.index[-1]

                    login = clean_text(
                        fresh.loc[idx, "Login"]
                    )

                    now_str = get_ist().strftime(
                        "%H:%M:%S"
                    )

                    duration, hours_dec = (
                        calculate_duration_str(
                            login,
                            now_str,
                        )
                    )

                    status = determine_attendance_status(
                        hours_dec
                    )

                    row_number = int(idx) + 2

                    try:
                        sheet.update_cell(
                            row_number,
                            4,
                            now_str,
                        )

                        sheet.update_cell(
                            row_number,
                            5,
                            duration,
                        )

                        sheet.update_cell(
                            row_number,
                            6,
                            status,
                        )

                        sheet.update_cell(
                            row_number,
                            10,
                            lat,
                        )

                        sheet.update_cell(
                            row_number,
                            11,
                            lon,
                        )

                        clear_data_cache()

                        st.success(
                            f"✅ Clock-Out recorded. "
                            f"Hours: {duration} · "
                            f"Status: {status}"
                        )

                        st.rerun()

                    except Exception as exc:
                        st.error(
                            f"❌ Clock-Out update failed: {exc}"
                        )

            else:
                st.success(
                    f"🎉 Shift completed · "
                    f"In: {login} · "
                    f"Out: {logout} · "
                    f"Hours: "
                    f"{clean_text(row['Working Hours'], '00:00:00')} · "
                    f"Status: "
                    f"{clean_text(row['Status'], 'Completed')}"
                )

    with c2:
        st.markdown(
            """
            <div class="saas-card">
                <div class="section-title">
                    Shift Policies & Rules
                </div>

                <ul style="
                    font-size:.82rem;
                    color:#64748B;
                    line-height:1.8;
                    padding-left:18px;
                ">
                    <li><b>Shift Start:</b> 09:30 AM</li>
                    <li><b>Grace Period:</b> Up to 09:35 AM</li>
                    <li><b>Early:</b> Before 09:15 AM</li>
                    <li><b>On Time:</b> 09:15 AM – 09:35 AM</li>
                    <li><b>Late:</b> After 09:35 AM</li>
                    <li><b>Full Day:</b> ≥ 8 hours</li>
                    <li><b>Half Day:</b> ≥ 4 hours and &lt; 8 hours</li>
                    <li><b>Short Day:</b> &lt; 4 hours</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# 14. ATTENDANCE RECORDS
# ============================================================

def render_attendance_records(df_att):
    st.markdown(
        "### 📋 Attendance Records"
    )

    df = prepare_attendance(
        df_att
    )

    if st.session_state["role"] != "admin":
        df = df[
            df["Employee"]
            == norm_name(
                st.session_state["employee"]
            )
        ]

    if df.empty:
        st.info(
            "No attendance records found."
        )
        return

    c1, c2, c3 = st.columns(3)

    with c1:
        emp_options = [
            "All Employees"
        ] + sorted(
            df["Employee"]
            .unique()
            .tolist()
        )

        emp_filter = st.selectbox(
            "Employee",
            emp_options,
            key="records_emp_filter",
        )

    with c2:
        status_options = [
            "All Statuses"
        ] + sorted(
            df["Status"]
            .unique()
            .tolist()
        )

        status_filter = st.selectbox(
            "Status",
            status_options,
            key="records_status_filter",
        )

    with c3:
        type_options = [
            "All Types"
        ] + sorted(
            df["Type"]
            .unique()
            .tolist()
        )

        type_filter = st.selectbox(
            "Type",
            type_options,
            key="records_type_filter",
        )

    filtered = df.copy()

    if emp_filter != "All Employees":
        filtered = filtered[
            filtered["Employee"]
            == emp_filter
        ]

    if status_filter != "All Statuses":
        filtered = filtered[
            filtered["Status"]
            == status_filter
        ]

    if type_filter != "All Types":
        filtered = filtered[
            filtered["Type"]
            == type_filter
        ]

    show_cols = [
        c
        for c in [
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
            "Logout Longitude",
        ]
        if c in filtered.columns
    ]

    st.dataframe(
        filtered[show_cols],
        use_container_width=True,
        hide_index=True,
    )

    st.download_button(
        "⬇ Download Filtered CSV",
        data=filtered.to_csv(
            index=False
        ).encode("utf-8"),
        file_name=(
            f"Attendance_Export_"
            f"{datetime.now().strftime('%d%m%Y')}.csv"
        ),
        mime="text/csv",
        key="records_download",
    )


# ============================================================
# 15. EMPLOYEE PROFILE
# ============================================================

def render_employee_profile(df_emp, df_att):
    st.markdown(
        "### 👤 Employee Attendance Profile"
    )

    employees = get_employee_names(
        df_emp,
        df_att,
    )

    if not employees:
        st.info(
            "No employees available."
        )
        return

    if st.session_state["role"] == "admin":
        selected = st.selectbox(
            "Select Employee",
            employees,
            key="profile_employee",
        )
    else:
        selected = norm_name(
            st.session_state["employee"]
        )

    master = (
        df_emp[
            df_emp["Employee Name"]
            .astype(str)
            .map(norm_name)
            == norm_name(selected)
        ]
        if not df_emp.empty
        else pd.DataFrame()
    )

    att = prepare_attendance(
        df_att
    )

    if not att.empty:
        att = att[
            att["Employee"]
            == norm_name(selected)
        ]

    c1, c2 = st.columns(
        [1, 2.5]
    )

    with c1:
        def master_value(
            column,
            fallback="N/A",
        ):
            if (
                not master.empty
                and column in master.columns
            ):
                return clean_text(
                    master.iloc[0][column],
                    fallback,
                )

            return fallback

        st.markdown(
            f"""
            <div class="saas-card">
                <div style="text-align:center;">
                    <div style="font-size:2.7rem;">
                        👤
                    </div>

                    <div style="
                        font-size:1.1rem;
                        font-weight:800;
                        color:#0F172A;
                    ">
                        {html_text(
                            str(selected).title()
                        )}
                    </div>

                    <div class="small-muted">
                        {html_text(
                            master_value(
                                "Designation"
                            )
                        )}
                        ·
                        {html_text(
                            master_value(
                                "Department"
                            )
                        )}
                    </div>
                </div>

                <hr>

                <div class="small-muted">
                    <b>Employee ID:</b>
                    {html_text(
                        master_value(
                            "Employee ID"
                        )
                    )}
                </div>

                <div class="small-muted"
                     style="margin-top:7px;">
                    <b>Manager:</b>
                    {html_text(
                        master_value(
                            "Reporting Manager"
                        )
                    )}
                </div>

                <div class="small-muted"
                     style="margin-top:7px;">
                    <b>Joining Date:</b>
                    {html_text(
                        master_value(
                            "Joining Date"
                        )
                    )}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:
        total = len(att)

        full = (
            int(
                (
                    att["Status"]
                    == "Full Day"
                ).sum()
            )
            if not att.empty
            else 0
        )

        half = (
            int(
                (
                    att["Status"]
                    == "Half Day"
                ).sum()
            )
            if not att.empty
            else 0
        )

        late = (
            int(
                sum(
                    get_lateness_category(
                        value
                    )
                    == "Late"
                    for value
                    in att["Login"].dropna()
                )
            )
            if not att.empty
            else 0
        )

        p1, p2, p3, p4 = st.columns(4)

        p1.metric(
            "Total Shifts",
            total,
        )

        p2.metric(
            "Full Days",
            full,
        )

        p3.metric(
            "Half Days",
            half,
        )

        p4.metric(
            "Late",
            late,
        )

        st.markdown(
            "#### Recent Attendance"
        )

        if att.empty:
            st.info(
                "No attendance records found "
                "for this employee."
            )
        else:
            st.dataframe(
                att[
                    [
                        "Date",
                        "Login",
                        "Logout",
                        "Working Hours",
                        "Status",
                        "Type",
                    ]
                ].sort_values(
                    "Date",
                    ascending=False,
                ),
                use_container_width=True,
                hide_index=True,
            )


# ============================================================
# 16. ANALYTICS
# ============================================================

def render_analytics(df_att):
    st.markdown(
        "### 📈 Workforce Analytics"
    )

    df = prepare_attendance(
        df_att
    )

    if df.empty:
        st.info(
            "No attendance data available "
            "for analytics."
        )
        return

    df["Date_dt"] = pd.to_datetime(
        df["Date"],
        dayfirst=True,
        format="mixed",
        errors="coerce",
    )

    df["Hours"] = (
        df["Working Hours"]
        .map(working_hours_to_decimal)
    )

    df["Month"] = (
        df["Date_dt"]
        .dt
        .strftime("%Y-%m")
    )

    month_options = sorted(
        df["Month"]
        .dropna()
        .unique()
        .tolist(),
        reverse=True,
    )

    if not month_options:
        st.info(
            "No valid dates found."
        )
        return

    selected_month = st.selectbox(
        "Select Month",
        month_options,
        key="analytics_month",
    )

    month_df = df[
        df["Month"]
        == selected_month
    ].copy()

    c1, c2 = st.columns(2)

    with c1:
        status_counts = (
            month_df["Status"]
            .value_counts()
        )

        fig = go.Figure(
            go.Bar(
                x=status_counts.index,
                y=status_counts.values,
                marker_color="#10B981",
                hovertemplate=(
                    "%{x}: %{y}"
                    "<extra></extra>"
                ),
            )
        )

        fig.update_xaxes(
            showgrid=False
        )

        fig.update_yaxes(
            showgrid=True,
            gridcolor="#EEF2F7",
        )

        fig.update_layout(
            title="Monthly Attendance Classification"
        )

        chart_base(fig, 320)

        st.plotly_chart(
            fig,
            use_container_width=True,
            config={
                "displayModeBar": False
            },
        )

    with c2:
        daily = (
            month_df
            .groupby(
                "Date",
                as_index=False,
            )["Hours"]
            .sum()
        )

        fig = go.Figure(
            go.Scatter(
                x=daily["Date"],
                y=daily["Hours"],
                mode="lines+markers",
                line=dict(
                    color="#F5B914",
                    width=3,
                ),
                marker=dict(
                    color="#F5B914",
                    size=6,
                ),
                hovertemplate=(
                    "%{x}: %{y:.1f} hrs"
                    "<extra></extra>"
                ),
            )
        )

        fig.update_xaxes(
            showgrid=False
        )

        fig.update_yaxes(
            showgrid=True,
            gridcolor="#EEF2F7",
        )

        fig.update_layout(
            title="Working Hours Trend"
        )

        chart_base(fig, 320)

        st.plotly_chart(
            fig,
            use_container_width=True,
            config={
                "displayModeBar": False
            },
        )


# ============================================================
# 17. DEPARTMENT ANALYSIS
# ============================================================

def render_department_analysis(
    df_emp,
    df_att,
):
    st.markdown(
        "### 🏢 Department Analysis"
    )

    df = prepare_attendance(
        df_att
    )

    if df.empty:
        st.info(
            "No attendance data available."
        )
        return

    if (
        not df_emp.empty
        and "Department"
        in df_emp.columns
    ):
        master = df_emp[
            [
                "Employee Name",
                "Department",
            ]
        ].copy()

        master["Employee"] = (
            master["Employee Name"]
            .map(norm_name)
        )

        df = df.merge(
            master[
                [
                    "Employee",
                    "Department",
                ]
            ],
            on="Employee",
            how="left",
            suffixes=(
                "",
                "_master",
            ),
        )

        if (
            "Department_master"
            in df.columns
        ):
            df["Department"] = (
                df[
                    "Department_master"
                ]
                .fillna(
                    df.get(
                        "Department",
                        "General",
                    )
                )
            )

            df.drop(
                columns=[
                    "Department_master"
                ],
                inplace=True,
            )

    if "Department" not in df.columns:
        df["Department"] = "General"

    summary = (
        df.groupby("Department")
        .agg(
            Employees=(
                "Employee",
                "nunique",
            ),
            Attendance_Records=(
                "Employee",
                "size",
            ),
            Hours=(
                "Working Hours",
                lambda s: round(
                    s.map(
                        working_hours_to_decimal
                    ).sum(),
                    1,
                ),
            ),
        )
        .reset_index()
        .sort_values(
            "Employees",
            ascending=False,
        )
    )

    st.dataframe(
        summary,
        use_container_width=True,
        hide_index=True,
    )

    fig = go.Figure(
        go.Bar(
            x=summary["Department"],
            y=summary["Employees"],
            marker_color="#10B981",
            hovertemplate=(
                "%{x}: %{y} employees"
                "<extra></extra>"
            ),
        )
    )

    fig.update_xaxes(
        showgrid=False
    )

    fig.update_yaxes(
        showgrid=True,
        gridcolor="#EEF2F7",
    )

    fig.update_layout(
        title="Employees by Department"
    )

    chart_base(fig, 330)

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "displayModeBar": False
        },
    )


# ============================================================
# 18. LOCATION TRACKER
# ============================================================

def render_location_tracker(df_att):
    st.markdown(
        "### 📍 Attendance Location Tracker"
    )

    df = prepare_attendance(
        df_att
    )

    if (
        df.empty
        or "Login Latitude"
        not in df.columns
    ):
        st.info(
            "No GPS attendance data available."
        )
        return

    coords = df[
        [
            "Employee",
            "Date",
            "Login Latitude",
            "Login Longitude",
        ]
    ].copy()

    coords["lat"] = pd.to_numeric(
        coords["Login Latitude"],
        errors="coerce",
    )

    coords["lon"] = pd.to_numeric(
        coords["Login Longitude"],
        errors="coerce",
    )

    coords = coords.dropna(
        subset=[
            "lat",
            "lon",
        ]
    )

    if coords.empty:
        st.info(
            "No valid latitude/longitude "
            "values found."
        )
        return

    st.map(
        coords[
            [
                "lat",
                "lon",
            ]
        ],
        zoom=5,
    )

    st.dataframe(
        coords[
            [
                "Employee",
                "Date",
                "lat",
                "lon",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# 19. LEAVE MANAGEMENT
# ============================================================

def render_leave_management(
    df_leave,
):
    st.markdown(
        "### 🏖️ Leave Management"
    )

    role = st.session_state["role"]

    current_employee = norm_name(
        st.session_state["employee"]
    )

    if role == "employee":
        st.markdown(
            "#### Apply for Leave"
        )

        with st.form(
            "leave_application_form"
        ):
            leave_date = st.date_input(
                "Leave Date",
                datetime.now(
                    IST
                ).date(),
                key="leave_date",
            )

            reason = st.text_area(
                "Reason",
                key="leave_reason",
            )

            submit = (
                st.form_submit_button(
                    "Submit Leave Request",
                    use_container_width=True,
                )
            )

        if submit:
            target_date = (
                leave_date.strftime(
                    "%d-%m-%y"
                )
            )

            existing = (
                df_leave[
                    (
                        df_leave["Employee"]
                        == current_employee
                    )
                    & (
                        df_leave["Date"]
                        == target_date
                    )
                ]
                if not df_leave.empty
                else pd.DataFrame()
            )

            if not existing.empty:
                st.warning(
                    "⚠ Leave is already "
                    "applied for this date."
                )

            elif not clean_text(reason):
                st.warning(
                    "Please enter a leave reason."
                )

            else:
                _, leave_sheet = connect_sheet()

                leave_sheet.append_row(
                    [
                        current_employee,
                        target_date,
                        reason.strip(),
                        "Pending",
                    ]
                )

                clear_data_cache()

                st.success(
                    "✅ Leave request submitted."
                )

                st.rerun()

        st.markdown(
            "#### My Leave Requests"
        )

        mine = df_leave[
            df_leave["Employee"]
            == current_employee
        ]

        st.dataframe(
            mine,
            use_container_width=True,
            hide_index=True,
        )

    else:
        st.markdown(
            "#### Pending Leave Requests"
        )

        pending = df_leave[
            df_leave["Status"]
            .astype(str)
            .str.strip()
            .str.upper()
            == "PENDING"
        ].copy()

        if pending.empty:
            st.success(
                "No pending leave requests."
            )
            return

        _, leave_sheet = connect_sheet()

        all_values = (
            leave_sheet.get_all_values()
        )

        for idx, row in pending.iterrows():
            st.markdown(
                '<div class="saas-card">',
                unsafe_allow_html=True,
            )

            c1, c2, c3 = st.columns(
                [3, 2, 2]
            )

            with c1:
                st.write(
                    f"**{row['Employee'].title()}**"
                )

                st.caption(
                    clean_text(
                        row["Reason"],
                        "No reason provided",
                    )
                )

            with c2:
                st.write(
                    f"Date: **{row['Date']}**"
                )

                st.caption(
                    "Status: Pending"
                )

            with c3:
                approve_key = (
                    f"approve_leave_{idx}"
                )

                reject_key = (
                    f"reject_leave_{idx}"
                )

                sheet_row = None

                for rno, values in enumerate(
                    all_values[1:],
                    start=2,
                ):
                    values = values + [
                        ""
                    ] * max(
                        0,
                        4 - len(values),
                    )

                    if (
                        norm_name(
                            values[0]
                        )
                        == norm_name(
                            row["Employee"]
                        )
                        and date_key(
                            values[1]
                        )
                        == date_key(
                            row["Date"]
                        )
                        and clean_text(
                            values[2]
                        )
                        == clean_text(
                            row["Reason"]
                        )
                        and clean_text(
                            values[3]
                        ).upper()
                        == "PENDING"
                    ):
                        sheet_row = rno
                        break

                b1, b2 = st.columns(2)

                with b1:
                    if st.button(
                        "Approve",
                        key=approve_key,
                        use_container_width=True,
                    ):
                        if sheet_row:
                            leave_sheet.update_cell(
                                sheet_row,
                                4,
                                "Approved",
                            )

                            # Preserve existing behavior:
                            # approved leave is also reflected
                            # in the AttendanceData sheet.
                            attendance_sheet, _ = connect_sheet()

                            clear_data_cache()

                            fresh_att = (
                                prepare_attendance(
                                    load_attendance()
                                )
                            )

                            leave_date = date_key(
                                row["Date"]
                            )

                            leave_employee = (
                                norm_name(
                                    row["Employee"]
                                )
                            )

                            existing_leave_att = (
                                fresh_att[
                                    (
                                        fresh_att["Date"]
                                        == leave_date
                                    )
                                    & (
                                        fresh_att["Employee"]
                                        == leave_employee
                                    )
                                ]
                                if not fresh_att.empty
                                else pd.DataFrame()
                            )

                            if existing_leave_att.empty:
                                attendance_sheet.append_row(
                                    [
                                        leave_date,
                                        leave_employee,
                                        "",
                                        "",
                                        "",
                                        "Leave",
                                        "Leave",
                                        "",
                                        "",
                                        "",
                                        "",
                                    ]
                                )

                            clear_data_cache()

                            st.success(
                                "Leave approved and reflected "
                                "in attendance."
                            )

                            st.rerun()

                        else:
                            st.error(
                                "Could not locate "
                                "the leave row."
                            )

                with b2:
                    if st.button(
                        "Reject",
                        key=reject_key,
                        use_container_width=True,
                    ):
                        if sheet_row:
                            leave_sheet.update_cell(
                                sheet_row,
                                4,
                                "Rejected",
                            )

                            clear_data_cache()

                            st.warning(
                                "Leave rejected."
                            )

                            st.rerun()

                        else:
                            st.error(
                                "Could not locate "
                                "the leave row."
                            )

            st.markdown(
                "</div>",
                unsafe_allow_html=True,
            )


# ============================================================
# 20. REPORTS
# ============================================================

def render_reports(
    df_att,
    df_leave,
):
    st.markdown(
        "### 📑 Reports & Export"
    )

    c1, c2 = st.columns(2)

    with c1:
        st.markdown(
            """
            <div class="saas-card">
                <div class="section-title">
                    Attendance Report
                </div>

                <div class="small-muted">
                    Complete historical attendance,
                    login/logout and working hours.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.download_button(
            "⬇ Download Attendance CSV",
            data=df_att.to_csv(
                index=False
            ).encode("utf-8"),
            file_name="Attendance_Report.csv",
            mime="text/csv",
            key="download_attendance_report",
            use_container_width=True,
        )

    with c2:
        st.markdown(
            """
            <div class="saas-card">
                <div class="section-title">
                    Leave Report
                </div>

                <div class="small-muted">
                    Leave applications
                    and approval status.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.download_button(
            "⬇ Download Leave CSV",
            data=df_leave.to_csv(
                index=False
            ).encode("utf-8"),
            file_name="Leave_Report.csv",
            mime="text/csv",
            key="download_leave_report",
            use_container_width=True,
        )

    st.divider()

    if df_att.empty:
        return

    df = prepare_attendance(
        df_att
    )

    df["Month"] = pd.to_datetime(
        df["Date"],
        dayfirst=True,
        format="mixed",
        errors="coerce",
    ).dt.strftime(
        "%Y-%m"
    )

    months = sorted(
        df["Month"]
        .dropna()
        .unique()
        .tolist(),
        reverse=True,
    )

    if months:
        selected_month = st.selectbox(
            "Report Month",
            months,
            key="report_month",
        )

        month_df = df[
            df["Month"]
            == selected_month
        ]

        st.dataframe(
            month_df,
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# 21. ADMIN CONTROL PANEL
# ============================================================

def render_admin_panel(
    df_att,
    df_emp,
):
    st.markdown(
        "### ⚙️ Admin Control Panel"
    )

    st.markdown(
        """
        <div class="saas-card">
            <div class="section-title">
                Google Sheets Connection
            </div>

            <div class="small-muted">
                Attendance data is stored in
                <b>AttendanceData</b> and leave data in
                the <b>Leave</b> worksheet.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    try:
        connect_sheet()

        st.success(
            "🟢 Google Sheets API: Connected & Live"
        )

    except Exception:
        st.warning(
            "🟡 Google Sheets API: Connection unavailable"
        )

    st.divider()

    with st.expander(
        "🛠️ Manual Attendance Data Editor"
    ):
        edited = st.data_editor(
            df_att,
            num_rows="dynamic",
            use_container_width=True,
            key="admin_attendance_editor",
        )

        if st.button(
            "💾 Save Attendance Changes",
            key="save_admin_attendance",
        ):
            try:
                save_attendance_dataframe(
                    edited
                )

                st.success(
                    "✅ Attendance database updated."
                )

                st.rerun()

            except Exception as exc:
                st.error(
                    f"❌ Save failed: {exc}"
                )

    with st.expander(
        "🧹 Attendance Maintenance"
    ):
        confirm = st.checkbox(
            "I understand these actions modify attendance records.",
            key="confirm_admin_maintenance",
        )

        c1, c2 = st.columns(2)

        with c1:
            if st.button(
                "Remove Duplicate Entries",
                key="remove_duplicates",
                disabled=not confirm,
                use_container_width=True,
            ):
                if df_att.empty:
                    st.info(
                        "No attendance records found."
                    )
                else:
                    clean_df = (
                        df_att
                        .drop_duplicates()
                        .copy()
                    )

                    removed = (
                        len(df_att)
                        - len(clean_df)
                    )

                    save_attendance_dataframe(
                        clean_df
                    )

                    st.success(
                        f"✅ Removed {removed} "
                        "duplicate records."
                    )

                    st.rerun()

        with c2:
            if st.button(
                "Clear All Attendance",
                key="clear_all_attendance",
                disabled=not confirm,
                use_container_width=True,
            ):
                try:
                    sheet, _ = connect_sheet()

                    sheet.clear()

                    sheet.append_row(
                        ATTENDANCE_HEADERS
                    )

                    clear_data_cache()

                    st.success(
                        "✅ Attendance sheet cleared."
                    )

                    st.rerun()

                except Exception as exc:
                    st.error(
                        f"❌ Clear failed: {exc}"
                    )

    st.divider()

    st.markdown(
        "#### Employee Master Preview"
    )

    st.dataframe(
        df_emp,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# 22. APPLICATION ENTRY POINT
# ============================================================

def main():
    df_emp = load_employee_master()

# ============================================================
# ✅ SESSION STATE INITIALIZATION
# ============================================================
if "page" not in st.session_state:
    st.session_state["page"] = "Dashboard"  # set to your default starting page

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if "role" not in st.session_state:
    st.session_state["role"] = ""

if "employee" not in st.session_state:
    st.session_state["employee"] = ""

    st.session_state["users"] = build_users(
        df_emp
    )

    if not st.session_state["logged_in"]:
        render_login_page()
        return

    df_att = load_attendance()
    df_leave = load_leave()

    render_sidebar()

    # 👈 PUT THE NEW DYNAMIC HEADER HERE

    # THEN CONTINUE
    # ✅ Safely returns "Dashboard" (or your default page name) if not set
    page = st.session_state.get("page", "Dashboard")

    if page == "📊 Dashboard":
        render_dashboard(...)

        render_brand_header(
            st.session_state["employee"],
            st.session_state["role"],
        )

# ============================================================
# PASTE DYNAMIC HEADER HERE
# ============================================================

now_ist = get_ist()
current_hour = now_ist.hour

if current_hour < 12:
    greeting = "Good Morning"
elif current_hour < 17:
    greeting = "Good Afternoon"
else:
    greeting = "Good Evening"

formatted_date = now_ist.strftime("%A, %d %B %Y")

user_display_name = str(
    st.session_state.get("employee", "ADMIN")
).strip().title()

user_role_display = str(
    st.session_state.get("role", "Admin")
).strip().title()

st.markdown(
    f"""
    <div style="
        display:flex;
        justify-content:space-between;
        align-items:center;
        background:linear-gradient(
            135deg,
            #0F172A 0%,
            #1E293B 100%
        );
        padding:16px 24px;
        border-radius:14px;
        border:1px solid rgba(255,255,255,0.08);
        box-shadow:0 4px 20px rgba(0,0,0,0.15);
        margin-bottom:20px;
    ">

        <div>
            <h3 style="
                margin:0;
                color:#FFFFFF;
                font-size:1.25rem;
                font-weight:700;
            ">
                Lancers Risk Consulting
            </h3>

            <p style="
                margin:2px 0 0 0;
                color:#94A3B8;
                font-size:0.82rem;
            ">
                Enterprise Attendance & Workforce Analytics
            </p>
        </div>

        <div style="text-align:right;">

            <div style="
                color:#FFFFFF;
                font-weight:700;
                font-size:0.95rem;
            ">
                {greeting}, {user_display_name} 👋
            </div>

            <div style="
                color:#94A3B8;
                font-size:0.78rem;
                margin-top:2px;
            ">
                {formatted_date} · Role:
                <span style="
                    color:#7DD3FC;
                    font-weight:600;
                    background:rgba(56,189,248,0.15);
                    padding:2px 8px;
                    border-radius:6px;
                ">
                    {user_role_display}
                </span>
            </div>

        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# EXISTING PAGE LOGIC CONTINUES
# ============================================================

page = st.session_state["page"]
if page == "📊 Dashboard":
    render_dashboard(
        df_emp,
        df_att,
        df_leave,
    )

elif page == "⏱️ Clock In / Out":
        render_clock_in_out(
            df_att
        )

elif page == "📋 Attendance Records":
        render_attendance_records(
            df_att
        )

elif page == "👤 Employee Profile":
        render_employee_profile(
            df_emp,
            df_att,
        )

elif page == "🏖️ Leave Management":
        render_leave_management(
            df_leave
        )

elif page == "📈 Analytics":
        render_analytics(
            df_att
        )

elif page == "🏢 Department Analysis":
        if st.session_state["role"] == "admin":
            render_department_analysis(
                df_emp,
                df_att,
            )
        else:
            st.error(
                "🔒 Admin access required."
            )

elif page == "📍 Location Tracker":
        if st.session_state["role"] == "admin":
            render_location_tracker(
                df_att
            )
        else:
            st.error(
                "🔒 Admin access required."
            )

elif page == "📑 Reports & Export":
        render_reports(
            df_att,
            df_leave,
        )

elif page == "⚙️ Admin Control Panel":
        if st.session_state["role"] == "admin":
            render_admin_panel(
                df_att,
                df_emp,
            )
        else:
            st.error(
                "🔒 Admin access required."
            )


if __name__ == "__main__":
    main()