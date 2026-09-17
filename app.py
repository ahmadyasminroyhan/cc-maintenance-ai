import os
import google.generativeai as genai
import pandas as pd
import plotly.express as px
import streamlit as st

# =========================================================
# 🔑 KONFIGURASI HALAMAN & API KEY GEMINI
# =========================================================
st.set_page_config(
    page_title="SIM-CC | Analytics & Maintenance System",
    page_icon="🏗️",
    layout="wide",
)

st.markdown(
    """
    <meta name="google" content="notranslate">
    <style>
        html, body, [class*="css"] { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
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
# 1. DATABASE PERMANEN & SESSION STATE
# ---------------------------------------------------------
MASTER_FILE = "database_master.xlsx"

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "messages" not in st.session_state:
    st.session_state.messages = []

if "user_api_key" not in st.session_state:
    st.session_state.user_api_key = ""


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
# 2. PORTAL LOGIN
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
                if username == "admin" and password == "admin123":
                    st.session_state.logged_in = True
                    st.success("Login berhasil!")
                    st.rerun()
                else:
                    st.error("Username atau Password salah!")
    st.stop()

# ---------------------------------------------------------
# 3. PENANGANAN API KEY (SECRETS + SIDEBAR)
# ---------------------------------------------------------
secret_key = st.secrets.get("GEMINI_API_KEY", "")
final_api_key = (
    st.session_state.user_api_key if st.session_state.user_api_key else secret_key
)
clean_api_key = str(final_api_key).strip().strip('"').strip("'")

ai_is_active = False

if clean_api_key and len(clean_api_key) > 10:
    try:
        os.environ["GEMINI_API_KEY"] = clean_api_key
        os.environ["GOOGLE_API_KEY"] = clean_api_key
        genai.configure(api_key=clean_api_key)
        ai_is_active = True
    except Exception:
        ai_is_active = False


# ---------------------------------------------------------
# 4. LOGIKA PENGGABUNGAN DATA (DATA LAMA TIDAK TERHAPUS)
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
# 5. SIDEBAR
# ---------------------------------------------------------
st.sidebar.markdown("### 👤 Informasi User")
st.sidebar.info("Logged in as: **Administrator**")

st.sidebar.divider()
st.sidebar.markdown("### 🔑 Pengaturan API Key AI")
input_key = st.sidebar.text_input(
    "Masukkan API Key Gemini (Opsional):",
    value=st.session_state.user_api_key,
    type="password",
    help="Tempel API Key asli kamu di sini jika di Secrets belum terpasang!",
)
if input_key != st.session_state.user_api_key:
    st.session_state.user_api_key = input_key
    st.rerun()

st.sidebar.divider()

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
    "Unggah file Excel (bisa lebih dari 1 file):",
    type=["xlsx", "xls"],
    accept_multiple_files=True,
)

if uploaded_files:
    if st.sidebar.button("📥 Proses & Gabungkan Ke Database"):
        merged_db = process_and_merge_files(uploaded_files)
        st.session_state.data_sheets = merged_db
        save_master_database(merged_db)
        st.sidebar.success("✅ Data baru berhasil digabungkan tanpa menghapus data lama!")
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

df_wo = pd.DataFrame()
for key in st.session_state.data_sheets.keys():
    if "WORK ORDER" in key.upper() or "WO" in key.upper():
        df_wo = st.session_state.data_sheets[key]
        break

df_bd_freq = pd.DataFrame()
for key in st.session_state.data_sheets.keys():
    if "FREQ" in key.upper():
        df_bd_freq = st.session_state.data_sheets[key]
        break

# ---------------------------------------------------------
# 7. TAB APLIKASI
# ---------------------------------------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Ringkasan Kinerja Harian",
    "🚨 Rincian Berdasarkan Frekuensi",
    "📈 Analisis Diagram",
    "📋 Daftar Perintah Kerja (WO)",
    "🤖 Asisten Analis AI",
])

# FUNGSI PEMBERSIH UNTUK HEADER & SEL KOSONG
def clean_excel_dataframe(df):
    if df is None or df.empty:
        return pd.DataFrame()
    
    # Buang baris dan kolom yang 100% kosong
    df_clean = df.dropna(how="all").dropna(how="all", axis=1)
    
    # Cari baris yang kemungkinan header asli (berisi teks tidak kosong paling banyak)
    valid_row_idx = None
    for idx, row in df_clean.head(10).iterrows():
        non_null_count = row.notnull().sum()
        if non_null_count >= 3:
            valid_row_idx = idx
            break
            
    if valid_row_idx is not None and valid_row_idx > 0:
        new_header = df_clean.loc[valid_row_idx].values
        df_clean = df_clean.iloc[valid_row_idx + 1:].copy()
        df_clean.columns = new_header
        
    df_clean = df_clean.fillna("")
    # Buang kolom yang namanya kosong/Unnamed
    df_clean = df_clean.loc[:, ~df_clean.columns.astype(str).str.startswith("Unnamed")]
    return df_clean

with tab1:
    st.subheader("Matriks Kinerja Harian Crane (Bersih & Rapi)")
    sd_sheet = None
    for k in st.session_state.data_sheets.keys():
        if "SUMMARY" in k.upper() or "DAILY" in k.upper():
            sd_sheet = st.session_state.data_sheets[k]
            break
            
    if sd_sheet is not None and not sd_sheet.empty:
        sd_sheet_clean = clean_excel_dataframe(sd_sheet)
        st.dataframe(sd_sheet_clean, use_container_width=True)
    else:
        st.info("Unggah berkas Excel di sidebar untuk melihat data harian.")

with tab2:
    st.subheader("🚨 Frekuensi Breakdown per Subsystem & Asset CC")
    if not df_bd_freq.empty:
        df_freq_clean = clean_excel_dataframe(df_bd_freq)
        st.dataframe(df_freq_clean, use_container_width=True)
    else:
        st.info("Belum ada data frekuensi breakdown.")

with tab3:
    st.subheader("📈 Visualisasi Diagram & Trend Kinerja")
    if not df_wo.empty:
        col_g1, col_g2 = st.columns(2)

        with col_g1:
            st.markdown("##### **Distribusi Problem Code (Bar Chart)**")
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

        with col_g2:
            st.markdown(
                "##### **Proporsi Breakdown per Subsystem / Asset (Diagram Lingkaran)**"
            )
            asset_cols = [
                c for c in df_wo.columns if "ASSET" in str(c).upper()
            ]
            if asset_cols:
                asset_counts = (
                    df_wo[asset_cols[0]].value_counts().reset_index().head(6)
                )
                asset_counts.columns = ["Asset", "Total_WO"]

                fig_pie = px.pie(
                    asset_counts,
                    names="Asset",
                    values="Total_WO",
                    hole=0.4,
                    color_discrete_sequence=px.colors.qualitative.Set1,
                )
                fig_pie.update_traces(
                    textposition="inside", textinfo="percent+label"
                )
                st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("Diagram akan otomatis ditampilkan setelah file Excel dimuat.")

with tab4:
    st.subheader("Daftar Perintah Kerja (Work Orders)")
    if not df_wo.empty:
        df_wo_clean = clean_excel_dataframe(df_wo)
        st.dataframe(df_wo_clean, use_container_width=True)
    else:
        st.info("Data Work Order kosong.")

with tab5:
    st.subheader("🤖 Asisten Analis AI Pemeliharaan Crane")
    if not ai_is_active:
        st.warning(
            "⚠️ API Key belum terpasang atau tidak valid. Silakan masukkan API Key Gemini kamu di menu Sidebar sebelah kiri!"
        )

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
            err_msg = "AI belum aktif. Silakan masukkan API Key di menu Sidebar kiri terlebih dahulu."
            st.session_state.messages.append(
                {"role": "assistant", "content": err_msg}
            )
            with st.chat_message("assistant"):
                st.error(err_msg)
        else:
            grouped_context = "=== DATABASE KESELURUHAN TERKELOMPOK PER CONTAINER CRANE (CC/QC) ===\n\n"
            if not df_wo.empty:
                asset_cols = [
                    c for c in df_wo.columns if "ASSET" in str(c).upper()
                ]
                if asset_cols:
                    grouped_assets = df_wo.groupby(asset_cols[0])
                    for asset_name, group in grouped_assets:
                        grouped_context += f"--- UNIT CONTAINER CRANE: {asset_name} (Total: {len(group)} WO) ---\n"
                        grouped_context += group.fillna("").astype(str).to_csv(
                            index=False
                        )
                        grouped_context += "\n"
                else:
                    grouped_context += df_wo.fillna("").astype(str).to_csv(
                        index=False
                    )

            for sname, df_s in st.session_state.data_sheets.items():
                if "WORK ORDER" not in sname.upper() and not df_s.empty:
                    grouped_context += f"\n=== SHEET STATISTIK: {sname} ===\n"
                    grouped_context += df_s.fillna("").astype(str).to_csv(
                        index=False
                    )

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
                with st.spinner(
                    "Menganalisis seluruh database & menyusun jawaban..."
                ):
                    try:
                        model = genai.GenerativeModel("gemini-2.5-flash")
                        response = model.generate_content(full_prompt)
                        ai_reply = response.text
                    except Exception:
                        try:
                            model = genai.GenerativeModel("gemini-2.5-pro")
                            response = model.generate_content(full_prompt)
                            ai_reply = response.text
                        except Exception as ex:
                            ai_reply = f"Gagal memproses analisis AI: {ex}"

                    st.write(ai_reply)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": ai_reply}
                    )

st.markdown("</div>", unsafe_allow_html=True)
