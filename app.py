import streamlit as st
import pandas as pd
from datetime import datetime

# Page title
st.title("📊 Attendance Management System")

# ✅ Load Employee Master (file must be in same folder)
try:
    df_emp = pd.read_excel("employees.xlsx")
    employees = df_emp["Employee Name"].dropna().tolist()
except:
    st.error("❌ Employee file not found! Make sure 'employees.xlsx' is in the folder.")
    st.stop()

# ✅ Input Fields
date = st.date_input("Select Date")
employee = st.selectbox("Employee Name", employees)

login = st.time_input("Login Time")
logout = st.time_input("Logout Time")

# ✅ Save Attendance
if st.button("Save Attendance"):

    if login and logout:
        login_dt = datetime.combine(date, login)
        logout_dt = datetime.combine(date, logout)

        # ✅ Validation
        if logout_dt < login_dt:
            st.error("❌ Logout time cannot be before login time")
            st.stop()

        hours = (logout_dt - login_dt).seconds / 3600

        if hours >= 8:
            status = "Present"
        elif hours > 0:
            status = "Half Day"
        else:
            status = "Absent"
    else:
        hours = 0
        status = "Absent"

    new_data = pd.DataFrame([{
        "Date": str(date),
        "Employee": employee,
        "Login": str(login),
        "Logout": str(logout),
        "Working Hours": round(hours, 2),
        "Status": status
    }])

    file_name = "attendance.csv"

    # ✅ Prevent duplicate entry
    try:
        existing = pd.read_csv(file_name)

        duplicate = (
            (existing["Date"] == str(date)) &
            (existing["Employee"] == employee)
        )

        if duplicate.any():
            st.error("❌ Attendance already marked for this employee on this date!")
        else:
            updated = pd.concat([existing, new_data], ignore_index=True)
            updated.to_csv(file_name, index=False)
            st.success("✅ Attendance Saved Successfully!")
            st.dataframe(updated)

    except:
        new_data.to_csv(file_name, index=False)
        st.success("✅ Attendance Saved Successfully!")
        st.dataframe(new_data)

# ✅ Show Attendance Data
st.subheader("📋 Attendance Records")

try:
    df = pd.read_csv("attendance.csv")

    # ✅ Filters
    selected_employee = st.selectbox("Filter by Employee", ["All"] + list(df["Employee"].unique()))
    
    if selected_employee != "All":
        df = df[df["Employee"] == selected_employee]

    st.dataframe(df)

    # ✅ Download Report
    st.download_button(
        "📥 Download Attendance Report",
        df.to_csv(index=False),
        file_name="attendance_report.csv"
    )

    # ✅ Summary
    st.subheader("📊 Summary")
    st.write("Total Records:", len(df))
    st.write("Present:", (df["Status"] == "Present").sum())
    st.write("Half Day:", (df["Status"] == "Half Day").sum())
    st.write("Absent:", (df["Status"] == "Absent").sum())

except:
    st.info("No attendance data available yet.")