import streamlit as st
import base64
from datetime import timedelta
import gc

from components.ui_styles import apply_global_cyberpunk_theme, render_cyberpunk_header
from components.navbar import render_navbar
from core.auth import require_auth
from db_utils import generate_excel_report, get_waktu_wib

st.set_page_config(page_title="Laporan Manajemen", page_icon="📊", layout="centered")
apply_global_cyberpunk_theme()
require_auth(module_name="admin", secret_dict_name="users_admin")
render_navbar("admin")

# ==========================================
# 🛑 STATE MANAGEMENT & GARBAGE COLLECTION
# ==========================================
if "report_data" not in st.session_state: st.session_state.report_data = None
if "report_name" not in st.session_state: st.session_state.report_name = ""
if "active_trigger" not in st.session_state: st.session_state.active_trigger = ""

def reset_report():
    """Otomatis dipanggil saat parameter tanggal diubah untuk mencegah unduhan file usang."""
    st.session_state.report_data = None
    st.session_state.report_name = ""
    st.session_state.active_trigger = ""

def force_garbage_collect():
    """ENGINEERING FIX: Pembersih RAM manual untuk mencegah Out-of-Memory (OOM) 
    saat mengekspor file Excel berskala besar."""
    reset_report()
    st.cache_data.clear() # Membersihkan cache data Supabase
    gc.collect()          # Memaksa Python membuang memori yang tidak terpakai
    st.toast("🧹 Memori RAM & Cache Sistem berhasil dikosongkan!", icon="✅")

# ========== LOGO & HEADER ==========
try:
    with open("assets/logo.png", "rb") as img_file:
        img_b64 = base64.b64encode(img_file.read()).decode()
    st.markdown(f"""
        <div style='display: flex; justify-content: center; align-items: center; margin-bottom: 15px; width: 100%; padding-top: 10px;'>
            <img src='data:image/png;base64,{img_b64}' style='max-width: 160px; height: auto; filter: drop-shadow(0px 4px 6px rgba(0,0,0,0.1));'>
        </div>
    """, unsafe_allow_html=True)
except FileNotFoundError:
    pass

render_cyberpunk_header("EXPORT DATA OPERASIONAL", "Sistem Laporan Feeder PDP", "var(--accent-cyan)")
st.divider()

# ==========================================
# ⚙️ SYSTEM MAINTENANCE PANEL
# ==========================================
with st.expander("🛠️ System Maintenance & Memory Control"):
    st.markdown("<p style='font-size: 13px; color: var(--text-muted);'>Gunakan fitur ini jika aplikasi terasa lambat setelah Anda mengekspor laporan dengan rentang waktu yang sangat besar (akumulasi memori Pandas).</p>", unsafe_allow_html=True)
    if st.button("🧹 Bersihkan Cache & Bebaskan RAM", use_container_width=True):
        force_garbage_collect()

st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)

# ==========================================
# 📋 PANEL GENERATOR LAPORAN
# ==========================================
tab1, tab2, tab3 = st.tabs(["📅 HARIAN", "📆 RENTANG KUSTOM", "🗓️ BULANAN"])
waktu_sekarang = get_waktu_wib()

# --- TAB 1: HARIAN ---
with tab1:
    with st.container(border=True):
        st.markdown("<h4 style='color:var(--text-primary); font-family:\"Rajdhani\", sans-serif; font-size:16px; margin-top:0; margin-bottom:15px; letter-spacing:1px; border-left: 4px solid var(--accent-cyan); padding-left: 8px;'>EKSTRAKSI DATA HARIAN</h4>", unsafe_allow_html=True)
        
        tgl_pilih = st.date_input("Pilih Tanggal Laporan:", waktu_sekarang.date(), on_change=reset_report)
        
        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
        if st.button("🚀 COMPILE LAPORAN HARIAN", use_container_width=True, type="primary"):
            with st.spinner("Menarik data terenkripsi dari Supabase..."):
                st.session_state.report_data = generate_excel_report(tanggal_filter=tgl_pilih)
                st.session_state.report_name = f"Laporan_Harian_{tgl_pilih.strftime('%d_%b_%Y')}.xlsx"
                st.session_state.active_trigger = "harian"
                
        if st.session_state.active_trigger == "harian":
            if st.session_state.report_data:
                st.success("✅ Dokumen Excel Siap Diunduh!")
                st.download_button(f"📥 DOWNLOAD FILE HARIAN", data=st.session_state.report_data, file_name=st.session_state.report_name, use_container_width=True)
            else:
                st.warning("⚠️ Nihil: Tidak ada data operasional pada tanggal ini.")

# --- TAB 2: RENTANG WAKTU ---
with tab2:
    with st.container(border=True):
        st.markdown("<h4 style='color:var(--text-primary); font-family:\"Rajdhani\", sans-serif; font-size:16px; margin-top:0; margin-bottom:15px; letter-spacing:1px; border-left: 4px solid var(--accent-yellow); padding-left: 8px;'>EKSTRAKSI RENTANG KUSTOM</h4>", unsafe_allow_html=True)
        
        rentang_tanggal = st.date_input("Pilih Rentang Tanggal:", value=(waktu_sekarang.date() - timedelta(days=6), waktu_sekarang.date()), on_change=reset_report)
        
        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
        # 🛡️ Validasi untuk memastikan user memilih tanggal awal DAN tanggal akhir
        if isinstance(rentang_tanggal, tuple) and len(rentang_tanggal) == 2:
            start_date, end_date = rentang_tanggal
            
            if st.button("🚀 COMPILE LAPORAN RENTANG", use_container_width=True, type="primary"):
                with st.spinner(f"Sinkronisasi data dari {start_date.strftime('%d %b')} hingga {end_date.strftime('%d %b')}..."):
                    st.session_state.report_data = generate_excel_report(start_date=start_date, end_date=end_date)
                    st.session_state.report_name = f"Laporan_Rentang_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.xlsx"
                    st.session_state.active_trigger = "rentang"
                    
            if st.session_state.active_trigger == "rentang":
                if st.session_state.report_data:
                    st.success("✅ Dokumen Excel Siap Diunduh!")
                    st.download_button("📥 DOWNLOAD FILE RENTANG", data=st.session_state.report_data, file_name=st.session_state.report_name, use_container_width=True)
                else:
                    st.warning("⚠️ Nihil: Tidak ada data pada rentang tanggal tersebut.")
        else:
            st.info("💡 Pilih tanggal awal dan tanggal akhir pada kalender untuk membuka sistem eksekusi.")

# --- TAB 3: BULANAN ---
with tab3:
    with st.container(border=True):
        st.markdown("<h4 style='color:var(--text-primary); font-family:\"Rajdhani\", sans-serif; font-size:16px; margin-top:0; margin-bottom:15px; letter-spacing:1px; border-left: 4px solid var(--accent-red); padding-left: 8px;'>EKSTRAKSI DATA BULANAN</h4>", unsafe_allow_html=True)
        
        col_bln, col_thn = st.columns(2)
        list_bulan = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        
        with col_bln: 
            bln_pilih = st.selectbox("Pilih Bulan:", list_bulan, index=waktu_sekarang.month - 1, on_change=reset_report)
        with col_thn: 
            thn_pilih = st.number_input("Pilih Tahun:", min_value=2024, max_value=2030, value=waktu_sekarang.year, on_change=reset_report)
        
        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
        
        if st.button("🚀 COMPILE LAPORAN BULANAN", use_container_width=True, type="primary"):
            with st.spinner(f"Mengompilasi agregasi data periode {bln_pilih} {thn_pilih}..."):
                st.session_state.report_data = generate_excel_report(bulan_filter=bln_pilih, tahun_filter=str(thn_pilih))
                st.session_state.report_name = f"Laporan_Bulanan_{bln_pilih}_{thn_pilih}.xlsx"
                st.session_state.active_trigger = "bulanan"
                
        if st.session_state.active_trigger == "bulanan":
            if st.session_state.report_data:
                st.success("✅ Dokumen Excel Siap Diunduh!")
                st.download_button(f"📥 DOWNLOAD BULANAN ({bln_pilih})", data=st.session_state.report_data, file_name=st.session_state.report_name, use_container_width=True)
            else:
                st.warning(f"⚠️ Nihil: Tidak ditemukan records pada periode {bln_pilih} {thn_pilih}.")
