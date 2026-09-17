import os
import google.generativeai as genai
import pandas as pd
import plotly.express as px
import streamlit as st

# =========================================================
# 🔑 PASANG API KEY GEMINI LANGSUNG DI SINI
# =========================================================
GEMINI_API_KEY = "AQ.Ab8RN6KAx02YD9THgSin9eLiw_ibO6147ZvYDbx_MUDxg-Czwg"  # Masukkan API Key kamu

# ---------------------------------------------------------
# 1. KONFIGURASI HALAMAN
# ---------------------------------------------------------
st.set_page_config(
    page_title="SIM-CC | Analytics & Maintenance System",
    page_icon="🏗️",
    layout="wide",
)

st.markdown(
    """
    <meta name="google" content="notranslate">
    <style>
        html, body, [class*="css"] {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .main-header {
            background: linear-gradient(90deg, #0F52BA 0%, #1E3C72 100%);
            padding: 20px;
            border-radius: 10px;
            color: white;
            text-align: center;
            margin-bottom: 20px;
        }
    </style>
""",
    unsafe_allow_html=True,
)

st.markdown('<div class="notranslate">', unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. DATABASE PERMANEN & INISIALISASI SESSION STATE
# ---------------------------------------------------------
MASTER_FILE = "database_master.xlsx"

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "messages" not in st.session_state:
    st.session_state.messages = []


def load_master_database():
    sheets = {}
    if os.path.exists(MASTER_FILE):
        try:
            xls = pd.ExcelFile(MASTER_FILE)
            for sname in xls.sheet_names:
                sheets[sname] = pd.read_excel(MASTER_FILE, sheet_name=sname)
        except Exception:
            pass
    return sheets


def save_master_database(sheets_dict):
    try:
        with pd.ExcelWriter(MASTER_FILE, engine="openpyxl") as writer:
            for sname, df in sheets_dict.items():
                df.to_excel(writer, sheet_name=sname, index=False)
    except Exception as e:
        st.error(f"Gagal menyimpan database master: {e}")


if "data_sheets" not in st.session_state:
    st.session_state.data_sheets = load_master_database()

# ---------------------------------------------------------
# PERBAIKAN 1: Validasi API Key Fleksibel & Tepat
# ---------------------------------------------------------
clean_api_key = GEMINI_API_KEY.strip() if GEMINI_API_KEY else ""
ai_is_active = False

if clean_api_key and "MASUKKAN_API_KEY" not in clean_api_key and len(clean_api_key) > 5:
    try:
        genai.configure(api_key=clean_api_key)
        ai_is_active = True
    except Exception:
        ai_is_active = False

# ---------------------------------------------------------
# 3. PORTAL LOGIN
# ---------------------------------------------------------
if not st.session_state.logged_in:
    st.markdown(
        """
        <div class="main-header">
            <h1>🔒 Portal Login SIM-CC</h1>
            <p>Sistem Pemantauan Kinerja Operasional & Breakdown Crane Harian</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form(key="login_form"):
            st.subheader("🔑 Kredensial Masuk")
            username = st.text_input("Username", placeholder="admin")
            password = st.text_input(
                "Password", type="password", placeholder="••••••••"
            )
            btn_login = st.form_submit_button("Masuk Aplikasi")

            if btn_login:
                if username == "admin" and password == "11111":
                    st.session_state.logged_in = True
                    st.success("Login berhasil!")
                    st.rerun()
                else:
                    st.error("Username atau Password salah!")
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()


# ---------------------------------------------------------
# 4. PARSER & MULTI-FILE MERGE LOGIC
# ---------------------------------------------------------
def process_and_merge_files(uploaded_files):
    merged = st.session_state.data_sheets.copy()

    for up_file in uploaded_files:
        try:
            xls = pd.ExcelFile(up_file)
            for sname in xls.sheet_names:
                df_new = pd.read_excel(up_file, sheet_name=sname)
                if sname in merged and not merged[sname].empty:
                    merged[sname] = pd.concat(
                        [merged[sname], df_new], ignore_index=True
                    ).drop_duplicates()
                else:
                    merged[sname] = df_new
        except Exception as e:
            st.error(f"Eror membaca file {up_file.name}: {e}")

    return merged


# ---------------------------------------------------------
# 5. SIDEBAR (MULTI-FILE UPLOADER & RESET)
# ---------------------------------------------------------
st.sidebar.markdown("### 👤 Informasi User")
st.sidebar.info("Logged in as: **Administrator**")

if st.sidebar.button("🗑️ Reset Database Master"):
    if os.path.exists(MASTER_FILE):
        os.remove(MASTER_FILE)
    st.session_state.data_sheets = {}
    st.session_state.messages = []
    st.sidebar.success("Database berhasil dikosongkan!")
    st.rerun()

if st.sidebar.button("🚪 Keluar"):
    st.session_state.logged_in = False
    st.rerun()

st.sidebar.divider()
st.sidebar.markdown("### 📁 Upload File Performance Excel")
uploaded_files = st.sidebar.file_uploader(
    "Unggah satu atau beberapa file Excel sekaligus:",
    type=["xlsx", "xls"],
    accept_multiple_files=True,
)

if uploaded_files:
    if st.sidebar.button("📥 Proses & Gabungkan Ke Database"):
        merged_db = process_and_merge_files(uploaded_files)
        st.session_state.data_sheets = merged_db
        save_master_database(merged_db)
        st.sidebar.success("✅ File berhasil digabungkan secara kumulatif!")
        st.rerun()

# ---------------------------------------------------------
# 6. DASHBOARD UTAMA
# ---------------------------------------------------------
st.markdown(
    """
    <div class="main-header">
        <h1>🏗️ SIM-CC: Pemantauan & Analisis Container Crane</h1>
        <p>Sistem Pemantauan Kinerja Operasional & Breakdown Crane Harian</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Ekstraksi Sheet dari Database Master
df_wo = pd.DataFrame()
for key in st.session_state.data_sheets.keys():
    if "WORK ORDER" in key.upper() or "WO" in key.upper():
        df_wo = st.session_state.data_sheets[key]
        break

# Ekstraksi Breakdown Frequency Sheet
df_bd_freq = pd.DataFrame()
for key in st.session_state.data_sheets.keys():
    if "FREQ" in key.upper():
        df_bd_freq = st.session_state.data_sheets[key]
        break

st.divider()

# ---------------------------------------------------------
# 7. TAB ANALISIS & DIAGRAM
# ---------------------------------------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    [
        "📊 Ringkasan Kinerja Harian",
        "🚨 Rincian Berdasarkan Frekuensi",
        "📈 Analisis Diagram",
        "📋 Daftar Perintah Kerja (WO)",
        "🤖 Asisten Analis AI",
    ]
)

# TAB 1: SUMMARY DAILY PERFORMANCE
with tab1:
    st.subheader("Matriks Kinerja Harian Crane")
    sd_sheet = None
    for k in st.session_state.data_sheets.keys():
        if "SUMMARY" in k.upper() or "DAILY" in k.upper():
            sd_sheet = st.session_state.data_sheets[k]
            break

    if sd_sheet is not None and not sd_sheet.empty:
        st.dataframe(sd_sheet, use_container_width=True)
    else:
        st.info("Unggah berkas Excel di sidebar untuk melihat data.")

# TAB 2: BREAKDOWN BY FREQUENCY
with tab2:
    st.subheader("Frekuensi Breakdown per Subsystem & Asset CC")
    if not df_bd_freq.empty:
        st.dataframe(df_bd_freq, use_container_width=True)
    else:
        st.info("Belum ada data frekuensi breakdown.")

# TAB 3: DIAGRAM ANALYTICS
with tab3:
    st.subheader("Visualisasi Diagram & Trend Kinerja")
    if not df_wo.empty:
        col_g1, col_g2 = st.columns(2)

        with col_g1:
            st.markdown("##### **Distribusi Problem Code / Kerusakan**")
            prob_cols = [
                c
                for c in df_wo.columns
                if "PROBLEM" in str(c).upper() or "CODE" in str(c).upper()
            ]
            if prob_cols:
                prob_counts = (
                    df_wo[prob_cols[0]]
                    .value_counts()
                    .reset_index()
                    .head(7)
                )
                prob_counts.columns = ["Problem_Code", "Jumlah"]
                fig_prob = px.bar(
                    prob_counts,
                    x="Problem_Code",
                    y="Jumlah",
                    text="Jumlah",
                    color="Jumlah",
                    color_continuous_scale="Reds",
                )
                st.plotly_chart(fig_prob, use_container_width=True)
            else:
                st.write("Kolom Problem Code tidak ditemukan.")

        with col_g2:
            st.markdown("##### **Jumlah Work Order per Unit Asset (CC)**")
            asset_cols = [
                c for c in df_wo.columns if "ASSET" in str(c).upper()
            ]
            if asset_cols:
                asset_counts = (
                    df_wo[asset_cols[0]].value_counts().reset_index()
                )
                asset_counts.columns = ["Asset", "Total_WO"]
                fig_asset = px.bar(
                    asset_counts,
                    x="Asset",
                    y="Total_WO",
                    text="Total_WO",
                    color="Total_WO",
                    color_continuous_scale="Blues",
                )
                st.plotly_chart(fig_asset, use_container_width=True)
            else:
                st.write("Kolom Asset tidak ditemukan.")

    else:
        st.info("Diagram akan otomatis ditampilkan setelah file Excel dimuat.")

# TAB 4: LIST OF WORK ORDERS
with tab4:
    st.subheader("Daftar Perintah Kerja (Work Orders)")
    if not df_wo.empty:
        st.dataframe(df_wo, use_container_width=True)
    else:
        st.info("Data Work Order kosong.")

# TAB 5: ASISTEN ANALIS AI SOLUTIF & PRESISI (PEMBACAAN UTUH PER-CC)
with tab5:
    st.subheader("🤖 Asisten Analis AI Pemeliharaan Crane")

    if not ai_is_active:
        st.warning(
            "⚠️ API Key belum terpasang dengan benar di dalam kode Python."
        )

    # Tampilkan Riwayat Chat Interaktif
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    user_query = st.chat_input("Ketik pertanyaan analisis kamu di sini...")

    if user_query:
        st.session_state.messages.append(
            {"role": "user", "content": user_query}
        )
        with st.chat_message("user"):
            st.write(user_query)

        if not ai_is_active:
            err_msg = "AI belum aktif. Pastikan API Key Gemini di baris 11 sudah diisi dengan benar."
            st.session_state.messages.append(
                {"role": "assistant", "content": err_msg}
            )
            with st.chat_message("assistant"):
                st.error(err_msg)
        else:
            # Mengelompokkan Data Per-Asset/CC Agar Pembacaan AI Sangat Presisi
            grouped_context = "=== DATABASE KESELURUHAN TERKELOMPOK PER CONTAINER CRANE (CC/QC) ===\n\n"

            if not df_wo.empty:
                asset_cols = [
                    c for c in df_wo.columns if "ASSET" in str(c).upper()
                ]
                if asset_cols:
                    grouped_assets = df_wo.groupby(asset_cols[0])
                    for asset_name, group in grouped_assets:
                        grouped_context += f"--- UNIT CONTAINER CRANE: {asset_name} (Total: {len(group)} WO) ---\n"
                        grouped_context += group.astype(str).to_csv(
                            index=False
                        )
                        grouped_context += "\n"
                else:
                    grouped_context += df_wo.astype(str).to_csv(index=False)
            else:
                grouped_context += "Data Work Orders Kosong.\n"

            # Memasukkan Sheet Pendukung Lainnya
            for sname, df_s in st.session_state.data_sheets.items():
                if "WORK ORDER" not in sname.upper() and not df_s.empty:
                    grouped_context += f"\n=== SHEET STATISTIK: {sname} ===\n"
                    grouped_context += df_s.astype(str).to_csv(index=False)

            system_prompt = f"""
            Kamu adalah Asisten AI Pakar Pemeliharaan & Senior Engineer Container Crane (CC).

            TUGAS & PENALARAN SANGAT AKURAT:
            1. Jawab pertanyaan pengguna dengan menganalisis KESELURUHAN data per-CC/Asset di bawah ini.
            2. Hitung jumlah transaksi, jenis kerusakan, dan durasi secara eksak dari tabel data.
            3. JIKA detail spesifik yang ditanyakan pengguna TIDAK ADA dalam catatan log:
               - Jelaskan bahwa detail spesifik tersebut tidak tercatat di database.
               - SEGERA BERIKAN rekomendasi teknis, standar SOP pemeliharaan (PM/CM), atau langkah-langkah troubleshooting standar untuk Container Crane yang valid, profesional, dan solutif.
            4. Gunakan bahasa yang rapi, terstruktur, dan teknis.

            --- DATABASE PEMELIHARAAN CONTAINER CRANE (UTUH & KUMULATIF) ---
            {grouped_context[:60000]}
            """

            full_prompt = f"{system_prompt}\n\nPertanyaan: {user_query}"

            with st.chat_message("assistant"):
                with st.spinner("Menganalisis seluruh database & menyusun jawaban..."):
                    # PERBAIKAN 2: Menggunakan Nama Model Standar yang Valid (gemini-1.5-flash / gemini-1.5-pro)
                    try:
                        model = genai.GenerativeModel("gemini-3.6-flash")
                        response = model.generate_content(full_prompt)
                        ai_reply = response.text
                    except Exception:
                        try:
                            model = genai.GenerativeModel("gemini-1.5-pro")
                            response = model.generate_content(full_prompt)
                            ai_reply = response.text
                        except Exception as ex:
                            ai_reply = f"Gagal memproses analisis AI: {ex}"

                    st.write(ai_reply)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": ai_reply}
                    )

st.markdown("</div>", unsafe_allow_html=True)
