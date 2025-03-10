import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Konfigurasi Awal
st.set_page_config(page_title="Bike Sharing Analysis", layout="wide")
sns.set_style("whitegrid")

# Mapping untuk musim dan cuaca
season_map = {1: "Spring", 2: "Summer", 3: "Fall", 4: "Winter"}
weather_map = {1: "Cerah", 2: "Mendung", 3: "Hujan/Salju Ringan", 4: "Hujan Lebat"}


# Fungsi Load Data
@st.cache_data
def load_data():
    days_url = "https://raw.githubusercontent.com/Fxf28/projek-analisis-data-1/main/dashboard/days_processed.csv"
    hours_url = "https://raw.githubusercontent.com/Fxf28/projek-analisis-data-1/main/dashboard/hours_processed.csv"

    days = pd.read_csv(days_url, parse_dates=["date"])
    hours = pd.read_csv(hours_url, parse_dates=["date"])

    # Preprocessing untuk data harian
    days["season"] = days["season_code"].map(season_map)
    days["month"] = days["date"].dt.month_name().str[:3]
    days["holiday_label"] = days["holiday"].map({True: "Libur", False: "Bukan Libur"})
    days["workingday_label"] = days["workingday"].map({True: "Hari Kerja", False: "Akhir Pekan/Libur"})
    days["year"] = days["date"].dt.year

    # Preprocessing untuk data per jam
    hours["hour"] = hours["hour"].astype(int)
    hours["weather_label"] = hours["weather_condition"].map(weather_map)
    hours["season"] = hours["season_code"].map(season_map)

    return days, hours


days_df, hours_df = load_data()

# Sidebar Filter
st.sidebar.header("Filter Data")
selected_year = st.sidebar.selectbox("Pilih Tahun", ["Semua", 2012, 2011])

# Apply Filter
if selected_year != "Semua":
    days_df = days_df[days_df["year"] == selected_year]
    hours_df = hours_df[hours_df["date"].dt.year == selected_year]

# Main Dashboard
st.title("Analisis Penyewaan Sepeda")
tab1, tab2, tab3 = st.tabs(["Data Harian", "Data Per Jam", "Insights"])

with tab1:
    st.header("Analisis Data Harian")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Tren Bulanan")
        days_df["year"] = days_df["year"].astype(str)
        year_palette = {"2011": "blue", "2012": "orange"}
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.lineplot(
            data=days_df,
            x="month",
            y="total_rentals",
            hue="year",
            marker="o",
            palette=year_palette,
            ax=ax
        )
        ax.set_xticks(range(12))
        ax.set_xticklabels(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
        ax.set_xlabel("Bulan")
        ax.set_ylabel("Total Penyewaan")
        st.pyplot(fig)

        st.markdown("**Insight Tren Bulanan:**")
        st.markdown("""
        - **Peningkatan Penyewaan:** Terjadi peningkatan penyewaan dari April hingga mencapai puncak pada bulan Juni.
        - **Perbandingan Tahun:** Data menunjukkan bahwa tahun **2012** memiliki kenaikan penyewaan yang lebih signifikan dibandingkan tahun **2011**.
        - **Penurunan di Akhir Tahun:** Penyewaan menurun tajam pada bulan Desember, kemungkinan akibat kondisi cuaca ekstrem.
        """)

    with col2:
        st.subheader("Distribusi per Musim")
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.boxplot(
            data=days_df,
            x="season",
            y="total_rentals",
            hue="season",
            palette="Set2",
            legend=False,
            ax=ax
        )
        ax.set_xlabel("Musim")
        ax.set_ylabel("Total Penyewaan")
        st.pyplot(fig)

        st.markdown("**Insight Distribusi Musiman:**")
        st.markdown("""
        - **Musim Terbaik:** Musim Panas dan Gugur menunjukkan median penyewaan yang lebih tinggi.
        - **Variabilitas:** Musim Dingin memiliki penyewaan yang lebih rendah dengan beberapa outlier, sedangkan musim Semi menunjukkan fluktuasi yang besar.
        """)

    st.subheader("Pengaruh Hari Libur & Hari Kerja")
    fig, ax = plt.subplots(1, 2, figsize=(15, 5))

    sns.barplot(
        data=days_df,
        x="holiday_label",
        y="total_rentals",
        hue="holiday_label",
        palette={"Libur": "#e74c3c", "Bukan Libur": "#7f8c8d"},
        errorbar=('ci', 95),
        legend=False,
        ax=ax[0]
    )
    ax[0].set_title("Hari Libur vs Bukan Libur")
    ax[0].set_xlabel("")
    ax[0].set_ylabel("Total Penyewaan")

    sns.barplot(
        data=days_df,
        x="workingday_label",
        y="total_rentals",
        hue="workingday_label",
        palette={"Hari Kerja": "#2ecc71", "Akhir Pekan/Libur": "#3498db"},
        errorbar=('ci', 95),
        ax=ax[1]
    )
    legend = ax[0].get_legend()
    if legend is not None:
        legend.remove()
    ax[1].set_title("Hari Kerja vs Bukan Hari Kerja")
    ax[1].set_xlabel("")
    ax[1].set_ylabel("")

    st.pyplot(fig)

    st.markdown("**Insight Hari Libur & Hari Kerja:**")
    st.markdown("""
    - **Hari Kerja:** Penyewaan lebih tinggi dengan dua puncak utama, mengindikasikan penggunaan sepeda untuk keperluan komuter.
    - **Hari Libur:** Penyewaan menurun, mencerminkan penurunan aktivitas komuter dan kecenderungan rekreasional.
    """)

with tab2:
    st.header("Analisis Data Per Jam")

    # Plot utama: Pola Penyewaan per Jam
    st.subheader("Pola Penyewaan per Jam")
    hours_df["workingday"] = hours_df["workingday"].astype(str)
    workingday_palette = {"Hari Kerja": "blue", "Hari Libur": "red"}
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.lineplot(
        data=hours_df,
        x="hour",
        y="total_rentals",
        hue="workingday",
        palette=workingday_palette,
        ax=ax
    )
    ax.set_xticks(range(0, 24))
    ax.set_xlabel("Jam")
    ax.set_ylabel("Total Penyewaan")
    st.pyplot(fig)

    st.markdown("**Insight Pola Penyewaan Per Jam:**")
    st.markdown("""
    - **Pola Harian:** Grafik per jam menunjukkan puncak penyewaan pada jam 08:00 dan 17:00-18:00 pada hari kerja, mencerminkan penggunaan sepeda sebagai alat transportasi komuter.
    - **Hari Libur:** Pada hari libur, pola penyewaan lebih merata tanpa puncak yang tajam.
    """)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Pengaruh Cuaca")
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.scatterplot(
            data=hours_df,
            x="normalized_temperature",
            y="total_rentals",
            hue="weather_label",
            palette="cool",
            ax=ax
        )
        ax.set_xlabel("Suhu Ternormalisasi")
        ax.set_ylabel("Total Penyewaan")
        st.pyplot(fig)

        st.markdown("**Insight Pengaruh Cuaca:**")
        st.markdown("""
        - **Suhu Optimal:** Peningkatan suhu mendekati nilai optimal secara signifikan meningkatkan penyewaan.
        - **Cuaca Buruk:** Kondisi seperti hujan atau salju menyebabkan penurunan drastis dalam penyewaan per jam.
        """)

    with col2:
        st.subheader("Korelasi Variabel")
        corr = hours_df[["normalized_temperature", "normalized_humidity",
                         "normalized_wind_speed", "total_rentals"]].corr()
        fig, ax = plt.subplots(figsize=(8, 6))
        sns.heatmap(corr, annot=True, cmap="coolwarm", ax=ax)
        st.pyplot(fig)

        st.markdown("**Insight Korelasi Variabel:**")
        st.markdown("""
        - **Korelasi Suhu:** Suhu memiliki korelasi positif yang kuat dengan jumlah penyewaan.
        - **Korelasi Negatif:** Kelembapan dan kecepatan angin menunjukkan korelasi negatif, yang mengindikasikan bahwa kondisi lingkungan yang tidak mendukung menurunkan permintaan.
        """)

with tab3:
    st.header("Key Insights")

    st.subheader("Temuan Utama")
    st.markdown("""
    **Analisis Data Harian:**
    - Tren bulanan menunjukkan peningkatan signifikan penyewaan dari awal hingga pertengahan tahun, dengan puncak di bulan Juni.
    - Distribusi musiman mengungkap bahwa Musim Panas dan Gugur memiliki performa terbaik, sedangkan Musim Dingin cenderung lebih rendah.
    - Hari kerja mendominasi penggunaan sepeda, yang mengindikasikan peran penting sepeda sebagai moda transportasi untuk komuter.

    **Analisis Data Per Jam:**
    - Pola per jam mengungkapkan puncak penyewaan pada jam sibuk (pagi dan sore) pada hari kerja, sementara hari libur menunjukkan distribusi yang lebih stabil.
    - Kondisi cuaca secara signifikan mempengaruhi penyewaan, dengan suhu optimal meningkatkan permintaan dan cuaca buruk menurunkan penyewaan.
    - Korelasi antar variabel menekankan bahwa suhu adalah faktor utama yang mempengaruhi jumlah penyewaan per jam.
    """)

    st.subheader("Rekomendasi Bisnis")
    st.markdown("""
    - **Optimasi Armada:** Tingkatkan jumlah sepeda pada jam sibuk (pagi dan sore) terutama di hari kerja.
    - **Integrasi Cuaca:** Implementasikan sistem peringatan cuaca real-time untuk menyesuaikan distribusi sepeda.
    - **Strategi Pemasaran:** Fokuskan promosi pada periode dengan penyewaan tinggi dan pertimbangkan diskon saat cuaca buruk.
    - **Analisis Lanjutan:** Lakukan penelitian lebih mendalam untuk mengidentifikasi faktor-faktor lain yang dapat meningkatkan efisiensi operasional.
    """)

st.sidebar.markdown("---")
st.sidebar.info("""
**Dashboard Bike Sharing Analysis**
- Data: [Capital Bikeshare](https://www.capitalbikeshare.com/system-data)
- Dibuat dengan Streamlit
- MC828D5Y0055 Faiz Fajar MC-21
""")