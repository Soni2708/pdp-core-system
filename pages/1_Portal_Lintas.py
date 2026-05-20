import streamlit as st
import uuid
import base64

from components.ui_styles import apply_global_cyberpunk_theme, render_cyberpunk_header
from components.navbar import render_navbar
from db_utils import safe_append_reguler, get_waktu_wib, fetch_mapped_data
from services.jadwal_service import get_semua_rute, get_jadwal_dinamis
from core.logger import setup_logger
from core.auth import require_auth

log = setup_logger("PORTAL_AWAL")

st.set_page_config(page_title="PORTAL LINTAS", page_icon="🚐", layout="centered")
apply_global_cyberpunk_theme()
require_auth(module_name="portal", secret_dict_name="users_portal")
render_navbar("portal")

# ========== LOGO ==========
try:
    with open("assets/logo.png", "rb") as img_file:
        img_b64 = base64.b64encode(img_file.read()).decode()
    st.markdown(f"""
        <div style='display: flex; justify-content: center; align-items: center; margin-bottom: 15px; width: 100%; padding-top: 10px;'>
            <img src='data:image/png;base64,{img_b64}' style='max-width: 140px; height: auto; object-fit: contain; filter: drop-shadow(0px 4px 6px rgba(0,0,0,0.1));'>
        </div>
    """, unsafe_allow_html=True)
except FileNotFoundError:
    pass

# ========== HEADER ==========
render_cyberpunk_header("PORTAL KEBERANGKATAN", "Sistem Integrasi Feeder PDP", "var(--accent-red)")
st.divider()

# ========== INIT STATE ==========
if 'kunci_reset' not in st.session_state: 
    st.session_state.kunci_reset = 0

if 'pesan_sukses' not in st.session_state: 
    st.session_state.pesan_sukses = None

if st.session_state.pesan_sukses:
    st.toast(st.session_state.pesan_sukses, icon="🚀")
    st.session_state.pesan_sukses = None 

# ==========================================
# 🛑 MODAL DIALOG KONFIRMASI
# ==========================================
@st.dialog("🚀 Konfirmasi Keberangkatan", width="small")
def show_confirm_dialog(data_konfirmasi):
    st.markdown("""
        <style>
        div[data-testid="stDialog"] div[role="dialog"] { max-height: 85vh; }
        div[data-testid="stDialog"] .stMarkdown { margin-bottom: 0px; }
        div[data-testid="stDialog"] hr { margin: 8px 0px; }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
        <div style="display: flex; justify-content: space-between; margin-bottom: 12px; gap: 10px;">
            <div style="flex: 1;">
                <span style="color: var(--text-muted); font-size: 11px;">📍 RUTE</span><br>
                <span style="font-weight: 600; font-size: 13px;">{data_konfirmasi['rute']}</span>
            </div>
            <div style="flex: 1;">
                <span style="color: var(--text-muted); font-size: 11px;">🕒 JADWAL</span><br>
                <span style="font-weight: 600; font-size: 13px;">{data_konfirmasi['jadwal']}</span>
            </div>
        </div>
        <div style="display: flex; justify-content: space-between; margin-bottom: 12px; gap: 10px;">
            <div style="flex: 1;">
                <span style="color: var(--text-muted); font-size: 11px;">👤 DRIVER</span><br>
                <span style="font-weight: 600; font-size: 13px;">{data_konfirmasi['driver']}</span>
            </div>
            <div style="flex: 1;">
                <span style="color: var(--text-muted); font-size: 11px;">🚖 NOPOL</span><br>
                <span style="font-weight: 600; font-size: 13px;">{data_konfirmasi['nopol']}</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<hr style='margin: 8px 0px;'>", unsafe_allow_html=True)
    
    st.markdown(f"""
        <div style="display: flex; justify-content: space-between; gap: 8px; margin-bottom: 12px;">
            <div style="flex: 1; text-align: center; background: var(--expander-bg); padding: 6px 4px; border-radius: 6px;">
                <span style="color: var(--text-muted); font-size: 10px;">MIM / BB</span><br>
                <span style="font-weight: 700; font-size: 18px; color: var(--accent-cyan);">{data_konfirmasi['pax_mim']}</span>
            </div>
            <div style="flex: 1; text-align: center; background: var(--expander-bg); padding: 6px 4px; border-radius: 6px;">
                <span style="color: var(--text-muted); font-size: 10px;">KOPO</span><br>
                <span style="font-weight: 700; font-size: 18px; color: var(--accent-cyan);">{data_konfirmasi['pax_kopo']}</span>
            </div>
            <div style="flex: 1; text-align: center; background: var(--expander-bg); padding: 6px 4px; border-radius: 6px;">
                <span style="color: var(--text-muted); font-size: 10px;">JATINANGOR</span><br>
                <span style="font-weight: 700; font-size: 18px; color: var(--accent-cyan);">{data_konfirmasi['pax_jtn']}</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    total_pax = data_konfirmasi['pax_mim'] + data_konfirmasi['pax_kopo'] + data_konfirmasi['pax_jtn']
    if total_pax == 0:
        st.markdown("<p style='color: var(--accent-yellow); font-size: 12px; margin: 4px 0px; text-align: center;'>ℹ️ Unit kosong</p>", unsafe_allow_html=True)
    
    st.markdown("<hr style='margin: 8px 0px;'>", unsafe_allow_html=True)
    st.markdown("<p style='color: var(--accent-red); font-size: 12px; margin: 4px 0px 12px 0px; text-align: center;'>⚠️ Data tidak dapat diubah setelah dikirim!</p>", unsafe_allow_html=True)
    
    col_yes, col_no = st.columns(2)
    with col_yes:
        if st.button("✅ Kirim", type="primary", use_container_width=True):
            with st.spinner("Transmisi ke database..."):
                waktu_wib = get_waktu_wib().strftime("%d-%b-%Y %H:%M:%S")
                trip_id = "TRP-" + uuid.uuid4().hex[:8].upper()
                
                payload_data = {
                    "timestamp": waktu_wib,
                    "rute": data_konfirmasi["rute"],
                    "jadwal": data_konfirmasi["jadwal"],
                    "driver_reguler": data_konfirmasi["driver"],
                    "nopol": data_konfirmasi["nopol"],
                    "pax_mim_bbt": int(data_konfirmasi["pax_mim"]),
                    "pax_kopo": int(data_konfirmasi["pax_kopo"]),
                    "pax_jtn": int(data_konfirmasi["pax_jtn"]),
                    "status": "IN TRANSIT",
                    "trip_id": trip_id
                }
                
                sukses, pesan = safe_append_reguler(payload_data)
                petugas_sekarang = st.session_state.get('petugas_portal', 'Unknown')
                
                if sukses:
                    log.info(f"TRANSMIT: {petugas_sekarang} - {data_konfirmasi['driver']} ({data_konfirmasi['nopol']}) rute {data_konfirmasi['rute']} jam {data_konfirmasi['jadwal']}")
                    
                    fetch_mapped_data.clear()
                    st.session_state.kunci_reset += 1
                    st.session_state.pesan_sukses = f"{data_konfirmasi['nopol']} - {data_konfirmasi['rute']} Diberangkatkan"
                    st.rerun() 
                else:
                    log.error(f"TRANSMIT GAGAL: {petugas_sekarang} - {data_konfirmasi['nopol']}. Error: {pesan}")
                    st.error(f"❌ Gagal mengirim data: {pesan}")

    with col_no:
        if st.button("❌ Batal", use_container_width=True):
            st.rerun()

# ==========================================
# 📋 FORM UTAMA (DATA OPERASIONAL)
# ==========================================
with st.container(border=True):
    st.markdown("<h4 style='color:var(--accent-cyan); font-family:\"Rajdhani\", sans-serif; font-size:16px; margin-top:0; margin-bottom:15px; letter-spacing:1px;'>DATA OPERASIONAL</h4>", unsafe_allow_html=True)
    
    list_rute_pilihan = get_semua_rute()
    col1, col2 = st.columns(2)
    with col1:
        pilihan_rute = st.selectbox("📍 Outlet / Rute", options=list_rute_pilihan, key=f"rute_{st.session_state.kunci_reset}")
    with col2:
        opsi_jadwal = get_jadwal_dinamis(pilihan_rute) if pilihan_rute != "-- Pilih Rute --" else ["-- Pilih Rute Dulu --"]
        pilihan_jadwal = st.selectbox("🕒 Jadwal Keberangkatan", options=opsi_jadwal, key=f"jadwal_{st.session_state.kunci_reset}")
    
    with st.expander("📥 Jadwal tidak ada? Klik untuk jadwal Extra"):
        pakai_jadwal_extra = st.checkbox("Gunakan Jadwal Extra", key=f"cek_extra_{st.session_state.kunci_reset}")
        jam_extra = st.time_input("Pilih Jam Keberangkatan", disabled=not pakai_jadwal_extra, key=f"jam_extra_{st.session_state.kunci_reset}")
    
    col_drv, col_npl = st.columns(2)
    with col_drv:
        nama_driver = st.text_input("👤 Nama Driver", placeholder="Ketik nama driver...", max_chars=50, key=f"driver_{st.session_state.kunci_reset}").upper()
    with col_npl:
        nopol_reguler = st.text_input("🚖 Nomor Polisi", placeholder="Contoh: D 1234 ABC", max_chars=15, key=f"nopol_{st.session_state.kunci_reset}").upper()

st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)

# ========== PAX TRANSIT ==========
with st.container(border=True):
    st.markdown("<h4 style='color:var(--accent-yellow); font-family:\"Rajdhani\", sans-serif; font-size:16px; margin-top:0; margin-bottom:15px; letter-spacing:1px;'>JUMLAH PENUMPANG TRANSIT</h4>", unsafe_allow_html=True)
    
    col_mim, col_kopo, col_jtn = st.columns(3)
    with col_mim: 
        pax_mim = st.number_input("MIM / BUAH BATU", min_value=0, step=1, key=f"mim_{st.session_state.kunci_reset}")
    with col_kopo: 
        pax_kopo = st.number_input("KOPO", min_value=0, step=1, key=f"kopo_{st.session_state.kunci_reset}")
    with col_jtn: 
        pax_jtn = st.number_input("JATINANGOR", min_value=0, step=1, key=f"jtn_{st.session_state.kunci_reset}")

st.divider()

# ==========================================
# 🛡️ ENGINE VALIDASI (BUG FIXED)
# ==========================================
jadwal_final = jam_extra.strftime("%H:%M") if pakai_jadwal_extra else pilihan_jadwal
tombol_terkunci = False

if pilihan_rute == "-- Pilih Rute --":
    tombol_terkunci = True
    st.warning("⚠️ Pilih rute terlebih dahulu")
elif not nama_driver.strip():
    tombol_terkunci = True
    st.warning("⚠️ Masukkan nama driver")
elif not nopol_reguler.strip():
    tombol_terkunci = True
    st.warning("⚠️ Masukkan nomor polisi")
# 🚀 ARCHITECT FIX: Memblokir SEMUA string yang berawalan "--" sebagai jadwal tidak valid
elif not pakai_jadwal_extra and pilihan_jadwal.startswith("--"):
    tombol_terkunci = True
    st.warning("⚠️ Jadwal reguler tidak tersedia/valid. Silakan tunggu jadwal berikutnya atau gunakan Jadwal Extra.")

if pakai_jadwal_extra:
    waktu_sekarang = get_waktu_wib()
    jam_extra_real = waktu_sekarang.replace(hour=jam_extra.hour, minute=jam_extra.minute, second=0, microsecond=0)
    selisih_menit = (jam_extra_real - waktu_sekarang).total_seconds() / 60
    if selisih_menit > 60:
        tombol_terkunci = True
        st.error("⛔ Jadwal extra tidak boleh lebih dari 1 jam dari sekarang!")
    elif selisih_menit < -1440: 
        pass
    elif selisih_menit < 0:
        tombol_terkunci = True
        st.error("⛔ Jadwal extra tidak boleh kurang dari waktu sekarang!")

if not tombol_terkunci and pax_mim == 0 and pax_kopo == 0 and pax_jtn == 0:
    st.info("ℹ️ Armada kosong (0 penumpang) diberangkatkan.")

# ==========================================
# 🚀 TOMBOL TRANSMIT UTAMA
# ==========================================
st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
col_left, col_btn, col_right = st.columns([1, 2, 1])

with col_btn:
    if st.button("TRANSMIT DATA", disabled=tombol_terkunci, type="primary", use_container_width=True):
        data_siap_kirim = {
            "rute": pilihan_rute,
            "jadwal": jadwal_final,
            "driver": nama_driver.strip(),
            "nopol": nopol_reguler.strip(),
            "pax_mim": pax_mim,
            "pax_kopo": pax_kopo,
            "pax_jtn": pax_jtn
        }
        show_confirm_dialog(data_siap_kirim)
