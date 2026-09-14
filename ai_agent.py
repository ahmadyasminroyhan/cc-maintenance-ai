import sqlite3
import google.generativeai as genai
import datetime

# 1. Konfigurasi API Key (Ganti teks di bawah dengan API Key kamu)
GEMINI_API_KEY = "AQ.Ab8RN6IxexkatHpNSauuuvcLnW6YyRiO8hhp_jH8Wzm6jRKwlg"
genai.configure(api_key=GEMINI_API_KEY)

# Menggunakan model Gemini terbaru yang cepat
model = genai.GenerativeModel('gemini-3.6-flash')

DB_NAME = "maintenance.db"

def jalankan_sql(query):
    """Menjalankan perintah SQL langsung ke database SQLite dan mengembalikan hasilnya"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute(query)
        hasil = cursor.fetchall()
        conn.close()
        return hasil
    except Exception as e:
        conn.close()
        return f"Error Query: {e}"

def tanyakan_ke_ai(pertanyaan_user):
    """Fungsi utama: Mengubah bahasa natural -> SQL -> Ambil Data -> Menyusun Jawaban AI"""
    
    # Dapatkan tanggal hari ini agar AI tahu waktu 'bulan ini' / 'tahun ini'
    tanggal_hari_ini = datetime.date.today().strftime("%Y-%m-%d")
    
    # Prompt khusus untuk menyuruh AI menerjemahkan pertanyaan menjadi SQL
    prompt_penterjemah = f"""
    Kamu adalah pakar database SQLite untuk analisis maintenance Container Crane (CC).
    Tanggal hari ini adalah: {tanggal_hari_ini}.

    Struktur tabel database kami adalah:
    Tabel 'maintenance' dengan kolom:
    - id (INTEGER)
    - tanggal (TEXT, format YYYY-MM-DD)
    - no_cc (TEXT, contoh: 'CC01')
    - sistem (TEXT, contoh: 'Hoist', 'Trolley', 'Gantry')
    - komponen (TEXT, contoh: 'Brake', 'Motor')
    - jenis_kerusakan (TEXT)
    - penyebab (TEXT)
    - tindakan (TEXT)
    - downtime_jam (REAL)

    Tugasmu:
    Ubah pertanyaan pengguna berikut menjadi HANYA kueri SQL SQLite yang valid.
    JANGAN tambahkan penjelasan, JANGAN pakai tanda kurung siku atau ```sql. Berikan TULISAN SQL POLOS SAJA.

    Pertanyaan pengguna: "{pertanyaan_user}"
    Query SQL:
    """
    
    # 1. Minta AI buatkan perintah SQL
    respon_sql = model.generate_content(prompt_penterjemah)
    query_sql = respon_sql.text.strip().replace("```sql", "").replace("```", "").strip()
    
    # 2. Eksekusi SQL ke database asli
    data_real = jalankan_sql(query_sql)
    
    # 3. Minta AI menyusun jawaban berdasarkan data real
    prompt_jawaban = f"""
    Kamu adalah Asisten AI Analisis Maintenance Container Crane yang ramah dan profesional.
    
    Pertanyaan Pengguna: "{pertanyaan_user}"
    Query SQL yang dijalankan: `{query_sql}`
    Data Real dari Database SQLite: {data_real}
    
    Tugasmu:
    Jawablah pertanyaan pengguna di atas dengan jelas dan rinci BERDASARKAN Data Real dari Database tersebut.
    Jika data kosong/kosong ([]), katakan bahwa tidak ada catatan kerusakan terkait.
    Jangan pernah mengarang data di luar hasil database!
    """
    
    jawaban_akhir = model.generate_content(prompt_jawaban)
    return jawaban_akhir.text, query_sql