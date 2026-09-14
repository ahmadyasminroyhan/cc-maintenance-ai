import streamlit as st
import pandas as pd
import plotly.express as px
from database import get_all_data, tambah_data, hapus_data
from ai_agent import tanyakan_ke_ai

st.set_page_config(page_title="Sistem Maintenance CC AI", layout="wide")

st.title("🚜 Sistem Analisis & Maintenance Container Crane Berbasis AI")

# Menu Navigasi
menu = st.sidebar.selectbox("Pilih Menu:", [
    "🤖 Chatbot AI", 
    "📊 Dashboard Analytics", 
    "📋 Lihat Data Database", 
    "➕ Tambah Data", 
    "🗑️ Hapus Data"
])

# ---------------- MENU 1: CHATBOT AI ----------------
if menu == "🤖 Chatbot AI":
    st.subheader("💬 Tanya Jawab Data Kerusakan & Maintenance")
    st.caption("Kamu bisa menanyakan tren kerusakan, perbandingan bulan, bagian paling sering rusak, dll.")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Tanyakan sesuatu (contoh: 'Berapa perbaikan di bulan September 2026?')"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Menganalisis database..."):
                try:
                    jawaban, query_dijalankan = tanyakan_ke_ai(prompt)
                    st.markdown(jawaban)
                    
                    with st.expander("🔍 Lihat Query Database (SQL) yang digunakan AI"):
                        st.code(query_dijalankan, language="sql")
                        
                    st.session_state.messages.append({"role": "assistant", "content": jawaban})
                except Exception as e:
                    st.error(f"Terjadi kesalahan saat menghubungkan ke AI: {e}")

# ---------------- MENU 2: DASHBOARD ANALYTICS ----------------
elif menu == "📊 Dashboard Analytics":
    st.subheader("📊 Visualisasi & Analisis Data Maintenance")
    df = get_all_data()

    if not df.empty:
        # Ringkasan Atas
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Kejadian", len(df))
        c2.metric("Total Downtime", f"{df['downtime_jam'].sum()} Jam")
        c3.metric("Rata-rata Downtime", f"{round(df['downtime_jam'].mean(), 1)} Jam")
        c4.metric("CC Paling Sering Rusak", df['no_cc'].mode()[0])

        st.markdown("---")

        # Baris Grafik Pertama
        col_grafik1, col_grafik2 = st.columns(2)

        with col_grafik1:
            st.write("### 🛠️ Jumlah Kerusakan per Sistem")
            df_sistem = df['sistem'].value_counts().reset_index()
            df_sistem.columns = ['Sistem', 'Jumlah']
            fig_sistem = px.bar(df_sistem, x='Sistem', y='Jumlah', color='Sistem', text='Jumlah',
                                title="Distribusi Kerusakan Berdasarkan Sistem")
            st.plotly_chart(fig_sistem, use_container_width=True)

        with col_grafik2:
            st.write("### 🏗️ Kerusakan per Container Crane (CC)")
            df_cc = df['no_cc'].value_counts().reset_index()
            df_cc.columns = ['No CC', 'Jumlah']
            fig_cc = px.pie(df_cc, names='No CC', values='Jumlah', hole=0.4,
                            title="Persentase Kerusakan per Unit Crane")
            st.plotly_chart(fig_cc, use_container_width=True)

        st.markdown("---")

        # Baris Grafik Kedua: Downtime per Komponen
        st.write("### ⏱️ Total Downtime (Jam) Berdasarkan Komponen")
        df_downtime = df.groupby('komponen')['downtime_jam'].sum().reset_index()
        fig_downtime = px.bar(df_downtime, x='komponen', y='downtime_jam', color='downtime_jam',
                              labels={'downtime_jam': 'Total Jam Downtime', 'komponen': 'Komponen'},
                              title="Komponen Penyebab Downtime Terlama")
        st.plotly_chart(fig_downtime, use_container_width=True)

    else:
        st.info("Belum ada data untuk ditampilkan dalam bentuk grafik.")

# ---------------- MENU 3: LIHAT DATA ----------------
elif menu == "📋 Lihat Data Database":
    st.subheader("📋 Riwayat Kerusakan & Perbaikan (Real Database)")
    df = get_all_data()
    
    if not df.empty:
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Perbaikan", len(df))
        col2.metric("Total Downtime (Jam)", f"{df['downtime_jam'].sum()} Jam")
        col3.metric("CC Paling Sering Rusak", df['no_cc'].mode()[0])
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Belum ada data perbaikan di database.")

# ---------------- MENU 4: TAMBAH DATA ----------------
elif menu == "➕ Tambah Data":
    st.subheader("➕ Tambah Record Perbaikan Baru")
    with st.form("form_tambah", clear_on_submit=True):
        tanggal = st.date_input("Tanggal Kerusakan")
        no_cc = st.text_input("Nomor CC (Contoh: CC01)")
        sistem = st.selectbox("Sistem", ["Hoist", "Trolley", "Gantry", "Spreader", "Lainnya"])
        komponen = st.text_input("Nama Komponen (Contoh: Brake, Motor)")
        jenis_kerusakan = st.text_area("Jenis Kerusakan")
        penyebab = st.text_area("Penyebab Kerusakan")
        tindakan = st.text_area("Tindakan Perbaikan")
        downtime_jam = st.number_input("Downtime (Jam)", min_value=0.0, step=0.5)
        
        submitted = st.form_submit_button("Simpan Data")
        if submitted:
            if no_cc.strip() == "" or komponen.strip() == "":
                st.error("Nomor CC dan Nama Komponen tidak boleh kosong!")
            else:
                tambah_data(str(tanggal), no_cc, sistem, komponen, jenis_kerusakan, penyebab, tindakan, downtime_jam)
                st.success(f"Data perbaikan untuk {no_cc} berhasil disimpan!")

# ---------------- MENU 5: HAPUS DATA ----------------
elif menu == "🗑️ Hapus Data":
    st.subheader("🗑️ Hapus Record Perbaikan")
    df = get_all_data()
    if not df.empty:
        st.dataframe(df[["id", "tanggal", "no_cc", "jenis_kerusakan"]], use_container_width=True)
        id_hapus = st.number_input("Masukkan ID Data yang Ingin Dihapus:", min_value=1, step=1)
        if st.button("Hapus Data"):
            hapus_data(id_hapus)
            st.warning(f"Data ID {id_hapus} dihapus!")
            st.rerun()