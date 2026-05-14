import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Attendance App", layout="centered")

st.title("📊 Attendance Management System")

# ✅ Load Employees
try:
    df_emp = pd.read_excel("employees.xlsx")
    employees = df_emp["Employee Name"].dropna().tolist()
except:
    st.error("❌ employees.xlsx not found")
    st.stop()

# ✅ Inputs
date = st.date_input("Select Date")
employee = st.selectbox("Employee Name", employees)

attendance_type = st.selectbox(
    "Attendance Type",
    ["Present WFO", "Present WFH", "Half Day", "Leave"]
)

# ✅ Load/Create Data
file_name = "attendance.csv"

try:
    df = pd.read_csv(file_name)
except:
    df = pd.DataFrame(columns=[
        "Date", "Employee", "Login", "Logout", "Working Hours", "Status", "Type"
    ])

# ✅ FIND EXISTING RECORD
existing_index = df[
    (df["Date"] == str(date)) &
    (df["Employee"] == employee)
].index

# ✅ BUTTON SECTION (IMPORTANT UI FIX)
col1, col2, col3 = st.columns(3)

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
                st.warning("⚠️ Login already done")

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


with col2:
    if st.button("🔴 Logout Now"):
        current_time = datetime.now().strftime("%H:%M:%S")

        if len(existing_index) > 0:
            idx = existing_index[0]

            if df.at[idx, "Login"] == "":
                st.error("❌ Please login first")

            elif df.at[idx, "Logout"] == "" or pd.isna(df.at[idx, "Logout"]):

                df.at[idx, "Logout"] = current_time

                try:
                    login_time = pd.to_datetime(df.at[idx, "Login"])
                    logout_time = pd.to_datetime(current_time)

                    hours = (logout_time - login_time).total_seconds() / 3600
                    df.at[idx, "Working Hours"] = round(hours, 2)

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

                except:
                    st.error("❌ Error calculating hours")

            else:
                st.warning("⚠️ Already logged out")

        else:
            st.error("❌ Login not found")

        df.to_csv(file_name, index=False)


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
            st.warning("⚠️ Use Login/Logout for WFO/WFH")


# ✅ DISPLAY DATA
st.subheader("📋 Attendance Records")

try:
    df = pd.read_csv(file_name)
    st.dataframe(df)

    st.download_button(
        "📥 Download Report",
        df.to_csv(index=False),
        file_name="attendance_report.csv"
    )
except:
    st.info("No attendance data yet")