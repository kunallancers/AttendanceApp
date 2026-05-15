import streamlit as st
import pandas as pd
import datetime

# ✅ SESSION INIT
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# ✅ PAGE CONFIG
st.set_page_config(page_title="Attendance System", layout="wide")

# ✅ LOAD EMPLOYEES
try:
    df_emp = pd.read_excel("employees.xlsx")
    df_emp.columns = df_emp.columns.str.strip()
except:
    st.error("❌ employees.xlsx not found")
    st.stop()

# ✅ CREATE USERS AUTO
users = {
    "admin": {"password": "admin123", "role": "admin", "employee": "ADMIN"}
}

for _, row in df_emp.iterrows():
    name = str(row["Employee Name"]).strip()
    pwd = str(row["Password"]).strip()
    username = name.split()[0].lower()

    users[username] = {
        "password": pwd,
        "role": "employee",
        "employee": name
    }

# ✅ LOGIN PAGE
if not st.session_state["logged_in"]:

    st.title("🔐 Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username in users and users[username]["password"] == password:
            st.session_state.update({
                "logged_in": True,
                "user": username,
                "role": users[username]["role"],
                "employee": users[username]["employee"]
            })
            st.rerun()
        else:
            st.error("❌ Invalid login")

    st.stop()

# ✅ LOGOUT
if st.button("Logout"):
    st.session_state.clear()
    st.rerun()

role = st.session_state["role"]

# ✅ LOAD ATTENDANCE
try:
    df = pd.read_csv("attendance.csv")
except:
    df = pd.DataFrame(columns=[
        "Date","Employee","Login","Logout","Working Hours","Status","Type"
    ])

# ✅ LOAD LEAVE
try:
    leave_df = pd.read_csv("leave_requests.csv")
except:
    leave_df = pd.DataFrame(columns=["Employee","Date","Reason","Status"])

# ✅ HEADER
st.title("📊 Attendance Dashboard")
st.write(f"👋 Welcome, {st.session_state['employee']}")

# ✅ INPUT
date = st.date_input("Select Date", datetime.date.today())

if role == "employee":
    employee = st.session_state["employee"]
else:
    employee = st.selectbox("Employee", df_emp["Employee Name"])

attendance_type = st.selectbox(
    "Attendance Type",
    ["Present WFO","Present WFH","Half Day","Leave"]
)

# ✅ EXISTING RECORD
existing = df[
    (df["Date"] == str(date)) &
    (df["Employee"] == employee)
].index

# ✅ ATTENDANCE BUTTONS
col1, col2 = st.columns(2)

# ✅ LOGIN ATTENDANCE
with col1:
    if st.button("🟢 Login Attendance"):

        now = datetime.datetime.now().strftime("%H:%M:%S")

        if len(existing) > 0:
            idx = existing[0]
            if df.at[idx,"Login"] != "":
                st.warning("Already logged in")
            else:
                df.at[idx,"Login"] = now
        else:
            df = pd.concat([df, pd.DataFrame([{
                "Date": str(date),
                "Employee": employee,
                "Login": now,
                "Logout":"",
                "Working Hours":"",
                "Status":"In Progress",
                "Type":attendance_type
            }])], ignore_index=True)

        df.to_csv("attendance.csv", index=False)
        st.success("✅ Login marked")

# ✅ LOGOUT ATTENDANCE
with col2:
    if st.button("🔴 Logout Attendance"):

        now = datetime.datetime.now().strftime("%H:%M:%S")

        if len(existing) > 0:
            idx = existing[0]

            if df.at[idx,"Login"] == "":
                st.error("Login first")

            elif df.at[idx,"Logout"] != "":
                st.warning("Already logged out")

            else:
                df.at[idx,"Logout"] = now

                hrs = (pd.to_datetime(now) - pd.to_datetime(df.at[idx,"Login"])).total_seconds()/3600
                df.at[idx,"Working Hours"] = round(hrs,2)

                if hrs >= 8:
                    status = "Present"
                else:
                    status = "Half Day"

                if attendance_type == "Leave":
                    status = "Leave"

                df.at[idx,"Status"] = status
                df.at[idx,"Type"] = attendance_type

        df.to_csv("attendance.csv", index=False)
        st.success("✅ Logout marked")

# ✅ LEAVE REQUEST SECTION
st.subheader("📩 Leave System")

# ---------------- EMPLOYEE ----------------
if role == "employee":

    reason = st.text_input("Enter reason")

    existing_leave = leave_df[
        (leave_df["Employee"] == employee) &
        (leave_df["Date"] == str(date))
    ]

    if st.button("Submit Leave Request"):

        if not existing_leave.empty:
            st.warning("Leave already requested")

        else:
            new = {
                "Employee": employee,
                "Date": str(date),
                "Reason": reason,
                "Status": "Pending"
            }

            leave_df = pd.concat([leave_df, pd.DataFrame([new])], ignore_index=True)
            leave_df.to_csv("leave_requests.csv", index=False)

            st.success("✅ Leave requested")

    st.write("Your Requests")
    st.dataframe(leave_df[leave_df["Employee"] == employee])

# ---------------- ADMIN ----------------
if role == "admin":

    st.subheader("✅ Pending Approvals")

    pending = leave_df[leave_df["Status"] == "Pending"]

    if not pending.empty:

        for i, row in pending.iterrows():

            st.write(f"{row['Employee']} | {row['Date']} | {row['Reason']}")

            c1, c2 = st.columns(2)

            # APPROVE
            with c1:
                if st.button(f"Approve {i}"):

                    leave_df.at[i,"Status"] = "Approved"

                    # AUTO ATTENDANCE
                    new_row = {
                        "Date": row["Date"],
                        "Employee": row["Employee"],
                        "Login":"",
                        "Logout":"",
                        "Working Hours":"",
                        "Status":"Leave",
                        "Type":"Leave"
                    }

                    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                    df.to_csv("attendance.csv", index=False)

                    st.success("✅ Approved")

            # REJECT
            with c2:
                if st.button(f"Reject {i}"):
                    leave_df.at[i,"Status"] = "Rejected"

        leave_df.to_csv("leave_requests.csv", index=False)

    else:
        st.info("No pending leave requests")

# ✅ ATTENDANCE TABLE
st.subheader("📋 Attendance Records")
st.dataframe(df)

# ✅ DOWNLOAD
st.download_button(
    "📥 Download Report",
    df.to_csv(index=False),
    file_name="attendance.csv"
)

# ✅ ADMIN RESET
if role == "admin":

    st.subheader("⚙️ Admin Controls")

    confirm = st.checkbox("Confirm delete")

    if confirm:
        if st.button("Clear Attendance"):
            pd.DataFrame(columns=df.columns).to_csv("attendance.csv", index=False)
            st.success("✅ Cleared")