import sqlite3
import pandas as pd

DB_NAME = "maintenance.db"

def init_db():
    """Membuat tabel jika belum ada"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS maintenance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tanggal TEXT NOT NULL,
            no_cc TEXT NOT NULL,
            sistem TEXT NOT NULL,
            komponen TEXT NOT NULL,
            jenis_kerusakan TEXT NOT NULL,
            penyebab TEXT NOT NULL,
            tindakan TEXT NOT NULL,
            downtime_jam REAL DEFAULT 0.0
        )
    ''')
    conn.commit()
    conn.close()

def import_csv_to_db(csv_file):
    """Mengimpor data dari file CSV ke database SQLite"""
    init_db()
    df = pd.read_csv(csv_file)
    conn = sqlite3.connect(DB_NAME)
    # Masukkan data CSV ke tabel maintenance tanpa menghapus struktur
    df.to_sql('maintenance', conn, if_exists='append', index=False)
    conn.close()
    print("Data CSV berhasil diimpor ke Database!")

def get_all_data():
    """Mengambil seluruh data dari database untuk ditampilkan"""
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM maintenance ORDER BY id DESC", conn)
    conn.close()
    return df

def tambah_data(tanggal, no_cc, sistem, komponen, jenis_kerusakan, penyebab, tindakan, downtime_jam):
    """Menambah 1 baris data perbaikan baru"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO maintenance (tanggal, no_cc, sistem, komponen, jenis_kerusakan, penyebab, tindakan, downtime_jam)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (tanggal, no_cc, sistem, komponen, jenis_kerusakan, penyebab, tindakan, downtime_jam))
    conn.commit()
    conn.close()

def hapus_data(id_data):
    """Menghapus data berdasarkan ID"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM maintenance WHERE id = ?", (id_data,))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    import_csv_to_db("data_maintenance.csv")