import logging
from datetime import datetime, timedelta
from db_utils import fetch_master_config, get_waktu_wib

log = logging.getLogger("JADWAL_SERVICE")

def get_semua_rute() -> list:
    """Menarik daftar rute murni dari Supabase."""
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
    Hanya memunculkan jadwal yang rentangnya: [Waktu Sekarang - 15 Menit] s.d [Waktu Sekarang + 60 Menit]
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
                
                # Hitung selisih waktu dalam menit
                selisih_menit = (jadwal_dt - waktu_sekarang).total_seconds() / 60
                
                # 🛡️ ENGINE VALIDASI WAKTU (STRICT TIMING)
                # selisih >= -15 : Otomatis menghilangkan jadwal yang sudah lewat lebih dari 15 menit
                # selisih <= 60  : Memblokir jadwal yang masih lebih dari 1 jam di masa depan
                if -15 <= selisih_menit <= 60:
                    jadwal_aktif.append(jam_str)
                    
            except Exception as e:
                log.warning(f"Format jam tidak valid dilewati: {jam_str}")
                continue 
        
        # Jika semua jadwal terkunci (karena belum waktunya / sudah terlewat semua)
        if not jadwal_aktif:
            return ["-- Tidak ada jadwal aktif terdekat --"]
            
        return ["-- Pilih Jadwal --"] + jadwal_aktif
        
    except Exception as e:
        log.error(f"Error saat memuat jadwal dinamis: {e}")
        return ["-- Pilih Jadwal --"]
