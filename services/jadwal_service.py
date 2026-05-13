from datetime import datetime
from db_utils import get_waktu_wib, fetch_master_config

def get_semua_rute():
    """Mengembalikan list semua rute yang terdaftar di Google Sheets."""
    config = fetch_master_config()
    rute_aktif = list(config["JADWAL"].keys())
    # Sortir alfabetis agar UI rapi
    return ["-- Pilih Rute --"] + sorted(rute_aktif)

def get_jadwal_dinamis(pilihan_rute):
    """
    ENGINE PAGAR WAKTU DINAMIS
    Membaca jadwal dari database, lalu memfilter 30 menit ke belakang & 60 menit ke depan.
    """
    config = fetch_master_config()
    
    if pilihan_rute not in config["JADWAL"]:
        return ["-- Pilih Rute Dulu --"]

    waktu_sekarang = get_waktu_wib()
    jadwal_tersedia = []
    
    for jw in config["JADWAL"][pilihan_rute]:
        try:
            jam_dt = datetime.strptime(jw, "%H:%M")
            jam_real = waktu_sekarang.replace(hour=jam_dt.hour, minute=jam_dt.minute, second=0, microsecond=0)
            
            selisih_menit = (jam_real - waktu_sekarang).total_seconds() / 60
            
            if -30 <= selisih_menit <= 60:
                jadwal_tersedia.append(jw)
        except Exception:
            pass
    
    if not jadwal_tersedia:
        return ["-- Menunggu Jadwal Berikutnya --"]
    return ["-- Pilih Jadwal --"] + jadwal_tersedia