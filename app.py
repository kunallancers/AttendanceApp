import os
import time
from datetime import date, datetime, timezone
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import pytz
import streamlit as st
import streamlit.components.v1 as components
from streamlit_geolocation import streamlit_geolocation

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

# ============================================================
# ✅ GOOGLE SHEET CONNECTION (FINAL STABLE VERSION)
# ============================================================


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
    return pd.Timestamp.now(
        tz="Asia/Kolkata"
    ).tz_localize(None)


# ============================================================
# ✅ LOAD ATTENDANCE (CACHE BYPASS FIX)
# ============================================================

def load_attendance(force_refresh=False):
    """Loads attendance data directly from Google Sheets."""
    if force_refresh:
        st.cache_data.clear()

    try:
        sheet, _ = connect_sheet()
        data = sheet.get_all_records()

        if not data:
            return pd.DataFrame(columns=[
                "Date", "Employee", "Login", "Logout", "Working Hours",
                "Status", "Type", "Login Latitude", "Login Longitude",
                "Logout Latitude", "Logout Longitude"
            ])

        df = pd.DataFrame(data)
        df.columns = df.columns.str.strip()

        if "Date" in df.columns:
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.strftime("%Y-%m-%d")

        if "Employee" in df.columns:
            df["Employee"] = df["Employee"].astype(str).str.strip().str.upper()

        return df

    except Exception as e:
        st.error(f"❌ Error loading attendance: {e}")
        return pd.DataFrame()


# ============================================================
# ✅ ACTION BUTTONS (CLOCK IN / CLOCK OUT REFACTORED)
# ============================================================

col1_act, col2_act = st.columns(2)

# --- LOGIN ATTENDANCE ---
with col1_act:
    if st.button("🔑 Login", key="login_att_action_btn", use_container_width=True):
        login_time_str = get_ist().strftime("%H:%M:%S")
        date_str = selected_date.strftime("%Y-%m-%d")
        employee_clean = str(employee).strip().upper()

        # Fetch fresh data directly from sheet
        df_att = load_attendance(force_refresh=True)

        # Check approved leaves
        leave_df = load_leave()
        approved_leave = leave_df[
            (leave_df["Employee"].astype(str).str.strip().str.upper() == employee_clean) &
            (leave_df["Date"].astype(str).str[:10] == date_str) &
            (leave_df["Status"].astype(str).str.strip().str.upper() == "APPROVED")
        ]

        if not approved_leave.empty and role != "admin":
            st.error("❌ Approved leave exists for today. Attendance cannot be marked.")
        else:
            existing_today = df_att[
                (df_att["Date"] == date_str) &
                (df_att["Employee"] == employee_clean)
            ]

            if not existing_today.empty:
                last_logout = str(existing_today.iloc[-1].get("Logout", "")).strip()
                if last_logout in ["", "nan", "None", "Pending"]:
                    st.warning("⚠ Already logged in today. Clock out first.")
                else:
                    st.warning("⚠ Attendance already completed for today.")
            else:
                lat_val, lon_val = get_location_values()
                sheet, _ = connect_sheet()

                try:
                    sheet.append_row([
                        date_str,
                        employee_clean,
                        login_time_str,
                        "",
                        "",
                        "In Progress",
                        attendance_type,
                        lat_val,
                        lon_val,
                        "",
                        ""
                    ])
                    
                    # Force cache invalidation so portal updates immediately
                    st.cache_data.clear()
                    st.success(f"✅ Login Recorded: {login_time_str}")
                    st.rerun()

                except Exception as e:
                    st.error(f"❌ Login insertion failed: {e}")


# --- LOGOUT ATTENDANCE ---
with col2_act:
    if st.button("🔴 Logout Attendance", key="logout_attendance_btn", use_container_width=True):
        date_str = selected_date.strftime("%Y-%m-%d")
        employee_clean = str(employee).strip().upper()

        # Force fresh sheet load to locate active row accurately
        sheet, _ = connect_sheet()
        all_rows = sheet.get_all_records()

        if not all_rows:
            st.warning("⚠ No records found in sheet.")
        else:
            # Find matching row index directly in Google Sheets (1-based index + header offset)
            target_sheet_row = None
            login_time_str = None

            for row_idx, r in enumerate(all_rows, start=2):  # Header is Row 1
                r_date = str(r.get("Date", "")).strip()
                r_emp = str(r.get("Employee", "")).strip().upper()
                r_logout = str(r.get("Logout", "")).strip()

                if r_date == date_str and r_emp == employee_clean and r_logout in ["", "nan", "None", "Pending"]:
                    target_sheet_row = row_idx
                    login_time_str = str(r.get("Login", "")).strip()
                    break

            if target_sheet_row is None:
                st.warning("⚠ No active clock-in record found for today. Please clock in first.")
            else:
                logout_dt = get_ist()
                login_dt = pd.to_datetime(f"{date_str} {login_time_str}", errors="coerce")

                if pd.isna(login_dt):
                    st.error("❌ Invalid login time found in sheet.")
                else:
                    login_dt = login_dt.tz_localize(None)
                    logout_dt = logout_dt.tz_localize(None)

                    if logout_dt < login_dt:
                        logout_dt += pd.Timedelta(days=1)

                    time_diff = logout_dt - login_dt
                    total_hours = time_diff.total_seconds() / 3600
                    working_hours = str(time_diff).split(".")[0]

                    if total_hours >= 8:
                        status = "Full Day"
                    elif total_hours >= 4:
                        status = "Half Day"
                    else:
                        status = "Short Day"

                    lat_val, lon_val = get_location_values()

                    try:
                        # Direct cell updates on verified row index
                        sheet.update_cell(target_sheet_row, 4, logout_dt.strftime("%H:%M:%S"))
                        sheet.update_cell(target_sheet_row, 5, working_hours)
                        sheet.update_cell(target_sheet_row, 6, status)
                        sheet.update_cell(target_sheet_row, 10, lat_val)
                        sheet.update_cell(target_sheet_row, 11, lon_val)

                        # Clear cache and refresh app state
                        st.cache_data.clear()
                        st.success(f"✅ Logout Recorded! Hours: {working_hours} | Status: {status}")
                        st.rerun()

                    except Exception as e:
                        st.error(f"❌ Sheet update failed: {e}")

    # ========================================================
    # ✅ REMOVE DUPLICATE ENTRIES
    # ========================================================

    st.divider()

    if st.button(
        "🧹 Remove Duplicate Entries",
        key="remove_duplicates_btn"
    ):

        try:

            sheet, _ = connect_sheet()

            df = load_attendance()

            df.columns = df.columns.str.strip()

            if df.empty:

                st.warning(
                    "⚠ No data found in attendance sheet"
                )
                st.stop()

            df["Date"] = pd.to_datetime(
                df["Date"],
                errors="coerce"
            ).dt.strftime("%Y-%m-%d")

            # Remove only truly identical rows
            df_clean = df.drop_duplicates()

            removed_count = len(df) - len(df_clean)

            sheet.clear()

            data_to_write = [
                df_clean.columns.tolist()
            ] + df_clean.values.tolist()

            sheet.update(
                "A1",
                data_to_write
            )

            try:
                load_attendance.clear()
            except Exception:
                pass

            st.success(
                f"✅ Removed {removed_count} duplicate entries"
            )

            st.rerun()

        except Exception as e:

            st.error(
                f"❌ Error removing duplicates: {e}"
            )

# ============================================================
# ✅ LEAVE MANAGEMENT
# ============================================================
st.subheader("📩 Leave Management")

leave_df = load_leave()

employee_clean = str(employee).strip().upper()

# ============================================================
# ✅ EMPLOYEE LEAVE
# ============================================================
if role == "employee":

    colA, colB = st.columns(2)

    with colA:

        start_date = st.date_input(
            "Leave From",
            today,
            min_value=today,
            key="emp_leave_start_date"
        )

    with colB:

        end_date = st.date_input(
            "Leave To",
            start_date,
            min_value=start_date,
            key="emp_leave_end_date"
        )

    reason = st.text_input("Leave Reason", key="emp_leave_reason_input")

    if st.button("Submit Leave", key="submit_leave_request_btn"):

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
        leave_df[leave_df["Employee"] == employee_clean]
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

                if st.button(f"Approve {i}", key=f"approve_leave_btn_{i}"):

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

                if st.button(f"Reject {i}", key=f"reject_leave_btn_{i}"):

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
                sorted(df["Employee"].dropna().unique()),
                key="admin_filter_emp_select"
            )

        with f2:

            date_filter = st.date_input(
                "Filter Date",
                None,
                key="admin_filter_date_input"
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
    key="employee_filter_top"
)

# ========================================================
# ✅ FILTERS (FIXED ALIGNMENT)
# ========================================================

col1_flt, col2_flt = st.columns(2)

with col1_flt:
    months = ["All"] + sorted(df["Month"].dropna().unique())
    selected_month = st.selectbox(
        "📅 Select Month",
        months,
        key="month_filter_top"
    )

with col2_flt:
    employee_list = ["All"] + sorted(
        df["Employee"].dropna().astype(str).unique()
    )

    selected_employee = st.selectbox(
        "👤 Select Employee",
        employee_list,
        key="employee_filter_bottom"
    )

# ✅ Load data (IMPORTANT ✅)
df = load_attendance()

df.columns = df.columns.str.strip()

df["Date"] = pd.to_datetime(
    df["Date"],
    errors="coerce"
).dt.strftime("%Y-%m-%d")

# ✅ Check if data exists
if df.empty:
    st.info("⚠ No attendance data found")
    st.stop()

# ✅ Ensure Date column exists
if "Date" not in df.columns:
    st.error("❌ Date column missing in data")
    st.stop()

# ✅ Create Month column
df["Month"] = pd.to_datetime(
    df["Date"],
    errors="coerce"
).dt.strftime("%Y-%m")

# ========================================================
# ✅ FILTERS
# ========================================================

col1_mflt, col2_mflt = st.columns(2)

# ✅ Month filter
with col1_mflt:
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
with col2_mflt:
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

unique_employees = (
    monthly_df["Employee"]
    .nunique()
)

full_days = len(
    monthly_df[
        monthly_df["Status"] == "Full Day"
    ]
)

half_days = len(
    monthly_df[
        monthly_df["Status"] == "Half Day"
    ]
)

short_days = len(
    monthly_df[
        monthly_df["Status"] == "Short Day"
    ]
)

col1_kpi, col2_kpi, col3_kpi, col4_kpi, col5_kpi = st.columns(5)

with col1_kpi:
    st.metric("📋 Total Records", total_records)

with col2_kpi:
    st.metric("👥 Employees", unique_employees)

with col3_kpi:
    st.metric("✅ Full Days", full_days)

with col4_kpi:
    st.metric("⏱ Half Days", half_days)

with col5_kpi:
    st.metric("⚠️ Short Days", short_days)

st.divider()

# ============================================================
# ✅ TABLE + DOWNLOAD (WITH INTERACTIVE CALENDAR FILTER)
# ============================================================

if not monthly_df.empty:

    st.markdown("### 📅 Attendance Details")

    # Convert date strings in monthly_df to actual date objects for calendar bounds
    monthly_dates = pd.to_datetime(monthly_df["Date"]).dt.date
    min_month_date = monthly_dates.min()
    max_month_date = monthly_dates.max()

    # Toggle to choose between All Dates or Specific Calendar Date
    col_cal1, col_cal2 = st.columns([1, 2])

    with col_cal1:
        filter_mode = st.radio(
            "Filter View",
            ["All Dates in Month", "Specific Date"],
            horizontal=True,
            key="details_date_filter_mode"
        )

    with col_cal2:
        if filter_mode == "Specific Date":
            selected_calendar_date = st.date_input(
                "📅 Select Date from Calendar",
                value=min_month_date,
                min_value=min_month_date,
                max_value=max_month_date,
                key="attendance_details_calendar"
            )
            date_str_filter = selected_calendar_date.strftime("%Y-%m-%d")
        else:
            date_str_filter = None

    # Filter display DataFrame based on calendar selection
    if date_str_filter:
        display_df = monthly_df[monthly_df["Date"] == date_str_filter]
    else:
        display_df = monthly_df.copy()

    # ✅ Display Table
    if not display_df.empty:
        st.dataframe(display_df, use_container_width=True, hide_index=True)

        st.divider()

        # ✅ Download filtered report
        file_suffix = date_str_filter if date_str_filter else selected_month
        st.download_button(
            label="⬇ Download Selected Report",
            data=display_df.to_csv(index=False).encode("utf-8"),
            file_name=f"attendance_report_{file_suffix}.csv",
            mime="text/csv",
            key="download_monthly_report_btn"
        )
    else:
        st.info(f"⚠ No attendance records found for {date_str_filter}")

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