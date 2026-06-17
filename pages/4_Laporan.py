import streamlit as st
from datetime import timedelta
import gc
import pandas as pd

# Menggunakan arsitektur tema Neo-Tokyo yang baru
from components.ui_styles import apply_neo_tokyo_corporate, render_neo_tokyo_header, render_logo
from components.navbar import render_navbar
from core.auth import require_auth
from db_utils import generate_excel_report, get_waktu_wib, fetch_master_config

st.set_page_config(page_title="LAPORAN MANAJEMEN", layout="wide", initial_sidebar_state="collapsed")
apply_neo_tokyo_corporate()
require_auth(module_name="admin", secret_dict_name="users_admin")
render_navbar("admin")

# ==========================================
# 🛑 STATE MANAGEMENT & GARBAGE COLLECTION
# ==========================================
if "report_data" not in st.session_state: 
    st.session_state.report_data = None
if "report_name" not in st.session_state: 
    st.session_state.report_name = ""
if "active_trigger" not in st.session_state: 
    st.session_state.active_trigger = ""
if "last_preview" not in st.session_state:
    st.session_state.last_preview = None

def reset_report():
    st.session_state.report_data = None
    st.session_state.report_name = ""
    st.session_state.active_trigger = ""

def force_garbage_collect():
    reset_report()
    st.cache_data.clear() 
    gc.collect()          

# ========== LOGO & HEADER ==========
render_logo(align="left", margin_bottom="5px")

col_judul, col_status = st.columns([3, 1.5])
with col_judul:
    render_neo_tokyo_header(
        title="EXPORT DATA OPERASIONAL", 
        subtitle="Sistem Laporan & Agregasi Feeder", 
        accent="var(--nt-text-muted)", 
        align="left"
    )

with col_status:
    petugas_aktif = st.session_state.get('petugas_admin', 'UNKNOWN')
    waktu_sekarang_dt = get_waktu_wib()
    tanggal_str = waktu_sekarang_dt.strftime("%d %B %Y")
    waktu_str = waktu_sekarang_dt.strftime("%H:%M:%S")

    st.markdown(f"""
    <div style="text-align: right; margin-top: 5px;">
        <div style='display: inline-block; background: rgba(139, 148, 158, 0.05); border: 1px solid rgba(139, 148, 158, 0.2); padding: 4px 12px; border-radius: 4px; font-size: 11px; font-weight: 700; color: var(--nt-text-muted); margin-bottom: 10px;'>
            <span style='color: #00E676;'>●</span> USER ACTIVE: <span style='color: #F8F9FA; letter-spacing: 0.5px;'>{petugas_aktif}</span>
        </div>
        <div style="margin-top: 2px; margin-bottom: 8px;">
            <span style="background: rgba(0, 230, 118, 0.15); color: #00E676; padding: 4px 12px; border-radius: 20px; font-size: 10px; font-weight: 800; letter-spacing: 0.5px; border: 1px solid rgba(0, 230, 118, 0.3);">SISTEM AKTIF</span>
        </div>
        <div style="font-size: 11px; color: #8B949E; margin-bottom: 12px; font-weight: 500;">
            {tanggal_str} | <span style="color: #F8F9FA;">{waktu_str} WIB</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ==========================================
# ⚙️ SYSTEM MAINTENANCE PANEL
# ==========================================
with st.expander("🔧 SYSTEM MAINTENANCE & MEMORY CONTROL"):
    st.markdown("<p style='font-size: 13px; color: var(--nt-text-muted); margin: 0 0 10px 0;'>Gunakan fitur ini untuk mereset alokasi RAM server setelah mengekspor laporan dengan rentang waktu/data yang sangat besar.</p>", unsafe_allow_html=True)
    
    col_maint1, col_maint2 = st.columns(2)
    with col_maint1:
        if st.button("🧹 BERSIHKAN CACHE", use_container_width=True):
            force_garbage_collect()
            st.toast("✅ MEMORI & CACHE SISTEM BERHASIL DIKOSONGKAN")
    with col_maint2:
        if st.button("📊 INFO SISTEM", use_container_width=True):
            st.info("""
            **Informasi Sistem:**
            - Batas maksimal export: 31 hari
            - Format file: Excel (.xlsx)
            - Data diambil dari Supabase
            """)

st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)

# ==========================================
# 📋 PANEL GENERATOR LAPORAN
# ==========================================
tab1, tab2, tab3 = st.tabs(["📅 HARIAN", "📆 MINGGUAN KUSTOM", "📊 BULANAN"])
waktu_sekarang = get_waktu_wib()

# --- TAB 1: HARIAN ---
with tab1:
    with st.container(border=True):
        st.markdown("<div class='nt-meta' style='color: var(--nt-cyan); border-bottom: 1px solid var(--nt-border); padding-bottom: 8px; margin-bottom: 16px;'>[ 01 ] EKSTRAKSI DATA HARIAN</div>", unsafe_allow_html=True)
        
        tgl_pilih = st.date_input("PILIH TANGGAL", waktu_sekarang.date(), on_change=reset_report)
        
        # Preview info
        st.caption(f"📌 Akan mengekspor data untuk tanggal: **{tgl_pilih.strftime('%d %b %Y')}**")
        
        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
        
        col_gen1, col_gen2 = st.columns([2, 1])
        with col_gen1:
            if st.button("📊 COMPILE LAPORAN HARIAN", use_container_width=True, type="primary"):
                with st.spinner(f"Menarik data dari Supabase untuk tanggal {tgl_pilih.strftime('%d %b %Y')}..."):
                    st.session_state.report_data = generate_excel_report(tanggal_filter=tgl_pilih)
                    st.session_state.report_name = f"Laporan_Harian_{tgl_pilih.strftime('%d_%b_%Y')}.xlsx"
                    st.session_state.active_trigger = "harian"
                    
        if st.session_state.active_trigger == "harian":
            if st.session_state.report_data:
                st.success(f"✅ DOKUMEN EXCEL SIAP DIUNDUH - {tgl_pilih.strftime('%d %b %Y')}")
                
                col_dl1, col_dl2 = st.columns([2, 1])
                with col_dl1:
                    st.download_button(
                        label="📥 DOWNLOAD FILE HARIAN", 
                        data=st.session_state.report_data, 
                        file_name=st.session_state.report_name, 
                        use_container_width=True,
                        on_click=force_garbage_collect
                    )
                with col_dl2:
                    if st.button("🔄 RESET", use_container_width=True):
                        reset_report()
                        st.rerun()
            else:
                st.warning(f"⚠️ NIHIL: TIDAK ADA DATA PADA TANGGAL {tgl_pilih.strftime('%d %b %Y')}.")

# --- TAB 2: RENTANG WAKTU ---
with tab2:
    with st.container(border=True):
        st.markdown("<div class='nt-meta' style='color: var(--nt-warning); border-bottom: 1px solid var(--nt-border); padding-bottom: 8px; margin-bottom: 16px;'>[ 02 ] EKSTRAKSI RENTANG KUSTOM</div>", unsafe_allow_html=True)
        
        rentang_tanggal = st.date_input(
            "PILIH RENTANG TANGGAL", 
            value=(waktu_sekarang.date() - timedelta(days=6), waktu_sekarang.date()), 
            on_change=reset_report
        )
        
        if isinstance(rentang_tanggal, tuple) and len(rentang_tanggal) == 2:
            start_date, end_date = rentang_tanggal
            delta_days = (end_date - start_date).days + 1
            
            # Preview info dengan warning jika terlalu besar
            if delta_days > 31:
                st.error(f"⚠️ RENTANG {delta_days} HARI MELEBIHI BATAS MAKSIMAL (31 HARI)!")
                st.caption("Silakan pilih rentang maksimal 31 hari atau gunakan tab BULANAN.")
            else:
                st.caption(f"📌 Akan mengekspor **{delta_days} hari** data dari **{start_date.strftime('%d %b %Y')}** s.d. **{end_date.strftime('%d %b %Y')}**")
        
        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
        
        if isinstance(rentang_tanggal, tuple) and len(rentang_tanggal) == 2:
            start_date, end_date = rentang_tanggal
            delta_days = (end_date - start_date).days + 1
            
            col_gen1, col_gen2 = st.columns([2, 1])
            with col_gen1:
                if st.button("📊 COMPILE LAPORAN RENTANG", use_container_width=True, type="primary"):
                    if delta_days > 31:
                        st.error(f"❌ RENTANG {delta_days} HARI MELEBIHI BATAS MAKSIMAL (31 HARI)")
                    else:
                        with st.spinner(f"Sinkronisasi data dari {start_date.strftime('%d %b')} hingga {end_date.strftime('%d %b')}..."):
                            try:
                                st.session_state.report_data = generate_excel_report(start_date=start_date, end_date=end_date)
                                if st.session_state.report_data:
                                    st.session_state.report_name = f"Laporan_Rentang_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.xlsx"
                                    st.session_state.active_trigger = "rentang"
                            except ValueError as e:
                                st.error(str(e))
                                st.session_state.active_trigger = ""
                            
            if st.session_state.active_trigger == "rentang":
                if st.session_state.report_data:
                    st.success(f"✅ DOKUMEN EXCEL SIAP DIUNDUH - {delta_days} hari data")
                    
                    col_dl1, col_dl2 = st.columns([2, 1])
                    with col_dl1:
                        st.download_button(
                            label="📥 DOWNLOAD FILE RENTANG", 
                            data=st.session_state.report_data, 
                            file_name=st.session_state.report_name, 
                            use_container_width=True,
                            on_click=force_garbage_collect
                        )
                    with col_dl2:
                        if st.button("🔄 RESET", use_container_width=True):
                            reset_report()
                            st.rerun()
                else:
                    st.warning(f"⚠️ NIHIL: TIDAK ADA DATA PADA RENTANG TANGGAL TERSEBUT.")
        else:
            st.info("📌 PILIH TANGGAL AWAL DAN AKHIR UNTUK MEMBUKA SISTEM EKSEKUSI.")

# --- TAB 3: BULANAN ---
with tab3:
    with st.container(border=True):
        st.markdown("<div class='nt-meta' style='color: var(--nt-violet); border-bottom: 1px solid var(--nt-border); padding-bottom: 8px; margin-bottom: 16px;'>[ 03 ] EKSTRAKSI DATA BULANAN</div>", unsafe_allow_html=True)
        
        col_bln, col_thn = st.columns(2)
        list_bulan = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        
        with col_bln: 
            bln_pilih = st.selectbox("PILIH BULAN", list_bulan, index=waktu_sekarang.month - 1, on_change=reset_report)
        with col_thn: 
            thn_pilih = st.number_input("PILIH TAHUN", min_value=2024, max_value=2030, value=waktu_sekarang.year, on_change=reset_report)
        
        # Preview info
        bulan_num = list_bulan.index(bln_pilih) + 1
        st.caption(f"📌 Akan mengekspor data untuk periode: **{bln_pilih} {thn_pilih}** (bulan ke-{bulan_num})")
        
        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
        
        col_gen1, col_gen2 = st.columns([2, 1])
        with col_gen1:
            if st.button("📊 COMPILE LAPORAN BULANAN", use_container_width=True, type="primary"):
                with st.spinner(f"Mengompilasi agregasi data periode {bln_pilih} {thn_pilih}..."):
                    st.session_state.report_data = generate_excel_report(bulan_filter=bln_pilih, tahun_filter=str(thn_pilih))
                    st.session_state.report_name = f"Laporan_Bulanan_{bln_pilih}_{thn_pilih}.xlsx"
                    st.session_state.active_trigger = "bulanan"
                    
        if st.session_state.active_trigger == "bulanan":
            if st.session_state.report_data:
                st.success(f"✅ DOKUMEN EXCEL SIAP DIUNDUH - {bln_pilih} {thn_pilih}")
                
                col_dl1, col_dl2 = st.columns([2, 1])
                with col_dl1:
                    st.download_button(
                        label=f"📥 DOWNLOAD BULANAN ({bln_pilih.upper()})", 
                        data=st.session_state.report_data, 
                        file_name=st.session_state.report_name, 
                        use_container_width=True,
                        on_click=force_garbage_collect
                    )
                with col_dl2:
                    if st.button("🔄 RESET", use_container_width=True):
                        reset_report()
                        st.rerun()
            else:
                st.warning(f"⚠️ NIHIL: TIDAK DITEMUKAN RECORDS PADA PERIODE {bln_pilih.upper()} {thn_pilih}.")

# ==========================================
# 📋 FOOTER INFO
# ==========================================
st.divider()
st.markdown("""
<div style='text-align: center; color: var(--nt-text-muted); font-size: 11px;'>
    <span>📌 Format file: Microsoft Excel (.xlsx)</span>
    <span style='margin: 0 10px'>|</span>
    <span>🔒 Data dienkripsi selama transfer</span>
    <span style='margin: 0 10px'>|</span>
    <span>⏱️ Batas maksimal export: 31 hari</span>
</div>
""", unsafe_allow_html=True)
