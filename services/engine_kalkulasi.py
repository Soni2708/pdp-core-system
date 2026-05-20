import re
from datetime import datetime, timedelta
import logging
from db_utils import fetch_master_config

log = logging.getLogger("ENGINE_KALKULASI")

def normalize_time_format(jam_str):
    """Auto-healing format waktu (mengubah 08.30 atau 08 30 menjadi 08:30)"""
    if not jam_str: return None
    jam_bersih = re.sub(r'[^0-9:]', '', str(jam_str).replace('.', ':').replace(' ', ':'))
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
        jam_dt = datetime.strptime(jam_aman, "%H:%M")
        jam_real = waktu_sekarang.replace(hour=jam_dt.hour, minute=jam_dt.minute, second=0, microsecond=0)

        # Menangani edge-case jika kendaraan tiba melewati tengah malam
        if waktu_sekarang < jam_real: 
            jam_real -= timedelta(days=1)

        return int((waktu_sekarang - jam_real).total_seconds() / 60)
    except Exception: 
        return 999  # Fallback ekstrim untuk memicu visual alarm jika data korup
