import streamlit as st
import pandas as pd
import plotly.express as px

# ----------------------------------------------------------------
# Konfigurasi Awal
# ----------------------------------------------------------------
st.set_page_config(page_title="Bike Sharing Analysis", layout="wide")

# Mapping untuk musim dan cuaca
SEASON_MAP = {1: "Spring", 2: "Summer", 3: "Fall", 4: "Winter"}
WEATHER_MAP = {1: "Cerah", 2: "Mendung", 3: "Hujan/Salju Ringan", 4: "Badai"}


# ----------------------------------------------------------------
# Fungsi untuk memuat dan memproses data dengan error handling
# ----------------------------------------------------------------
@st.cache_data
def load_data():
    """
    Memuat data harian dan data per jam dari URL dan melakukan preprocessing.
    Mengembalikan dua DataFrame: days dan hours.
    """
    try:
        days_url = "dashboard/days_processed.csv"
        hours_url = "dashboard/hours_processed.csv"

        days = pd.read_csv(days_url, parse_dates=["date"])
        hours = pd.read_csv(hours_url, parse_dates=["date"])

        # Preprocessing data harian
        days["season"] = days["season_code"].map(SEASON_MAP)
        days["month"] = days["date"].dt.month_name().str[:3]
        days["year"] = days["date"].dt.year
        days["holiday_label"] = days["holiday"].map({True: "Libur", False: "Bukan Libur"})
        days["workingday_label"] = days["workingday"].map({True: "Hari Kerja", False: "Akhir Pekan/Libur"})
        days["weather_label"] = days["weather_condition"].map(WEATHER_MAP)

        # Preprocessing data per jam
        hours["hour"] = hours["hour"].astype(int)
        hours["weather_label"] = hours["weather_condition"].map(WEATHER_MAP)
        hours["season"] = hours["season_code"].map(SEASON_MAP)

        return days, hours
    except Exception as e:
        st.error(f"Gagal memuat data: {str(e)}")
        return pd.DataFrame(), pd.DataFrame()


days_df, hours_df = load_data()

# ----------------------------------------------------------------
# Sidebar: Filter Data dan Metrik Utama
# ----------------------------------------------------------------
st.sidebar.header("Filter Data")

# Filter tahun menggunakan dropdown
selected_year = st.sidebar.selectbox(
    "Pilih Tahun",
    ["Semua"] + sorted(days_df["year"].unique().tolist())
)

# Filter musim dengan multiselect
selected_seasons = st.sidebar.multiselect(
    "Pilih Musim",
    options=list(SEASON_MAP.values()),
    default=list(SEASON_MAP.values())
)

# Filter cuaca dengan multiselect
selected_weather = st.sidebar.multiselect(
    "Pilih Kondisi Cuaca",
    options=list(WEATHER_MAP.values()),
    default=list(WEATHER_MAP.values())
)

# Terapkan filter tahun
if selected_year != "Semua":
    filtered_days = days_df[days_df["year"] == selected_year].copy()
    filtered_hours = hours_df[hours_df["date"].dt.year == selected_year].copy()
else:
    filtered_days = days_df.copy()
    filtered_hours = hours_df.copy()

# Terapkan filter musim dan cuaca pada data harian
filter_cond_days = (
        filtered_days["season"].isin(selected_seasons) &
        filtered_days["weather_label"].isin(selected_weather)
)
filtered_days = filtered_days[filter_cond_days]

# Terapkan filter musim dan cuaca pada data per jam
filter_cond_hours = (
        filtered_hours["season"].isin(selected_seasons) &
        filtered_hours["weather_label"].isin(selected_weather)
)
filtered_hours = filtered_hours[filter_cond_hours]

# Validasi data kosong
if filtered_days.empty:
    st.warning("Tidak ada data yang sesuai dengan filter yang dipilih!")
    st.stop()

if filtered_hours.empty:
    st.warning("Tidak ada data yang sesuai dengan filter yang dipilih!")
    st.stop()

# Tambahan Metrik Kunci di Sidebar
total_rentals = filtered_days["total_rentals"].sum()
avg_daily = filtered_days["total_rentals"].mean()

st.sidebar.markdown("---")
st.sidebar.metric("Total Penyewaan", f"{total_rentals:,} sepeda")
st.sidebar.metric("Rata-rata Harian", f"{avg_daily:.1f} sepeda/hari")


# ----------------------------------------------------------------
# Fungsi untuk Visualisasi
# ----------------------------------------------------------------
@st.cache_data
def process_monthly_data(df):
    """Agregasi data penyewaan per bulan dan tahun."""
    return df.groupby(["month", "year"])["total_rentals"].sum().reset_index()


def plot_monthly_rentals(df):
    """Visualisasi total penyewaan per bulan dengan bar chart."""
    monthly_data = process_monthly_data(df)
    month_order = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    monthly_data["month"] = pd.Categorical(monthly_data["month"], categories=month_order, ordered=True)
    monthly_data = monthly_data.sort_values("month")

    fig = px.bar(
        monthly_data,
        x="month",
        y="total_rentals",
        color="year",
        barmode="group",
        title="Total Penyewaan Sepeda per Bulan",
        labels={"month": "Bulan", "total_rentals": "Total Penyewaan", "year": "Tahun"}
    )
    # Tambahkan hover template dan anotasi untuk puncak penyewaan
    fig.update_traces(hovertemplate="<b>%{x}</b><br>Total: %{y} sepeda<extra></extra>")
    max_val = monthly_data["total_rentals"].max()
    max_month = monthly_data[monthly_data["total_rentals"] == max_val]["month"].iloc[0]
    fig.add_annotation(
        x=max_month,
        y=max_val,
        text="Puncak Penyewaan",
        showarrow=True,
        arrowhead=1
    )
    return fig


def plot_seasonal_distribution(df):
    """Visualisasi distribusi penyewaan per musim dengan bar chart."""
    seasonal_data = df.groupby("season")["total_rentals"].sum().reset_index()
    seasonal_order = ["Spring", "Summer", "Fall", "Winter"]
    seasonal_data["season"] = pd.Categorical(seasonal_data["season"], categories=seasonal_order, ordered=True)
    seasonal_data = seasonal_data.sort_values("season")

    fig = px.bar(
        seasonal_data,
        x="season",
        y="total_rentals",
        color="season",
        title="Distribusi Penyewaan per Musim",
        labels={"total_rentals": "Total Penyewaan", "season": "Musim"},
        category_orders={"season": seasonal_order},
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    return fig


def plot_weather_impact(df):
    """Visualisasi pola penyewaan per jam berdasarkan kondisi cuaca dengan line chart."""
    weather_data = df.groupby(["weather_label", "hour"])["total_rentals"].mean().reset_index()
    fig = px.line(
        weather_data,
        x="hour",
        y="total_rentals",
        color="weather_label",
        title="Pola Penyewaan per Jam Berdasarkan Cuaca",
        labels={"hour": "Jam", "total_rentals": "Rata-rata Penyewaan", "weather_label": "Kondisi Cuaca"}
    )
    return fig


def plot_holiday_vs_workingday(df):
    """Visualisasi perbandingan penyewaan antara hari libur dan hari kerja."""
    holiday_data = df.groupby("holiday_label")["total_rentals"].sum().reset_index()
    fig_holiday = px.bar(
        holiday_data,
        x="holiday_label",
        y="total_rentals",
        color="holiday_label",
        title="Total Penyewaan: Libur vs Bukan Libur",
        labels={"holiday_label": "Kategori Hari", "total_rentals": "Total Penyewaan"}
    )

    workingday_data = df.groupby("workingday_label")["total_rentals"].sum().reset_index()
    fig_workingday = px.bar(
        workingday_data,
        x="workingday_label",
        y="total_rentals",
        color="workingday_label",
        title="Total Penyewaan: Hari Kerja vs Akhir Pekan/Libur",
        labels={"workingday_label": "Kategori Hari", "total_rentals": "Total Penyewaan"}
    )
    return fig_holiday, fig_workingday


def plot_hourly_pattern(df):
    """Visualisasi rata-rata penyewaan per jam dengan bar chart."""
    hourly_data = df.groupby(["hour", "workingday"])["total_rentals"].mean().reset_index()
    fig = px.bar(
        hourly_data,
        x="hour",
        y="total_rentals",
        color="workingday",
        title="Rata-rata Penyewaan Sepeda per Jam",
        labels={"hour": "Jam", "total_rentals": "Rata-rata Penyewaan", "workingday": "Hari Kerja"}
    )
    return fig


def plot_temperature_effect(df):
    """
    Visualisasi pengaruh suhu dan kondisi cuaca pada penyewaan.
    Menambahkan trendline jika modul statsmodels tersedia.
    """
    try:
        fig = px.scatter(
            df,
            x="normalized_temperature",
            y="total_rentals",
            color="weather_label",
            title="Pengaruh Suhu dan Kondisi Cuaca pada Penyewaan Sepeda",
            labels={
                "normalized_temperature": "Suhu Ternormalisasi",
                "total_rentals": "Total Penyewaan",
                "weather_label": "Kondisi Cuaca"
            },
            trendline="ols"
        )
    except ModuleNotFoundError:
        fig = px.scatter(
            df,
            x="normalized_temperature",
            y="total_rentals",
            color="weather_label",
            title="Pengaruh Suhu dan Kondisi Cuaca pada Penyewaan Sepeda (tanpa trendline)",
            labels={
                "normalized_temperature": "Suhu Ternormalisasi",
                "total_rentals": "Total Penyewaan",
                "weather_label": "Kondisi Cuaca"
            }
        )
    return fig


def plot_correlation_heatmap(df):
    """Visualisasi heatmap korelasi antar variabel."""
    corr_data = df[["normalized_temperature", "normalized_humidity", "normalized_wind_speed", "total_rentals"]].corr()
    fig = px.imshow(
        corr_data,
        text_auto=True,
        aspect="auto",
        title="Korelasi antar Variabel"
    )
    return fig


# ----------------------------------------------------------------
# Layout Dashboard: Tab dan Kolom
# ----------------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["Data Harian", "Data Per Jam", "Insights"])

with tab1:
    st.header("Analisis Data Harian")

    # Layout dua kolom: Penyewaan per Bulan dan Distribusi Musiman
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("Penyewaan per Bulan")
        fig_monthly = plot_monthly_rentals(filtered_days)
        st.plotly_chart(fig_monthly, use_container_width=True)
    with col2:
        st.subheader("Distribusi Musiman")
        fig_seasonal = plot_seasonal_distribution(filtered_days)
        st.plotly_chart(fig_seasonal, use_container_width=True)

    st.subheader("Pengaruh Hari Libur & Hari Kerja")
    figure_holiday, figure_workingday = plot_holiday_vs_workingday(filtered_days)
    st.plotly_chart(figure_holiday, use_container_width=True)
    st.plotly_chart(figure_workingday, use_container_width=True)

    st.subheader("Pola Penyewaan per Jam Berdasarkan Cuaca")
    fig_weather = plot_weather_impact(filtered_hours)
    st.plotly_chart(fig_weather, use_container_width=True)

with tab2:
    st.header("Analisis Data Per Jam")

    st.subheader("Pola Penyewaan per Jam")
    fig_hourly = plot_hourly_pattern(filtered_hours)
    st.plotly_chart(fig_hourly, use_container_width=True)

    st.subheader("Pengaruh Suhu dan Kondisi Cuaca")
    fig_temp = plot_temperature_effect(filtered_hours)
    st.plotly_chart(fig_temp, use_container_width=True)

    st.subheader("Korelasi antar Variabel")
    fig_corr = plot_correlation_heatmap(filtered_hours)
    st.plotly_chart(fig_corr, use_container_width=True)

with tab3:
    st.header("Key Insights")
    st.markdown("""
    **Analisis Data Harian:**
    - Penyewaan per bulan divisualisasikan dengan bar chart dan dilengkapi anotasi untuk puncak penyewaan.
    - Distribusi penyewaan per musim menunjukkan musim yang paling dominan.
    - Perbandingan hari libur dan hari kerja mengungkap perbedaan penggunaan sepeda.
    - Pola penyewaan per jam berdasarkan cuaca memberikan insight tambahan mengenai pengaruh lingkungan.

    **Analisis Data Per Jam:**
    - Bar chart menyajikan rata-rata penyewaan per jam untuk identifikasi jam sibuk.
    - Scatter plot menggambarkan pengaruh suhu dan cuaca, dengan trendline jika memungkinkan.
    - Heatmap korelasi membantu mengidentifikasi faktor utama yang memengaruhi penyewaan.
    """)

st.sidebar.markdown("---")
st.sidebar.info("""
**Dashboard Bike Sharing Analysis**
- Data: [Sumber Data](https://raw.githubusercontent.com/Fxf28/projek-analisis-data-1/main/dashboard/days_processed.csv)
- Dibuat dengan Streamlit & Plotly
""")
