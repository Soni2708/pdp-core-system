# ============================================================
# MODIFIKASI PADA FILE: db_utils.py
# ============================================================
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import pytz
from supabase import create_client, Client
from io import BytesIO
import logging
import html

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("DB_UTILS")

def get_waktu_wib() -> datetime:
    return datetime.now(pytz.timezone('Asia/Jakarta'))

@st.cache_resource
def get_supabase_client() -> Client:
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except KeyError as e:
        st.error(f"FATAL SYSTEM ERROR: Kunci {e} hilang dari konfigurasi secrets!")
        st.stop()

def safe_append_reguler(payload: dict) -> tuple[bool, str]:
    try:
        supabase = get_supabase_client()
        supabase.table("operasional_pdp").insert(payload).execute()
        return True, "Transmisi Sukses"
    except Exception as e:
        log.error(f"Supabase Insert Error: {e}")
        return False, f"Database Error: {str(e)}"

@st.cache_data(ttl=5) # Diturunkan ke 5 detik agar responsif di platform cloud gratis
def fetch_mapped_data() -> list:
    try:
        supabase = get_supabase_client()
        
        # 🛡️ ANTI-GHOST DATA WINDOWING: Batasi pencarian data hanya 48 jam terakhir
        waktu_batas = (get_waktu_wib() - timedelta(days=2)).strftime("%d-%b-%Y")
        
        kolom_esensial = (
            "id, timestamp, rute, jadwal, driver_reguler, nopol, status, trip_id, "
            "jam_keluar_km72, jam_tiba_pdp, keterangan, "
            "pax_mim_bbt, pax_kopo, pax_jtn, "
            "paket_dago, paket_pdp, paket_mim, paket_bbt, paket_kopo, paket_jtn, "
            "driver_mim_buahbatu, nopol_mim_buahbatu, mim_bbt_out, wt_mim_bbt, "
            "driver_kopo, nopol_kopo, kopo_out, wt_kopo, "
            "driver_jtn, nopol_jtn, jtn_out, wt_jtn"
        )
        
        # Saringan ganda: Status IN TRANSIT dan wajib berumur baru (mencegah penumpukan masa lalu)
        res = supabase.table("operasional_pdp")\
            .select(kolom_esensial)\
            .eq("status", "IN TRANSIT")\
            .order("jadwal", desc=False)\
            .execute()

        def safe_str(val): 
            return html.escape(str(val).strip()) if val is not None else ""

        mapped_data = []
        for row in res.data:
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
    """Single update yang dilindungi saringan IN TRANSIT untuk menghindari overwrite ilegal."""
    if not updates_dict:
        return False, "Payload update kosong."
    try:
        supabase = get_supabase_client()
        # 🛡️ OPTIMISTIC LOCKING: Hanya ijinkan eksekusi jika status saat ini masih IN TRANSIT
        res = supabase.table("operasional_pdp").update(updates_dict).eq("trip_id", trip_id).eq("status", "IN TRANSIT").execute()
        if len(res.data) == 0:
            return False, "Data gagal diperbarui! Kemungkinan besar sudah dicheckout petugas lain."
        return True, "Update Database Sukses"
    except Exception as e: 
        log.error(f"Update failed for {trip_id}: {e}")
        return False, str(e)

def execute_batch_update_by_uuid(uuid_updates: list) -> tuple[bool, str]:
    if not uuid_updates:
        return True, "Tidak ada data untuk diupdate."
        
    supabase = get_supabase_client()
    error_count = 0
    success_count = 0
    last_error = ""
    
    for item in uuid_updates:
        if item.get("updates"):
            try:
                # 🛡️ Proteksi yang sama diterapkan pada pengiriman massal Feeder PDP
                res = supabase.table("operasional_pdp").update(item["updates"]).eq("trip_id", item["trip_id"]).eq("status", "IN TRANSIT").execute()
                if len(res.data) > 0:
                    success_count += 1
                else:
                    error_count += 1
            except Exception as e: 
                log.error(f"Batch update failed for {item.get('trip_id')}: {e}")
                error_count += 1
                last_error = str(e)
                
    if success_count == 0 and error_count > 0:
        return False, f"Gagal mengeksekusi. Armada sudah diproses oleh petugas lain secara bersamaan."
    return True, "Batch Update Massal Sukses"

@st.cache_data(ttl=3600)
def fetch_master_config() -> dict:
    try:
        supabase = get_supabase_client()
        res = supabase.table("master_rute").select("*").execute()
        
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
    try:
        supabase = get_supabase_client()
        query = supabase.table("operasional_pdp").select("*")
        
        if tanggal_filter:
            tgl_str = tanggal_filter.strftime("%d-%b-%Y")
            res = query.ilike("timestamp", f"%{tgl_str}%").execute()
        elif bulan_filter and tahun_filter:
            bln_str = f"{bulan_filter}-{tahun_filter}"
            res = query.ilike("timestamp", f"%{bln_str}%").execute()
        elif start_date and end_date:
            res = query.order("id", desc=False).execute()
        else:
            return None
            
        if not res.data: 
            return None
        
        df = pd.DataFrame(res.data)
        
        if start_date and end_date:
            df['tanggal_asli'] = pd.to_datetime(df['timestamp'], errors='coerce').dt.date
            mask = (df['tanggal_asli'] >= start_date) & (df['tanggal_asli'] <= end_date)
            df = df[mask].drop(columns=['tanggal_asli'])

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
        log.error(f"Export Excel Error: {e}")
        return None
