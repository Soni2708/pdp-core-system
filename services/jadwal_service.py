import logging
from datetime import datetime, timedelta
from db_utils import fetch_master_config, get_waktu_wib

log = logging.getLogger("JADWAL_SERVICE")

# Konstanta
DEFAULT_TIME_WINDOW_START = -30   # menit (jadwal yang terlewat maksimal 30 menit yang lalu)
DEFAULT_TIME_WINDOW_END = 60      # menit (jadwal maksimal 90 menit ke depan)
EXTRA_TIME_WINDOW_START = -60    # menit (jadwal extra bisa sampai 2 jam terlewat)
EXTRA_TIME_WINDOW_END = 60       # menit (jadwal extra bisa sampai 2 jam ke depan)

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

def _fix_midnight_crossing(jadwal_dt: datetime, sekarang: datetime) -> datetime:
    """
    Memperbaiki datetime yang cross midnight.
    Menggunakan batas 12 jam (720 menit) untuk menentukan apakah suatu jadwal
    seharusnya kemarin atau besok.
    """
    selisih_menit = (jadwal_dt - sekarang).total_seconds() / 60
    
    # Jika selisih > 12 jam (720 menit), berarti jadwal_dt adalah HARI INI 
    # yang seharusnya KEMARIN (contoh: sekarang jam 00:05, jadwal 23:50)
    if selisih_menit > 720:
        jadwal_dt -= timedelta(days=1)
    # Jika selisih < -12 jam, berarti jadwal_dt adalah HARI INI 
    # yang seharusnya BESOK (contoh: sekarang jam 23:55, jadwal 00:10)
    elif selisih_menit < -720:
        jadwal_dt += timedelta(days=1)
    
    return jadwal_dt

def _is_within_time_window(jadwal_dt: datetime, sekarang: datetime, is_extra: bool = False) -> tuple[bool, int]:
    """
    Memeriksa apakah jadwal berada dalam time window yang diizinkan.
    Returns: (is_valid, selisih_menit)
    """
    start_window = EXTRA_TIME_WINDOW_START if is_extra else DEFAULT_TIME_WINDOW_START
    end_window = EXTRA_TIME_WINDOW_END if is_extra else DEFAULT_TIME_WINDOW_END
    
    selisih_menit = (jadwal_dt - sekarang).total_seconds() / 60
    
    is_valid = start_window <= selisih_menit <= end_window
    return is_valid, int(selisih_menit)

def get_jadwal_dinamis(rute_pilihan: str, is_extra_mode: bool = False) -> list:
    """
    Menarik jadwal dari Supabase dan memfilternya dengan Time-Window.
    
    Args:
        rute_pilihan: Nama rute yang dipilih
        is_extra_mode: Jika True, time window lebih lebar (untuk jadwal extra)
    
    Returns:
        List jadwal yang valid dalam format string "HH:MM"
    """
    if not rute_pilihan or rute_pilihan == "-- Pilih Rute --":
        return ["-- Pilih Rute Dulu --"]
        
    try:
        config = fetch_master_config()
        jadwal_list = config["JADWAL"].get(rute_pilihan, [])
        
        if not jadwal_list:
            # Jika rute tidak memiliki jadwal baku
            return ["-- Tidak ada jadwal terdaftar untuk rute ini --"]
            
        waktu_sekarang = get_waktu_wib()
        jadwal_aktif = []
        skipped_count = 0
        
        for jam_str in jadwal_list:
            try:
                # Parsing string "07:00" menjadi objek jam
                jam, menit = map(int, jam_str.split(':'))
                jadwal_dt = waktu_sekarang.replace(hour=jam, minute=menit, second=0, microsecond=0)
                
                # Perbaiki jika cross midnight
                jadwal_dt = _fix_midnight_crossing(jadwal_dt, waktu_sekarang)
                
                # Cek apakah dalam time window
                is_valid, selisih_menit = _is_within_time_window(
                    jadwal_dt, waktu_sekarang, is_extra_mode
                )
                
                if is_valid:
                    jadwal_aktif.append(jam_str)
                else:
                    skipped_count += 1
                    log.debug(f"Jadwal {jam_str} dilewati (selisih {selisih_menit} menit)")
                    
            except Exception as e:
                log.warning(f"Format jam tidak valid dilewati: {jam_str}. Error: {e}")
                continue 
        
        # Jika semua jadwal terkunci
        if not jadwal_aktif:
            if skipped_count > 0:
                return ["-- Tidak ada jadwal terdekat yang aktif --"]
            return ["-- Tidak ada jadwal terdaftar untuk rute ini --"]
            
        # Urutkan jadwal secara kronologis
        jadwal_aktif.sort(key=lambda x: int(x.split(':')[0]) * 60 + int(x.split(':')[1]))
        
        return ["-- Pilih Jadwal --"] + jadwal_aktif
        
    except Exception as e:
        log.error(f"Error saat memuat jadwal dinamis: {e}")
        return ["-- Error memuat jadwal --"]

def get_jadwal_extra_info(rute_pilihan: str, jam_extra: str) -> dict:
    """
    Mendapatkan informasi validasi untuk jadwal extra.
    Returns dict dengan keys: is_valid, selisih_menit, message
    """
    if not rute_pilihan or rute_pilihan == "-- Pilih Rute --":
        return {
            "is_valid": False,
            "selisih_menit": None,
            "message": "Pilih rute terlebih dahulu"
        }
    
    try:
        waktu_sekarang = get_waktu_wib()
        jam, menit = map(int, jam_extra.split(':'))
        jadwal_dt = waktu_sekarang.replace(hour=jam, minute=menit, second=0, microsecond=0)
        
        # Perbaiki jika cross midnight
        jadwal_dt = _fix_midnight_crossing(jadwal_dt, waktu_sekarang)
        
        selisih_menit = (jadwal_dt - waktu_sekarang).total_seconds() / 60
        
        # Untuk jadwal extra, kita beri toleransi lebih longgar
        if selisih_menit > EXTRA_TIME_WINDOW_END:
            return {
                "is_valid": False,
                "selisih_menit": int(selisih_menit),
                "message": f"Jadwal terlalu jauh ke depan ({int(selisih_menit)} menit). Maksimal {EXTRA_TIME_WINDOW_END} menit."
            }
        elif selisih_menit < EXTRA_TIME_WINDOW_START:
            return {
                "is_valid": False,
                "selisih_menit": int(selisih_menit),
                "message": f"Jadwal sudah terlewat terlalu lama ({abs(int(selisih_menit))} menit). Maksimal {abs(EXTRA_TIME_WINDOW_START)} menit."
            }
        
        return {
            "is_valid": True,
            "selisih_menit": int(selisih_menit),
            "message": f"Valid ({int(selisih_menit)} menit dari sekarang)"
        }
        
    except Exception as e:
        log.error(f"Error validasi jadwal extra: {e}")
        return {
            "is_valid": False,
            "selisih_menit": None,
            "message": "Error validasi jadwal"
        }
