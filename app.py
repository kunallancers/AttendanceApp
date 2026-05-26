import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, date, timezone
import pytz
import os

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

# ============================================================
# ✅ HEADER
# ============================================================
st.title("📊 Attendance Dashboard")

st.write(f"👋 Welcome: {employee}")

st.write(
    "🕒 Current IST Time:",
    get_ist().strftime("%Y-%m-%d %H:%M:%S")
)

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

        sheet, _ = connect_sheet()

        df = load_attendance()

        now = get_ist().strftime("%Y-%m-%d %H:%M:%S")

        mask = (
            (df["Date"] == date_str) &
            (df["Employee"] == employee)
        )

        if mask.any():

            idx = df[mask].index[0]

            existing_login = df.at[idx, "Login"]

            if pd.notna(existing_login) and str(existing_login).strip() != "":
                st.warning("⚠ Already Logged In")
                st.stop()

            row_number = idx + 2

            sheet.update_cell(row_number, 3, now)

            sheet.update_cell(row_number, 6, "In Progress")

        else:

            new_row = [
                date_str,
                employee,
                now,
                "",
                "",
                "In Progress",
                attendance_type
            ]

            sheet.append_row(new_row)

        st.success("✅ Login Recorded")

# ============================================================
# ✅ LOGOUT ATTENDANCE
# ============================================================
with col2:

    if st.button("🔴 Logout Attendance"):

        sheet, _ = connect_sheet()

        df = load_attendance()

        now = get_ist().strftime("%Y-%m-%d %H:%M:%S")

        match = df[
            (df["Employee"] == employee) &
            (df["Date"] == date_str)
        ]

        if match.empty:
            st.error("❌ No Login Record Found")
            st.stop()

        idx = match.index[0]

        login_val = match.iloc[0]["Login"]

        logout_val = match.iloc[0]["Logout"]

        if pd.isna(login_val) or str(login_val).strip() == "":
            st.error("❌ Please Login First")
            st.stop()

        if pd.notna(logout_val) and str(logout_val).strip() != "":
            st.warning("⚠ Already Logged Out")
            st.stop()

        login_time = pd.to_datetime(login_val)

        logout_time = pd.to_datetime(now)

        hours = round(
            (logout_time - login_time).total_seconds() / 3600,
            2
        )

        status = "Present" if hours >= 8 else "Half Day"

        row_number = idx + 2

        sheet.update_cell(row_number, 4, now)

        sheet.update_cell(row_number, 5, hours)

        sheet.update_cell(row_number, 6, status)

        st.success(
            f"✅ Logout Recorded | Working Hours: {hours}"
        )

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

    st.dataframe(
        df,
        use_container_width=True
    )

else:

    st.info("No attendance records found")

# ============================================================
# ✅ MONTHLY REPORT
# ============================================================
st.subheader("📅 Monthly Attendance Report")

monthly_df = load_attendance()

if not monthly_df.empty:

    monthly_df["Month"] = monthly_df["Date"].astype(str).str[:7]

    month_list = sorted(
        monthly_df["Month"].dropna().unique(),
        reverse=True
    )

    selected_month = st.selectbox(
        "Select Month",
        month_list
    )

    report_df = monthly_df[
        monthly_df["Month"] == selected_month
    ]

    st.dataframe(
        report_df,
        use_container_width=True
    )

    st.download_button(
        label="📥 Download Monthly Report",
        data=report_df.to_csv(index=False).encode("utf-8"),
        file_name=f"attendance_{selected_month}.csv",
        mime="text/csv"
    )

else:

    st.info("No data available")

# ============================================================
# ✅ FULL DOWNLOAD
# ============================================================
full_df = load_attendance()

st.download_button(
    "📥 Download Full Attendance",
    data=full_df.to_csv(index=False).encode("utf-8"),
    file_name="attendance.csv",
    mime="text/csv"
)