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

# Get location values safely
loc = st.session_state.get("location", {})

lat = str(loc.get("lat", "NA"))
lon = str(loc.get("lon", "NA"))

# ✅ Read stored location
loc = st.session_state.get("location", {})

lat = str(loc.get("lat", "NA"))
lon = str(loc.get("lon", "NA"))
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
# ✅ LOGIN ATTENDANCE (FINAL DUPLICATE-PROOF VERSION)
# ============================================================

with col1:

    if st.button("🟢 Login Attendance", key="login_att_btn"):

        # ✅ Get stored location
        loc = st.session_state.get("location", {})
        lat = str(loc.get("lat", "NA"))
        lon = str(loc.get("lon", "NA"))

        # ✅ Connect & load data
        sheet, _ = connect_sheet()
        df = load_attendance()

        now_dt = get_ist()
        now_str = now_dt.strftime("%Y-%m-%d %H:%M:%S")

        # ====================================================
        # ✅ STEP 1 — CHECK EXISTING ENTRY
        # ====================================================
        existing_today = df[
            (df["Date"] == date_str) &
            (df["Employee"] == employee)
        ]

        if not existing_today.empty:
            st.warning("⚠ Already logged in for today")
            st.stop()

        # ====================================================
        # ✅ STEP 2 — CREATE NEW RECORD
        # ====================================================
        new_row = [
            date_str,
            employee,
            now_str,
            "",
            "",
            "In Progress",
            attendance_type,
            lat,
            lon,
            "",
            ""
        ]

        # ====================================================
        # ✅ STEP 3 — SAVE DATA
        # ====================================================
        try:
            sheet.append_row(new_row)
            st.success(f"✅ Login Recorded\n📍 Location: {lat}, {lon}")

        except Exception as e:
            st.error(f"❌ Error saving data: {e}")
# ============================================================
# ✅ LOGOUT ATTENDANCE
# ============================================================
with col2:

    if st.button("🔴 Logout Attendance"):
        sheet, _ = connect_sheet()
        # ✅ Get stored location
        loc = st.session_state.get("location", {})

        lat = str(loc.get("lat", "NA"))
        lon = str(loc.get("lon", "NA"))

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
                now_dt = get_ist()
                
                
                time_diff = now_dt - login_dt
                
                
                total_seconds = int(time_diff.total_seconds())


                hours = (now_dt - login_dt).total_seconds() / 3600
                hours = round(hours, 2)
                minutes = (total_seconds % 3600) // 60

                working_hours = f"{hours:02d}:{minutes:02d}"   # ✅ HH:MM format
            except:
                hours = 0

            # ✅ Save working hours
            
            sheet.update_cell(row_number, 5, working_hours)


            # ✅ Update status
            if hours >= 8:
                status = "Full Day"
            elif hours >= 6:
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
# ✅ TODAY'S ATTENDANCE STATUS (FINAL ALIGNED VERSION)
# ============================================================

st.subheader("📋 Today's Attendance")

df_today = load_attendance()
today_str = date.today().strftime("%Y-%m-%d")

# ✅ Check if sheet is empty
if df_today.empty:
    st.info("Attendance sheet is empty.")

else:
    # ========================================================
    # ✅ FILTER DATA (ADMIN vs EMPLOYEE)
    # ========================================================
    if role == "admin":
        today_data = df_today[df_today["Date"] == today_str]
    else:
        today_data = df_today[
            (df_today["Date"] == today_str) &
            (df_today["Employee"] == employee)
        ]

    # ========================================================
    # ✅ DISPLAY TODAY DATA
    # ========================================================
    if not today_data.empty:

        # ✅ Convert datetime safely
        try:
            today_data["Login"] = pd.to_datetime(
                today_data["Login"], errors="coerce"
            )
            today_data["Logout"] = pd.to_datetime(
                today_data["Logout"], errors="coerce"
            )
        except:
            pass

        # ✅ Sort by login time
        try:
            today_data = today_data.sort_values(by="Login")
        except:
            pass

        # ✅ Format time to HH:MM
        try:
            today_data["Login"] = today_data["Login"].dt.strftime("%H:%M")
            today_data["Logout"] = today_data["Logout"].dt.strftime("%H:%M")
        except:
            pass

        # ✅ Show clean table
        st.dataframe(
            today_data[
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
# ✅ CLEAR ATTENDANCE (FINAL CLEAN VERSION)
# ============================================================

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

                st.success("✅ Attendance Cleared Successfully")

                # ✅ Refresh UI
                st.rerun()

            except Exception as e:
                st.error(f"❌ Error clearing attendance: {e}")

if st.button("🧹 Remove Duplicate Entries", key="remove_duplicates_btn"):

    st.write("✅ Button Clicked")
    sheet, _ = connect_sheet()
    df = load_attendance()

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
    df_clean = df.groupby(["Employee", "Date"], as_index=False).last()

    # ✅ Convert Login back to string
    df_clean["Login"] = df_clean["Login"].astype(str)

    # ✅ Clear sheet
    sheet.clear()

    # ✅ Re-add header (IMPORTANT)
    sheet.append_row([
        "Date","Employee","Login","Logout",
        "Working Hours","Status","Type",
        "Login Latitude","Login Longitude",
        "Logout Latitude","Logout Longitude"
    ])

    # ✅ Convert dataframe to list of lists
    data_to_write = [df_clean.columns.tolist()] + df_clean.values.tolist()

    # ✅ Write entire sheet at once (VERY IMPORTANT)
    sheet.update("A1", data_to_write)

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

# Create Month column if missing
if "Month" not in df.columns:
    df["Month"] = pd.to_datetime(
        df["Date"],
        errors="coerce"
    ).dt.strftime("%Y-%m")
    
with col2:
    search = st.text_input("👤 Search Employee")


# ============================================================
# ✅ PREPARE DATA
# ============================================================

df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
df["Month"] = df["Date"].dt.strftime("%Y-%m")

# ============================================================
# ✅ FILTER DATA
# ============================================================

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
        key="month_filter_unique"
    )

# ✅ Employee filter
with col2:
    employee_list = ["All"] + sorted(df["Employee"].dropna().astype(str).unique())

    selected_employee = st.selectbox(
        "👤 Select Employee",
        employee_list,
        key="employee_filter_unique"
    )

# ✅ Optional search
search = st.text_input("🔍 Search Employee")

# ============================================================
# ✅ APPLY FILTERS
# ============================================================

monthly_df = df[df["Month"] == selected_month]

if selected_employee != "All":
    monthly_df = monthly_df[
        monthly_df["Employee"] == selected_employee
    ]

if search:
    monthly_df = monthly_df[
        monthly_df["Employee"].astype(str).str.contains(search, case=False, na=False)
    ]

st.divider()

# ============================================================
# ✅ KPI DASHBOARD (ADD HERE ✅)
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

# ============================================================
# ✅ DISPLAY RESULT
# ============================================================


def highlight_status(val):
    if val == "Full Day":
        return "background-color: #d4edda; color: black"
    elif val == "Half Day":
        return "background-color: #fff3cd; color: black"
    elif val == "Absent":
        return "background-color: #f8d7da; color: black"
    else:
        return ""

# ============================================================
# ✅ APPLY STYLING (SAFE VERSION)
# ============================================================

if isinstance(monthly_df, pd.DataFrame) and not monthly_df.empty:

    # ✅ Ensure Status column exists
    if "Status" in monthly_df.columns:

        styled_df = (
            monthly_df.style
            .applymap(highlight_status, subset=["Status"])
            .set_properties(subset=["Status"], **{"text-align": "center"})
        )

        st.dataframe(styled_df, use_container_width=True)

    else:
        # fallback if column missing
        st.dataframe(monthly_df, use_container_width=True)

else:
    st.info("⚠ No data available for selected filters")

# ============================================================
# ✅ MONTHLY ATTENDANCE REPORT (FINAL CLEAN VERSION)
# ============================================================

st.subheader("📅 Monthly Attendance Report")

# ✅ Load data (IMPORTANT ✅)
df = load_attendance()

# ✅ Check if data exists
if df.empty:
    st.info("⚠ No attendance data found")
    st.stop()

# ✅ Ensure Date column exists
if "Date" not in df.columns:
    st.error("❌ Date column missing in data")
    st.stop()

# ========================================================
# ✅ PREPARE DATA (MUST COME FIRST ✅)
# ========================================================

df = load_attendance()

df.columns = df.columns.str.strip()

df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
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
# ✅ FILTER DATA
# ========================================================

monthly_df = df[df["Month"] == selected_month]

# ✅ Apply employee filter
if selected_employee != "All":
    monthly_df = monthly_df[
        monthly_df["Employee"] == selected_employee
    ]

# ✅ Apply search filter
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