import streamlit as st
import base64 # Injeksi untuk Logo Adaptive
from components.ui_styles import apply_global_cyberpunk_theme, render_cyberpunk_header
from core.auth import require_auth
from db_utils import generate_excel_report, get_waktu_wib
from datetime import datetime, timedelta

# --- KONFIGURASI HALAMAN (MURNI CENTERED) ---
st.set_page_config(page_title="Laporan Manajemen", page_icon="📊", layout="centered")
apply_global_cyberpunk_theme()
require_auth(module_name="admin", secret_dict_name="users_admin")

# ============================================================
# 🚀 ADAPTIVE BRANDING LOGO (FLEXBOX)
# ============================================================
# 💉 NEXUS PRIME REFACTOR: Mencegah logo pecah/terpotong di layar Admin
try:
    with open("assets/logo.png", "rb") as img_file:
        img_b64 = base64.b64encode(img_file.read()).decode()
    st.markdown(f"""
        <div style='display: flex; justify-content: center; align-items: center; margin-bottom: 15px; width: 100%; padding-top: 10px;'>
            <img src='data:image/png;base64,{img_b64}' style='max-width: 160px; height: auto; object-fit: contain; filter: drop-shadow(0px 4px 6px rgba(0,0,0,0.1));'>
        </div>
    """, unsafe_allow_html=True)
except FileNotFoundError:
    pass

# Menggunakan variabel adaptif var(--accent-cyan)
render_cyberpunk_header("EXPORT DATA OPERASIONAL", "Sistem Laporan Feeder PDP", "var(--accent-cyan)")
st.divider()

# ============================================================
# INISIALISASI STATE CACHE LAPORAN (ANTI-REDUNDANT FETCH)
# ============================================================
if "cache_harian" not in st.session_state: st.session_state.cache_harian = None
if "cache_kustom" not in st.session_state: st.session_state.cache_kustom = None
if "cache_bulanan" not in st.session_state: st.session_state.cache_bulanan = None

if "tgl_harian_last" not in st.session_state: st.session_state.tgl_harian_last = None
if "rentang_kustom_last" not in st.session_state: st.session_state.rentang_kustom_last = None
if "periode_bulanan_last" not in st.session_state: st.session_state.periode_bulanan_last = None

# 📑 URUTAN TAB ERGONOMIS
tab1, tab2, tab3 = st.tabs(["📅 HARIAN", "📆 MINGGUAN / CUSTOM", "🗓️ BULANAN"])

# ==========================================
# TAB 1: HARIAN
# ==========================================
with tab1:
    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
    tgl_pilih = st.date_input("Pilih Tanggal:", get_waktu_wib().date())
    
    # Deteksi jika user mengubah tanggal input, hancurkan cache lama
    if tgl_pilih != st.session_state.tgl_harian_last:
        st.session_state.cache_harian = None
        st.session_state.tgl_harian_last = tgl_pilih

    # Spacer agar jarak antara Input dan Tombol tidak sesak
    st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
    
    if st.session_state.cache_harian is None:
        if st.button("UNDUH LAPORAN HARIAN", key="btn_prep_hari", width="stretch"):
            with st.spinner("Mengompilasi enkripsi data harian dari Supabase..."):
                st.session_state.cache_harian = generate_excel_report(tanggal_filter=tgl_pilih)
                if not st.session_state.cache_harian:
                    st.toast("Nihil: Tidak ditemukan records data pada tanggal ini.", icon="⚠️")
                st.rerun()
    
    # Tombol unduh asli hanya muncul jika dokumen sudah matang di memori
    if st.session_state.cache_harian:
        st.success(f"✅ Dokumen Excel Berhasil Dikompilasi!")
        st.download_button(
            label=f"📥 DOWNLOAD FILE HARIAN ({tgl_pilih.strftime('%d %b %Y')})",
            data=st.session_state.cache_harian,
            file_name=f"Laporan_Harian_{tgl_pilih.strftime('%Y-%m-%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            width="stretch",
            type="primary"
        )

# ==========================================
# TAB 2: MINGGUAN / KUSTOM
# ==========================================
with tab2:
    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
    # 💉 PERBAIKAN: Warna hint diubah menjadi adaptif var(--text-muted)
    st.markdown("<p style='color:var(--text-muted); font-size:13px; margin-bottom:15px; font-weight:500;'>💡 <i>Pilih tanggal mulai dan tanggal akhir.</i></p>", unsafe_allow_html=True)
    
    tanggal_mulai_default = get_waktu_wib().date() - timedelta(days=6)
    tanggal_akhir_default = get_waktu_wib().date()
    
    rentang_tanggal = st.date_input(
        "Pilih Tanggal Laporan:", 
        value=(tanggal_mulai_default, tanggal_akhir_default)
    )
    
    if rentang_tanggal != st.session_state.rentang_kustom_last:
        st.session_state.cache_kustom = None
        st.session_state.rentang_kustom_last = rentang_tanggal

    if isinstance(rentang_tanggal, tuple) and len(rentang_tanggal) == 2:
        start_date, end_date = rentang_tanggal
        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
        
        if st.session_state.cache_kustom is None:
            if st.button("UNDUH LAPORAN MINGGUAN / CUSTOM", key="btn_prep_kustom", width="stretch"):
                with st.spinner("Memproses sinkronisasi data rentang kustom..."):
                    st.session_state.cache_kustom = generate_excel_report(start_date=start_date, end_date=end_date)
                    if not st.session_state.cache_kustom:
                        st.toast("Nihil: Tidak ada records data pada rentang tanggal tersebut.", icon="⚠️")
                    st.rerun()
        
        if st.session_state.cache_kustom:
            st.success(f"✅ Dokumen Excel Berhasil Dikompilasi!")
            st.download_button(
                label=f"📥 DOWNLOAD FILE RENTANG ({start_date.strftime('%d %b')} - {end_date.strftime('%d %b %Y')})",
                data=st.session_state.cache_kustom,
                file_name=f"Laporan_Kustom_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                width="stretch",
                type="primary"
            )
    else:
        st.warning("Silakan lengkapi pemilihan tanggal mulai dan tanggal akhir pada kalender untuk membuka panel.")

# ==========================================
# TAB 3: BULANAN
# ==========================================
with tab3:
    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
    col_bln, col_thn = st.columns(2)
    with col_bln:
        list_bulan = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        bln_pilih = st.selectbox("Pilih Bulan:", list_bulan, index=get_waktu_wib().month - 1)
    with col_thn:
        thn_pilih = st.number_input("Pilih Tahun:", min_value=2024, max_value=2030, value=get_waktu_wib().year)
    
    current_periode = f"{bln_pilih}_{thn_pilih}"
    if current_periode != st.session_state.periode_bulanan_last:
        st.session_state.cache_bulanan = None
        st.session_state.periode_bulanan_last = current_periode

    st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)

    if st.session_state.cache_bulanan is None:
        if st.button("UNDUH LAPORAN BULANAN", key="btn_prep_bulan", width="stretch"):
            with st.spinner(f"Mengompilasi data skala besar untuk periode {bln_pilih} {thn_pilih}..."):
                st.session_state.cache_bulanan = generate_excel_report(bulan_filter=bln_pilih, tahun_filter=str(thn_pilih))
                if not st.session_state.cache_bulanan:
                    st.toast(f"Nihil: Tidak ada records data pada periode {bln_pilih} {thn_pilih}.", icon="⚠️")
                st.rerun()
                
    if st.session_state.cache_bulanan:
        st.success(f"✅ Dokumen Excel Berhasil Dikompilasi!")
        st.download_button(
            label=f"📥 DOWNLOAD FILE BULANAN ({bln_pilih} {thn_pilih})",
            data=st.session_state.cache_bulanan,
            file_name=f"Laporan_Bulanan_{bln_pilih}_{thn_pilih}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            width="stretch",
            type="primary"
        )
