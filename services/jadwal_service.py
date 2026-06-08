import logging
from datetime import datetime, timedelta
from db_utils import fetch_master_config, get_waktu_wib

log = logging.getLogger("JADWAL_SERVICE")

def get_semua_rute() -> list:
    """Menarik daftar rute murni dari Supabase master_rute."""
    try:
        config = fetch_master_config()
        if not config or "JADWAL" not in config:
            return ["-- Pilih Rute --"]
            
        rute_list = list(config["JADWAL"].keys())
        return ["-- Pilih Rute --"] + sorted(rute_list)
    except Exception as e:
        log.error(f"Error saat memuat list rute: {e}")
        return ["-- Pilih Rute --"]

def get_jadwal_dinamis(rute_pilihan: str) -> list:
    """
    Menarik jadwal dari Supabase dan memfilternya dengan Time-Window Strict:
    Hanya memunculkan jadwal yang rentangnya: [Waktu Sekarang - 15 Menit] s.d [Waktu Sekarang + 60 Menit].
    Kebal terhadap pergeseran waktu tengah malam (Cross-Day/Midnight Proof).
    """
    if not rute_pilihan or rute_pilihan == "-- Pilih Rute --":
        return ["-- Pilih Rute Dulu --"]
        
    try:
        config = fetch_master_config()
        jadwal_list = config["JADWAL"].get(rute_pilihan, [])
        
        if not jadwal_list:
            # Jika rute memang tidak memiliki jadwal baku (contoh kasus dinamis)
            return ["-- Menunggu Jadwal Berikutnya --"]
            
        waktu_sekarang = get_waktu_wib()
        jadwal_aktif = []
        
        for jam_str in jadwal_list:
            try:
                # Parsing string "07:00" menjadi objek jam
                jam, menit = map(int, jam_str.split(':'))
                jadwal_dt = waktu_sekarang.replace(hour=jam, minute=menit, second=0, microsecond=0)
                
                # 🛡️ ENGINE VALIDASI WAKTU (ANTI-MIDNIGHT BUG)
                # Kasus 1: Sekarang jam 00:05 WIB, jadwal yang dicek jam 23:50 (Kemarin Malam).
                # replace() akan membuat jadwal_dt menjadi jam 23:50 HARI INI (Maju 23 jam ke depan).
                # Jika selisih > 20 jam di masa depan, artinya ini adalah jadwal kemarin malam.
                if (jadwal_dt - waktu_sekarang).total_seconds() / 3600 > 20:
                    jadwal_dt -= timedelta(days=1)
                
                # Kasus 2: Sekarang jam 23:55 WIB, jadwal yang dicek jam 00:10 (Besok Dini Hari).
                # replace() akan membuat jadwal_dt menjadi jam 00:10 HARI INI (Mundur 23 jam ke belakang).
                # Jika selisih < -20 jam di masa lalu, artinya ini adalah jadwal esok dini hari.
                elif (jadwal_dt - waktu_sekarang).total_seconds() / 3600 < -20:
                    jadwal_dt += timedelta(days=1)
                
                # Hitung selisih waktu final dalam satuan menit
                selisih_menit = (jadwal_dt - waktu_sekarang).total_seconds() / 60
                
                # ⏳ TIME-WINDOW STRICT FILTER
                # selisih >= -15 : Otomatis menghilangkan jadwal yang sudah lewat lebih dari 15 menit
                # selisih <= 60  : Memblokir jadwal yang masih lebih dari 1 jam di masa depan
                if -15 <= selisih_menit <= 60:
                    jadwal_aktif.append(jam_str)
                    
            except Exception as e:
                log.warning(f"Format jam tidak valid dilewati: {jam_str}. Error: {e}")
                continue 
        
        # Jika semua jadwal terkunci (karena belum waktunya / sudah terlewat semua)
        if not jadwal_aktif:
            return ["-- Tidak ada jadwal aktif terdekat --"]
            
        return ["-- Pilih Jadwal --"] + jadwal_aktif
        
    except Exception as e:
        log.error(f"Error saat memuat jadwal dinamis: {e}")
        return ["-- Pilih Jadwal --"]
