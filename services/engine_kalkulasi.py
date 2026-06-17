import re
from datetime import datetime, timedelta
import logging
from db_utils import fetch_master_config

log = logging.getLogger("ENGINE_KALKULASI")

def normalize_time_format(jam_str: str) -> str:
    """Auto-healing format waktu yang kebal terhadap string korup."""
    if not jam_str: 
        return "00:00"
        
    # Ganti pemisah umum (titik, spasi, strip) menjadi titik dua
    jam_bersih = re.sub(r'[\.\s\-]', ':', str(jam_str).strip())
    # Hapus seluruh karakter non-numerik dan non-titik-dua
    jam_bersih = re.sub(r'[^0-9:]', '', jam_bersih)
    
    # Validasi panjang standar (minimal memiliki 1 titik dua, contoh 1:00)
    if len(jam_bersih) < 3 or ':' not in jam_bersih:
        return "00:00"
        
    return jam_bersih

def get_sla_limit(rute: str) -> int:
    """
    Mengambil batas SLA (Waktu Tunggu) langsung dari memory cache Supabase.
    Jika terjadi kegagalan, otomatis mengamankan batas maksimal 30 menit.
    """
    try:
        config = fetch_master_config()
        # Mengambil data dari key "SLA" dari master_rute. Default aman: 30
        return config["SLA"].get(rute.strip().upper(), 30)
    except Exception as e:
        log.error(f"SLA Fallback dipicu untuk rute {rute}: {e}")
        return 30

def hitung_wt(jam_str: str, waktu_sekarang: datetime) -> int:
    """Engine penghitung selisih Waktu Tunggu (WT) dalam menit."""
    if not jam_str: 
        return 0
    try:
        jam_aman = normalize_time_format(jam_str)
        # Proteksi lanjutan saat konversi ke objek Datetime
        jam_dt = datetime.strptime(jam_aman, "%H:%M")
        jam_real = waktu_sekarang.replace(hour=jam_dt.hour, minute=jam_dt.minute, second=0, microsecond=0)

        # Menangani edge-case jika kendaraan tiba melewati tengah malam
        if waktu_sekarang < jam_real: 
            jam_real -= timedelta(days=1)

        return int((waktu_sekarang - jam_real).total_seconds() / 60)
    except Exception as e: 
        log.warning(f"Terjadi anomali kalkulasi waktu pada input '{jam_str}'. Output diarahkan ke fallback 999. Err: {e}")
        return 999  # Fallback ekstrim untuk memicu visual alarm jika data korup parah
