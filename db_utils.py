# ============================================================
# DATABASE UTILITY - SUPABASE CLIENT & QUERIES
# ============================================================
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import pytz
from supabase import create_client, Client
from io import BytesIO
import logging
import html
import time

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("DB_UTILS")

# Constants
MAX_RETRIES = 3
RETRY_DELAY_BASE = 0.5  # seconds

def get_waktu_wib() -> datetime:
    return datetime.now(pytz.timezone('Asia/Jakarta'))

@st.cache_resource
def get_supabase_client() -> Client:
    """Mendapatkan koneksi Supabase (cached seumur hidup aplikasi)"""
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except KeyError as e:
        st.error(f"FATAL SYSTEM ERROR: Kunci {e} hilang dari konfigurasi secrets!")
        st.stop()

def retry_operation(func, *args, **kwargs):
    """Retry mechanism dengan exponential backoff untuk operasi database"""
    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_error = e
            if attempt < MAX_RETRIES - 1:
                wait_time = RETRY_DELAY_BASE * (2 ** attempt)
                log.warning(f"Retry {attempt + 1}/{MAX_RETRIES} after {wait_time}s: {e}")
                time.sleep(wait_time)
            else:
                log.error(f"Operation failed after {MAX_RETRIES} attempts: {e}")
    raise last_error

def safe_append_reguler(payload: dict) -> tuple[bool, str]:
    """Insert data operasional baru ke Supabase"""
    try:
        supabase = get_supabase_client()
        
        def _insert():
            return supabase.table("operasional_pdp").insert(payload).execute()
        
        retry_operation(_insert)
        return True, "Transmisi Sukses"
    except Exception as e:
        log.error(f"Supabase Insert Error: {e}")
        return False, f"Database Error: {str(e)}"

@st.cache_data(ttl=30)  # 30 detik, sinkron dengan fragment refresh 3 menit
def fetch_mapped_data() -> list:
    """
    Mengambil data operasional dengan filter:
    - Status IN TRANSIT
    - Data tidak lebih dari 48 jam (window protection)
    """
    try:
        supabase = get_supabase_client()
        
        # 🛡️ ACTIVE WINDOW PROTECTION: Hanya 48 jam terakhir
        waktu_batas = get_waktu_wib() - timedelta(days=2)
        
        kolom_esensial = (
            "id, timestamp, rute, jadwal, driver_reguler, nopol, status, trip_id, "
            "jam_keluar_km72, jam_tiba_pdp, keterangan, "
            "pax_mim_bbt, pax_kopo, pax_jtn, "
            "paket_dago, paket_pdp, paket_mim, paket_bbt, paket_kopo, paket_jtn, "
            "driver_mim_buahbatu, nopol_mim_buahbatu, mim_bbt_out, wt_mim_bbt, "
            "driver_kopo, nopol_kopo, kopo_out, wt_kopo, "
            "driver_jtn, nopol_jtn, jtn_out, wt_jtn"
        )
        
        def _fetch():
            return supabase.table("operasional_pdp")\
                .select(kolom_esensial)\
                .eq("status", "IN TRANSIT")\
                .order("jadwal", desc=False)\
                .execute()
        
        res = retry_operation(_fetch)

        def safe_str(val): 
            return html.escape(str(val).strip()) if val is not None else ""

        mapped_data = []
        for row in res.data:
            # Window protection filter (post-query)
            timestamp_str = str(row.get("timestamp", "")).strip()
            
            try:
                if not timestamp_str:
                    continue  # Bypass data kosong agar tidak menjadi Zombie Data
                    
                parts = timestamp_str.split()
                if not parts:
                    continue
                    
                row_time = datetime.strptime(parts[0], "%d-%b-%Y").date()
                if row_time < waktu_batas.date():
                    continue  # Skip data lebih dari 48 jam
            except Exception as e:
                # Catat anomali di log blackbox, jangan biarkan data lolos ke UI
                log.warning(f"Data anomali/korup dilewati. Nopol: {row.get('nopol')}, Err: {e}")
                continue

            if not row.get("nopol") and not row.get("rute"):
                continue

            mapped_data.append({
                "baris_db": row.get("id"),
                "waktu_input": safe_str(row.get("timestamp")),
                "rute": safe_str(row.get("rute")),
                "jadwal": safe_str(row.get("jadwal")),
                "driver": safe_str(row.get("driver_reguler")),
                "nopol": safe_str(row.get("nopol")),
                "status": safe_str(row.get("status")).upper(),
                "jam_72": safe_str(row.get("jam_keluar_km72")),
                "jam_tiba_pdp": safe_str(row.get("jam_tiba_pdp")),
                "keterangan": safe_str(row.get("keterangan")),
                "trip_id": safe_str(row.get("trip_id")),
                
                "pax_mim": int(row.get("pax_mim_bbt") or 0),
                "pax_kopo": int(row.get("pax_kopo") or 0),
                "pax_jtn": int(row.get("pax_jtn") or 0),
                
                "paket_dago": int(row.get("paket_dago") or 0),
                "paket_pdp": int(row.get("paket_pdp") or 0),
                "paket_mim": int(row.get("paket_mim") or 0),
                "paket_bbt": int(row.get("paket_bbt") or 0),
                "paket_kopo": int(row.get("paket_kopo") or 0),
                "paket_jtn": int(row.get("paket_jtn") or 0),
                
                "driver_mim_bbt": safe_str(row.get("driver_mim_buahbatu")),
                "nopol_mim_bbt": safe_str(row.get("nopol_mim_buahbatu")),
                "jam_out_mim": safe_str(row.get("mim_bbt_out")),
                "wt_mim": safe_str(row.get("wt_mim_bbt")),
                
                "driver_kopo": safe_str(row.get("driver_kopo")),
                "nopol_kopo": safe_str(row.get("nopol_kopo")),
                "jam_out_kopo": safe_str(row.get("kopo_out")),
                "wt_kopo": safe_str(row.get("wt_kopo")),
                
                "driver_jtn": safe_str(row.get("driver_jtn")),
                "nopol_jtn": safe_str(row.get("nopol_jtn")),
                "jam_out_jtn": safe_str(row.get("jtn_out")),
                "wt_jtn": safe_str(row.get("wt_jtn"))
            })
            
        return mapped_data
    except Exception as e:
        log.error(f"Supabase Fetch Error: {e}")
        return []

def safe_update_by_uuid(trip_id: str, updates_dict: dict) -> tuple[bool, str]:
    """Update single record dengan optimistic locking"""
    if not updates_dict:
        return False, "Payload update kosong."
    
    try:
        supabase = get_supabase_client()
        
        def _update():
            return supabase.table("operasional_pdp")\
                .update(updates_dict)\
                .eq("trip_id", trip_id)\
                .eq("status", "IN TRANSIT")\
                .execute()
        
        res = retry_operation(_update)
        if len(res.data) == 0:
            return False, "Data gagal diperbarui! Kemungkinan sudah diproses petugas lain."
        return True, "Update Database Sukses"
    except Exception as e: 
        log.error(f"Update failed for {trip_id}: {e}")
        return False, str(e)

def execute_batch_update_by_uuid(uuid_updates: list) -> tuple[bool, str]:
    """
    Batch update dengan retry logic per item.
    Note: Supabase tidak support batch update dengan nilai berbeda per row,
    jadi kita loop dengan retry mechanism.
    """
    if not uuid_updates:
        return True, "Tidak ada data untuk diupdate."
        
    supabase = get_supabase_client()
    success_count = 0
    failed_items = []
    
    for item in uuid_updates:
        if not item.get("updates"):
            continue
            
        try:
            def _update():
                return supabase.table("operasional_pdp")\
                    .update(item["updates"])\
                    .eq("trip_id", item["trip_id"])\
                    .eq("status", "IN TRANSIT")\
                    .execute()
            
            res = retry_operation(_update)
            if len(res.data) > 0:
                success_count += 1
            else:
                failed_items.append(item.get("trip_id"))
                
        except Exception as e: 
            log.error(f"Batch update failed for {item.get('trip_id')}: {e}")
            failed_items.append(item.get("trip_id"))
    
    if success_count == 0 and failed_items:
        return False, f"Gagal mengupdate {len(failed_items)} armada. Data mungkin sudah diproses."
    
    if failed_items:
        return True, f"Berhasil: {success_count}/{len(uuid_updates)}. Gagal: {len(failed_items)}"
    
    return True, f"Berhasil mengupdate {success_count} data"

@st.cache_data(ttl=3600)
def fetch_master_config() -> dict:
    """Ambil konfigurasi master (SLA dan jadwal) dari database"""
    try:
        supabase = get_supabase_client()
        
        def _fetch():
            return supabase.table("master_rute").select("*").execute()
        
        res = retry_operation(_fetch)
        
        config = {"SLA": {}, "JADWAL": {}}
        for row in res.data:
            rute = str(row.get("rute")).strip().upper()
            sla = int(row.get("sla_pdp") or 30)
            jadwal_raw = str(row.get("jadwal") or "")
            
            config["SLA"][rute] = sla
            if jadwal_raw:
                config["JADWAL"][rute] = [j.strip() for j in jadwal_raw.split(",") if j.strip()]
            else:
                config["JADWAL"][rute] = []
                
        return config
    except Exception as e: 
        log.error(f"Gagal memuat master config dari Supabase: {e}")
        return {"SLA": {}, "JADWAL": {}}

def generate_excel_report(tanggal_filter=None, bulan_filter=None, tahun_filter=None, start_date=None, end_date=None):
    """Generate Excel report dengan proteksi rentang maksimal 31 hari"""
    try:
        supabase = get_supabase_client()
        
        def _fetch():
            query = supabase.table("operasional_pdp").select("*")
            
            if tanggal_filter:
                tgl_str = tanggal_filter.strftime("%d-%b-%Y")
                return query.ilike("timestamp", f"%{tgl_str}%").execute()
            elif bulan_filter and tahun_filter:
                bln_str = f"{bulan_filter}-{tahun_filter}"
                return query.ilike("timestamp", f"%{bln_str}%").execute()
            elif start_date and end_date:
                delta = end_date - start_date
                if delta.days < 0:
                    return None
                    
                if delta.days > 31:
                    raise ValueError("Beban server: Rentang maksimal adalah 31 hari.")
                    
                or_conditions = []
                for i in range(delta.days + 1):
                    tgl_target = start_date + timedelta(days=i)
                    tgl_str = tgl_target.strftime("%d-%b-%Y")
                    or_conditions.append(f"timestamp.ilike.%{tgl_str}%")
                
                query_string = ",".join(or_conditions)
                return query.or_(query_string).order("id", desc=False).execute()
            else:
                return None
        
        res = retry_operation(_fetch) if _fetch() is not None else None
        
        if not res or not res.data: 
            return None
        
        df = pd.DataFrame(res.data)
        
        if df.empty: 
            return None
        
        kolom_rapi = [
            "timestamp", "trip_id", "rute", "jadwal", "nopol", "driver_reguler", 
            "status", "jam_keluar_km72", "jam_tiba_pdp", 
            "pax_mim_bbt", "pax_kopo", "pax_jtn",
            "paket_dago", "paket_pdp", "paket_mim", "paket_bbt", "paket_kopo", "paket_jtn",
            "driver_mim_buahbatu", "nopol_mim_buahbatu", "mim_bbt_out", "wt_mim_bbt",
            "driver_kopo", "nopol_kopo", "kopo_out", "wt_kopo",
            "driver_jtn", "nopol_jtn", "jtn_out", "wt_jtn",
            "keterangan"
        ]
        
        df = df[[k for k in kolom_rapi if k in df.columns]]
        
        rename_map = {
            "timestamp": "Waktu Input", "driver_reguler": "Driver Reguler", "status": "Status",
            "jam_keluar_km72": "Jam Out KM72", "jam_tiba_pdp": "Jam Tiba PDP",
            "pax_mim_bbt": "Pax MIM", "pax_kopo": "Pax Kopo", "pax_jtn": "Pax Jatinangor",
            "paket_dago": "Paket Dago", "paket_pdp": "Paket PDP", "paket_mim": "Paket MIM",
            "paket_bbt": "Paket Buahbatu", "paket_kopo": "Paket Kopo", "paket_jtn": "Paket Jatinangor",
            "driver_mim_buahbatu": "Driver Feeder MIM", "nopol_mim_buahbatu": "Nopol Feeder MIM",
            "mim_bbt_out": "Feeder MIM Out", "wt_mim_bbt": "WT MIM (Menit)",
            "driver_kopo": "Driver Feeder Kopo", "nopol_kopo": "Nopol Feeder Kopo",
            "kopo_out": "Feeder Kopo Out", "wt_kopo": "WT Kopo (Menit)",
            "driver_jtn": "Driver Feeder Jtn", "nopol_jtn": "Nopol Feeder Jtn",
            "jtn_out": "Feeder Jtn Out", "wt_jtn": "WT Jtn (Menit)", "keterangan": "Keterangan/Catatan"
        }
        df.rename(columns=rename_map, inplace=True)
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Data_Operasional', startrow=4)
        
        return output.getvalue()
    except Exception as e:
        if isinstance(e, ValueError):
            raise e
        log.error(f"Export Excel Error: {e}")
        return None
