import streamlit as st
import uuid

# IMPORT KOMPONEN UI GLOBAL & MESIN DATABASE
from components.ui_styles import apply_global_cyberpunk_theme, render_cyberpunk_header
from db_utils import safe_append_reguler, get_waktu_wib, fetch_mapped_data

# IMPORT SERVICES BARU
from services.jadwal_service import get_semua_rute, get_jadwal_dinamis

# INJEKSI LOGGER (BLACKBOX)
from core.logger import setup_logger
log = setup_logger("PORTAL_AWAL")

# INJEKSI SISTEM KEAMANAN
from core.auth import require_auth, logout_user

# --- KONFIGURASI HALAMAN (MURNI CENTERED) ---
st.set_page_config(page_title="PORTAL LINTAS", page_icon="🚐", layout="centered")
apply_global_cyberpunk_theme()

# ============================================================
# 🛡️ PASANG GEMBOK KEAMANAN DI SINI
# ============================================================
require_auth(module_name="portal", secret_dict_name="users_portal")

# Tombol Logout diletakkan di Sidebar agar UI tengah tetap rapi
with st.sidebar:
    st.markdown(f"<h3 style='color:#00d2d3; margin-bottom:15px;'>👤 {st.session_state.get('petugas_portal', 'Petugas').upper()}</h3>", unsafe_allow_html=True)
    st.markdown('<div class="btn-logout">', unsafe_allow_html=True)
    if st.button("Logout", use_container_width=True):
        logout_user("portal")
    st.markdown('</div>', unsafe_allow_html=True)

# --- RENDER LOGO & HEADER ---
col1, col2, col3 = st.columns([2, 0.8, 2])
with col2:
    try: 
        st.image("assets/logo.png", use_container_width=True)
    except: 
        pass

render_cyberpunk_header("PORTAL KEBERANGKATAN", "Sistem Integrasi Feeder PDP - Lintas Jabodetabek & Sekitarnya", "#ff0055")
st.divider()

# ============================================================
# INISIALISASI MESIN RESET STATE
# ============================================================
if 'kunci_reset' not in st.session_state: st.session_state.kunci_reset = 0
if 'pesan_sukses' not in st.session_state: st.session_state.pesan_sukses = None

if st.session_state.pesan_sukses:
    st.toast(st.session_state.pesan_sukses, icon="✅")
    st.session_state.pesan_sukses = None 

# ============================================================
# 📋 CARD 1: FORM VALIDASI DATA UTAMA ARMADA
# ============================================================
with st.container(border=True):
    st.markdown("<h4 style='color:#00d2d3; font-family:\"Rajdhani\", sans-serif; font-size:16px; margin-top:0; margin-bottom:15px; letter-spacing:1px;'>📋 DATA OPERASIONAL</h4>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        pilihan_rute = st.selectbox("📍 Pilih Outlet/Rute", options=get_semua_rute(), key=f"rute_{st.session_state.kunci_reset}")

    with col2:
        opsi_jadwal = get_jadwal_dinamis(pilihan_rute) if pilihan_rute != "-- Pilih Rute --" else ["-- Pilih Rute Dulu --"]
        pilihan_jadwal = st.selectbox("🕒 Jadwal Keberangkatan", options=opsi_jadwal, key=f"jadwal_{st.session_state.kunci_reset}")
        
    # Baris Tambahan untuk Jadwal Ekstra didesain lebih ramping
    if pilihan_rute != "-- Pilih Rute --":
        st.markdown("<p style='color:#8b949e; font-size:12px; margin-top:-10px; margin-bottom:10px;'>🔒 <i>Menampilkan jadwal terdekat.</i></p>", unsafe_allow_html=True)
    
    with st.expander("📥 Jadwal tidak ada di daftar? Klik disini"):
        pakai_jadwal_extra = st.checkbox("Gunakan Jadwal Extra", key=f"cek_extra_{st.session_state.kunci_reset}")
        jam_extra = st.time_input("Pilih Jam Keberangkatan", disabled=not pakai_jadwal_extra, key=f"jam_extra_{st.session_state.kunci_reset}")
        if pakai_jadwal_extra: 
            st.caption("✅ Jadwal Extra diaktifkan.")

    # Input Driver & Nopol diletakkan berdampingan secara simetris
    c_drv, c_npl = st.columns(2)
    with c_drv:
        nama_driver = st.text_input("👤 Nama Driver Reguler", placeholder="Ketik nama driver...", key=f"driver_{st.session_state.kunci_reset}").upper()
    with c_npl:
        nopol_reguler = st.text_input("🚖 Nopol Unit", placeholder="Misal: D 1234 ABC", key=f"nopol_{st.session_state.kunci_reset}").upper()

st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)

# ============================================================
# 🧑‍🧑‍🧒‍🧒 CARD 2: FORM INPUT ALOKASI PAX TRANSIT
# ============================================================
with st.container(border=True):
    st.markdown("<h4 style='color:#feca57; font-family:\"Rajdhani\", sans-serif; font-size:16px; margin-top:0; margin-bottom:15px; letter-spacing:1px;'>🧑‍🧑‍🧒‍🧒 JUMLAH PAX TRANSIT</h4>", unsafe_allow_html=True)
    
    col_mim, col_kopo, col_jtn = st.columns(3)
    with col_mim: 
        pax_mim = st.number_input("MIM / BUAH BATU", min_value=0, step=1, key=f"mim_{st.session_state.kunci_reset}")
    with col_kopo: 
        pax_kopo = st.number_input("KOPO", min_value=0, step=1, key=f"kopo_{st.session_state.kunci_reset}")
    with col_jtn: 
        pax_jtn = st.number_input("JATINANGOR", min_value=0, step=1, key=f"jtn_{st.session_state.kunci_reset}")

st.divider()

# ============================================================
# SISTEM VALIDASI LIVE (MURNI & AMAN - JANGAN DISENTUH)
# ============================================================
jadwal_final = jam_extra.strftime("%H:%M") if pakai_jadwal_extra else pilihan_jadwal
tombol_terkunci = False

if pilihan_rute == "-- Pilih Rute --" or not nama_driver.strip() or not nopol_reguler.strip():
    tombol_terkunci = True
if not pakai_jadwal_extra and pilihan_jadwal in ["-- Pilih Rute Dulu --", "-- Pilih Jadwal --", "-- Menunggu Jadwal Berikutnya --"]:
    tombol_terkunci = True

if pakai_jadwal_extra:
    waktu_sekarang = get_waktu_wib()
    jam_extra_real = waktu_sekarang.replace(hour=jam_extra.hour, minute=jam_extra.minute, second=0, microsecond=0)
    if (jam_extra_real - waktu_sekarang).total_seconds() / 60 > 60:
        tombol_terkunci = True
        st.error("⛔ PERINGATAN: Tidak dapat menginput jadwal ekstra lebih dari 1 jam kedepan!")

if tombol_terkunci:
    st.warning("⚠️ PENTING: Nihil transit wajib diinput. Pilih Rute, Jadwal, Nama Driver, dan Nopol.")

# Di dalam pages/1_Portal_Lintas.py (Baris ~110)

# ============================================================
# EKSEKUSI TRANSMISI DATA (ABSOLUTE MAPPING)
# ============================================================
# 💉 NEXUS PRIME SURGICAL PATCH: Centering via Balanced Column Matrix (Proporsi Simetris 1:2:1)
col_space_l, col_transmit, col_space_r = st.columns([1, 2, 1])

with col_transmit:
    if st.button("TRANSMIT DATA KE SISTEM PDP", disabled=tombol_terkunci, type="primary"):
        with st.spinner('Membuka enkripsi jalur data aman Supabase...'):
            waktu_wib = get_waktu_wib().strftime("%d-%b-%Y %H:%M:%S")
            trip_id = "TRP-" + uuid.uuid4().hex[:8].upper()
            
            # Cetak skema array 26 kolom PostgreSQL
            data_baru = [""] * 26
            data_baru[0] = waktu_wib             # Kolom A: Timestamp
            data_baru[1] = pilihan_rute          # Kolom B: Rute
            data_baru[2] = jadwal_final          # Kolom C: Jadwal
            data_baru[3] = nama_driver.strip()   # Kolom D: Driver
            data_baru[4] = nopol_reguler.strip() # Kolom E: Nopol
            data_baru[5] = pax_mim               # Kolom F: Pax MIM
            data_baru[6] = pax_kopo              # Kolom G: Pax Kopo
            data_baru[7] = pax_jtn               # Kolom H: Pax Jatinangor
            data_baru[8] = "IN TRANSIT"          # Kolom I: Status
            data_baru[25] = trip_id              # Kolom Z: UUID (DNA Unik)
            
            sukses, pesan = safe_append_reguler(data_baru)
            petugas_sekarang = st.session_state.get('petugas_portal', 'Unknown')
            
            if sukses:
                log.info(f"TRANSMIT SUKSES: Petugas {petugas_sekarang} mendaftarkan Driver {nama_driver} ({nopol_reguler.strip()}) rute {pilihan_rute} jadwal {jadwal_final}.")
                
                # Pembersih Cache State Masa Lalu
                prefix_sampah = ("rute_", "jadwal_", "driver_", "nopol_", "mim_", "kopo_", "jtn_", "cek_extra_", "jam_extra_")
                for key in list(st.session_state.keys()):
                    if key.startswith(prefix_sampah):
                        del st.session_state[key]

                fetch_mapped_data.clear()
                st.session_state.pesan_sukses = f"Transmit Sukses. Unit {nopol_reguler.strip()} diBerangkatkan!"
                st.session_state.kunci_reset += 1
                st.rerun()
            else:
                log.error(f"TRANSMIT GAGAL: Petugas {petugas_sekarang} gagal mendaftarkan {nopol_reguler.strip()}. Alasan: {pesan}")
                st.toast(f"Transmisi Gagal: {pesan}", icon="⛔")
