import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
import requests
from PIL import Image
import re
from PIL import Image
import matplotlib.pyplot as plt
import seaborn as sns
import folium
from streamlit_folium import folium_static
from folium import plugins
import openpyxl

st.set_page_config(layout="wide", page_title="Hopcharge Dashboard", page_icon=":bar_chart:")


# Function to clean license plates
def clean_license_plate(plate):
    match = re.match(r"([A-Z]+[0-9]+)(_R)$", plate)
    if match:
        return match.group(1)
    return plate


def convert_to_datetime_with_current_year(date_string):
    current_year = datetime.now().year
    date = pd.to_datetime(date_string, errors='coerce')
    return date.replace(year=current_year)

def check_credentials():
    st.markdown(
        """
            <style>
                .appview-container .main .block-container {{
                    padding-top: {padding_top}rem;
                    padding-bottom: {padding_bottom}rem;
                    }}

            </style>""".format(
            padding_top=1, padding_bottom=1
        ),
        unsafe_allow_html=True,
    )
    col1, col2, col3 = st.columns(3)

    image = Image.open('LOGO HOPCHARGE-03.png')
    col2.image(image, use_column_width=True)
    col2.markdown(
        "<h2 style='text-align: center;'>ECMS Login</h2>", unsafe_allow_html=True)
    image = Image.open('roaming vans.png')
    col1.image(image, use_column_width=True)

    with col2:
        username = st.text_input("Username")
        password = st.text_input(
            "Password", type="password")
    flag = 0
    if username in st.secrets["username"] and password in st.secrets["password"]:
        index = st.secrets["username"].index(username)
        if st.secrets["password"][index] == password:
            st.session_state["logged_in"] = True
            flag = 1
        else:
            col2.warning("Invalid username or password.")
            flag = 0
    elif username not in st.secrets["username"] or password not in st.secrets["password"]:
        col2.warning("Invalid username or password.")
        flag = 0
    ans = [username, flag]
    return ans


def main_page(username):
    st.markdown(
        """
        <script>
        function refresh() {
            window.location.reload();
        }
        setTimeout(refresh, 120000);
        </script>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <style>
            .appview-container .main .block-container {{
                padding-top: {padding_top}rem;
                padding-bottom: {padding_bottom}rem;
            }}
        </style>
        """.format(padding_top=1, padding_bottom=1),
        unsafe_allow_html=True,
    )
    col1, col2, col3, col4, col5 = st.columns(5)
    col5.write("\n")
    if col5.button("Logout"):
        st.session_state.logged_in = False

    # Function to get data from the API
    def fetch_data(url):
        payload = {
            "username": "admin",
            "password": "Hopadmin@2024#"
        }
        headers = {
            'accept': 'application/json',
            'accept-language': 'en-US,en;q=0.9',
            'authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1aWQiOiI3NDIxZDRmNi0zZWI2LTRhODItOWU0Ny02MWU3MWViOTI5Y2EiLCJlbWFpbCI6ImhlbGxvQGhvcGNoYXJnZS5jb20iLCJwaG9uZU51bWJlciI6Iis5MTkzMTE2NjEyODgsICs5MTkyODkwNDYyOTcsKzkxOTgyMDg1NDAwNiwrOTE4NTg4ODYyNjQ4LCs5MTcwNTM0NTcxMjQiLCJmaXJzdE5hbWUiOiJTdXBlciIsImxhc3ROYW1lIjoiQWRtaW4iLCJjcmVhdGVkIjoiMjAyMS0wNi0wMVQxNzowMTozMC42MjhaIiwidXBkYXRlZCI6IjIwMjQtMDQtMDlUMDU6MTc6NDcuNzQ4WiIsImxhc3RMb2dpbiI6IjIwMjQtMDctMjRUMDU6Mzc6MjMuNTM3WiIsImxhc3RMb2dvdXQiOiIyMDI0LTA0LTA5VDA1OjE3OjQ3Ljc0OVoiLCJ1c2VybmFtZSI6ImFkbWluIiwicm9sZSI6InN1cGVyYWRtaW4iLCJpYXQiOjE3MjE3OTk0NDN9.eg_aP1gUcAJXGX1jNMgFX6CAfeLDSc5JpFFMWVG_ttU'
        }
        response = requests.request("GET", url, headers=headers, data=payload)

        # Print the response text to understand its structure
        # print(response.text)

        # Try to parse the response JSON
        response_json = response.json()
        if 'data' in response_json:
            return pd.json_normalize(response_json['data'])
        else:
            return pd.DataFrame()  # Return an empty DataFrame if 'data' key is not found

    # URLs for the APIs
    url_bookings = "https://2e855a4f93a0.api.hopcharge.com/admin/api/v1/bookings/past?filter={\"chargedAt_lte\":\"2024-06-01\",\"chargedAt_gte\":\"2024-07-30\"}&range=[0,300000]&sort=[\"created\",\"DESC\"]"
    url_drivers = "https://2e855a4f93a0.api.hopcharge.com/admin/api/v1/drivers-shifts/export-list?filter={\"action\":\"exporter\",\"startedAt_lte\":\"2024-06-01\",\"endedAt_gte\":\"2024-07-30\"}"

    # Fetch data from the APIs
    past_bookings_df = fetch_data(url_bookings)
    drivers_shifts_df = fetch_data(url_drivers)

    # Check if the DataFrame is empty
    if past_bookings_df.empty or drivers_shifts_df.empty:
        st.error("No data found in the API response.")
    else:
        # Printing the first few rows of the DataFrame for debugging
        print(past_bookings_df.head())
        print(drivers_shifts_df.head())

        # Calculate shift hours
        drivers_shifts_df['shiftStartedAt'] = pd.to_datetime(drivers_shifts_df['shiftStartedAt'])
        drivers_shifts_df['shiftEndedAt'] = pd.to_datetime(drivers_shifts_df['shiftEndedAt'])
        drivers_shifts_df['Shift_Hours'] = (drivers_shifts_df['shiftEndedAt'] - drivers_shifts_df[
            'shiftStartedAt']).dt.total_seconds() / 3600

        # Create a mapping of driverUid to operator names
        driver_uid_mapping = drivers_shifts_df.groupby('driverUid')[['driverFirstName', 'driverLastName']].apply(
            lambda x: x.iloc[0]['driverFirstName'] + ' ' + x.iloc[0]['driverLastName']).to_dict()

        # For the heatmap, prepare data for V_Mode
        v_mode_drivers_df = drivers_shifts_df[drivers_shifts_df['donorVMode'] == 'TRUE']
        v_mode_drivers_df['Actual OPERATOR NAME'] = v_mode_drivers_df['driverUid'].map(driver_uid_mapping)
        v_mode_drivers_df['licensePlate'] = v_mode_drivers_df['licensePlate'].apply(clean_license_plate)

        # Process V_Mode Data
        v_mode_final_df = v_mode_drivers_df[
            ['licensePlate', 'shiftUid', 'Actual OPERATOR NAME', 'donorVMode', 'shiftStartedAt', 'shiftEndedAt']]
        v_mode_final_df['Actual Date'] = pd.to_datetime(v_mode_final_df['shiftStartedAt'], errors='coerce')
        v_mode_final_df = v_mode_final_df.dropna(subset=['Actual Date'])

        past_bookings_df['Customer Name'] = past_bookings_df['firstName'] + " " + past_bookings_df['lastName']
        past_bookings_df['optChargeStartTime'] = pd.to_datetime(past_bookings_df['optChargeStartTime'], format='mixed',
                                                                errors='coerce')
        past_bookings_df['optChargeEndTime'] = pd.to_datetime(past_bookings_df['optChargeEndTime'], format='mixed',
                                                              errors='coerce')
        past_bookings_df['Reach Time'] = pd.to_datetime(past_bookings_df['optChargeStartTime'], format='mixed',
                                                        errors='coerce')
        past_bookings_df.rename(columns={
            'optBatteryBeforeChrg': 'Actual SoC_Start',
            'optBatteryAfterChrg': 'Actual SoC_End'
        }, inplace=True)
        past_bookings_df['Booking Session time'] = pd.to_datetime(past_bookings_df['fromTime'], format='mixed',
                                                                  errors='coerce')

        # Combine 'driverFirstName' and 'driverLastName' into 'Actual OPERATOR NAME'
        past_bookings_df['Actual OPERATOR NAME'] = past_bookings_df['driverUid'].map(driver_uid_mapping)

        # Calculate t-15_kpi
        def calculate_t_minus_15(row):
            booking_time = row['Booking Session time']
            arrival_time = row['Reach Time']

            time_diff = booking_time - arrival_time

            if time_diff >= timedelta(minutes=15):
                return 1
            elif time_diff < timedelta(seconds=0):
                return 2
            else:
                return 0

        # Apply the function to calculate t-15_kpi
        past_bookings_df['t-15_kpi'] = past_bookings_df.apply(calculate_t_minus_15, axis=1)

        if 'cancelledPenalty' not in past_bookings_df.columns:
            past_bookings_df['cancelledPenalty'] = 0
            past_bookings_df.loc[(past_bookings_df['canceled'] == True) & ((past_bookings_df['optChargeStartTime'] -
                                                                            past_bookings_df[
                                                                                'Reach Time']).dt.total_seconds() / 60 < 15), 'cancelledPenalty'] = 1

        # Filter where donorVMode is False
        filtered_drivers_df = drivers_shifts_df[drivers_shifts_df['donorVMode'] == 'FALSE']
        filtered_drivers_df = filtered_drivers_df.drop_duplicates(subset=['bookingUid'])
        filtered_drivers_df = drivers_shifts_df[drivers_shifts_df['bookingStatus'] == 'completed']

        heatmap_filtered_drivers_df = filtered_drivers_df.drop_duplicates(subset=['bookingUid'])
        heatmap_filtered_drivers_df = drivers_shifts_df[drivers_shifts_df['bookingStatus'] == 'completed']

        # Cleaning license plates
        filtered_drivers_df['licensePlate'] = filtered_drivers_df['licensePlate'].apply(clean_license_plate)
        heatmap_filtered_drivers_df['licensePlate'] = heatmap_filtered_drivers_df['licensePlate'].apply(
            clean_license_plate)

        # Extracting Customer Location City by matching bookingUid with uid from past_bookings_df
        merged_df = pd.merge(filtered_drivers_df, past_bookings_df[
            ['uid', 'location.state', 'Customer Name', 'Actual OPERATOR NAME', 'optChargeStartTime', 'optChargeEndTime',
             'Reach Time', 'Actual SoC_Start', 'Actual SoC_End', 'Booking Session time', 'canceled', 'cancelledPenalty',
             't-15_kpi', 'subscriptionName', 'location.lat', 'location.long']], left_on='bookingUid', right_on='uid',
                             how='left')

        heatmap_merged_df = pd.merge(heatmap_filtered_drivers_df, past_bookings_df[
            ['uid', 'location.state', 'Customer Name', 'Actual OPERATOR NAME', 'optChargeStartTime', 'optChargeEndTime',
             'Reach Time', 'Actual SoC_Start', 'Actual SoC_End', 'Booking Session time', 'canceled', 'cancelledPenalty',
             't-15_kpi', 'subscriptionName', 'location.lat', 'location.long']], left_on='bookingUid', right_on='uid',
                                     how='left')

        # Extracting Actual Date from bookingFromTime
        merged_df['Actual Date'] = pd.to_datetime(merged_df['bookingFromTime'], errors='coerce')
        heatmap_merged_df['Actual Date'] = pd.to_datetime(heatmap_merged_df['bookingFromTime'], errors='coerce')

        # Ensure necessary columns are present, and calculate additional columns if needed
        if 'Day' not in merged_df.columns:
            merged_df['Day'] = merged_df['Actual Date'].dt.day_name()

        if 'Day' not in heatmap_merged_df.columns:
            heatmap_merged_df['Day'] = heatmap_merged_df['Actual Date'].dt.day_name()

        # Selecting and renaming the required columns
        final_df = merged_df[
            ['Actual Date', 'licensePlate', 'location.state', 'bookingUid', 'uid', 'bookingFromTime', 'bookingStatus',
             'customerUid', 'totalUnitsCharged', 'Customer Name', 'Actual OPERATOR NAME', 'optChargeStartTime',
             'optChargeEndTime', 'Day', 'Reach Time', 'Actual SoC_Start', 'Actual SoC_End', 'Booking Session time',
             'canceled', 'cancelledPenalty', 't-15_kpi', 'subscriptionName', 'location.lat', 'location.long',
             'donorVMode']].rename(
            columns={'location.state': 'Customer Location City', 'totalUnitsCharged': 'KWH Pumped Per Session'})

        heatmap_final_df = heatmap_merged_df[
            ['Actual Date', 'licensePlate', 'location.state', 'bookingUid', 'uid', 'shiftUid', 'bookingFromTime',
             'bookingStatus', 'shiftStartedAt', 'shiftEndedAt', 'customerUid', 'totalUnitsCharged', 'Customer Name',
             'Actual OPERATOR NAME', 'optChargeStartTime', 'optChargeEndTime', 'Day', 'Reach Time', 'Actual SoC_Start',
             'Actual SoC_End', 'Booking Session time', 'canceled', 'cancelledPenalty', 't-15_kpi', 'subscriptionName',
             'location.lat', 'location.long', 'donorVMode']].rename(
            columns={'location.state': 'Customer Location City', 'totalUnitsCharged': 'KWH Pumped Per Session'})

        # Ensure that there are no NaT values in the Actual Date column
        final_df = final_df.dropna(subset=['Actual Date'])
        heatmap_final_df = heatmap_final_df.dropna(subset=['Actual Date'])

        # Removing duplicates based on uid and bookingUid
        final_df = final_df.drop_duplicates(subset=['uid', 'bookingUid', 'Actual Date'])
        heatmap_final_df = heatmap_final_df.drop_duplicates(subset=['uid', 'bookingUid', 'Actual Date'])

        # Drop records where totalUnitsCharged is 0
        final_df = final_df[final_df['KWH Pumped Per Session'] != 0]
        heatmap_final_df = heatmap_final_df[heatmap_final_df['KWH Pumped Per Session'] != 0]

        # Printing the first few rows of the DataFrame for debugging
        # st.write(final_df.head())

        # Reading EPOD data from CSV file
        df1 = pd.read_csv('EPOD NUMBER.csv')

        # Data cleaning and transformation
        final_df['licensePlate'] = final_df['licensePlate'].str.upper()
        final_df['licensePlate'] = final_df['licensePlate'].str.replace('HR55AJ4OO3', 'HR55AJ4003')

        heatmap_final_df['licensePlate'] = heatmap_final_df['licensePlate'].str.upper()
        heatmap_final_df['licensePlate'] = heatmap_final_df['licensePlate'].str.replace('HR55AJ4OO3', 'HR55AJ4003')

        # Replace specific license plates
        replace_dict = {
            'HR551305': 'HR55AJ1305',
            'HR552932': 'HR55AJ2932',
            'HR551216': 'HR55AJ1216',
            'HR555061': 'HR55AN5061',
            'HR554745': 'HR55AR4745',
            'HR55AN1216': 'HR55AJ1216',
            'HR55AN8997': 'HR55AN8997'
        }
        final_df['licensePlate'] = final_df['licensePlate'].replace(replace_dict)
        final_df['Actual Date'] = pd.to_datetime(final_df['Actual Date'], format='mixed', errors='coerce')
        final_df = final_df[final_df['Actual Date'].dt.year > 2021]
        final_df['Actual Date'] = final_df['Actual Date'].dt.date
        final_df['Customer Location City'].replace({'Haryana': 'Gurugram', 'Uttar Pradesh': 'Noida'}, inplace=True)
        cities = ['Gurugram', 'Noida', 'Delhi']
        final_df = final_df[final_df['Customer Location City'].isin(cities)]

        merged_df = pd.merge(final_df, df1, on=["licensePlate"])
        final_df = merged_df

        heatmap_final_df['licensePlate'] = heatmap_final_df['licensePlate'].replace(replace_dict)
        heatmap_final_df['Actual Date'] = pd.to_datetime(heatmap_final_df['Actual Date'], format='mixed',
                                                         errors='coerce')
        heatmap_final_df = heatmap_final_df[heatmap_final_df['Actual Date'].dt.year > 2021]
        heatmap_final_df['Actual Date'] = heatmap_final_df['Actual Date'].dt.date
        heatmap_final_df['Customer Location City'].replace({'Haryana': 'Gurugram', 'Uttar Pradesh': 'Noida'},
                                                           inplace=True)
        cities = ['Gurugram', 'Noida', 'Delhi']
        heatmap_final_df = heatmap_final_df[heatmap_final_df['Customer Location City'].isin(cities)]

        heatmap_merged_df = pd.merge(heatmap_final_df, df1, on=["licensePlate"])
        heatmap_final_df = heatmap_merged_df

        shift_data_df = heatmap_final_df.copy()
        shift_data_df = shift_data_df.drop_duplicates(subset=['shiftUid', 'Actual Date'])
        shift_data_df['shiftStartedAt'] = pd.to_datetime(shift_data_df['shiftStartedAt'])
        shift_data_df['shiftEndedAt'] = pd.to_datetime(shift_data_df['shiftEndedAt'])
        shift_data_df['Shift_Hours'] = (shift_data_df['shiftEndedAt'] - shift_data_df[
            'shiftStartedAt']).dt.total_seconds() / 3600

        v_mode_shift_hours_df = v_mode_final_df.copy()
        v_mode_shift_hours_df = v_mode_shift_hours_df.drop_duplicates(subset=['shiftUid', 'Actual Date'])
        v_mode_shift_hours_df['shiftStartedAt'] = pd.to_datetime(v_mode_shift_hours_df['shiftStartedAt'])
        v_mode_shift_hours_df['shiftEndedAt'] = pd.to_datetime(v_mode_shift_hours_df['shiftEndedAt'])
        v_mode_shift_hours_df['Shift_Hours'] = (v_mode_shift_hours_df['shiftEndedAt'] - v_mode_shift_hours_df[
            'shiftStartedAt']).dt.total_seconds() / 3600

        # Add image to the dashboard
        image = Image.open(r'Hpcharge.png')
        col1, col2, col3, col4, col5 = st.columns(5)
        col3.image(image, use_column_width=False)

        # Tabs for different sections
        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(
            ["Executive Dashboard", "Charge Pattern Insights", "EPod Stats", "Subscription Insights",
             "Geographical Insights", "Operators Dashboard", "KM Statistics"])

        with tab6:
            min_date = pd.to_datetime(final_df['Actual Date']).min().date()
            max_date = pd.to_datetime(final_df['Actual Date']).max().date()
            col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(8)

            with col1:
                start_date = st.date_input('Start Date', min_value=min_date, max_value=max_date, value=min_date,
                                           key="ops_start_date")
            with col2:
                end_date = st.date_input('End Date', min_value=min_date, max_value=max_date, value=max_date,
                                         key="ops_end_date")

            start_date = pd.to_datetime(start_date).tz_localize(None)
            end_date = pd.to_datetime(end_date).tz_localize(None)

            final_df['Actual Date'] = pd.to_datetime(final_df['Actual Date']).dt.tz_localize(None)

            filtered_df = final_df[(final_df['Actual Date'] >= start_date) & (final_df['Actual Date'] <= end_date)]

            max_sessions = filtered_df.groupby('Actual OPERATOR NAME')['Actual Date'].count().reset_index()
            max_sessions.columns = ['Actual OPERATOR NAME', 'Max Sessions']

            working_days = shift_data_df.groupby('Actual OPERATOR NAME')['shiftUid'].nunique().reset_index()
            working_days.columns = ['Actual OPERATOR NAME', 'Working Days']

            grouped_df = filtered_df.groupby(['Actual OPERATOR NAME', 'Customer Location City']).size().reset_index()
            grouped_df.columns = ['Operator', 'City', 'Count']

            cities_to_include = final_df['Customer Location City'].dropna().unique()
            grouped_df = grouped_df[grouped_df['City'].isin(cities_to_include)]

            pivot_df = grouped_df.pivot(index='Operator', columns='City', values='Count').fillna(0)

            figure_width = 1.9
            figure_height = 6
            font_size_heatmap = 5
            font_size_labels = 4

            plt.figure(figsize=(figure_width, figure_height), facecolor='none')

            sns.heatmap(pivot_df, cmap='YlGnBu', annot=True, fmt='g', linewidths=0.5, cbar=False,
                        annot_kws={'fontsize': font_size_heatmap})

            plt.title('Operator v/s Locations', fontsize=8, color='black')
            plt.xlabel('Customer Location City', fontsize=font_size_labels, color='black')
            plt.ylabel('Operator', fontsize=font_size_labels, color='black')

            plt.xticks(rotation=0, ha='center', fontsize=font_size_labels, color='black')
            plt.yticks(fontsize=font_size_labels, color='black')

            with col1:
                st.pyplot(plt, use_container_width=False)

            grouped_df = filtered_df.groupby(['Actual OPERATOR NAME', 'Customer Location City']).size().reset_index()
            grouped_df.columns = ['Operator', 'City', 'Count']

            cities_to_include = final_df['Customer Location City'].dropna().unique()
            grouped_df = grouped_df[grouped_df['City'].isin(cities_to_include)]

            cities = np.append(grouped_df['City'].unique(), "All")

            with col3:
                selected_city = st.selectbox('Select City', cities)

            if selected_city == "All":
                city_df = grouped_df
            else:
                city_df = grouped_df[grouped_df['City'] == selected_city]

            total_sessions = city_df.groupby('Operator')['Count'].sum().reset_index()

            # Rename the column to match with 'working_days' DataFrame
            total_sessions.columns = ['Actual OPERATOR NAME', 'Count']

            merged_df = pd.merge(total_sessions, working_days, on='Actual OPERATOR NAME')

            avg_sessions = pd.DataFrame()
            avg_sessions['Actual OPERATOR NAME'] = merged_df['Actual OPERATOR NAME']
            avg_sessions['Avg. Sessions'] = merged_df['Count'] / merged_df['Working Days']
            avg_sessions['Avg. Sessions'] = avg_sessions['Avg. Sessions'].round(0)

            fig_sessions = go.Figure()
            fig_sessions.add_trace(go.Bar(
                x=total_sessions['Actual OPERATOR NAME'],
                y=total_sessions['Count'],
                name='Total Sessions',
                text=total_sessions['Count'],
                textposition='auto',
                marker=dict(color='yellow'),
                width=0.5
            ))
            fig_sessions.add_trace(go.Bar(
                x=avg_sessions['Actual OPERATOR NAME'],
                y=avg_sessions['Avg. Sessions'],
                name='Average Sessions',
                text=avg_sessions['Avg. Sessions'],
                textposition='auto',
                marker=dict(color='green'),
                width=0.38
            ))
            fig_sessions.update_layout(
                title='Total Sessions and Average Sessions per Operator',
                xaxis=dict(title='Operator'),
                yaxis=dict(title='Count / Average Sessions'),
                margin=dict(l=50, r=50, t=80, b=80),
                legend=dict(yanchor="top", y=1.1, xanchor="left", x=0.01, orientation="h"),
                width=1050,
                height=500
            )

            with col4:
                for i in range(1, 10):
                    st.write("\n")
                st.plotly_chart(fig_sessions)

            if selected_city == "All":
                selected_working_days = working_days
            else:
                selected_working_days = working_days[working_days['Actual OPERATOR NAME'].isin(city_df['Operator'])]

            fig_working_days = go.Figure(data=go.Bar(
                x=selected_working_days['Actual OPERATOR NAME'],
                y=selected_working_days['Working Days'],
                marker=dict(color='lightgreen'),
                text=selected_working_days['Working Days']
            ))
            fig_working_days.update_layout(
                title='Working Days per Operator',
                xaxis=dict(title='Operator'),
                yaxis=dict(title='Working Days'),
                margin=dict(l=50, r=50, t=80, b=80),
                width=800,
                height=500
            )

            with col4:
                st.plotly_chart(fig_working_days)

            heatmap_final_df['Actual Date'] = pd.to_datetime(heatmap_final_df['Actual Date']).dt.tz_localize(None)
            shift_data_df['Actual Date'] = pd.to_datetime(shift_data_df['Actual Date']).dt.tz_localize(None)
            v_mode_final_df['Actual Date'] = pd.to_datetime(v_mode_final_df['Actual Date']).dt.tz_localize(None)
            v_mode_shift_hours_df['Actual Date'] = pd.to_datetime(v_mode_shift_hours_df['Actual Date']).dt.tz_localize(
                None)

            heatmap_final_df_filtered = heatmap_final_df[
                (heatmap_final_df['Actual Date'] >= start_date) & (heatmap_final_df['Actual Date'] <= end_date)]
            shift_data_df_filtered = shift_data_df[
                (shift_data_df['Actual Date'] >= start_date) & (shift_data_df['Actual Date'] <= end_date)]
            v_mode_final_df_filtered = v_mode_final_df[
                (v_mode_final_df['Actual Date'] >= start_date) & (v_mode_final_df['Actual Date'] <= end_date)]
            v_mode_shift_hours_df_filtered = v_mode_shift_hours_df[
                (v_mode_shift_hours_df['Actual Date'] >= start_date) & (
                            v_mode_shift_hours_df['Actual Date'] <= end_date)]

            # Calculate required metrics for heatmap
            d_mode_stats = heatmap_final_df_filtered.groupby('Actual OPERATOR NAME').agg(
                Total_Sessions=('Actual Date', 'count'),
                Avg_Sessions=('Actual Date', lambda x: len(x) / x.nunique()),
                Delay_Count=('t-15_kpi', lambda x: (x == 2).sum()),
                D_Mode_Sessions=('donorVMode', lambda x: (x == 'FALSE').sum()),
            ).reset_index()

            # Calculate V_Mode metrics
            v_mode_stats = v_mode_final_df_filtered.groupby('Actual OPERATOR NAME').agg(
                V_Mode_Sessions=('donorVMode', lambda x: (x == 'TRUE').sum()),
            ).reset_index()

            # Combine D_Mode and V_Mode data for shifts
            combined_shift_data = pd.concat([shift_data_df_filtered, v_mode_shift_hours_df_filtered]).drop_duplicates(
                subset=['shiftUid'])

            # Calculate total unique shifts and average shift hours
            total_shifts = combined_shift_data.groupby('Actual OPERATOR NAME').agg(
                Total_Unique_Shifts=('shiftUid', 'nunique'),
                Avg_Shift_Hours=('Shift_Hours', 'mean')
            ).reset_index()

            # Merge D_Mode and V_Mode metrics
            operator_stats = pd.merge(d_mode_stats, v_mode_stats, on='Actual OPERATOR NAME', how='outer').fillna(0)

            # Merge with total shifts and average shift hours
            operator_stats = pd.merge(operator_stats, total_shifts, on='Actual OPERATOR NAME', how='left')

            # Rename columns for better display
            operator_stats.columns = ['Operator', 'Total Sessions', 'Avg Sessions', 'Delay Count', 'D Mode Sessions',
                                      'V Mode Sessions', 'Total Unique Shifts', 'Avg Shift Hours']

            # Display the table
            st.markdown("### Operator Statistics Table")
            st.table(operator_stats[
                         ['Operator', 'Total Sessions', 'Avg Sessions', 'Total Unique Shifts', 'Avg Shift Hours',
                          'Delay Count', 'D Mode Sessions', 'V Mode Sessions']])

            # Export the table to CSV
            csv = operator_stats[
                ['Operator', 'Total Sessions', 'Avg Sessions', 'Total Unique Shifts', 'Avg Shift Hours', 'Delay Count',
                 'D Mode Sessions', 'V Mode Sessions']].to_csv(index=False)

            st.download_button(
                label="Download data as CSV",
                data=csv,
                file_name='operator_statistics.csv',
                mime='text/csv',
            )




if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

if st.session_state.logged_in:
    main_page(st.session_state.username)
else:
    ans = check_credentials()
    if ans[1]:
        st.session_state.logged_in = True
        st.session_state.username = ans[0]
        st.experimental_rerun()




