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

# 1. Ambil API Key dari Secrets Streamlit Cloud
RAW_KEY = st.secrets.get("GEMINI_API_KEY", "")
clean_api_key = str(RAW_KEY).strip().strip('"').strip("'")

# 2. Paksa Environment Variable agar tidak memicu fallback OAuth
if clean_api_key:
    os.environ["GEMINI_API_KEY"] = clean_api_key
    os.environ["GOOGLE_API_KEY"] = clean_api_key

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

# Inisialisasi Gemini AI
ai_is_active = False

if clean_api_key and len(clean_api_key) > 10:
    try:
        genai.configure(api_key=clean_api_key)
        ai_is_active = True
    except Exception:
        ai_is_active = False

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
# 3. MULTI-FILE MERGE LOGIC
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
# 4. SIDEBAR
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
    "Unggah file Excel (bisa lebih dari 1 file):",
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
# 5. DASHBOARD UTAMA
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

pm_count = 0
cm_count = 0
total_wo_count = len(df_wo)

if not df_wo.empty:
    df_clean = df_wo.fillna("")
    df_str = df_clean.apply(
        lambda row: " ".join(
            [str(val) for val in row if str(val).strip() != ""]
        ),
        axis=1,
    )

    cm_count = int(
        df_str.str.contains(
            r"Breakdown|CM|Corrective|Kerusakan|Repair|Trouble|Fault",
            case=False,
            regex=True,
        ).sum()
    )
    pm_count = int(
        df_str.str.contains(
            r"PM|Preventive|Pencegahan|Rutin|Inspection|Check|Perawatan",
            case=False,
            regex=True,
        ).sum()
    )

    if pm_count == 0 and cm_count == 0:
        cm_count = total_wo_count

df_bd_freq = pd.DataFrame()
for key in st.session_state.data_sheets.keys():
    if "FREQ" in key.upper():
        df_bd_freq = st.session_state.data_sheets[key]
        break

total_bd_freq = cm_count

col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
col_m1.metric("Total Pesanan Kerja", f"{total_wo_count} WO")
col_m2.metric("🛠️ Jumlah PM", f"{pm_count} WO")
col_m3.metric("🚨 Jumlah CM", f"{cm_count} WO")
col_m4.metric("📊 Total BD Event", f"{total_bd_freq} Event")
col_m5.metric("🤖 Status AI", "Aktif (Gemini)" if ai_is_active else "Mati")

st.divider()

# ---------------------------------------------------------
# 6. TAB APLIKASI
# ---------------------------------------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Ringkasan Kinerja Harian",
    "🚨 Rincian Berdasarkan Frekuensi",
    "📈 Analisis Diagram",
    "📋 Daftar Perintah Kerja (WO)",
    "🤖 Asisten Analis AI",
])

with tab1:
    st.subheader("Matriks Kinerja Harian Crane")
    sd_sheet = None
    for k in st.session_state.data_sheets.keys():
        if "SUMMARY" in k.upper() or "DAILY" in k.upper():
            sd_sheet = st.session_state.data_sheets[k]
            break
    if sd_sheet is not None and not sd_sheet.empty:
        # Bersihkan None pada tabel Ringkasan
        sd_sheet_clean = sd_sheet.fillna("")
        st.dataframe(sd_sheet_clean, use_container_width=True)
    else:
        st.info("Unggah berkas Excel di sidebar untuk melihat data.")

with tab2:
    st.subheader("🚨 Frekuensi Breakdown per Subsystem & Asset CC")
    if not df_bd_freq.empty:
        # Hapus baris dan kolom yang semuanya kosong, lalu ganti sisa None menjadi string kosong ""
        df_freq_clean = df_bd_freq.dropna(how="all").dropna(how="all", axis=1)
        df_freq_clean = df_freq_clean.fillna("")
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
                "##### **Proporsi Breakdown per Subsystem / Asset (Diagram Bulat)**"
            )
            asset_cols = [
                c for c in df_wo.columns if "ASSET" in str(c).upper()
            ]
            if asset_cols:
                asset_counts = (
                    df_wo[asset_cols[0]].value_counts().reset_index().head(6)
                )
                asset_counts.columns = ["Asset", "Total_WO"]

                # Diagram Bulat (Donut Chart)
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
        df_wo_clean = df_wo.fillna("")
        st.dataframe(df_wo_clean, use_container_width=True)
    else:
        st.info("Data Work Order kosong.")

with tab5:
    st.subheader("🤖 Asisten Analis AI Pemeliharaan Crane")
    if not ai_is_active:
        st.warning(
            "⚠️ API Key Gemini belum terpasang di Secrets Streamlit Cloud (GEMINI_API_KEY)."
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
            err_msg = "AI belum aktif. Sila pasang GEMINI_API_KEY di Secrets Streamlit Cloud."
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
