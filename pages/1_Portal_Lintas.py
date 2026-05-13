import streamlit as st
import uuid

# IMPORT KOMPONEN UI GLOBAL & MESIN DATABASE
from components.ui_styles import apply_global_cyberpunk_theme, render_cyberpunk_header
from db_utils import safe_append_reguler, get_waktu_wib

# IMPORT SERVICES BARU
from services.jadwal_service import get_semua_rute, get_jadwal_dinamis

# INJEKSI LOGGER
from core.logger import setup_logger
log = setup_logger("PORTAL_AWAL")

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="PORTAL LINTAS", page_icon="🚐", layout="centered")
apply_global_cyberpunk_theme()

# --- RENDER LOGO & HEADER ---
col1, col2, col3 = st.columns([2, 0.8, 2])
with col2:
    try: st.image("assets/logo.png", width="stretch")
    except: pass

render_cyberpunk_header("PORTAL KEBERANGKATAN REGULER", "Sistem Integrasi Feeder PDP - Lintas Jabodetabek dan Sekitarnya", "#ff0055")
st.divider()

# ============================================================
# INISIALISASI MESIN RESET STATE
# ============================================================
if 'kunci_reset' not in st.session_state: st.session_state.kunci_reset = 0
if 'pesan_sukses' not in st.session_state: st.session_state.pesan_sukses = None

if st.session_state.pesan_sukses:
    st.success(st.session_state.pesan_sukses)
    st.balloons()
    st.session_state.pesan_sukses = None 

# ============================================================
# FORM INPUT & LOGIKA UI
# ============================================================
col1, col2 = st.columns(2)
with col1:
    pilihan_rute = st.selectbox("📍 Pilih Outlet/Rute", options=get_semua_rute(), key=f"rute_{st.session_state.kunci_reset}")

with col2:
    opsi_jadwal = get_jadwal_dinamis(pilihan_rute) if pilihan_rute != "-- Pilih Rute --" else ["-- Pilih Rute Dulu --"]
            
    pilihan_jadwal = st.selectbox("🕒 Jadwal Operasional", options=opsi_jadwal, key=f"jadwal_{st.session_state.kunci_reset}")
    
    if pilihan_rute != "-- Pilih Rute --":
        st.caption("🔒 *Hanya menampilkan jadwal shift terdekat.*")
    
    with st.expander("Jadwal tidak ada di daftar? Klik di sini"):
        pakai_jadwal_extra = st.checkbox("Gunakan Jadwal Extra", key=f"cek_extra_{st.session_state.kunci_reset}")
        jam_extra = st.time_input("Pilih Jam Keberangkatan", disabled=not pakai_jadwal_extra, key=f"jam_extra_{st.session_state.kunci_reset}")
        if pakai_jadwal_extra: st.caption("✅ Jadwal Extra diaktifkan.")

nama_driver = st.text_input("👤 Nama Driver Reguler", placeholder="Ketik nama driver...", key=f"driver_{st.session_state.kunci_reset}").upper()
nopol_reguler = st.text_input("🚗 Nopol Reguler", placeholder="Misal: D 1234 ABC", key=f"nopol_{st.session_state.kunci_reset}").upper()

st.markdown("<p style='color:#ff0055; font-weight:700; margin-top:20px; font-size:14px;'>🧑‍🧑‍🧒‍🧒 JUMLAH PAX TRANSIT</p>", unsafe_allow_html=True)
col_mim, col_kopo, col_jtn = st.columns(3)
with col_mim: pax_mim = st.number_input("MIM/BUAH BATU", min_value=0, step=1, key=f"mim_{st.session_state.kunci_reset}")
with col_kopo: pax_kopo = st.number_input("KOPO", min_value=0, step=1, key=f"kopo_{st.session_state.kunci_reset}")
with col_jtn: pax_jtn = st.number_input("JATINANGOR", min_value=0, step=1, key=f"jtn_{st.session_state.kunci_reset}")

st.divider()

# ============================================================
# SISTEM VALIDASI LIVE
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
        st.error("⛔ PELANGGARAN: Tidak dapat menginput jadwal ekstra lebih dari 1 jam di muka!")

if tombol_terkunci:
    st.warning("⚠️ Nihil Transit tetap input. Lengkapi Data: Rute, Jadwal, Nama Driver, dan Nopol wajib diisi!")

# ============================================================
# EKSEKUSI TRANSMISI DATA (ABSOLUTE MAPPING)
# ============================================================
if st.button("TRANSMIT DATA KE SISTEM PDP", disabled=tombol_terkunci):
    with st.spinner('Mengirim koordinat data melalui jalur aman...'):
        waktu_wib = get_waktu_wib().strftime("%d-%b-%Y %H:%M:%S")
        trip_id = "TRP-" + uuid.uuid4().hex[:8].upper()
        
        # 1. Buat cetakan array kosong sebanyak 26 kolom (A sampai Z)
        data_baru = [""] * 26
        
        # 2. Isi data persis di index kolomnya (A=0, B=1, ... Z=25)
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
        
        if sukses:
            # ✅ LOGGING SUKSES
            log.info(f"TRANSMIT SUKSES: Driver {nama_driver} ({nopol_reguler.strip()}) rute {pilihan_rute} berangkat jam {jadwal_final}.")
            
            st.cache_data.clear()
            st.session_state.pesan_sukses = f"✅ TRANSMISI SUKSES! Armada {nopol_reguler.strip()} berangkat jam {jadwal_final}."
            st.session_state.kunci_reset += 1
            st.rerun()
        else:
            # ❌ LOGGING ERROR
            log.error(f"TRANSMIT GAGAL: Driver {nama_driver} ({nopol_reguler.strip()}). Alasan: {pesan}")
            st.error(f"⛔ Transmisi Gagal: {pesan}")