import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Attendance System", layout="centered")

# ✅ USER LOGIN DATA
users = {
    "admin": {"password": "admin123", "role": "admin"},
    "kunal": {"password": "1234", "role": "employee"},
    "rahul": {"password": "1234", "role": "employee"}
}

# ✅ LOGIN PANEL
st.sidebar.title("🔐 Login")
username = st.sidebar.text_input("Username")
password = st.sidebar.text_input("Password", type="password")

if st.sidebar.button("Login"):
    if username in users and users[username]["password"] == password:
        st.session_state["logged_in"] = True
        st.session_state["user"] = username
        st.session_state["role"] = users[username]["role"]
        st.success(f"✅ Welcome {username}")
    else:
        st.error("❌ Invalid credentials")

if "logged_in" not in st.session_state:
    st.stop()

# ✅ ROLE
role = st.session_state["role"]

st.title("📊 Attendance Management System")

# ✅ LOAD EMPLOYEES
try:
    df_emp = pd.read_excel("employees.xlsx")
    employees = df_emp["Employee Name"].dropna().tolist()
except:
    st.error("employees.xlsx not found")
    st.stop()

date = st.date_input("Select Date")

# ✅ Employee Restriction
if role == "employee":
    employee = st.session_state["user"]
else:
    employee = st.selectbox("Employee Name", employees)

attendance_type = st.selectbox(
    "Attendance Type",
    ["Present WFO", "Present WFH", "Half Day", "Leave"]
)

file_name = "attendance.csv"

try:
    df = pd.read_csv(file_name)
except:
    df = pd.DataFrame(columns=[
        "Date","Employee","Login","Logout","Working Hours","Status","Type"
    ])

existing_index = df[
    (df["Date"] == str(date)) &
    (df["Employee"] == employee)
].index

# ✅ BUTTONS (LOGIN / LOGOUT / MARK)
col1, col2, col3 = st.columns(3)

# LOGIN
with col1:
    if st.button("🟢 Login Now"):
        current_time = datetime.now().strftime("%H:%M:%S")

        if len(existing_index) > 0:
            idx = existing_index[0]
            if df.at[idx, "Login"] == "" or pd.isna(df.at[idx, "Login"]):
                df.at[idx, "Login"] = current_time
                df.at[idx, "Status"] = "In Progress"
                df.at[idx, "Type"] = attendance_type
                st.success(f"✅ Login at {current_time}")
            else:
                st.warning("⚠️ Already logged in")
        else:
            new_row = {
                "Date": str(date),
                "Employee": employee,
                "Login": current_time,
                "Logout": "",
                "Working Hours": "",
                "Status": "In Progress",
                "Type": attendance_type
            }
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            st.success(f"✅ Login at {current_time}")

        df.to_csv(file_name, index=False)

# LOGOUT
with col2:
    if st.button("🔴 Logout Now"):
        current_time = datetime.now().strftime("%H:%M:%S")

        if len(existing_index) > 0:
            idx = existing_index[0]

            if df.at[idx, "Login"] == "":
                st.error("❌ Login first")

            elif df.at[idx, "Logout"] == "" or pd.isna(df.at[idx, "Logout"]):
                df.at[idx, "Logout"] = current_time

                login_time = pd.to_datetime(df.at[idx, "Login"])
                logout_time = pd.to_datetime(current_time)

                hours = (logout_time - login_time).total_seconds()/3600
                df.at[idx, "Working Hours"] = round(hours,2)

                if attendance_type == "Leave":
                    status = "Leave"
                elif attendance_type == "Half Day":
                    status = "Half Day"
                elif hours >= 8:
                    status = "Present"
                else:
                    status = "Half Day"

                df.at[idx, "Status"] = status
                df.at[idx, "Type"] = attendance_type

                st.success(f"✅ Logout at {current_time}")

            else:
                st.warning("⚠️ Already logged out")
        else:
            st.error("❌ No login found")

        df.to_csv(file_name, index=False)

# MARK WITHOUT LOGIN
with col3:
    if st.button("✅ Mark Without Login"):
        if attendance_type in ["Leave", "Half Day"]:
            new_row = {
                "Date": str(date),
                "Employee": employee,
                "Login": "",
                "Logout": "",
                "Working Hours": "",
                "Status": attendance_type,
                "Type": attendance_type
            }

            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            df.to_csv(file_name, index=False)

            st.success(f"✅ {attendance_type} marked")
        else:
            st.warning("⚠️ Use login/logout for WFO/WFH")

# ✅ TABLE
st.subheader("📋 Attendance Records")
try:
    df = pd.read_csv(file_name)
    st.dataframe(df)

    st.download_button(
        "📥 Download Full Report",
        df.to_csv(index=False),
        file_name="attendance_report.csv"
    )
except:
    st.info("No attendance data")

# ✅ DASHBOARD (ADMIN ONLY)
if role == "admin":
    st.subheader("📊 Dashboard")

    present = (df["Status"] == "Present").sum()
    leave = (df["Status"] == "Leave").sum()
    half = (df["Status"] == "Half Day").sum()

    chart_df = pd.DataFrame({
        "Type": ["Present","Leave","Half Day"],
        "Count": [present, leave, half]
    })

    st.bar_chart(chart_df.set_index("Type"))

# ✅ LEAVE REQUEST
st.subheader("📩 Leave Request")

if role == "employee":
    reason = st.text_input("Reason for leave")

    if st.button("Submit Leave Request"):
        leave_data = {
            "Employee": employee,
            "Date": str(date),
            "Reason": reason,
            "Status": "Pending"
        }

        try:
            leave_df = pd.read_csv("leave_requests.csv")
        except:
            leave_df = pd.DataFrame(columns=["Employee","Date","Reason","Status"])

        leave_df = pd.concat([leave_df, pd.DataFrame([leave_data])])
        leave_df.to_csv("leave_requests.csv", index=False)

        st.success("✅ Leave Requested")

# ✅ ADMIN APPROVAL
if role == "admin":
    st.subheader("✅ Leave Approval Panel")

    try:
        leave_df = pd.read_csv("leave_requests.csv")

        for i, row in leave_df.iterrows():
            st.write(row)

            col1, col2 = st.columns(2)

            with col1:
                if st.button(f"Approve {i}"):
                    leave_df.at[i, "Status"] = "Approved"

            with col2:
                if st.button(f"Reject {i}"):
                    leave_df.at[i, "Status"] = "Rejected"

        leave_df.to_csv("leave_requests.csv", index=False)

    except:
        st.info("No leave requests")

# ✅ MONTHLY REPORT
st.subheader("📅 Monthly Report")

try:
    df["Date"] = pd.to_datetime(df["Date"])
    months = df["Date"].dt.to_period("M").astype(str).unique()

    selected_month = st.selectbox("Select Month", months)

    monthly_df = df[df["Date"].dt.to_period("M").astype(str) == selected_month]

    st.dataframe(monthly_df)

    st.download_button(
        "📥 Download Monthly Report",
        monthly_df.to_csv(index=False),
        file_name=f"attendance_{selected_month}.csv"
    )

except:
    st.info("No monthly data")