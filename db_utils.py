import gspread
import streamlit as st
from datetime import datetime
import pytz
import time
import random
from functools import wraps

def get_waktu_wib():
    return datetime.now(pytz.timezone('Asia/Jakarta'))

@st.cache_resource(ttl=3600)
def get_gspread_client():
    try:
        kredensial = dict(st.secrets["connections"]["gsheets"])
        return gspread.service_account_from_dict(kredensial)
    except Exception as e:
        st.error(f"FATAL ERROR: Kredensial Database Hilang/Salah! {e}")
        st.stop()

def get_worksheet(sheet_name="Trial_Data_Transit", worksheet_name="DATABASE_REGULER"):
    try:
        gc = get_gspread_client()
        return gc.open(sheet_name).worksheet(worksheet_name)
    except Exception as e:
        st.error(f"Koneksi Database Terputus: {e}")
        return None

def gspread_retry(max_retries=4, base_delay=1.0):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    error_msg = str(e)
                    if any(err in error_msg for err in ["429", "500", "502", "QuotaExceeded"]):
                        sleep_time = (base_delay * (2 ** retries)) + random.uniform(0, 1)
                        time.sleep(sleep_time)
                        retries += 1
                        continue
                    if "200" in error_msg:
                        return True, "Eksekusi Sukses"
                    return False, f"System Error: {error_msg}"
            return False, "Server sibuk."
        return wrapper
    return decorator

@gspread_retry(max_retries=4)
def execute_batch_update(payloads):
    sheet = get_worksheet()
    if not sheet or not payloads: return False, "Payload kosong."
    sheet.batch_update(payloads, value_input_option="USER_ENTERED")
    return True, "Update Batch Sukses"

def clean_pax(val):
    val_clean = str(val).strip()
    return val_clean if val_clean.isdigit() else "0"

# ============================================================
# 🎯 ABSOLUTE ANCHOR INSERTION (MENCEGAH HORIZONTAL SHIFT)
# ============================================================
@gspread_retry(max_retries=4)
def safe_append_reguler(data_baru):
    """
    Menembak data baru secara presisi di Kolom A sampai Z.
    Ini menghilangkan risiko Google Sheets melar ke Kolom AA, AX, dst.
    """
    sheet = get_worksheet()
    if not sheet: return False, "Koneksi terputus."
    
    try:
        # 1. Cari baris kosong pertama di Kolom A (mengabaikan border)
        kolom_a = sheet.col_values(1)
        baris_target = len(kolom_a) + 1 
        
        for i in range(4, len(kolom_a)):
            if str(kolom_a[i]).strip() == "":
                baris_target = i + 1
                break

        # 2. ABSOLUTE ANCHOR: Paksa tulis dari A sampai Z di baris tersebut.
        sheet.update(f"A{baris_target}:Z{baris_target}", [data_baru], value_input_option="USER_ENTERED")
        
        return True, "Transmisi Sukses"
    except Exception as e:
        return False, f"System Error saat Append: {str(e)}"

# ============================================================
# 🚨 PURE LIVE DATA (UUID ENABLED & CACHED)
# ============================================================
@st.cache_data(ttl=15)
def fetch_mapped_data():
    sheet = get_worksheet()
    if not sheet: return []
    
    try:
        raw_data = sheet.get_all_values()
    except Exception as e:
        st.error(f"Gagal Menarik Data: {e}")
        return []

    mapped_data = []
    for i, row in enumerate(raw_data):
        # Abaikan baris kosong, header, atau tabel yang tidak relevan
        if len(row) < 5 or "TIMESTAMP" in str(row).upper() or "RUTE" in str(row).upper(): 
            continue 
        
        if not str(row[0]).strip():
            continue
            
        # Perluasan array untuk mengakomodir Kolom Z (Index 25)
        while len(row) < 26: 
            row.append("") 
        
        mapped_data.append({
            "baris_db": i + 1,
            "waktu_input": str(row[0]).strip(),
            "rute": str(row[1]).strip(),
            "jadwal": str(row[2]).strip(),
            "driver": str(row[3]).strip(),
            "nopol": str(row[4]).strip(),
            "pax_mim": clean_pax(row[5]),
            "pax_kopo": clean_pax(row[6]),
            "pax_jtn": clean_pax(row[7]),
            "status": str(row[8]).strip().upper(),
            "jam_72": str(row[9]).strip(),
            "jam_tiba_pdp": str(row[10]).strip(),
            "jam_out_mim": str(row[13]).strip(), 
            "jam_out_kopo": str(row[17]).strip(), 
            "jam_out_jtn": str(row[21]).strip(),
            "trip_id": str(row[25]).strip() # DNA UNIK (KOLOM Z)
        })
        
    return mapped_data

# ============================================================
# 🛡️ ENGINE UPDATE PRESISI BERBASIS UUID
# ============================================================
@gspread_retry(max_retries=4)
def safe_update_by_uuid(trip_id, updates_dict):
    """ Eksekusi update presisi 1 target armada (Dipakai di KM72 & PDP TIBA) """
    sheet = get_worksheet()
    if not sheet: return False, "Koneksi terputus."
    
    try:
        kolom_z = sheet.col_values(26) 
        if trip_id not in kolom_z:
            return False, f"Target armada gagal dilacak."
        
        baris_aktual = kolom_z.index(trip_id) + 1 
        
        payloads = [{'range': f"{col}{baris_aktual}", 'values': [[val]]} for col, val in updates_dict.items()]
        sheet.batch_update(payloads, value_input_option="USER_ENTERED")
        return True, "Update Presisi Sukses"
    except Exception as e:
        return False, f"System Error: {str(e)}"

@gspread_retry(max_retries=4)
def execute_batch_update_by_uuid(uuid_updates):
    """ Eksekusi update massal armada Feeder dalam 1 API call (Dipakai di PDP Dispatch) """
    sheet = get_worksheet()
    if not sheet: return False, "Koneksi terputus."
    
    try:
        kolom_z = sheet.col_values(26) 
        payloads = []
        
        for item in uuid_updates:
            tid = item["trip_id"]
            if tid in kolom_z:
                baris_aktual = kolom_z.index(tid) + 1
                for col, val in item["updates"].items():
                    payloads.append({'range': f"{col}{baris_aktual}", 'values': [[val]]})
        
        if not payloads: 
            return False, "Data penumpang tidak ditemukan."
        
        sheet.batch_update(payloads, value_input_option="USER_ENTERED")
        return True, "Batch Update Massal Sukses"
    except Exception as e:
        return False, f"System Error: {str(e)}"
    
    # ============================================================
# ⚙️ DYNAMIC CONFIGURATION ENGINE
# ============================================================
@st.cache_data(ttl=3600) # Cache 1 Jam (Sangat Hemat API)
def fetch_master_config():
    """Menarik SLA dan Jadwal dinamis dari GSheets"""
    try:
        gc = get_gspread_client()
        sheet = gc.open("Trial_Data_Transit").worksheet("MASTER_CONFIG")
        raw_data = sheet.get_all_values()
        
        config = {"SLA": {}, "JADWAL": {}}
        for row in raw_data[1:]: # Skip baris pertama (Header)
            if len(row) >= 3:
                kategori = str(row[0]).strip().upper()
                rute = str(row[1]).strip().upper()
                value = str(row[2]).strip()
                
                if kategori == "SLA":
                    config["SLA"][rute] = int(value) if value.isdigit() else 150
                elif kategori == "JADWAL":
                    # Pecah string jam menjadi list array
                    config["JADWAL"][rute] = [j.strip() for j in value.split(",")]
                    
        return config
    except Exception as e:
        st.error(f"Gagal memuat MASTER_CONFIG: {e}")
        return {"SLA": {}, "JADWAL": {}}