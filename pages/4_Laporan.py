import streamlit as st
from components.ui_styles import apply_global_cyberpunk_theme
from core.auth import require_auth
from db_utils import generate_excel_report, get_waktu_wib
from datetime import datetime, timedelta

st.set_page_config(page_title="Laporan Manajemen", page_icon="📊", layout="centered")
apply_global_cyberpunk_theme()
require_auth(module_name="admin", secret_dict_name="users_admin")

st.markdown("<h2 style='color:#00d2d3; text-align:center;'>📊 EXPORT DATA OPERASIONAL</h2>", unsafe_allow_html=True)
st.divider()

# 📑 URUTAN TAB DIUBAH: HARIAN, MINGGUAN, BULANAN
tab1, tab2, tab3 = st.tabs(["📅 HARIAN", "📆 MINGGUAN / KUSTOM", "🗓️ BULANAN"])

# ==========================================
# TAB 1: HARIAN
# ==========================================
with tab1:
    tgl_pilih = st.date_input("Pilih Tanggal:", get_waktu_wib().date())
    data_harian = generate_excel_report(tanggal_filter=tgl_pilih)
    
    if data_harian:
        st.download_button(
            label=f"📥 DOWNLOAD HARIAN ({tgl_pilih.strftime('%d %b %Y')})",
            data=data_harian,
            file_name=f"Laporan_Harian_{tgl_pilih.strftime('%Y-%m-%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    else:
        st.warning("Tidak ada data untuk tanggal ini.")

# ==========================================
# TAB 2: MINGGUAN / KUSTOM (Sekarang di Tengah)
# ==========================================
with tab2:
    st.info("💡 Klik kalender lalu pilih rentang waktu (Contoh: Klik hari Senin, lalu klik hari Minggu).")
    
    # Bikin kalender yang otomatis milih 7 hari ke belakang
    tanggal_mulai_default = get_waktu_wib().date() - timedelta(days=6)
    tanggal_akhir_default = get_waktu_wib().date()
    
    rentang_tanggal = st.date_input(
        "Pilih Rentang Tanggal:", 
        value=(tanggal_mulai_default, tanggal_akhir_default)
    )
    
    # Cek apakah user sudah mengklik 2 tanggal (awal dan akhir)
    if isinstance(rentang_tanggal, tuple) and len(rentang_tanggal) == 2:
        start_date, end_date = rentang_tanggal
        data_mingguan = generate_excel_report(start_date=start_date, end_date=end_date)
        
        if data_mingguan:
            st.download_button(
                label=f"📥 DOWNLOAD RENTANG ({start_date.strftime('%d %b')} - {end_date.strftime('%d %b %Y')})",
                data=data_mingguan,
                file_name=f"Laporan_Kustom_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        else:
            st.warning(f"Tidak ada data antara {start_date.strftime('%d %b')} sampai {end_date.strftime('%d %b')}.")
    else:
        st.warning("Silakan pilih tanggal mulai dan tanggal akhir pada kalender.")

# ==========================================
# TAB 3: BULANAN (Sekarang di Kanan)
# ==========================================
with tab3:
    col_bln, col_thn = st.columns(2)
    with col_bln:
        list_bulan = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        bln_pilih = st.selectbox("Pilih Bulan:", list_bulan, index=get_waktu_wib().month - 1)
    with col_thn:
        thn_pilih = st.number_input("Pilih Tahun:", min_value=2024, max_value=2030, value=get_waktu_wib().year)
    
    data_bulanan = generate_excel_report(bulan_filter=bln_pilih, tahun_filter=str(thn_pilih))
    
    if data_bulanan:
        st.download_button(
            label=f"📥 DOWNLOAD BULANAN ({bln_pilih} {thn_pilih})",
            data=data_bulanan,
            file_name=f"Laporan_Bulanan_{bln_pilih}_{thn_pilih}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    else:
        st.warning(f"Tidak ada data untuk periode {bln_pilih} {thn_pilih}.")
