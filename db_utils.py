import gspread
import streamlit as st
from datetime import datetime
import pytz
import time
import random
from functools import wraps
from supabase import create_client, Client

def get_waktu_wib():
    return datetime.now(pytz.timezone('Asia/Jakarta'))

# ============================================================
# 🔑 KONEKSI DATABASE (SUPABASE UNTUK LIVE & GSHEETS UNTUK CONFIG)
# ============================================================
@st.cache_resource
def get_supabase_client() -> Client:
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"FATAL ERROR: Kunci Supabase Hilang! {e}")
        st.stop()

@st.cache_resource(ttl=3600)
def get_gspread_client():
    # TETAP DIPAKAI KHUSUS UNTUK MASTER CONFIG JADWAL
    try:
        kredensial = dict(st.secrets["connections"]["gsheets"])
        return gspread.service_account_from_dict(kredensial)
    except Exception as e:
        st.error(f"Gagal memuat kredensial Google: {e}")
        return None

# ============================================================
# ⚙️ MAPPING AJAIB: MENGUBAH ALAMAT EXCEL JADI SUPABASE
# ============================================================
COL_MAP = {
    "A": "timestamp",        "N": "mim_bbt_out",
    "B": "rute",             "O": "wt_mim_bbt",
    "C": "jadwal",           "P": "driver_kopo",
    "D": "driver_reguler",   "Q": "nopol_kopo",
    "E": "nopol",            "R": "kopo_out",
    "F": "pax_mim_bbt",      "S": "wt_kopo",
    "G": "pax_kopo",         "T": "driver_jtn",
    "H": "pax_jtn",          "U": "nopol_jtn",
    "I": "status",           "V": "jtn_out",
    "J": "jam_keluar_km72",  "W": "wt_jtn",
    "K": "jam_tiba_pdp",     "X": "keterangan",
    "L": "driver_mim_buahbatu",
    "M": "nopol_mim_buahbatu", "Z": "trip_id"
}

def clean_pax(val):
    val_clean = str(val).strip()
    return val_clean if val_clean.isdigit() else "0"

def gspread_retry(max_retries=4, base_delay=1.0):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try: return func(*args, **kwargs)
            except Exception as e: return False, f"System Error: {str(e)}"
        return wrapper
    return decorator

# ============================================================
# 🎯 WRITE: ENGINE INSERTION (SUPABASE V8)
# ============================================================
def safe_append_reguler(data_baru):
    """ Menembak data baru langsung ke PostgreSQL """
    try:
        supabase = get_supabase_client()
        payload = {
            "timestamp": str(data_baru[0]),
            "rute": str(data_baru[1]),
            "jadwal": str(data_baru[2]),
            "driver_reguler": str(data_baru[3]),
            "nopol": str(data_baru[4]),
            "pax_mim_bbt": int(data_baru[5]) if str(data_baru[5]).isdigit() else 0,
            "pax_kopo": int(data_baru[6]) if str(data_baru[6]).isdigit() else 0,
            "pax_jtn": int(data_baru[7]) if str(data_baru[7]).isdigit() else 0,
            "status": str(data_baru[8]),
            "trip_id": str(data_baru[25])  # Kolom Z
        }
        supabase.table("operasional_pdp").insert(payload).execute()
        return True, "Transmisi Sukses"
    except Exception as e:
        return False, f"Supabase Insert Error: {str(e)}"

# ============================================================
# 🚨 READ: PURE LIVE DATA (SUPABASE V8)
# ============================================================
@st.cache_data(ttl=2) # Kita turunin jadi 2 detik biar makin real-time
def fetch_mapped_data():
    try:
        supabase = get_supabase_client()
        # Kita ambil datanya, pastikan ID-nya urut
        res = supabase.table("operasional_pdp").select("*").order("id", desc=False).execute()
        
        def safe_str(val):
            if val is None: return ""
            return str(val).strip()

        mapped_data = []
        for row in res.data:
            # Saring baris yang minimal punya Nopol atau Rute
            if not row.get("nopol") and not row.get("rute"):
                continue

            mapped_data.append({
                "baris_db": row.get("id"),
                "waktu_input": safe_str(row.get("timestamp")),
                "rute": safe_str(row.get("rute")),
                "jadwal": safe_str(row.get("jadwal")),
                "driver": safe_str(row.get("driver_reguler")),
                "nopol": safe_str(row.get("nopol")),
                # Paksa jadi integer agar fungsi sum() di PDP tidak meledak
                "pax_mim": int(row.get("pax_mim_bbt") or 0),
                "pax_kopo": int(row.get("pax_kopo") or 0),
                "pax_jtn": int(row.get("pax_jtn") or 0),
                "status": safe_str(row.get("status")).upper(),
                "jam_72": safe_str(row.get("jam_keluar_km72")),
                "jam_tiba_pdp": safe_str(row.get("jam_tiba_pdp")),
                "jam_out_mim": safe_str(row.get("mim_bbt_out")), 
                "jam_out_kopo": safe_str(row.get("kopo_out")), 
                "jam_out_jtn": safe_str(row.get("jtn_out")),
                "trip_id": safe_str(row.get("trip_id")) 
            })
        
        # Debugging: Uncomment baris di bawah ini kalau masih belum muncul
        # st.write(f"DEBUG: Berhasil narik {len(mapped_data)} baris dari Supabase")
        
        return mapped_data
    except Exception as e:
        st.error(f"Gagal Menarik Data Supabase: {e}")
        return []

# ============================================================
# 🛡️ UPDATE: ENGINE PRESISI BERBASIS UUID & MAPPING
# ============================================================
def safe_update_by_uuid(trip_id, updates_dict):
    try:
        supabase = get_supabase_client()
        payload = {COL_MAP[col]: val for col, val in updates_dict.items() if col in COL_MAP}
        if payload: supabase.table("operasional_pdp").update(payload).eq("trip_id", trip_id).execute()
        return True, "Update Presisi Sukses"
    except Exception as e: return False, str(e)

def execute_batch_update_by_uuid(uuid_updates):
    try:
        supabase = get_supabase_client()
        for item in uuid_updates:
            payload = {COL_MAP[col]: val for col, val in item["updates"].items() if col in COL_MAP}
            if payload: supabase.table("operasional_pdp").update(payload).eq("trip_id", item["trip_id"]).execute()
        return True, "Batch Update Massal Sukses"
    except Exception as e: return False, str(e)

def execute_batch_update(payloads):
    """ Penerjemah Range Excel ke ID Database secara transparan """
    try:
        supabase = get_supabase_client()
        for p in payloads:
            range_str = p.get('range', '')
            if not range_str: continue
            
            col_letter, db_id = range_str[0].upper(), int(range_str[1:])
            val = p['values'][0][0]
            
            if col_letter in COL_MAP:
                supabase.table("operasional_pdp").update({COL_MAP[col_letter]: val}).eq("id", db_id).execute()
        return True, "Update Batch Sukses"
    except Exception as e: return False, str(e)

# ============================================================
# ⚙️ DYNAMIC CONFIGURATION ENGINE (TETAP PAKAI GSHEETS)
# ============================================================
@st.cache_data(ttl=3600)
def fetch_master_config():
    try:
        gc = get_gspread_client()
        sheet = gc.open("Trial_Data_Transit").worksheet("MASTER_CONFIG")
        raw_data = sheet.get_all_values()
        
        config = {"SLA": {}, "JADWAL": {}}
        for row in raw_data[1:]: 
            if len(row) >= 3:
                kat, rute, val = str(row[0]).strip().upper(), str(row[1]).strip().upper(), str(row[2]).strip()
                if kat == "SLA": config["SLA"][rute] = int(val) if val.isdigit() else 150
                elif kat == "JADWAL": config["JADWAL"][rute] = [j.strip() for j in val.split(",")]
        return config
    except Exception as e: return {"SLA": {}, "JADWAL": {}}
