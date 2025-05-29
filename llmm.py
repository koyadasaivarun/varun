import logging
logging.basicConfig(level=logging.DEBUG)

import streamlit as st
import pandas as pd
import mysql.connector
from mysql.connector import Error
import datetime

# Benchmark productivity data
urban_productivity = {
    "total_drivers": (571, 544),
    "weekly_off": (13.6, 14.0),
    "special_off": (23.7, 20.7),
    "others": (3.8, 2.0),
    "long_leave": (5.8, 5.0),
    "sick_leave": (4.5, 4.0),
    "spot_absent": (3.6, 2.0),
    "double_duty": (4.9, 4.0),
    "off_cancel": (1.7, 2.0),
    "driver_per_schedule": (2.57, 2.45),
    "drivers_required": (52, -22)
}

rural_productivity = {
    "total_drivers": (365, 365),
    "weekly_off": (12.7, 14.0),
    "special_off": (71.0, 71.0),
    "others": (3.9, 2.0),
    "long_leave": (3.7, 5.0),
    "sick_leave": (6.9, 4.0),
    "spot_absent": (1.2, 2.0),
    "double_duty": (9.7, 10.0),
    "off_cancel": (2.4, 2.0),
    "driver_per_schedule": (2.11, 1.95),
    "drivers_required": (42, -16)
}

# Utility function to show benchmarks beside input
def productivity_hint(label, key, mode, prod_data, type_hint="float"):
    current, estimate = prod_data.get(key, (0, 0))
    hint = f"{label} ({current} → {estimate})"
    return st.number_input(hint, min_value=0.0 if type_hint == "float" else 0, value=float(current) if type_hint == "float" else int(current), key=key)

# Page config
st.set_page_config(layout="wide", page_title="TGSRTC Productivity Dashboard")

# Sidebar
with st.sidebar:
    st.header("Select Depot")
    depot = st.selectbox("Depot", [
        "Mahaboobnagar", "Jagityal", "Khamareddy", "Khammam", "Adilabad",
        "Mahabubabad", "Falaknama", "Ranigunj", "Miryalaguda", "Sangareddy", "Hyderabad-2"
    ])

# Urban/Rural dropdown
mode = st.selectbox("Select Mode", ["Urban", "Rural"])
prod_data = urban_productivity if mode == "Urban" else rural_productivity

# Connect to MySQL database
try:
    conn = mysql.connector.connect(
        host="localhost",
        port=3306,
        user="root",
        password="system",
        database="tgsrtc_db"
    )
    cursor = conn.cursor()
except Error as e:
    st.error(f"Error connecting to MySQL: {e}")
    st.stop()



# Title
st.title("🚌 TGSRTC Driver Productivity Dashboard")

# Schedules
st.header("📅 Schedules")
col1, col2, col3 = st.columns(3)

with col1:
    if depot == "Mahaboobnagar":
        planned_schedules = 60
        st.markdown(f"**Planned Schedules:** {planned_schedules}")
    else:
        planned_schedules = st.number_input("Planned Schedules", min_value=0)
        
    actual_services = st.number_input("Actual Services", min_value=0)
    actual_km = st.number_input("Actual KM", min_value=0)

with col2:
    if depot == "Mahaboobnagar":
        planned_services = 60
        planned_km = 23739
        st.markdown(f"**Planned Services:** {planned_services}")
        st.markdown(f"**Planned KM:** {planned_km}")
    else:
        planned_services = st.number_input("Planned Services", min_value=0)
        planned_km = st.number_input("Planned KM", min_value=0)

with col3:
    service_variance = actual_services - planned_services
    km_variance = actual_km - planned_km
    st.metric("Service Variance", service_variance)
    st.metric("KM Variance", km_variance)


# Drivers
st.header("🧍 Drivers")
col4, col5, col6 = st.columns(3)
with col4:
    total_drivers = productivity_hint("Total Drivers", "total_drivers", mode, prod_data, "int")
    medically_unfit = st.number_input("🩺 Medically Unfit", min_value=0)
    suspended_drivers = st.number_input("❌ Suspended Drivers", min_value=0)
with col5:
    weekly_off = productivity_hint("Weekly Off %", "weekly_off", mode, prod_data, "float")
    special_off = productivity_hint("Special Off %", "special_off", mode, prod_data, "float")
    others = productivity_hint("Others (OD etc.)", "others", mode, prod_data, "float")
with col6:
    long_leave = productivity_hint("Long Leave %", "long_leave", mode, prod_data, "float")
    sick_leave = productivity_hint("Sick Leave %", "sick_leave", mode, prod_data, "float")
    long_absent = st.number_input("Long Absent", min_value=0)
    short_leave = st.number_input("Short Leave", min_value=0)

# Medically Unfit Reasons
st.subheader("🩺 Medically Unfit Reasons")
med_labels = ["Spondilitis", "Spinal Disc", "Vision / Color Blindness", "Neuro", "Paralysis"]
cols_med = st.columns(len(med_labels))
med_reasons = {}
for i, label in enumerate(med_labels):
    with cols_med[i]:
        med_reasons[label] = st.number_input(f"{label}", min_value=0, key=f"med_{i}")
med_total = sum(med_reasons.values())
st.write(f"**Total Medically Unfit (from reasons): {med_total}**")
st.write(f"**Difference: {medically_unfit - med_total}**")

# Sick Leave Reasons
st.subheader("🤒 Sick Leave Reasons")
sick_labels = med_labels
cols_sick = st.columns(len(sick_labels))
sick_reasons = {}
for i, label in enumerate(sick_labels):
    with cols_sick[i]:
        sick_reasons[label] = st.number_input(f"{label}", min_value=0, key=f"sick_{i}")
sick_total = sum(sick_reasons.values())
st.write(f"**Total Sick Leave (from reasons): {sick_total}**")
st.write(f"**Difference: {sick_leave - sick_total}**")

# Availability
available1 = total_drivers - (medically_unfit + suspended_drivers)
available2 = available1 - (weekly_off + special_off + others + long_leave + sick_leave + long_absent + short_leave)

col7, col8, col9 = st.columns(3)
with col7:
    st.metric("Available Drivers-1", available1)
    spot_absent = productivity_hint("Spot Absent %", "spot_absent", mode, prod_data, "float")
with col8:
    attending_drivers = available2 - spot_absent
    st.metric("Available Drivers-2", available2)
with col9:
    st.metric("Attending Drivers", attending_drivers)

# More Stats
st.subheader("📋 Other Driver Stats")
col10, col11, col12 = st.columns(3)
with col10:
    drivers_required = productivity_hint("New Drivers Requirement", "drivers_required", mode, prod_data, "int")
    double_duty = productivity_hint("Double Duty %", "double_duty", mode, prod_data, "float")
with col11:
    driver_per_schedule = productivity_hint("Driver/Schedule Ratio", "driver_per_schedule", mode, prod_data, "float")
    off_cancel = productivity_hint("Weekly Off Cancel %", "off_cancel", mode, prod_data, "float")
with col12:
    drivers_as_conductors = st.number_input("Drivers as Conductors", min_value=0)

driver_shortage = drivers_required - attending_drivers
on_duty = attending_drivers + double_duty + off_cancel
drivers_for_bus = on_duty - drivers_as_conductors
km_per_driver = actual_km / attending_drivers if attending_drivers else 0
services_per_driver = actual_services / attending_drivers if attending_drivers else 0

# Submit to MySQL
if st.button("✅ Submit Data"):
    if conn:
        try:
            query = """
                INSERT INTO productivity_summary (
                    planned_schedules, planned_services, planned_km,
                    actual_services, actual_km, service_variance, km_variance,
                    total_drivers, available1, available2, attending_drivers,
                    driver_shortage, on_duty, drivers_for_bus, km_per_driver,
                    services_per_driver, created_at, medically_unfit, suspended_drivers,
                    weekly_off, special_off, others, long_leave, sick_leave, long_absent,
                    short_leave, spot_absent, drivers_required, double_duty,
                    driver_per_schedule, off_cancel, drivers_as_conductors, entry_date
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """
            values = (
                planned_schedules, planned_services, planned_km,
                actual_services, actual_km, service_variance, km_variance,
                total_drivers, available1, available2, attending_drivers,
                driver_shortage, on_duty, drivers_for_bus, round(km_per_driver, 2),
                round(services_per_driver, 2), datetime.datetime.now(), medically_unfit, suspended_drivers,
                weekly_off, special_off, others, long_leave, sick_leave, long_absent,
                short_leave, spot_absent, drivers_required, double_duty,
                driver_per_schedule, off_cancel, drivers_as_conductors, datetime.date.today()
            )
            cursor.execute(query, values)
            conn.commit()
            st.success("✅ Data inserted into MySQL successfully!")
        except Error as e:
            st.error(f"❌ Failed to insert data: {e}")
    else:
        st.error("❌ No database connection established.")

# Summary
st.header("📊 Summary")
summary_data = {
    "Planned Services": planned_services,
    "Actual Services": actual_services,
    "Service Variance": service_variance,
    "Planned KM": planned_km,
    "Actual KM": actual_km,
    "KM Variance": km_variance,
    "Total Drivers": total_drivers,
    "Available Drivers-1": available1,
    "Available Drivers-2": available2,
    "Attending Drivers": attending_drivers,
    "Driver Shortage": driver_shortage,
    "Drivers on Duty": on_duty,
    "Drivers for Bus Services": drivers_for_bus,
    "KM per Driver": round(km_per_driver, 2),
    "Services per Driver": round(services_per_driver, 2)
}
st.dataframe(pd.DataFrame([summary_data]))

# Close MySQL connection
if conn and conn.is_connected():
    cursor.close()
    conn.close()