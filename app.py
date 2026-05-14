import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Attendance System", layout="centered")

# ✅ LOAD EMPLOYEES EXCEL
try:
    df_emp = pd.read_excel("employees.xlsx")
except:
    st.error("❌ employees.xlsx not found")
    st.stop()

# ✅ CREATE USERS AUTO FROM EXCEL
users = {
    "admin": {
        "password": "admin123",
        "role": "admin",
        "employee_name": "ADMIN"
    }
}

for _, row in df_emp.iterrows():
    emp_name = row["Employee Name"]
    password = str(row["Password"])

    username = emp_name.split()[0].lower()

    users[username] = {
        "password": password,
        "role": "employee",
        "employee_name": emp_name
    }

# ✅ LOGIN SYSTEM
st.sidebar.title("🔐 Login")

username = st.sidebar.text_input("Username")
password = st.sidebar.text_input("Password", type="password")

if st.sidebar.button("Login"):
    if username in users and users[username]["password"] == password:
        st.session_state["logged_in"] = True
        st.session_state["user"] = username
        st.session_state["role"] = users[username]["role"]
        st.session_state["employee_name"] = users[username]["employee_name"]
        st.success(f"✅ Welcome {username}")
    else:
        st.error("❌ Invalid credentials")

if "logged_in" not in st.session_state:
    st.stop()

# ✅ ROLE SETUP
role = st.session_state["role"]

st.title("📊 Attendance Management System")

date = st.date_input("Select Date")

# ✅ EMPLOYEE CONTROL
employees = df_emp["Employee Name"].dropna().tolist()

if role == "employee":
    employee = st.session_state["employee_name"]
    st.info(f"Logged in as: {employee}")
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

existing = df[
    (df["Date"] == str(date)) &
    (df["Employee"] == employee)
].index

# ✅ BUTTONS
col1, col2, col3 = st.columns(3)

# ✅ LOGIN BUTTON
with col1:
    if st.button("🟢 Login Now"):
        now = datetime.now().strftime("%H:%M:%S")

        if len(existing) > 0:
            idx = existing[0]
            if pd.isna(df.at[idx, "Login"]) or df.at[idx, "Login"] == "":
                df.at[idx, "Login"] = now
                df.at[idx, "Status"] = "In Progress"
                df.at[idx, "Type"] = attendance_type
                st.success(f"✅ Login at {now}")
            else:
                st.warning("Already Logged In")
        else:
            new = {
                "Date": str(date),
                "Employee": employee,
                "Login": now,
                "Logout": "",
                "Working Hours": "",
                "Status": "In Progress",
                "Type": attendance_type
            }
            df = pd.concat([df, pd.DataFrame([new])], ignore_index=True)
            st.success(f"✅ Login at {now}")

        df.to_csv(file_name, index=False)

# ✅ LOGOUT
with col2:
    if st.button("🔴 Logout Now"):
        now = datetime.now().strftime("%H:%M:%S")

        if len(existing) > 0:
            idx = existing[0]

            if df.at[idx, "Login"] == "":
                st.error("Login first")

            elif pd.isna(df.at[idx, "Logout"]) or df.at[idx, "Logout"] == "":
                df.at[idx, "Logout"] = now

                login_time = pd.to_datetime(df.at[idx, "Login"])
                logout_time = pd.to_datetime(now)

                hrs = (logout_time - login_time).total_seconds()/3600
                df.at[idx, "Working Hours"] = round(hrs,2)

                if attendance_type == "Leave":
                    status = "Leave"
                elif attendance_type == "Half Day":
                    status = "Half Day"
                elif hrs >= 8:
                    status = "Present"
                else:
                    status = "Half Day"

                df.at[idx, "Status"] = status
                df.at[idx, "Type"] = attendance_type

                st.success(f"✅ Logout at {now}")

            else:
                st.warning("Already logged out")
        else:
            st.error("No login found")

        df.to_csv(file_name, index=False)

# ✅ MARK WITHOUT LOGIN
with col3:
    if st.button("✅ Mark Without Login"):
        if attendance_type in ["Leave", "Half Day"]:
            new = {
                "Date": str(date),
                "Employee": employee,
                "Login": "",
                "Logout": "",
                "Working Hours": "",
                "Status": attendance_type,
                "Type": attendance_type
            }
            df = pd.concat([df, pd.DataFrame([new])], ignore_index=True)
            df.to_csv(file_name, index=False)

            st.success(f"✅ {attendance_type} marked")
        else:
            st.warning("Use Login for WFO/WFH")

# ✅ TABLE
st.subheader("📋 Attendance Records")

df = pd.read_csv(file_name)
st.dataframe(df)

st.download_button(
    "📥 Download Report",
    df.to_csv(index=False),
    file_name="attendance_report.csv"
)

# ✅ DASHBOARD (ADMIN ONLY)
if role == "admin":
    st.subheader("📊 Dashboard")

    p = (df["Status"] == "Present").sum()
    l = (df["Status"] == "Leave").sum()
    h = (df["Status"] == "Half Day").sum()

    chart = pd.DataFrame({
        "Type":["Present","Leave","Half Day"],
        "Count":[p,l,h]
    })

    st.bar_chart(chart.set_index("Type"))

# ✅ LEAVE REQUEST
st.subheader("📩 Leave Request")

if role == "employee":
    reason = st.text_input("Leave Reason")

    if st.button("Submit Leave"):
        try:
            leave_df = pd.read_csv("leave_requests.csv")
        except:
            leave_df = pd.DataFrame(columns=["Employee","Date","Reason","Status"])

        new_leave = {
            "Employee": employee,
            "Date": str(date),
            "Reason": reason,
            "Status": "Pending"
        }

        leave_df = pd.concat([leave_df, pd.DataFrame([new_leave])])
        leave_df.to_csv("leave_requests.csv", index=False)

        st.success("✅ Leave Requested")

# ✅ ADMIN APPROVAL
if role == "admin":
    st.subheader("✅ Leave Approval")

    try:
        leave_df = pd.read_csv("leave_requests.csv")

        for i, row in leave_df.iterrows():
            st.write(row)

            c1, c2 = st.columns(2)

            with c1:
                if st.button(f"Approve {i}"):
                    leave_df.at[i,"Status"] = "Approved"

            with c2:
                if st.button(f"Reject {i}"):
                    leave_df.at[i,"Status"] = "Rejected"

        leave_df.to_csv("leave_requests.csv", index=False)

    except:
        st.info("No leave requests")

# ✅ MONTHLY REPORT
st.subheader("📅 Monthly Report")

try:
    df["Date"] = pd.to_datetime(df["Date"])

    months = df["Date"].dt.to_period("M").astype(str).unique()

    month = st.selectbox("Select Month", months)

    mdf = df[df["Date"].dt.to_period("M").astype(str) == month]

    st.dataframe(mdf)

    st.download_button(
        "📥 Download Monthly",
        mdf.to_csv(index=False),
        file_name=f"attendance_{month}.csv"
)
except:
    st.info("No data")