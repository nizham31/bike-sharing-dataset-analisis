import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st

sns.set(style='dark')

# HELPER FUNCTIONS 
@st.cache_data
def load_data():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    day_csv_path = os.path.join(current_dir, 'day.csv')
    hour_csv_path = os.path.join(current_dir, 'hour.csv')
    
    df_Day = pd.read_csv(day_csv_path)
    df_Hour = pd.read_csv(hour_csv_path)
    
    # --- RENAME COLUMNS ---
    rename_dict = {
        'dteday':'date', 'yr':'year', 'mnth':'month', 'hr':'hour',
        'holiday':'is_holiday', 'weekday':'day_of_week', 'workingday':'is_workingday',
        'weathersit':'weather_condition', 'temp':'temperature_celsius',
        'atemp':'feels_like_temperature_celsius', 'hum':'humidity_percentage',
        'windspeed':'windspeed_kmh', 'casual':'casual_users',
        'registered':'registered_users', 'cnt':'total_users'
    }
    df_Day.rename(columns=rename_dict, inplace=True)
    df_Hour.rename(columns=rename_dict, inplace=True)

    # --- FIX TYPES ---
    df_Day['date'] = pd.to_datetime(df_Day['date'])
    df_Hour['date'] = pd.to_datetime(df_Hour['date'])

    # --- DENORMALIZE VALUES ---
    for df in [df_Day, df_Hour]:
        df['temperature_celsius'] = df['temperature_celsius'] * 41
        df['humidity_percentage'] = df['humidity_percentage'] * 100
        df['windspeed_kmh'] = df['windspeed_kmh'] * 67

    # --- MAP LABELS ---
    season_map = {1: 'Spring', 2: 'Summer', 3: 'Fall', 4: 'Winter'}
    weather_map = {1: 'Clear/Partly Cloudy', 2: 'Mist/Cloudy', 3: 'Light Snow/Rain', 4: 'Severe Weather'}
    
    df_Day['season_label'] = df_Day['season'].map(season_map)
    df_Day['weather_label'] = df_Day['weather_condition'].map(weather_map)
    df_Hour['season_label'] = df_Hour['season'].map(season_map)
    df_Hour['weather_label'] = df_Hour['weather_condition'].map(weather_map)

    # --- CLUSTERING ---
    def categorize_time(hour):
        if 0 <= hour < 6: return 'Night'
        elif 6 <= hour < 12: return 'Morning'
        elif 12 <= hour < 18: return 'Afternoon'
        else: return 'Evening'
    
    df_Hour['time_category'] = df_Hour['hour'].apply(categorize_time)
    
    # Ordering time category for plotting
    df_Hour['time_category'] = pd.Categorical(df_Hour['time_category'], 
                                              categories=['Morning', 'Afternoon', 'Evening', 'Night'], 
                                              ordered=True)

    return df_Day, df_Hour

df_Day, df_Hour = load_data()

# SIDEBAR FILTER
st.sidebar.header("Data Penyewaan Sepeda")

# Filter Rentang Tanggal
min_date = df_Day['date'].min()
max_date = df_Day['date'].max()

try:
    start_date, end_date = st.sidebar.date_input(
        label='Rentang Waktu',
        min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date]
    )
except ValueError:
    st.error("Mohon pilih rentang tanggal yang valid.")
    st.stop()

# Filter Data Berdasarkan Input User
main_df_Day = df_Day[(df_Day['date'] >= str(start_date)) & 
                     (df_Day['date'] <= str(end_date))]

main_df_Hour = df_Hour[(df_Hour['date'] >= str(start_date)) & 
                       (df_Hour['date'] <= str(end_date))]

# MAIN DASHBOARD LAYOUT
st.title("Bike Sharing Analytics Dashboard")
st.markdown("Dashboard ini menganalisis performa penyewaan sepeda berdasarkan data historis 2011-2012.")

# --- Key Metrics (KPI) ---
col1, col2, col3 = st.columns(3)

total_orders = main_df_Day['total_users'].sum()
total_casual = main_df_Day['casual_users'].sum()
total_registered = main_df_Day['registered_users'].sum()

with col1:
    st.metric("Total Penyewaan", value=f"{total_orders:,.0f}")
with col2:
    st.metric("Casual Users", value=f"{total_casual:,.0f}")
with col3:
    st.metric("Registered Users", value=f"{total_registered:,.0f}")

st.markdown("---")

# --- Tabs untuk Visualisasi ---
tab1, tab2, tab3 = st.tabs(["Tren & Cuaca", "Pola Jam (Clustering)", "Casual vs Registered"])

# TAB 1: Tren Harian & Cuaca
with tab1:
    st.subheader("Performa Harian & Faktor Cuaca")
    
    # Chart 1: Daily Trend
    fig, ax = plt.subplots(figsize=(16, 6))
    ax.plot(main_df_Day['date'], main_df_Day['total_users'], linewidth=2, color="#90CAF9")
    ax.set_title("Tren Penyewaan Sepeda Harian", fontsize=15)
    ax.set_xlabel("Tanggal")
    ax.set_ylabel("Jumlah Penyewa")
    st.pyplot(fig)

    # Chart 2: Season & Weather Impact
    col_a, col_b = st.columns(2)
    
    with col_a:
        fig2, ax2 = plt.subplots(figsize=(10, 6))
        sns.barplot(x='season_label', y='total_users', data=main_df_Day, palette='coolwarm', ax=ax2, errorbar=None)
        ax2.set_title("Rata-rata Penyewaan per Musim")
        st.pyplot(fig2)
        
    with col_b:
        fig3, ax3 = plt.subplots(figsize=(10, 6))
        sns.barplot(x='weather_label', y='total_users', data=main_df_Day, palette='viridis', ax=ax3, errorbar=None)
        ax3.set_title("Rata-rata Penyewaan per Cuaca")
        st.pyplot(fig3)

# TAB 2: Hourly & Clustering 
with tab2:
    st.subheader("Analisis Pola Waktu & Clustering")
    
    # Chart 3: Hourly Trend (Working Day vs Holiday)
    st.markdown("**Pola Penyewaan per Jam: Hari Kerja vs Libur**")
    fig4, ax4 = plt.subplots(figsize=(12, 6))
    sns.pointplot(x='hour', y='total_users', hue='is_workingday', data=main_df_Hour, errorbar=None, ax=ax4)
    ax4.set_title("Puncak Penyewaan: Jam 8 Pagi & 5 Sore (Hari Kerja)")
    ax4.legend(title='Hari Kerja', labels=['Libur', 'Kerja'])
    st.pyplot(fig4)
    
    # Chart 4: Clustering Time Category
    st.markdown("**Clustering Waktu (Pagi/Siang/Sore/Malam)**")
    
    # Hitung rata-rata per kategori
    time_stats = main_df_Hour.groupby('time_category')[['total_users']].mean().reset_index()
    
    fig5, ax5 = plt.subplots(figsize=(10, 5))
    sns.barplot(x='time_category', y='total_users', data=time_stats, palette='magma', ax=ax5)
    ax5.set_title("Kapan Waktu Paling Ramai?")
    st.pyplot(fig5)
    with st.expander("Penjelasan Clustering Waktu"):
        st.write("""
        Teknik Binning digunakan untuk mengelompokkan jam menjadi 4 kategori:
        - **Morning:** 06:00 - 11:00
        - **Afternoon:** 12:00 - 17:00
        - **Evening:** 18:00 - 23:00
        - **Night:** 00:00 - 05:00
        """)

# TAB 3: Casual vs Registered
with tab3:
    st.subheader("Perbandingan Tipe Pengguna")
    
    # Chart 5: Stacked Bar per Day
    # Re-order days for visualization
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    main_df_Day['day_name'] = main_df_Day['date'].dt.day_name()
    
    daily_user_stats = main_df_Day.groupby('day_name')[['casual_users', 'registered_users']].mean().reindex(day_order)
    
    # Melt for plotting
    daily_melt = daily_user_stats.reset_index().melt(id_vars='day_name', var_name='User Type', value_name='Avg Rentals')
    
    fig6, ax6 = plt.subplots(figsize=(12, 6))
    sns.barplot(x='day_name', y='Avg Rentals', hue='User Type', data=daily_melt, palette='Paired', ax=ax6)
    ax6.set_title("Registered (Kerja) vs Casual (Liburan)")
    st.pyplot(fig6)

st.caption("Copyright © 2026 | Dicoding Academy | Nizam Aufar")