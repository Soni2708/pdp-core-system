from datetime import datetime, timedelta
from db_utils import fetch_master_config

def get_sla_limit(rute: str) -> int:
    """Mengambil batas SLA secara otomatis dari Google Sheets. Default 150 menit."""
    config = fetch_master_config()
    return config["SLA"].get(rute.strip().upper(), 150)

def hitung_wt(jam_str: str, waktu_sekarang: datetime) -> int:
    """Engine penghitung selisih waktu (dalam menit)."""
    if not jam_str: 
        return 0
    try:
        jam_dt = datetime.strptime(jam_str, "%H:%M")
        jam_real = waktu_sekarang.replace(hour=jam_dt.hour, minute=jam_dt.minute, second=0, microsecond=0)

        if waktu_sekarang < jam_real: 
            jam_real -= timedelta(days=1)

        return int((waktu_sekarang - jam_real).total_seconds() / 60)
    except Exception: 
        return 0