import streamlit as st
from streamlit_geolocation import streamlit_geolocation
import streamlit.components.v1 as components
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, date, timezone
import pytz
import os
import time

# ============================================================
# ✅ PAGE CONFIG (MUST BE FIRST STREAMLIT COMMAND)
# ============================================================

st.set_page_config(
    page_title="Attendance Management System",
    layout="wide"
)
# ============================================================
# ✅ APP STYLING (BACKGROUND + UI)
# ============================================================

from datetime import datetime, date, timezone
import pytz
import os
import time

# ✅ Auto refresh every 5 seconds
if "last_refresh" not in st.session_state:
    st.session_state["last_refresh"] = time.time()

current_time = time.time()

if current_time - st.session_state["last_refresh"] > 5:
    st.session_state["last_refresh"] = current_time
    st.rerun()

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

    utc_now = datetime.now(timezone.utc)

    ist = pytz.timezone("Asia/Kolkata")

    return utc_now.astimezone(ist)

# ============================================================
# ✅ LOAD ATTENDANCE
# ============================================================
@st.cache_data(ttl=2)
def load_attendance():

    sheet, _ = connect_sheet()

    data = sheet.get_all_records()

    if not data:
        return pd.DataFrame(columns=[
            
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

    return pd.DataFrame(data)

df = load_attendance()
df.columns = df.columns.str.strip()

df["Date"] = pd.to_datetime(
    df["Date"], errors="coerce"
).dt.strftime("%Y-%m-%d")

# ============================================================
# ✅ LOAD LEAVE
# ============================================================
def load_leave():

    _, leave_sheet = connect_sheet()

    data = leave_sheet.get_all_records()

    if not data:
        return pd.DataFrame(columns=[
            "Employee",
            "Date",
            "Reason",
            "Status"
        ])

    return pd.DataFrame(data)

# ============================================================
# ✅ SESSION STATE
# ============================================================
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

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

    username = st.text_input("Username")

    password = st.text_input(
        "Password",
        type="password"
    )

    if st.button("Login"):

        if username in users and users[username]["password"] == password:

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
if st.button("Logout"):

    st.session_state.clear()

    st.rerun()

role = st.session_state["role"]

employee = st.session_state["employee"]

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
        today
    )

else:

    selected_date = st.date_input(
        "Attendance Date",
        today
    )

date_str = selected_date.strftime("%Y-%m-%d")

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
# ✅ ATTENDANCE TYPE
# ============================================================
attendance_type = st.selectbox(
    "Attendance Type",
    [
        "Present WFO",
        "Present WFH",
        "Half Day",
        "Leave"
    ]
)

# ============================================================
# ✅ ACTION BUTTONS
# ============================================================

col1, col2, col3 = st.columns(3)

# ============================================================
# ✅ LOGIN ATTENDANCE
# ============================================================

with col1:

    if st.button("🟢 Login Attendance", key="login_att_btn"):

        lat, lon = get_location_values()

        sheet, _ = connect_sheet()

        # ✅ Load latest attendance
        df = load_attendance()

        # ✅ Clean dataframe
        df.columns = df.columns.str.strip()

        # ✅ Normalize Date
        df["Date"] = pd.to_datetime(
            df["Date"],
            errors="coerce"
        ).dt.strftime("%Y-%m-%d")

        # ✅ Current Date & Time
        date_str = selected_date.strftime("%Y-%m-%d")

        login_time_str = get_ist().strftime("%H:%M:%S")

        # ====================================================
        # ✅ CHECK EXISTING LOGIN
        # ====================================================

        existing_today = df[
            (df["Date"] == date_str) &
            (df["Employee"] == employee)
        ]

        # ✅ Prevent duplicate only if logout pending
        if not existing_today.empty:

            last_logout = str(
                existing_today.iloc[-1]["Logout"]
            ).strip()

            if last_logout in ["", "nan", "None"]:

                st.warning("⚠ Already logged in today")

                st.stop()

        # ====================================================
        # ✅ SAVE LOGIN
        # ====================================================

        sheet.append_row([
            date_str,
            employee,
            login_time_str,
            "",
            "",
            "In Progress",
            attendance_type,
            lat,
            lon,
            "",
            ""
        ])

        # ✅ Clear cache
        load_attendance.clear()

        st.success(
            f"✅ Login Recorded Successfully 📍 {lat}, {lon}"
        )

        # ✅ Refresh immediately
        st.rerun()

# ============================================================
# ✅ LOGOUT ATTENDANCE
# ============================================================

with col2:
    if st.button("🔴 Logout Attendance"):

        lat, lon = get_location_values()
        sheet, _ = connect_sheet()

        df = load_attendance()
        df.columns = df.columns.str.strip()

        df["Date"] = pd.to_datetime(
            df["Date"],
            errors="coerce"
        ).dt.strftime("%Y-%m-%d")

        # ✅ FIXED
        today_date = selected_date.strftime("%Y-%m-%d")

        user_today = df[
            (df["Date"] == today_date) &
            (df["Employee"] == employee)
        ]

        if user_today.empty:
            st.warning("⚠ No login record found")
            st.stop()

# Continue normally
    last_index = user_today.index[-1]

login_str = str(
    user_today.iloc[-1]["Login"]
)

login_time = pd.to_datetime(
    f"{today_date} {login_str}",
            errors="coerce"
)

logout_time = pd.to_datetime(
    get_ist()
)

if pd.isna(login_time):

    st.error("❌ Invalid login time")

    st.stop()

existing_logout = str(
        user_today.iloc[-1]["Logout"]
).strip()

if existing_logout not in ["", "nan", "None"]:

    st.warning("⚠ Logout already completed")

    st.stop()

time_diff = logout_time - login_time

working_hours = str(
    time_diff
).split(".")[0]

total_hours = (
    time_diff.total_seconds() / 3600
)

if total_hours >= 8:
    status = "Full Day"

elif total_hours >= 4:
    status = "Half Day"

else:
    status = "Short Day"

row_number = last_index + 2

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

load_attendance.clear()

st.success(
            f"""
✅ Logout Recorded Successfully

📍 Logout Location: {lat}, {lon}

⏱ Working Hours: {working_hours}

📌 Status: {status}
"""
        )

st.rerun()

# ============================================================
# ✅ TODAY'S ATTENDANCE
# ============================================================

st.subheader("📋 Today's Attendance")

df_today = load_attendance()

df_today.columns = df_today.columns.str.strip()

df_today["Date"] = pd.to_datetime(
    df_today["Date"],
    errors="coerce"
).dt.strftime("%Y-%m-%d")

today_date = date.today().strftime("%Y-%m-%d")

if role == "admin":

    today_data = df_today[
        df_today["Date"] == today_date
    ]

else:

    today_data = df_today[
        (df_today["Date"] == today_date) &
        (df_today["Employee"] == employee)
    ]

if not today_data.empty:

    display_df = today_data.copy()

    display_df["Login"] = pd.to_datetime(
        display_df["Login"],
        errors="coerce"
    ).dt.strftime("%H:%M:%S")

    display_df["Logout"] = pd.to_datetime(
        display_df["Logout"],
        errors="coerce"
    ).dt.strftime("%H:%M:%S")

    display_df["Logout"] = display_df[
        "Logout"
    ].fillna("Pending")

    st.dataframe(
        display_df[
            [
                "Employee",
                "Login",
                "Logout",
                "Working Hours",
                "Status",
                "Type"
            ]
        ],
        use_container_width=True
    )

else:

    st.info("No attendance recorded today.")

# ============================================================
# ✅ ADMIN CONTROLS
# ============================================================

st.divider()

if role == "admin":

    st.markdown("### ⚠️ Admin Controls")

    # ✅ STEP 1 — Confirmation Checkbox
    confirm_clear = st.checkbox(
        "Confirm Clear Attendance",
        key="confirm_clear_attendance"
    )

    # ✅ STEP 2 — Action Button
    if confirm_clear:

        if st.button("🧹 Clear Attendance", key="clear_attendance_btn"):

            try:
                sheet, _ = connect_sheet()

                # ✅ Clear whole sheet
                sheet.clear()

                # ✅ Recreate headers (VERY IMPORTANT)
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

                # ✅ CLEAR CACHE
                load_attendance.clear()

                st.success("✅ Attendance Cleared Successfully")

                st.rerun()

            except Exception as e:
                st.error(f"❌ Error clearing attendance: {e}")

if st.button("🧹 Remove Duplicate Entries", key="remove_duplicates_btn"):

    st.write("✅ Button Clicked")
    sheet, _ = connect_sheet()
    df = load_attendance()
    
    df.columns = df.columns.str.strip()

    df["Date"] = pd.to_datetime(
    df["Date"], errors="coerce"
    ).dt.strftime("%Y-%m-%d")
    if df.empty:
        st.warning("No data found in sheet")
        st.stop()

    # ✅ FORCE Date format (THIS IS THE MAIN FIX ✅)
    df["Date"] = df["Date"].astype(str).str[:10]

    # ✅ Convert Login to datetime
    df["Login"] = pd.to_datetime(df["Login"], errors="coerce")

    # ✅ Sort so latest login comes last
    df = df.sort_values(by=["Employee", "Date", "Login"])

    # ✅ Remove duplicates → keep last (latest login)
    # Prefer completed records (those with Logout)
    df_clean = (
    df.sort_values(
        by=["Employee", "Date", "Logout"],
        na_position="first"
    )
    .groupby(["Employee", "Date"], as_index=False)
    .last()
)

    # ✅ Convert Login back to string
    df_clean["Login"] = df_clean["Login"].astype(str)

    # ✅ Clear sheet
    sheet.clear()

    # ✅ Convert dataframe to list of lists
    data_to_write = [
        df_clean.columns.tolist()
    ] + df_clean.values.tolist()

    # ✅ Write entire sheet at once (VERY IMPORTANT)
    sheet.update("A1", data_to_write)
    
    load_attendance.clear()

    st.success("✅ Duplicate entries removed successfully")
# ============================================================
# ✅ LEAVE MANAGEMENT
# ============================================================
st.subheader("📩 Leave Management")

leave_df = load_leave()

# ============================================================
# ✅ EMPLOYEE LEAVE
# ============================================================
if role == "employee":

    colA, colB = st.columns(2)

    with colA:

        start_date = st.date_input(
            "Leave From",
            today,
            min_value=today
        )

    with colB:

        end_date = st.date_input(
            "Leave To",
            start_date,
            min_value=start_date
        )

    reason = st.text_input("Leave Reason")

    if st.button("Submit Leave"):

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

                d_str = d.strftime("%Y-%m-%d")

                duplicate = leave_df[
                    (leave_df["Employee"] == employee) &
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

            if added:
                st.success("✅ Leave Submitted")

            else:
                st.warning("⚠ Leave Already Applied")

    st.subheader("My Leave Requests")

    leave_df = load_leave()

    st.dataframe(
        leave_df[leave_df["Employee"] == employee]
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

                if st.button(f"Approve {i}"):

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

                    st.success("✅ Leave Approved")

                    st.rerun()

            with c2:

                if st.button(f"Reject {i}"):

                    _, leave_sheet = connect_sheet()

                    row_num = i + 2

                    leave_sheet.update_cell(
                        row_num,
                        4,
                        "Rejected"
                    )

                    st.warning("❌ Leave Rejected")

                    st.rerun()

# ============================================================
# ✅ ATTENDANCE RECORDS
# ============================================================
st.subheader("📋 Attendance Records")

df = load_attendance()

df.columns = df.columns.str.strip()

df["Date"] = pd.to_datetime(
    df["Date"],
    errors="coerce"
).dt.strftime("%Y-%m-%d")

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
                sorted(df["Employee"].dropna().unique())
            )

        with f2:

            date_filter = st.date_input(
                "Filter Date",
                None
            )

        if emp_filter != "All":

            df = df[
                df["Employee"] == emp_filter
            ]

        if date_filter:

            df = df[
                df["Date"] ==
                date_filter.strftime("%Y-%m-%d")
            ]

    # ========================================================
    # EMPLOYEE FILTER
    # ========================================================
    if role == "employee":

        df = df[
            df["Employee"] == employee
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


# ✅ Employee filter with col2:
employee_list = ["All"] + sorted(df["Employee"].dropna().astype(str).unique())

selected_employee = st.selectbox(
    "👤 Select Employee",
    employee_list,
    key="employee_filter_unique"
)

# ========================================================
# ✅ FILTERS (FIXED ALIGNMENT)
# ========================================================

col1, col2 = st.columns(2)

with col1:
    months = ["All"] + sorted(df["Month"].dropna().unique())
    selected_month = st.selectbox(
        "📅 Select Month",
        months
    )

with col2:
    employee_list = ["All"] + sorted(
        df["Employee"].dropna().astype(str).unique()
    )

    selected_employee = st.selectbox(
        "👤 Select Employee",
        employee_list,
        key="employee_filter_unique"
    )

# ✅ Safe copy
monthly_df = monthly_df.copy()
# ============================================================
# ✅ CLEANING FIXES
# ============================================================

monthly_df["Date"] = pd.to_datetime(
    monthly_df["Date"],
    errors="coerce"
).dt.strftime("%Y-%m-%d")

monthly_df["Logout"] = monthly_df[
    "Logout"
].replace("None", "Pending")
# ============================================================
# ✅ SUMMARY
# ============================================================

st.markdown("### 📊 Summary")

if not monthly_df.empty:

    total_records = len(monthly_df)

    status_counts = (
        monthly_df["Status"]
        .astype(str)
        .str.strip()
        .value_counts()
    )

    full_days = status_counts.get("Full Day", 0)

    half_days = status_counts.get("Half Day", 0)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "📋 Total Records",
            total_records
        )

    with col2:
        st.metric(
            "✅ Full Days",
            full_days
        )

    with col3:
        st.metric(
            "⏱ Half Days",
            half_days
        )

else:

    st.info(
        "⚠ No data available for selected filters"
    )

# ============================================================
# ✅ DISPLAY RESULT
# ============================================================

def highlight_status(val):

    if val == "Full Day":
        return "background-color: #d4edda"

    elif val == "Half Day":
        return "background-color: #fff3cd"

    elif val == "Absent":
        return "background-color: #f8d7da"

    else:
        return ""

# ============================================================
# ✅ APPLY STYLING
# ============================================================

if not monthly_df.empty:

    styled_df = monthly_df.style.map(
        highlight_status,
        subset=["Status"]
    )

    st.dataframe(
        styled_df,
        use_container_width=True
    )

else:

    st.info(
        "⚠ No data available for selected filters"
    )
# ============================================================
# ✅ MONTHLY ATTENDANCE REPORT (FINAL CLEAN VERSION)
# ============================================================

st.subheader("📅 Monthly Attendance Report")

# ✅ Load data (IMPORTANT ✅)
df = load_attendance()
df.columns = df.columns.str.strip()

df["Date"] = pd.to_datetime(
    df["Date"], errors="coerce"
).dt.strftime("%Y-%m-%d")
# ✅ Check if data exists
if df.empty:
    st.info("⚠ No attendance data found")
    st.stop()

# ✅ Ensure Date column exists
if "Date" not in df.columns:
    st.error("❌ Date column missing in data")
    st.stop()

# ========================================================
# ✅ PREPARE DATA (FINAL VERSION ✅)
# ========================================================

df = load_attendance()

df.columns = df.columns.str.strip()

# ✅ Convert Date safely
df["Date"] = pd.to_datetime(
    df["Date"],
    errors="coerce"
)

# ✅ Create Month column
df["Month"] = df["Date"].dt.strftime("%Y-%m")

# ========================================================
# ✅ FILTERS
# ========================================================

col1, col2 = st.columns(2)

# ✅ Month filter
with col1:
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
with col2:
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
monthly_df["Date"] = pd.to_datetime(monthly_df["Date"]).dt.strftime("%Y-%m-%d")
monthly_df["Logout"] = monthly_df["Logout"].replace("None", "Pending")

st.divider()

# ============================================================
# ✅ DASHBOARD SUMMARY (KPI CARDS)
# ============================================================

st.markdown("### 📊 Summary")

total_records = len(monthly_df)
full_days = len(monthly_df[monthly_df["Status"] == "Full Day"])
half_days = len(monthly_df[monthly_df["Status"] == "Half Day"])

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("📋 Total Records", total_records)

with col2:
    st.metric("✅ Full Days", full_days)

with col3:
    st.metric("⏱ Half Days", half_days)

st.divider()


# ============================================================
# ✅ TABLE + DOWNLOAD
# ============================================================

if not monthly_df.empty:

    st.markdown("### 📅 Attendance Details")

    # ✅ Show entries dropdown
    entries = st.selectbox(
        "Show entries",
        [10, 25, 50, 100],
        index=0,
        key="entries_month"
    )

    display_df = monthly_df.head(entries)

    # ✅ Show table
    st.dataframe(display_df, use_container_width=True)

    st.divider()

    # ✅ Download monthly report
    st.download_button(
        label="⬇ Download Monthly Report",
        data=monthly_df.to_csv(index=False).encode("utf-8"),
        file_name=f"attendance_{selected_month}.csv",
        mime="text/csv",
        key="download_monthly_report"
    )

else:
    st.info("⚠ No data available for selected month")


# ============================================================
# ✅ FULL DOWNLOAD (ALL DATA)
# ============================================================

st.markdown("### 📥 Download Full Data")

st.download_button(
    label="📥 Download Full Attendance",
    data=df.to_csv(index=False).encode("utf-8"),
    file_name="attendance_full.csv",
    mime="text/csv",
    key="download_full_attendance"
)