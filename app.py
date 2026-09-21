import base64
import gc
import os
import re
import google.generativeai as genai
import pandas as pd
import plotly.express as px
import streamlit as st

# =========================================================
# 🔑 KONFIGURASI API KEY GEMINI
# =========================================================
API_KEY_KAMU = "AQ.Ab8RN6IVVot3bCb4xZm2UzyGEZEQLpONk6z1pXmz8q5-ro3f7A"
clean_api_key = str(API_KEY_KAMU).strip().strip('"').strip("'")

# Cek dari st.secrets jika ada secara aman
try:
  if "GEMINI_API_KEY" in st.secrets:
    clean_api_key = (
        str(st.secrets["GEMINI_API_KEY"]).strip().strip('"').strip("'")
    )
except Exception:
  pass

ai_is_active = False
if clean_api_key and len(clean_api_key) > 10:
  try:
    for k in ["GEMINI_API_KEY", "GOOGLE_API_KEY"]:
      if k in os.environ:
        del os.environ[k]
    genai.configure(api_key=clean_api_key)
    ai_is_active = True
  except Exception:
    ai_is_active = False


# =========================================================
# 🖼️ FUNGSI UNTUK KONVERSI GAMBAR KE BASE64
# =========================================================
def get_base64_of_bin_file(bin_file):
  try:
    with open(bin_file, "rb") as f:
      data = f.read()
    return base64.b64encode(data).decode()
  except Exception:
    return ""


# Load gambar lokal
bg_login_b64 = get_base64_of_bin_file("bg_login.jpg")
bg_header_b64 = get_base64_of_bin_file("bg_dashboard.jpg")
if not bg_header_b64:
  bg_header_b64 = get_base64_of_bin_file("background.jpg")

# CSS Header Dashboard Dalam (Ada Gambar Samar)
header_inside_style = (
    f"""background: linear-gradient(135deg, rgba(0, 45, 98, 0.85) 0%, rgba(0, 56, 116, 0.80) 50%, rgba(0, 145, 210, 0.85) 100%), url("data:image/jpg;base64,{bg_header_b64}"); background-size: cover; background-position: center;"""
    if bg_header_b64
    else """background: linear-gradient(90deg, #002D62 0%, #003874 50%, #0091D2 100%);"""
)

# CSS Header Portal Login Luar (Biru Tua Polos Kosongan Tanpa Gambar)
header_login_style = """background: linear-gradient(90deg, #001F42 0%, #002D62 50%, #003874 100%);"""

# CSS Background Halaman Login (Gambar Pelabuhan Utuh & Tajam)
login_bg_style = (
    f"""[data-testid="stAppViewContainer"] {{ background-image: url("data:image/jpg;base64,{bg_login_b64}"); background-size: cover; background-position: center; background-repeat: no-repeat; background-attachment: fixed; }}"""
    if bg_login_b64
    else """[data-testid="stAppViewContainer"] {{ background-color: #002D62; }}"""
)

# Config Awal Streamlit
st.set_page_config(
    page_title="SIM-CC | Analytics System", page_icon="🏗️", layout="wide"
)

# Base CSS Styling
st.markdown(
    """
    <style>
        html, body, [class*="css"] { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        
        /* HEADER PORTAL LOGIN (BIRU TUA POLOS) */
        .login-header {
            background: linear-gradient(90deg, #001F42 0%, #002D62 50%, #003874 100%);
            padding: 28px 20px;
            border-radius: 14px;
            color: white;
            text-align: center;
            margin-bottom: 25px;
            box-shadow: 0 6px 20px rgba(0,0,0,0.3);
            border: 1px solid rgba(255,255,255,0.15);
        }
        .login-header h1 {
            margin: 0;
            font-size: 30px;
            font-weight: 700;
            letter-spacing: 0.5px;
            text-shadow: 0 2px 4px rgba(0,0,0,0.5);
        }
        .login-header p {
            margin-top: 8px;
            margin-bottom: 0;
            font-size: 15px;
            opacity: 0.95;
            text-shadow: 0 1px 2px rgba(0,0,0,0.5);
        }

        /* HEADER DASHBOARD DALAM (GAMBAR SAMAR) */
        .main-header {
            """
    + header_inside_style
    + """
            padding: 28px 20px;
            border-radius: 14px;
            color: white;
            text-align: center;
            margin-bottom: 25px;
            box-shadow: 0 6px 20px rgba(0,0,0,0.25);
            border: 1px solid rgba(255,255,255,0.2);
        }
        .main-header h1 {
            margin: 0;
            font-size: 30px;
            font-weight: 700;
            letter-spacing: 0.5px;
            text-shadow: 0 2px 4px rgba(0,0,0,0.5);
        }
        .main-header p {
            margin-top: 8px;
            margin-bottom: 0;
            font-size: 15px;
            opacity: 0.95;
            text-shadow: 0 1px 2px rgba(0,0,0,0.5);
        }
        
        /* FORM LOGIN KOTAK PUTIH SOLID */
        [data-testid="stForm"] {
            background-color: #ffffff !important;
            padding: 35px 28px !important;
            border-radius: 16px !important;
            box-shadow: 0 12px 35px rgba(0, 0, 0, 0.45) !important;
            border-top: 6px solid #0091D2 !important;
            border-left: none !important;
            border-right: none !important;
            border-bottom: none !important;
        }
        
        /* KARTU METRIK PELINDO */
        .metric-card {
            background-color: #ffffff;
            border-left: 5px solid #003874;
            padding: 16px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            margin-bottom: 15px;
        }
        .metric-value { font-size: 24px; font-weight: bold; color: #002D62; }
        .metric-label { font-size: 13px; color: #666666; text-transform: uppercase; letter-spacing: 0.5px; }
        
        /* HEADER SUB-BULAN TEMA PELINDO */
        .month-header {
            background: linear-gradient(90deg, #002D62 0%, #0091D2 100%);
            color: white;
            padding: 10px 18px;
            border-radius: 8px;
            font-size: 17px;
            font-weight: bold;
            margin-top: 25px;
            margin-bottom: 15px;
        }
        
        /* KOTAK STATISTIK UNIT PELINDO */
        .stat-box {
            background: linear-gradient(135deg, #003874 0%, #00A3E0 100%);
            color: white;
            padding: 16px;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 12px;
            box-shadow: 0 4px 10px rgba(0,56,116,0.2);
        }
        .stat-title { font-size: 12px; opacity: 0.9; text-transform: uppercase; letter-spacing: 1px; }
        .stat-num { font-size: 22px; font-weight: bold; margin-top: 4px; }
    </style>
""",
    unsafe_allow_html=True,
)

# PALETTE BIRU PELINDO UNTUK CHART & GRAFIK
PELINDO_GRADIENT = [
    "#001F42",
    "#002D62",
    "#003874",
    "#004B93",
    "#0062B1",
    "#007ACC",
    "#0091D2",
    "#00A3E0",
    "#33B5E5",
]

MONTH_LIST = [
    "Januari",
    "Februari",
    "Maret",
    "April",
    "Mei",
    "Juni",
    "Juli",
    "Agustus",
    "September",
    "Oktober",
    "November",
    "Desember",
]

# =========================================================
# 💾 DATABASE MANAGEMENT
# =========================================================
MASTER_FILE = "database_master.xlsx"


def load_master_database():
  sheets = {}
  if os.path.exists(MASTER_FILE):
    try:
      with pd.ExcelFile(MASTER_FILE) as xls:
        for sname in xls.sheet_names:
          sheets[sname] = pd.read_excel(xls, sheet_name=sname)
    except Exception:
      pass
  return sheets


def save_master_database(sheets_dict):
  try:
    with pd.ExcelWriter(MASTER_FILE, engine="openpyxl") as writer:
      for sname, df in sheets_dict.items():
        if not df.empty:
          df.to_excel(writer, sheet_name=sname[:31], index=False)
  except Exception as e:
    st.error(f"Gagal menyimpan database master: {e}")


def safe_reset_database():
  st.session_state.data_sheets = {}
  gc.collect()
  if os.path.exists(MASTER_FILE):
    try:
      os.remove(MASTER_FILE)
    except PermissionError:
      with pd.ExcelWriter(MASTER_FILE, engine="openpyxl") as writer:
        pd.DataFrame().to_excel(writer, sheet_name="EMPTY", index=False)


if "logged_in" not in st.session_state:
  st.session_state.logged_in = False

if "uploader_key" not in st.session_state:
  st.session_state.uploader_key = 0

if "messages" not in st.session_state:
  st.session_state.messages = []

# =========================================================
# 🔒 PORTAL LOGIN (Luar)
# =========================================================
if not st.session_state.logged_in:
  st.markdown(f"<style>{login_bg_style}</style>", unsafe_allow_html=True)

  st.markdown(
      """
        <div class="login-header">
            <h1>🔒 Portal Login SIM-CC</h1>
            <p>Sistem Pemantauan Kinerja Operasional & Breakdown Crane Harian</p>
        </div>
        """,
      unsafe_allow_html=True,
  )

  _, col2, _ = st.columns([1, 2, 1])
  with col2:
    with st.form("login_form"):
      st.markdown(
          "<h3 style='text-align: center; color: #002D62; margin-top: 0px;"
          " margin-bottom: 20px;'>Masuk Akun Administrator</h3>",
          unsafe_allow_html=True,
      )

      # Field terisi kosong agar pengguna mengetik manual
      u = st.text_input("Username", value="", placeholder="Masukkan username")
      p = st.text_input(
          "Password",
          type="password",
          value="",
          placeholder="Masukkan password",
      )

      submitted = st.form_submit_button(
          "Masuk Aplikasi", use_container_width=True
      )
      if submitted:
        if u == "admin" and p == "admin123":
          st.session_state.logged_in = True
          st.rerun()
        else:
          st.error("Kredensial salah! Silakan periksa username dan password.")
  st.stop()

# Set background bersih terang khusus area Dashboard Dalam
st.markdown(
    """
    <style>
        [data-testid="stAppViewContainer"] {
            background-color: #f7f9fc !important;
            background-image: none !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# ⚙️ LOGIKA PARSING DATA
# =========================================================
def process_and_merge_files(uploaded_files, manual_month):
  merged = load_master_database()

  for up_file in uploaded_files:
    file_month = (
        manual_month if (manual_month and manual_month != "Otomatis") else "Agustus"
    )

    try:
      with pd.ExcelFile(up_file) as xls:
        for sname in xls.sheet_names:
          df_new = pd.read_excel(xls, sheet_name=sname)
          if df_new.empty:
            continue

          df_new["BULAN_TAG"] = str(file_month)
          sheet_key = f"{sname}_{file_month}"[:31]

          if sheet_key in merged and not merged[sheet_key].empty:
            merged[sheet_key] = pd.concat(
                [merged[sheet_key], df_new], ignore_index=True
            )
          else:
            merged[sheet_key] = df_new
    except Exception as e:
      st.error(f"Error membaca file {up_file.name}: {e}")

  save_master_database(merged)
  return merged


def parse_daily_boxes(data_sheets):
  records = []

  for sheet_name, df in data_sheets.items():
    if df.empty or sheet_name == "EMPTY":
      continue

    try:
      header_idx = None
      for idx in range(min(12, len(df))):
        row_vals = " ".join(df.iloc[idx].dropna().astype(str)).upper()
        if "UNIT / TANGGAL" in row_vals or "UNIT" in row_vals:
          header_idx = idx
          break

      if header_idx is None:
        continue

      header_row = df.iloc[header_idx]

      for r_idx in range(header_idx + 1, header_idx + 15):
        if r_idx >= len(df):
          break

        row = df.iloc[r_idx]
        unit_name = str(row.iloc[0]).strip().upper()

        if not re.match(r"^CC\d+", unit_name):
          continue

        b_tag = (
            row["BULAN_TAG"]
            if "BULAN_TAG" in row and pd.notna(row["BULAN_TAG"])
            else "Agustus"
        )

        for c_idx in range(1, len(row)):
          col_raw = header_row.iloc[c_idx]
          col_str = str(col_raw).strip().upper()

          if (
              "TOTAL" in col_str
              or "BULAN_TAG" in col_str
              or col_str == "NAN"
              or col_str in [m.upper() for m in MONTH_LIST]
          ):
            continue

          val = pd.to_numeric(row.iloc[c_idx], errors="coerce")
          val_num = int(val) if (pd.notna(val) and val >= 0) else 0

          dt_obj = pd.to_datetime(col_raw, errors="coerce")
          if not pd.isna(dt_obj):
            day_num = dt_obj.day
            tgl_name = f"Tgl {day_num:02d}"
          else:
            clean_digit = re.sub(r"\D", "", col_str)
            if clean_digit:
              day_num = int(clean_digit)
              tgl_name = f"Tgl {day_num:02d}"
            else:
              continue

          records.append({
              "Bulan": str(b_tag),
              "DayNum": day_num,
              "Tanggal": tgl_name,
              "Asset": unit_name,
              "Boxes": val_num,
          })
    except Exception:
      continue

  if records:
    df_rec = pd.DataFrame(records)
    df_rec = df_rec[df_rec["Bulan"].str.lower() != "nan"]
    return df_rec.groupby(
        ["Bulan", "DayNum", "Tanggal", "Asset"], as_index=False
    )["Boxes"].sum()

  return pd.DataFrame()


def parse_clean_breakdown(data_sheets):
  bd_frames = []
  MONTH_LIST_UPPER = [m.upper() for m in MONTH_LIST]
  all_standard_qcs = [f"QC{i:02d}" for i in range(1, 26)]

  for sname, df in data_sheets.items():
    if df.empty or sname == "EMPTY":
      continue

    upper_sname = str(sname).upper()
    if "FREQ" in upper_sname or "BREAKDOWN BY FREQ" in upper_sname:
      df_c = df.copy()

      unit_header_idx = None
      for i in range(min(15, len(df_c))):
        row_items = [
            str(x).strip().upper() for x in df_c.iloc[i].dropna() if pd.notna(x)
        ]
        if any(re.search(r"(QC|CC)\s*\d+", item) for item in row_items):
          unit_header_idx = i
          break

      if unit_header_idx is not None:
        headers = df_c.iloc[unit_header_idx].astype(str).str.strip()
        new_cols = []
        seen_cols = {}
        for idx_c, val in enumerate(headers):
          v_upper = str(val).upper() if pd.notna(val) else ""
          if idx_c == 0:
            c_name = "Description"
          elif idx_c == 1:
            c_name = "Nama Subsystem"
          elif v_upper in [
              "NAN",
              "NONE",
              "0",
              "0.0",
              "UNNAMED",
              "ASSET CC",
              "BREAKDOWN BY FREQUENCY",
          ]:
            c_name = f"Kolom_{idx_c}"
          else:
            c_name = str(val).strip()

          qc_match = re.search(r"(QC|CC)\s*(\d+)", c_name.upper())
          if qc_match:
            c_num = int(qc_match.group(2))
            c_name = f"QC{c_num:02d}"

          if c_name in seen_cols:
            seen_cols[c_name] += 1
            c_name = f"{c_name}_{seen_cols[c_name]}"
          else:
            seen_cols[c_name] = 0

          new_cols.append(c_name)

        df_c = df_c.iloc[unit_header_idx + 1 :].copy()
        df_c.columns = new_cols
      else:
        df_c.columns = [str(c).strip() for c in df_c.columns]

      b_tag = "Agustus"
      if "BULAN_TAG" in df.columns:
        val_tag = str(df["BULAN_TAG"].iloc[0]).strip()
        if val_tag != "" and val_tag.lower() != "nan":
          b_tag = val_tag

      cols_to_keep = []
      for col in df_c.columns:
        col_upper = str(col).strip().upper()
        if col_upper in MONTH_LIST_UPPER or col_upper == "BULAN_TAG":
          continue
        cols_to_keep.append(col)

      df_c = df_c[cols_to_keep]
      df_c = df_c.dropna(how="all")

      def is_valid_bd_row(row):
        desc = str(row.iloc[0]).strip().upper() if len(row) > 0 else ""
        subsys = str(row.iloc[1]).strip().upper() if len(row) > 1 else ""

        invalid_keywords = [
            "TOTAL",
            "CANCEL",
            "TGL",
            "SYSTEM",
            "SPREADER SYST",
            "GANTRY SYSTEM",
            "TRIM LIST",
            "BOOM SYSTEM",
            "TROLLEY SYST",
            "HOIST SYSTEM",
            "ELECTRIC CONT",
            "NB",
        ]

        if any(
            kw in desc for kw in ["TOTAL BD", "CANCEL", "( TGL", "SYSTEM"]
        ) and subsys in ["NB", "-", ""]:
          return False
        if desc in invalid_keywords or subsys.isdigit():
          return False
        if desc in ["NAN", "NONE", "", "0", "-"]:
          return False
        return True

      mask_clean = df_c.apply(is_valid_bd_row, axis=1)
      df_c = df_c[mask_clean]

      if df_c.empty:
        continue

      df_c.insert(0, "Bulan", str(b_tag))

      for qc_unit in all_standard_qcs:
        if qc_unit not in df_c.columns:
          df_c[qc_unit] = 0
        else:
          df_c[qc_unit] = (
              pd.to_numeric(df_c[qc_unit], errors="coerce")
              .fillna(0)
              .astype(int)
          )

      fixed_cols = [
          c
          for c in ["Bulan", "Description", "Nama Subsystem"]
          if c in df_c.columns
      ]
      crane_cols = sorted(all_standard_qcs)
      total_cols = [
          c
          for c in df_c.columns
          if "TOTAL" in str(c).strip().upper()
          or "BD ASSET" in str(c).strip().upper()
      ]
      other_cols = [
          c
          for c in df_c.columns
          if c not in fixed_cols and c not in crane_cols and c not in total_cols
      ]

      final_col_order = fixed_cols + crane_cols + other_cols + total_cols
      final_col_order = list(dict.fromkeys(final_col_order))

      df_c = df_c[[c for c in final_col_order if c in df_c.columns]]
      bd_frames.append(df_c)

  if bd_frames:
    cleaned_frames = []
    for df_f in bd_frames:
      df_f = df_f.loc[:, ~df_f.columns.duplicated()]
      cleaned_frames.append(df_f)

    merged = pd.concat(cleaned_frames, ignore_index=True)
    text_cols = [c for c in merged.columns if c not in all_standard_qcs]
    merged[text_cols] = (
        merged[text_cols].fillna("-").replace(["nan", "None", "NaT", ""], "-")
    )
    merged[all_standard_qcs] = merged[all_standard_qcs].fillna(0).astype(int)
    return len(merged), merged

  return 0, pd.DataFrame()


def format_time_no_seconds(val):
  if pd.isna(val) or str(val).strip() in ["-", "", "nan", "None", "NaT"]:
    return "-"
  val_str = str(val).strip()
  if " " in val_str:
    val_str = val_str.split()[-1]
  if ":" in val_str:
    parts = val_str.split(":")
    if len(parts) >= 2:
      return f"{parts[0].zfill(2)}:{parts[1].zfill(2)}"
  return val_str


def format_date_only(val):
  if pd.isna(val) or str(val).strip() in ["-", "", "nan", "None", "NaT"]:
    return "-"
  val_str = str(val).strip()
  if " " in val_str:
    val_str = val_str.split()[0]
  dt = pd.to_datetime(val_str, errors="coerce")
  if pd.notna(dt):
    return dt.strftime("%Y-%m-%d")
  return val_str


def calculate_wo_duration(row):
  try:
    d_start_raw = str(
        row.get("DATE Start", "") if pd.notna(row.get("DATE Start")) else ""
    )
    t_start_raw = str(
        row.get("TIME Start", "") if pd.notna(row.get("TIME Start")) else ""
    )
    d_finish_raw = str(
        row.get("DATE Finish", "") if pd.notna(row.get("DATE Finish")) else ""
    )
    t_finish_raw = str(
        row.get("TIME Finish", "") if pd.notna(row.get("TIME Finish")) else ""
    )

    if (
        d_finish_raw in ["", "-", "nan"]
        and "DOC DATE/ SCH" in row
        and pd.notna(row["DOC DATE/ SCH"])
    ):
      doc_raw = str(row["DOC DATE/ SCH"]).strip()
      if " " in doc_raw:
        d_finish_raw, t_finish_raw = (
            doc_raw.split()[0],
            doc_raw.split()[-1],
        )

    d_start = d_start_raw.split()[0] if d_start_raw else ""
    t_start = t_start_raw.split()[-1] if t_start_raw else ""
    d_finish = d_finish_raw.split()[0] if d_finish_raw else ""
    t_finish = t_finish_raw.split()[-1] if t_finish_raw else ""

    start_dt = pd.to_datetime(f"{d_start} {t_start}".strip(), errors="coerce")
    finish_dt = pd.to_datetime(
        f"{d_finish} {t_finish}".strip(), errors="coerce"
    )

    if pd.isna(start_dt) or pd.isna(finish_dt):
      return "-"

    diff = finish_dt - start_dt
    total_seconds = int(diff.total_seconds())

    if total_seconds <= 0:
      return "-"

    hrs = total_seconds // 3600
    mins = (total_seconds % 3600) // 60

    if hrs > 0 and mins > 0:
      return f"{hrs} Jam {mins} Menit"
    elif hrs > 0:
      return f"{hrs} Jam"
    elif mins > 0:
      return f"{mins} Menit"
    else:
      return "< 1 Menit"
  except Exception:
    return "-"


def parse_clean_wo(data_sheets):
  wo_frames = []
  for sname, df in data_sheets.items():
    if df.empty or sname == "EMPTY":
      continue

    upper_sname = str(sname).upper()
    if any(
        k in upper_sname for k in ["WORK", "LIST OF WORK", "WO", "WORK ORDER"]
    ):
      df_c = df.dropna(how="all").copy()

      header_idx = None
      for i in range(min(10, len(df_c))):
        row_str = " ".join(df_c.iloc[i].dropna().astype(str)).upper()
        if any(
            k in row_str
            for k in ["WORK ORDER", "DESCRIPTION", "ASSET", "PROBLEM CODE"]
        ):
          header_idx = i
          break

      if header_idx is not None:
        df_c.columns = df_c.iloc[header_idx].astype(str).str.strip()
        df_c = df_c.iloc[header_idx + 1 :].copy()

      drop_cancel_cols = [
          c
          for c in df_c.columns
          if "CANCEL" in str(c).upper() or "DIHAPUS" in str(c).upper()
      ]
      if drop_cancel_cols:
        df_c = df_c.drop(columns=drop_cancel_cols)

      def is_valid_wo_row(r):
        desc = str(r.get("Description", "")).strip().lower()
        task = str(r.get("TASK", "")).strip().lower()
        wo_num = str(r.get("Work Order", "")).strip().lower()
        invalid_vals = ["", "nan", "none", "-", "nat", "0"]
        return (
            (desc not in invalid_vals)
            or (task not in invalid_vals)
            or (wo_num not in invalid_vals)
        )

      valid_mask = df_c.apply(is_valid_wo_row, axis=1)
      df_c = df_c[valid_mask]

      if df_c.empty:
        continue

      for col in df_c.columns:
        c_up = str(col).strip().upper()
        if "DATE" in c_up and "TIME" not in c_up:
          df_c[col] = df_c[col].apply(format_date_only)
        elif "TIME" in c_up:
          df_c[col] = df_c[col].apply(format_time_no_seconds)

      df_c["DURATION"] = df_c.apply(calculate_wo_duration, axis=1)

      date_col = None
      for col in df_c.columns:
        c_up = str(col).strip().upper()
        if "DOC. DATE" in c_up or "DATE START" in c_up or "DATE" in c_up:
          date_col = col
          break

      if date_col:
        dt_series = pd.to_datetime(df_c[date_col], errors="coerce")
        df_c["Tanggal"] = dt_series.dt.day.apply(
            lambda x: f"Tgl {int(x):02d}" if pd.notna(x) else "Lainnya"
        )
      else:
        df_c["Tanggal"] = "Semua Tanggal"

      b_tag = "Umum"
      for m in MONTH_LIST:
        if m.lower() in upper_sname.lower():
          b_tag = m
          break
      if "BULAN_TAG" in df_c.columns:
        val_tag = (
            str(df_c["BULAN_TAG"].iloc[0]).strip() if not df_c.empty else ""
        )
        if val_tag != "" and val_tag.lower() != "nan":
          b_tag = val_tag

      dup_cols = [
          c
          for c in df_c.columns
          if str(c).strip().upper() in ["BULAN", "BULAN_TAG"]
      ]
      if dup_cols:
        df_c = df_c.drop(columns=dup_cols)

      df_c.insert(0, "Bulan", str(b_tag))
      wo_frames.append(df_c)

  if wo_frames:
    merged = pd.concat(wo_frames, ignore_index=True)
    merged = merged.fillna("-").replace(
        ["nan", "None", "NaT", "", "0000-00-00 00:00:00"], "-"
    )
    merged = merged.loc[:, (merged != "-").any(axis=0)]
    merged = merged.loc[:, ~merged.columns.duplicated()]
    return merged

  return pd.DataFrame()


# Load Database
st.session_state.data_sheets = load_master_database()

# Load Extracted Data
df_prod = parse_daily_boxes(st.session_state.data_sheets)
df_wo = parse_clean_wo(st.session_state.data_sheets)
total_bd_events, df_bd_clean = parse_clean_breakdown(
    st.session_state.data_sheets
)

# Opsi Bulan yang Tersedia
available_months_set = set()
if not df_prod.empty:
  available_months_set.update(df_prod["Bulan"].unique())
if not df_bd_clean.empty:
  available_months_set.update(df_bd_clean["Bulan"].unique())
if not df_wo.empty:
  available_months_set.update(df_wo["Bulan"].unique())

global_month_options = ["Semua Bulan"] + sorted(list(available_months_set))

if "shared_selected_month" not in st.session_state:
  st.session_state.shared_selected_month = global_month_options[0]

# =========================================================
# 🎛️ SIDEBAR
# =========================================================
st.sidebar.markdown("### 👤 User: Administrator")
st.sidebar.caption("📁 Master Database Status: Synchronized")

if st.sidebar.button("🗑️ Reset/Hapus Database Master"):
  safe_reset_database()
  st.sidebar.success("Database berhasil di-reset!")
  st.rerun()

if st.sidebar.button("🚪 Keluar"):
  st.session_state.logged_in = False
  st.rerun()

st.sidebar.divider()
st.sidebar.markdown("### 📁 Upload File Excel Baru")

target_month = st.sidebar.selectbox(
    "Labeli File Sebagai Bulan:", ["Otomatis"] + MONTH_LIST
)

uploaded_files = st.sidebar.file_uploader(
    "Unggah File Excel:",
    type=["xlsx", "xls"],
    accept_multiple_files=True,
    key=f"uploader_{st.session_state.uploader_key}",
)

if uploaded_files:
  if st.sidebar.button("📥 Simpan ke Database"):
    merged_db = process_and_merge_files(uploaded_files, target_month)
    st.session_state.data_sheets = merged_db
    st.session_state.uploader_key += 1
    st.sidebar.success("✅ Data berhasil disimpan secara permanen!")
    st.rerun()

# Dashboard Utama Header
st.markdown(
    """
    <div class="main-header">
        <h1>🏗️ SIM-CC: Pemantauan & Analisis Container Crane</h1>
        <p>Sistem Pemantauan Kinerja Operasional & Breakdown Crane Harian</p>
    </div>
    """,
    unsafe_allow_html=True,
)

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Ringkasan Kinerja",
    "🚨 Rincian Breakdown",
    "📈 Diagram Analytics",
    "📋 Work Order (WO)",
    "🤖 Asisten AI",
])

# ---------------------------------------------------------
# TAB 1: RINGKASAN KINERJA
# ---------------------------------------------------------
with tab1:
  curr_m = st.session_state.shared_selected_month
  f_prod = (
      df_prod if curr_m == "Semua Bulan" else df_prod[df_prod["Bulan"] == curr_m]
  )
  f_wo = df_wo if curr_m == "Semua Bulan" else df_wo[df_wo["Bulan"] == curr_m]
  f_bd = (
      df_bd_clean
      if curr_m == "Semua Bulan"
      else df_bd_clean[df_bd_clean["Bulan"] == curr_m]
  )

  col_m1, col_d1 = st.columns(2)
  with col_m1:
    st.selectbox(
        "📅 **Pilih Bulan:**",
        options=global_month_options,
        key="shared_selected_month",
    )

  with col_d1:
    if not f_prod.empty:
      sorted_dates = (
          f_prod[["DayNum", "Tanggal"]].drop_duplicates().sort_values("DayNum")
      )
      avail_d = ["Semua Tanggal (Full Month)"] + list(sorted_dates["Tanggal"])
    else:
      avail_d = ["Semua Tanggal (Full Month)"]

    sel_d = st.selectbox(
        "📆 **Pilih Tanggal (Drill-Down Harian):**", options=avail_d
    )

  st.subheader(f"📌 Ringkasan Eksekutif Operasional ({curr_m})")

  if st.session_state.data_sheets and any(
      k != "EMPTY" for k in st.session_state.data_sheets.keys()
  ):
    c1, c2, c3, c4 = st.columns(4)
    tot_b = int(f_prod["Boxes"].sum()) if not f_prod.empty else 0
    c1.markdown(
        f'<div class="metric-card"><div class="metric-label">📦 Total'
        f' Produksi</div><div class="metric-value">{tot_b:,} Boxes</div></div>',
        unsafe_allow_html=True,
    )
    c2.markdown(
        f'<div class="metric-card"><div class="metric-label">📋 Total Work'
        f' Order</div><div class="metric-value">{len(f_wo):,} WO</div></div>',
        unsafe_allow_html=True,
    )
    c3.markdown(
        f'<div class="metric-card"><div class="metric-label">🚨 Record'
        f' Breakdown</div><div class="metric-value">{len(f_bd):,}'
        " Event</div></div>",
        unsafe_allow_html=True,
    )
    c4.markdown(
        '<div class="metric-card"><div class="metric-label">🤖 Status AI'
        f' System</div><div class="metric-value">{"🟢 Aktif" if ai_is_active else "🔴 Nonaktif"}</div></div>',
        unsafe_allow_html=True,
    )

    st.divider()

    if not f_prod.empty:
      if sel_d != "Semua Tanggal (Full Month)":
        final_filtered = f_prod[f_prod["Tanggal"] == sel_d]
      else:
        final_filtered = f_prod

      for m_name, grp_m in final_filtered.groupby("Bulan"):
        header_title = (
            f"📅 BULAN: {str(m_name).upper()}"
            if sel_d == "Semua Tanggal (Full Month)"
            else f"📅 BULAN: {str(m_name).upper()} ({sel_d})"
        )
        st.markdown(
            f'<div class="month-header">{header_title}</div>',
            unsafe_allow_html=True,
        )

        asset_grp = (
            grp_m.groupby("Asset", as_index=False)["Boxes"]
            .sum()
            .reset_index(drop=True)
        )

        cols = st.columns(4)
        for idx, r in asset_grp.iterrows():
          cols[idx % 4].markdown(
              '<div class="stat-box"><div'
              f' class="stat-title">UNIT {r["Asset"]}</div><div'
              f' class="stat-num">{int(r["Boxes"]):,} Boxes</div></div>',
              unsafe_allow_html=True,
          )
  else:
    st.info(
        "Database kosong. Unggah file Excel di sidebar lalu klik 'Simpan ke"
        " Database'."
    )

# ---------------------------------------------------------
# TAB 2: RINCIAN BREAKDOWN (QC01 - QC25 URUT PAS)
# ---------------------------------------------------------
with tab2:
  st.subheader("🚨 Rincian Kejadian Breakdown Container Crane (QC01 - QC25)")

  if not df_bd_clean.empty:
    col_bd_m, col_bd_d = st.columns(2)

    with col_bd_m:
      sel_bd_month = st.selectbox(
          "📅 **Pilih Bulan Breakdown:**",
          options=global_month_options,
          key="bd_selected_month",
      )

    df_show_bd = (
        df_bd_clean
        if sel_bd_month == "Semua Bulan"
        else df_bd_clean[df_bd_clean["Bulan"] == sel_bd_month]
    )

    with col_bd_d:
      if "Tanggal" in df_show_bd.columns and not df_show_bd.empty:
        avail_bd_dates = ["Semua Tanggal (Full Month)"] + sorted(
            [t for t in df_show_bd["Tanggal"].unique() if t != "Lainnya"]
        )
      else:
        avail_bd_dates = ["Semua Tanggal (Full Month)"]

      sel_bd_date = st.selectbox(
          "📆 **Pilih Tanggal Breakdown:**",
          options=avail_bd_dates,
          key="bd_selected_date",
      )

    if (
        sel_bd_date != "Semua Tanggal (Full Month)"
        and "Tanggal" in df_show_bd.columns
    ):
      df_show_bd = df_show_bd[df_show_bd["Tanggal"] == sel_bd_date]

    col_b1, col_b2 = st.columns([2, 1])
    with col_b1:
      st.write(
          f"Tampilan rincian breakdown untuk **{sel_bd_month}** |"
          f" **{sel_bd_date}** (QC01 - QC25 terurut presisi)."
      )
    with col_b2:
      search_bd = st.text_input(
          "🔍 Cari Kata Kunci:", "", key="search_bd_input"
      )

    if search_bd:
      mask = df_show_bd.astype(str).apply(
          lambda row: row.str.contains(search_bd, case=False).any(), axis=1
      )
      df_show_bd = df_show_bd[mask]

    st.dataframe(df_show_bd, use_container_width=True, height=500)
  else:
    st.info("Belum ada data breakdown yang tersimpan.")

# ---------------------------------------------------------
# TAB 3: DIAGRAM ANALYTICS
# ---------------------------------------------------------
with tab3:
  st.subheader("📈 Visualisasi Diagram Analytics (Tema Pelindo Blue)")

  if not df_prod.empty or not df_bd_clean.empty:
    col_m_analytics, col_d_analytics = st.columns(2)

    with col_m_analytics:
      sel_m_analytics = st.selectbox(
          "📅 **Pilih Bulan Analytics:**",
          options=global_month_options,
          key="analytics_selected_month",
      )

    f_prod_chart = (
        df_prod
        if sel_m_analytics == "Semua Bulan"
        else df_prod[df_prod["Bulan"] == sel_m_analytics]
    )
    f_bd_chart = (
        df_bd_clean
        if sel_m_analytics == "Semua Bulan"
        else df_bd_clean[df_bd_clean["Bulan"] == sel_m_analytics]
    )

    with col_d_analytics:
      if not f_prod_chart.empty:
        sorted_dates = (
            f_prod_chart[["DayNum", "Tanggal"]]
            .drop_duplicates()
            .sort_values("DayNum")
        )
        avail_d = ["Semua Tanggal (Full Month)"] + list(sorted_dates["Tanggal"])
      else:
        avail_d = ["Semua Tanggal (Full Month)"]

      sel_d_analytics = st.selectbox(
          "📆 **Pilih Tanggal Analytics:**",
          options=avail_d,
          key="analytics_selected_date",
      )

    if sel_d_analytics != "Semua Tanggal (Full Month)":
      f_prod_chart = f_prod_chart[f_prod_chart["Tanggal"] == sel_d_analytics]

    filter_label = f"{sel_m_analytics} - {sel_d_analytics}"

    st.divider()

    g_col1, g_col2 = st.columns(2)

    with g_col1:
      st.markdown("##### **1. Produksi Boxes per Unit Crane**")
      if not f_prod_chart.empty:
        df_chart_prod = (
            f_prod_chart.groupby("Asset", as_index=False)["Boxes"]
            .sum()
            .sort_values("Boxes", ascending=False)
        )
        fig_bar = px.bar(
            df_chart_prod,
            x="Asset",
            y="Boxes",
            text="Boxes",
            color="Boxes",
            color_continuous_scale=PELINDO_GRADIENT,
            title=f"Total Produksi per Unit CC ({filter_label})",
        )
        fig_bar.update_traces(textposition="outside")
        fig_bar.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig_bar, use_container_width=True)
      else:
        st.info(f"Data produksi belum tersedia untuk filter ({filter_label}).")

    with g_col2:
      st.markdown("##### **2. Proporsi Breakdown Subsystem (BIG 6)**")
      if not f_bd_chart.empty:
        try:
          qc_cols = [
              c for c in f_bd_chart.columns if re.search(r"QC\d+", str(c))
          ]
          df_pie = f_bd_chart.copy()
          df_pie["Total_Events"] = (
              df_pie[qc_cols]
              .apply(pd.to_numeric, errors="coerce")
              .fillna(0)
              .sum(axis=1)
          )

          df_pie_sum = (
              df_pie.groupby("Nama Subsystem", as_index=False)["Total_Events"]
              .sum()
              .sort_values("Total_Events", ascending=False)
              .head(6)
          )

          fig_pie = px.pie(
              df_pie_sum,
              names="Nama Subsystem",
              values="Total_Events",
              hole=0.35,
              color_discrete_sequence=PELINDO_GRADIENT,
              title=f"BIG 6 Breakdown Subsystem ({filter_label})",
          )
          fig_pie.update_traces(textinfo="percent+label")
          st.plotly_chart(fig_pie, use_container_width=True)
        except Exception:
          st.info("Gagal menampilkan diagram pie breakdown.")
      else:
        st.info(f"Data breakdown belum tersedia untuk filter ({filter_label}).")

    st.divider()

    st.markdown("##### **3. Tren Produksi Harian (Daily Production Trend)**")
    if not f_prod_chart.empty:
      df_line_trend = (
          f_prod_chart.groupby(["DayNum", "Tanggal"], as_index=False)["Boxes"]
          .sum()
          .sort_values("DayNum")
      )
      fig_line = px.line(
          df_line_trend,
          x="Tanggal",
          y="Boxes",
          markers=True,
          title=f"Tren Produksi Boxes ({filter_label})",
          color_discrete_sequence=["#003874"],
      )
      fig_line.update_traces(
          line=dict(width=3), marker=dict(size=8), textposition="top center"
      )
      fig_line.update_layout(
          xaxis_title="Tanggal",
          yaxis_title="Jumlah Boxes",
          hovermode="x unified",
      )
      st.plotly_chart(fig_line, use_container_width=True)
    else:
      st.info(
          f"Data tren produksi harian belum tersedia untuk filter ({filter_label})."
      )

  else:
    st.info("Data analytics belum tersedia.")

# ---------------------------------------------------------
# TAB 4: WORK ORDER (WO)
# ---------------------------------------------------------
with tab4:
  st.subheader("📋 Daftar Perintah Kerja (Work Orders)")

  if not df_wo.empty:
    col_wo_m, col_wo_d = st.columns(2)

    with col_wo_m:
      sel_wo_month = st.selectbox(
          "📅 **Pilih Bulan Work Order:**",
          options=global_month_options,
          key="wo_selected_month",
      )

    f_wo_tab = (
        df_wo
        if sel_wo_month == "Semua Bulan"
        else df_wo[df_wo["Bulan"] == sel_wo_month]
    )

    with col_wo_d:
      if "Tanggal" in f_wo_tab.columns and not f_wo_tab.empty:
        avail_wo_dates = ["Semua Tanggal (Full Month)"] + sorted(
            [t for t in f_wo_tab["Tanggal"].unique() if t != "Lainnya"]
        )
      else:
        avail_wo_dates = ["Semua Tanggal (Full Month)"]

      sel_wo_date = st.selectbox(
          "📆 **Pilih Tanggal Work Order:**",
          options=avail_wo_dates,
          key="wo_selected_date",
      )

    if sel_wo_date != "Semua Tanggal (Full Month)":
      f_wo_tab = f_wo_tab[f_wo_tab["Tanggal"] == sel_wo_date]

    st.markdown(
        f"**Menampilkan data WO untuk:** `{sel_wo_month}` | `{sel_wo_date}`"
    )
    st.dataframe(f_wo_tab, use_container_width=True, height=500)
  else:
    st.info("Data Work Order belum tersedia.")

# ---------------------------------------------------------
# TAB 5: ASISTEN AI (SUPER KILAT & ULTRA FAST)
# ---------------------------------------------------------
with tab5:
  st.subheader("🤖 Asisten AI Pemeliharaan Crane")

  active_key = clean_api_key if len(clean_api_key) > 10 else ""

  if not active_key:
    st.warning(
        "⚠️ **API Key Gemini belum terdeteksi.** Masukkan API Key kamu di bawah"
        " ini."
    )
    user_key_input = st.text_input(
        "🔑 Masukkan API Key Gemini Kamu:",
        type="password",
        key="user_gemini_key",
        placeholder="Tempel API Key di sini...",
    )
    if user_key_input:
      active_key = user_key_input.strip()

  # Tampilkan riwayat percakapan
  for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
      st.write(msg["content"])

  user_query = st.chat_input("Ketik pertanyaan analisis kamu di sini...")

  if user_query:
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
      st.write(user_query)

    if not active_key or len(active_key) <= 10:
      err_msg = "⚠️ API Key tidak valid! Pastikan kamu sudah memasukkan API Key Gemini yang benar."
      st.session_state.messages.append(
          {"role": "assistant", "content": err_msg}
      )
      with st.chat_message("assistant"):
        st.error(err_msg)
    else:
      # Deteksi Sapaan Umum (Biar Nggak Perlu Load Data Excel yang Berat)
      greeting_keywords = [
          "halo",
          "hai",
          "hi",
          "permisi",
          "pagi",
          "siang",
          "sore",
          "malam",
          "tes",
          "test",
      ]
      is_simple_greeting = any(
          k in user_query.lower().strip() for k in greeting_keywords
      ) and len(user_query.split()) <= 3

      if is_simple_greeting:
        context_data = "User hanya menyapa, berikan salam balik yang ramah dan tanyakan apa yang bisa dibantu terkait crane."
      else:
        # Ekstrak kata kunci untuk pencarian data
        keywords = [
            w.lower()
            for w in user_query.split()
            if len(w) > 1 and w.lower() not in ["ada", "apa", "di", "ke", "bulan"]
        ]

        def get_light_data(df, max_rows=15):
          if df.empty:
            return ""
          if not keywords:
            return df.head(max_rows).to_string(index=False)

          # Filter baris yang cocok dengan kata kunci
          mask = df.astype(str).apply(
              lambda r: any(k in " ".join(r.values).lower() for k in keywords),
              axis=1,
          )
          filtered = df[mask]
          if not filtered.empty:
            return filtered.head(max_rows).to_string(index=False)
          return df.head(10).to_string(index=False)

        context_data = f"""
                === DATA RELEVAN DASHBOARD ===
                PRODUKSI:
                {get_light_data(df_prod)}

                BREAKDOWN:
                {get_light_data(df_bd_clean)}

                WORK ORDER:
                {get_light_data(df_wo)}
                """

      # Prompt Ringkas
      system_prompt = f"""
            Kamu adalah Asisten AI Senior Maintenance Engineer Container Crane (CC) Pelindo.
            Jawab ramah, lugas, presisi, dan berikan rekomendasi teknis jika ada kendala.

            {context_data}
            """

      full_prompt = f"{system_prompt}\n\nPertanyaan: {user_query}"

      with st.chat_message("assistant"):
        with st.spinner("Menganalisis..."):
          try:
            genai.configure(api_key=active_key)
            # Menggunakan gemini-2.5-flash untuk kecepatan maksimal
            model = genai.GenerativeModel("gemini-3.6-flash")
            response = model.generate_content(full_prompt)
            ai_reply = response.text
          except Exception:
            # Fallback ke gemini-1.5-flash jika versi 2.5 belum tersedia di region kamu
            try:
              model = genai.GenerativeModel("gemini-3.6-flash")
              response = model.generate_content(full_prompt)
              ai_reply = response.text
            except Exception as ex:
              ai_reply = f"⚠️ Gagal memproses respon AI: {ex}"

          st.write(ai_reply)
          st.session_state.messages.append(
              {"role": "assistant", "content": ai_reply}
          )
