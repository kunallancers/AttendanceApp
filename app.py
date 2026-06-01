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
# ✅ APP STYLING (BACKGROUND + UI)
# ============================================================

st.markdown("""
<style>
    /* Main background */
    .stApp {
        background-color: #F4F6F7;
    }

    /* Remove padding for top header */
    .block-container {
        padding-top: 2rem;
    }

    /* Style buttons */
    .stButton > button {
        background-color: #2E86C1;
        color: white;
        border-radius: 8px;
        padding: 0.5em 1em;
        border: none;
    }

    /* Hover effect */
    .stButton > button:hover {
        background-color: #1B4F72;
    }

    /* Selectbox styling */
    .stSelectbox div {
        border-radius: 8px;
    }

</style>
""", unsafe_allow_html=True)
# ✅ Auto refresh every 5 seconds
if "last_refresh" not in st.session_state:
    st.session_state["last_refresh"] = time.time()

current_time = time.time()

if current_time - st.session_state["last_refresh"] > 5:
    st.session_state["last_refresh"] = current_time
    st.rerun()
# ✅ Initialize session for location
if "location" not in st.session_state:
    st.session_state["location"] = None


# ✅ Function to fetch location
def get_location():
    location_js = """
    <script>
    function sendLocation() {
        navigator.geolocation.getCurrentPosition(
            (position) => {
                const lat = position.coords.latitude;
                const lon = position.coords.longitude;
                const data = lat + "," + lon;
                window.parent.postMessage(data, "*");
            }
        );
    }
    sendLocation();
    </script>
    """

    components.html(location_js, height=0)
    
# ✅ Save location

# ============================================================
# ✅ PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="Attendance Management System",
    layout="wide"
)

# ============================================================
# ✅ GOOGLE SHEET CONNECTION
# ============================================================
import streamlit as st

from oauth2client.service_account import ServiceAccountCredentials
import gspread

def connect_sheet():

    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    creds_dict = st.secrets["gcp_service_account"]

    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        creds_dict, scope
    )

    client = gspread.authorize(creds)

    sheet = client.open("AttendanceData").sheet1
    leave_sheet = client.open("AttendanceData").worksheet("Leave")

    return sheet, leave_sheet
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
            "Type"
        ])

    return pd.DataFrame(data)

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

# ============================================================
# ✅ HEADER + LOCATION (FINAL CLEAN STRUCTURE)
# ============================================================

st.markdown("""
<h1 style='text-align: center; color: #2E86C1;'>📊 Attendance Management Dashboard</h1>
<hr>
""", unsafe_allow_html=True)

st.markdown(f"<h4 style='text-align: center;'>Welcome, {employee}</h4>", unsafe_allow_html=True)
# ============================================================
# ✅ LOGIN SECTION (ADMIN + USER)
# ============================================================

ADMIN_USERS = ["ADMIN"]

login_user = st.text_input("Enter Your ID (ADMIN/User)")

df = load_attendance()

employee_list = []
if not df.empty and "Employee" in df.columns:
    employee_list = sorted(df["Employee"].dropna().unique())

# ✅ IMPORTANT: show dropdown BEFORE clicking login (better UX)
selected_employee = None
if login_user.upper() in ADMIN_USERS:
    selected_employee = st.selectbox(
        "Select Employee",
        employee_list,
        key="admin_employee_select"
    )

# ✅ Login button
if st.button("Login"):

    if login_user.upper() in ADMIN_USERS:
        st.session_state["employee"] = login_user
        st.session_state["selected_employee"] = selected_employee

    else:
        if login_user:
            st.session_state["employee"] = login_user
            st.session_state["selected_employee"] = login_user


# ✅ Stop if not logged in
if "employee" not in st.session_state:
    st.warning("⚠ Please login to continue")
    st.stop()

employee = st.session_state["employee"]
selected_employee = st.session_state["selected_employee"]

# ✅ Nice layout for login status + logout
col1, col2 = st.columns([6,1])

with col1:
    st.success(f"✅ Logged in as: {employee}")

with col2:
    if st.button("Logout"):
        del st.session_state["employee"]
        del st.session_state["selected_employee"]
        st.rerun()
# ============================================================
# ✅ GEOLOCATION SECTION
# ============================================================

location = streamlit_geolocation()

if location:
    st.success("📍 Location captured successfully ✅")
    st.write(f"Latitude: {location['latitude']}")
    st.write(f"Longitude: {location['longitude']}")


# ============================================================
# ✅ MONTHLY REPORT
# ============================================================

st.subheader("📅 Monthly Attendance Report")

# ✅ Load data
df = load_attendance()

if df.empty:
    st.info("⚠ No attendance data found")
    st.stop()

# ✅ Ensure Date exists
if "Date" not in df.columns:
    st.error("❌ Date column missing")
    st.stop()

# ✅ Create Month column
df["Month"] = pd.to_datetime(df["Date"], errors="coerce").dt.strftime("%Y-%m")

# ✅ Filters
col1, col2 = st.columns(2)

with col1:
    selected_month = st.selectbox(
        "📅 Select Month",
        sorted(df["Month"].dropna().unique(), reverse=True),
        key="month_filter"
    )

with col2:
    search = st.text_input("👤 Search Employee")

# ✅ Filter data
monthly_df = df[df["Month"] == selected_month]

if search:
    monthly_df = monthly_df[
        monthly_df["Employee"].astype(str).str.contains(search, case=False, na=False)
    ]

# ✅ Display
if not monthly_df.empty:
    st.dataframe(monthly_df, use_container_width=True)
else:
    st.info("⚠ No data available for selected month")
# ============================================================
# ✅ STEP 1: INITIAL LOAD (RUNS FIRST TIME)
# ============================================================
if "location" not in st.session_state:
    location = streamlit_geolocation()

    if location and location.get("latitude") and location.get("longitude"):
        lat = str(location["latitude"])
        lon = str(location["longitude"])
        st.session_state["location"] = f"{lat},{lon}"

# ============================================================
# ✅ STEP 2: MAIN LOCATION FETCH (ALWAYS RUNS)
# ============================================================
location = streamlit_geolocation()

if location and location.get("latitude") and location.get("longitude"):
    lat = str(location["latitude"])
    lon = str(location["longitude"])

    # ✅ Update latest location
    st.session_state["location"] = f"{lat},{lon}"

else:
    loc = st.session_state.get("location", "NA,NA")
    try:
        lat, lon = loc.split(",")
    except:
        lat, lon = "NA", "NA"

# ============================================================
# ✅ STEP 3: DISPLAY LOCATION
# ============================================================
st.write("📍 Current Location:")
st.write(f"Latitude: {lat}")
st.write(f"Longitude: {lon}")

# ✅ Google Maps link
if lat != "NA" and lon != "NA":
    st.markdown(f"https://www.google.com/maps?q={lat},{lon}")

# ✅ Status message
if lat != "NA":
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
        sorted(df_emp["Employee Name"].unique())
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

    if st.button("🟢 Login Attendance"):

        # ✅ Fresh location (UNIQUE KEY)
        location = streamlit_geolocation()

        if location and location.get("latitude") and location.get("longitude"):
            lat = str(location["latitude"])
            lon = str(location["longitude"])
        else:
            loc = st.session_state.get("location", "NA,NA")
            try:
                lat, lon = loc.split(",")
            except:
                lat, lon = "NA", "NA"

        sheet, _ = connect_sheet()
        df = load_attendance()

        now = get_ist().strftime("%Y-%m-%d %H:%M:%S")

        mask = (
            (df["Date"] == date_str) &
            (df["Employee"] == employee)
        )

        if not df.empty and mask.any():

            idx = df[mask].index[0]

            existing_login = df.at[idx, "Login"]

            if pd.notna(existing_login) and str(existing_login).strip() != "":
                st.warning("⚠ Already Logged In")
                st.stop()

            row_number = idx + 2

            # ✅ Update login time
            sheet.update_cell(row_number, 3, now)

            # ✅ Save login location
            sheet.update_cell(row_number, 8, lat)
            sheet.update_cell(row_number, 9, lon)

            # ✅ Update status
            sheet.update_cell(row_number, 6, "In Progress")

        else:

            new_row = [
                date_str,
                employee,
                now,
                "",
                "",
                "In Progress",
                attendance_type,
                lat,
                lon
            ]

            sheet.append_row(new_row)

        st.success(f"✅ Login Recorded\n📍 Location: {lat}, {lon}")

# ============================================================
# ✅ LOGOUT ATTENDANCE
# ============================================================
with col2:

    if st.button("🔴 Logout Attendance"):

        # ✅ Capture fresh location (same as login)
        location = streamlit_geolocation(key="Logout_location")

        if location and location.get("latitude") and location.get("longitude"):
            lat = str(location["latitude"])
            lon = str(location["longitude"])
        else:
            loc = st.session_state.get("location", "NA,NA")
            try:
                lat, lon = loc.split(",")
            except:
                lat, lon = "NA", "NA"

        sheet, _ = connect_sheet()
        df = load_attendance()

        now_dt = get_ist()
        now_str = now_dt.strftime("%Y-%m-%d %H:%M:%S")

        mask = (
            (df["Date"] == date_str) &
            (df["Employee"] == employee)
        )

        if not df.empty and mask.any():

            idx = df[mask].index[0]
            row_number = idx + 2

            login_value = df.at[idx, "Login"]
            existing_logout = df.at[idx, "Logout"]

            # ✅ Prevent duplicate logout
            if pd.notna(existing_logout) and str(existing_logout).strip() != "":
                st.warning("⚠ Already Logged Out")
                st.stop()

            # ✅ Update logout time
            sheet.update_cell(row_number, 4, now_str)

            # ✅ Calculate working hours
            try:
                login_dt = pd.to_datetime(login_value)
                hours = (now_dt - login_dt).total_seconds() / 3600
                hours = round(hours, 2)
            except:
                hours = 0

            # ✅ Save working hours
            sheet.update_cell(row_number, 5, str(hours))

            # ✅ Update status
            if hours >= 8:
                status = "Full Day"
            elif hours >= 4:
                status = "Half Day"
            else:
                status = "Absent"

            sheet.update_cell(row_number, 6, status)

            # ✅ Save logout location
            sheet.update_cell(row_number, 10, lat)
            sheet.update_cell(row_number, 11, lon)

            st.success(f"✅ Logout Recorded\n⏱ Hours: {hours} hrs\n📍 Location: {lat}, {lon}")

        else:
            st.warning("⚠ No login record found")

# ============================================================
# ✅ CLEAR ATTENDANCE
# ============================================================
with col3:

    if role == "admin":

        confirm = st.checkbox("Confirm Clear Attendance")

        if confirm and st.button("🧹 Clear Attendance"):

            sheet, _ = connect_sheet()

            sheet.clear()

            sheet.append_row([
                "Date",
                "Employee",
                "Login",
                "Logout",
                "Working Hours",
                "Status",
                "Type"
            ])

            st.success("✅ Attendance Cleared")

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
                        "Leave"
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

# ============================================================
# ✅ FILTER PANEL
# ============================================================

st.markdown("### 🔍 Filters")

col1, col2 = st.columns(2)


with col1:
    selected_month = st.selectbox(
        "📅 Select Month",
        sorted(df["Month"].dropna().unique(), reverse=True),
        key="month_filter"
    )

with col2:
    search = st.text_input("👤 Search Employee")


# ============================================================
# ✅ FILTER DATA
# ============================================================

monthly_df = df[df["Month"] == selected_month]

if search:
    monthly_df = monthly_df[
        monthly_df["Employee"].astype(str).str.contains(search, case=False, na=False)
    ]


# ============================================================
# ✅ DISPLAY DATA
# ============================================================

if not monthly_df.empty:

    st.markdown("### 📅 Attendance Details")

    # ✅ Show limited rows
    entries = st.selectbox(
        "Show entries",
        [10, 25, 50, 100],
        index=0,
        key="entries_month"
    )

    display_df = monthly_df.head(entries)

    st.dataframe(display_df, use_container_width=True)

    st.divider()

    # ✅ Download button
    st.download_button(
        label="⬇ Download Monthly Report",
        data=monthly_df.to_csv(index=False).encode("utf-8"),
        file_name=f"attendance_{selected_month}.csv",
        mime="text/csv"
    )

else:
    st.info("⚠ No data available for selected month")
    
    st.divider()
# ============================================================
# ✅ MONTHLY ATTENDANCE REPORT (FULL + CLEAN)
# ============================================================

st.subheader("📅 Monthly Attendance Report")

# ✅ Load data
df = load_attendance()

# ✅ Check if data exists
if df.empty:
    st.info("⚠ No attendance data found")
    st.stop()

# ✅ Ensure Date column exists
if "Date" not in df.columns:
    st.error("❌ Date column missing in data")
    st.stop()

# ✅ Create Month column (ONLY ONCE ✅)
df["Month"] = pd.to_datetime(df["Date"], errors="coerce").dt.strftime("%Y-%m")


# ============================================================
# ✅ FILTER PANEL
# ============================================================

st.markdown("### 🔍 Filters")

col1, col2 = st.columns(2)

with col1:
    selected_month = st.selectbox(
        "📅 Select Month",
        sorted(df["Month"].dropna().unique(), reverse=True),
        key="month_filter"
    )

with col2:
    search = st.text_input("👤 Search Employee")


# ============================================================
# ✅ FILTER DATA
# ============================================================

monthly_df = df[df["Month"] == selected_month]

if search:
    monthly_df = monthly_df[
        monthly_df["Employee"].astype(str).str.contains(search, case=False, na=False)
    ]

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
        mime="text/csv"
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
    mime="text/csv"
)