import streamlit as st
import base64
from datetime import datetime

# Menggunakan arsitektur tema Neo-Tokyo yang baru
from components.ui_styles import apply_neo_tokyo_corporate, render_neo_tokyo_header
from components.navbar import render_navbar
from core.auth import require_auth
from db_utils import get_waktu_wib, fetch_mapped_data, safe_update_by_uuid
from core.logger import setup_logger

log = setup_logger("RADAR_KM72")

st.set_page_config(page_title="CHECKPOINT KM72", layout="wide")
apply_neo_tokyo_corporate()
require_auth(module_name="km72", secret_dict_name="users_km72")
render_navbar("km72")

# ========== LOGO LINTAS ==========
try:
    with open("assets/logo.png", "rb") as img_file:
        img_b64 = base64.b64encode(img_file.read()).decode()
    st.markdown(f"""
        <div style='display: flex; justify-content: flex-start; align-items: center; margin-bottom: 5px; width: 100%; padding-top: 10px;'>
            <img src='data:image/png;base64,{img_b64}' style='max-width: 140px; height: auto; object-fit: contain; filter: drop-shadow(0 0 10px rgba(255,255,255,0.1));'>
        </div>
    """, unsafe_allow_html=True)
except FileNotFoundError:
    pass

# ==========================================
# 🛑 MODAL DIALOG KONFIRMASI CHECKOUT (NEO-TOKYO UI)
# ==========================================
@st.dialog("KONFIRMASI CHECKOUT KM72", width="small")
def confirm_checkout_dialog(unit):
    st.markdown(f"<div class='nt-nopol' style='text-align: center; font-size: 28px;'>{unit['nopol']}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='nt-meta' style='text-align: center; margin-bottom: 20px;'>DRIVER: {unit['driver']}</div>", unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        st.caption("RUTE")
        st.write(f"**{unit['rute']}**")
    with c2:
        st.caption("JADWAL")
        st.write(f"**{unit['jadwal']}**")
        
    st.warning("TINDAKAN INI AKAN MENCATAT JAM KELUAR ARMADA DI CHECKPOINT KM72 SECARA PERMANEN.")
    
    st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
    col_yes, col_no = st.columns(2)
    with col_yes:
        if 'sedang_checkout' not in st.session_state:
            st.session_state.sedang_checkout = False
            
        if st.button("CHECKOUT SEKARANG", type="primary", use_container_width=True, disabled=st.session_state.sedang_checkout):
            st.session_state.sedang_checkout = True
            with st.spinner("Transmisi..."):
                waktu_wib = get_waktu_wib().strftime("%H:%M")
                sukses, pesan = safe_update_by_uuid(unit['trip_id'], {"jam_keluar_km72": waktu_wib})
                
                if sukses:
                    petugas = st.session_state.get('petugas_km72', 'Unknown')
                    log.info(f"CHECKOUT KM72: {unit['nopol']} oleh {petugas} ({waktu_wib}).")
                    st.toast(f"{unit['nopol']} Berhasil Checkout")
                    fetch_mapped_data.clear()
                    st.session_state.sedang_checkout = False
                    st.rerun()
                else:
                    log.error(f"ERROR KM72: Gagal checkout {unit['nopol']}. Alasan: {pesan}")
                    st.error(f"TRANSMISI GAGAL: {pesan}")
                    st.session_state.sedang_checkout = False
    with col_no:
        if st.button("BATAL", use_container_width=True):
            st.rerun()

# ==========================================
# 🎨 UI HEADER STATIC (NEO-TOKYO)
# ==========================================
col_judul, col_sync = st.columns([4, 1], vertical_alignment="bottom")
with col_judul:
    render_neo_tokyo_header(
        title="CHECKPOINT KM72", 
        subtitle=f"SISTEM PEMANTAUAN RADAR | USER: {st.session_state.get('petugas_km72', 'UNKNOWN')}", 
        accent="var(--nt-cyan)",
        align="left"
    )
with col_sync:
    st.markdown("<div style='margin-bottom: 24px;'></div>", unsafe_allow_html=True)
    if st.button("REFRESH", use_container_width=True): 
        fetch_mapped_data.clear() 
        st.rerun() 

# ==========================================
# ⚡ STREAMLIT FRAGMENT (Auto Radar Engine)
# ==========================================
@st.fragment(run_every=180)
def radar_dashboard():
    semua_data = fetch_mapped_data()
    armada_aktif = []

    if semua_data:
        for row in semua_data:
            status = str(row.get('status', '')).strip().upper()
            jam_72 = str(row.get('jam_72', '')) 
            
            if status == "IN TRANSIT" and not jam_72:
                armada_aktif.append({
                    "nopol": str(row.get('nopol', '')), 
                    "rute": str(row.get('rute', '')), 
                    "jadwal": str(row.get('jadwal', '')), 
                    "driver": str(row.get('driver', '')), 
                    "trip_id": str(row.get('trip_id', ''))
                })

    armada_aktif.sort(key=lambda x: x['jadwal'])

    # --- TACTICAL HUD BAR ---
    st.metric(label="UNIT DALAM PERJALANAN MENUJU KM72", value=f"{len(armada_aktif)} UNIT", delta="SISTEM AKTIF", delta_color="normal")
    st.markdown("<hr style='margin: 15px 0 25px 0; border-color: var(--nt-border);'>", unsafe_allow_html=True)

    # --- CARD RENDER VEHICLE (Zero Inline CSS) ---
    if not armada_aktif:
        st.info("TIDAK ADA UNIT MENUJU KM72")
    else:
        cols = st.columns(3)
        for i, unit in enumerate(armada_aktif):
            with cols[i % 3]:
                # Glassmorphism container otomatis ter-apply dari CSS global
                with st.container(border=True):
                    st.markdown(f"<div class='nt-nopol'>{unit['nopol']}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='nt-meta' style='margin-top: 4px; color: var(--nt-cyan);'>{unit['rute']} | JAM: {unit['jadwal']}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='nt-meta' style='margin-bottom: 12px;'>DRIVER: {unit['driver'][:12]}</div>", unsafe_allow_html=True)
                    
                    if st.button("CHECKOUT", key=f"btn_{unit['trip_id']}", use_container_width=True):
                        confirm_checkout_dialog(unit)

radar_dashboard()
