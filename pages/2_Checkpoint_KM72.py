import streamlit as st
import base64
from datetime import datetime

from components.ui_styles import apply_global_cyberpunk_theme
from components.navbar import render_navbar
from core.auth import require_auth
from db_utils import get_waktu_wib, fetch_mapped_data, safe_update_by_uuid
from core.logger import setup_logger

log = setup_logger("RADAR_KM72")

st.set_page_config(page_title="CHECKPOINT KM72", page_icon="📡", layout="wide")
apply_global_cyberpunk_theme()
require_auth(module_name="km72", secret_dict_name="users_km72")
render_navbar("km72")

# ==========================================
# 🛑 MODAL DIALOG KONFIRMASI CHECKOUT
# ==========================================
@st.dialog("📡 Konfirmasi Checkout KM72", width="small")
def confirm_checkout_dialog(unit):
    st.markdown("""
        <style>
        div[data-testid="stDialog"] div[role="dialog"] { max-height: 85vh; }
        div[data-testid="stDialog"] .stMarkdown { margin-bottom: 0px; }
        div[data-testid="stDialog"] hr { margin: 8px 0px; }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
        <div style="background-color: var(--bg-surface); padding: 15px; border-radius: 8px; border: 1px solid var(--border-color); box-shadow: var(--shadow-subtle); text-align: center; margin-bottom: 15px;">
            <span style="font-family:'Rajdhani', sans-serif; font-size: 26px; font-weight: 700; color: var(--text-primary); letter-spacing: 1px;">{unit['nopol']}</span><br>
            <span style="color: var(--accent-cyan); font-weight: 700; font-size: 16px;">[ {unit['driver']} ]</span>
        </div>
        <div style="display: flex; justify-content: space-between; margin-bottom: 20px; gap: 10px;">
            <div style="flex: 1; text-align: center; background: var(--expander-bg); padding: 10px; border-radius: 6px; border: 1px solid var(--border-color);">
                <span style="color: var(--text-muted); font-size: 11px; font-weight: bold; letter-spacing: 1px;">📍 RUTE</span><br>
                <span style="font-weight: 700; font-size: 14px; color: var(--text-primary);">{unit['rute']}</span>
            </div>
            <div style="flex: 1; text-align: center; background: var(--expander-bg); padding: 10px; border-radius: 6px; border: 1px solid var(--border-color);">
                <span style="color: var(--text-muted); font-size: 11px; font-weight: bold; letter-spacing: 1px;">🕒 JADWAL</span><br>
                <span style="font-weight: 700; font-size: 14px; color: var(--accent-yellow);">{unit['jadwal']}</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<p style='color: var(--accent-red); font-size: 12px; margin: 4px 0px 12px 0px; text-align: center; font-weight: 600;'>⚠️ Konfirmasi ini akan mencatat jam keluar armada di Checkpoint KM72.</p>", unsafe_allow_html=True)
    
    col_yes, col_no = st.columns(2)
    with col_yes:
        if st.button("✅ YA, CHECKOUT", type="primary", use_container_width=True):
            with st.spinner("Mencatat checkout..."):
                waktu_wib = get_waktu_wib().strftime("%H:%M")
                sukses, pesan = safe_update_by_uuid(unit['trip_id'], {"jam_keluar_km72": waktu_wib})
                
                if sukses:
                    petugas = st.session_state.get('petugas_km72', 'Unknown')
                    log.info(f"CHECKOUT KM72: {unit['nopol']} dicheckout oleh {petugas} ({waktu_wib}).")
                    st.toast(f"✅ {unit['nopol']} Berhasil Checkout", icon="🚐")
                    fetch_mapped_data.clear()
                    st.rerun()
                else:
                    log.error(f"ERROR KM72: Gagal checkout {unit['nopol']}. Alasan: {pesan}")
                    st.error(f"❌ Transmisi Gagal: {pesan}")
    with col_no:
        if st.button("❌ BATAL", use_container_width=True):
            st.rerun()

# ==========================================
# 🎨 UI HEADER STATIC (Dikeluarkan dari Fragment)
# ==========================================
# Dengan meletakkan ini di luar fragment, logo bebas dari clipping container
try:
    with open("assets/logo.png", "rb") as img_file:
        img_b64 = base64.b64encode(img_file.read()).decode()
    st.markdown(f"""
        <div style='display: flex; justify-content: center; align-items: center; margin-bottom: 15px; width: 100%; padding-top: 10px;'>
            <img src='data:image/png;base64,{img_b64}' style='max-width: 140px; height: auto; object-fit: contain; filter: drop-shadow(0px 4px 6px rgba(0,0,0,0.1));'>
        </div>
    """, unsafe_allow_html=True)
except FileNotFoundError:
    st.markdown("<div style='text-align: center; margin-bottom: 20px; font-weight: bold;'>LINTAS SHUTTLE</div>", unsafe_allow_html=True)

col_judul, col_sync = st.columns([4, 1], vertical_alignment="bottom")
with col_judul:
    st.markdown("<h2 style='color: var(--text-primary); font-family: \"Rajdhani\", sans-serif; font-size: 28px; font-weight: 700; margin-top: -10px; margin-bottom: 5px; letter-spacing: 2px; border-bottom: 3px solid var(--accent-yellow); display: inline-block; padding-bottom: 6px;'>CHECKPOINT KM72</h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: left; margin-top:-5px; font-size:12px; font-family:\"Inter\", sans-serif;'><span style='color:var(--text-muted);'>Sistem Pemantauan Checkpoint</span> | <span style='color:var(--accent-cyan); font-weight:bold;'>USER: {st.session_state.get('petugas_km72', '')}</span></p>", unsafe_allow_html=True)
with col_sync:
    if st.button("🔄 Refresh", use_container_width=True): 
        fetch_mapped_data.clear() 
        st.rerun() 

st.divider()

# ==========================================
# ⚡ STREAMLIT FRAGMENT (Live Radar Engine)
# ==========================================
# Fragment kini HANYA berisi data dinamis (Kanban Board)
@st.fragment(run_every=30)
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
    st.markdown(f"""
<div style="background-color: var(--bg-surface); padding: 20px; border-radius: 8px; border: 1px solid var(--border-color); border-left: 6px solid var(--accent-cyan); box-shadow: var(--shadow-subtle); margin-bottom: 24px;">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <span style="font-size: 11px; color: var(--text-muted); font-weight: 700; letter-spacing: 2px; text-transform: uppercase;">unit Dalam Perjalanan</span><br>
            <span style="font-size: 36px; font-weight: 800; color: var(--text-primary); font-family: 'Rajdhani', sans-serif;">{len(armada_aktif)} <span style="font-size: 16px; color: var(--text-muted);">UNIT</span></span>
        </div>
        <div style="text-align: right;">
            <div style="background: rgba(0, 210, 211, 0.1); padding: 6px 14px; border-radius: 4px; border: 1px solid var(--accent-cyan);">
                <span style="color: var(--accent-cyan); font-size: 11px; font-weight: 800; letter-spacing: 1.5px;">SISTEM AKTIF</span>
            </div>
            <div style="margin-top: 6px; font-size: 10px; color: var(--text-muted); letter-spacing: 0.5px; font-weight: 600;">AUTO-REFRESH (30s)</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

    # --- CARD RENDER VEHICLE ---
    if not armada_aktif:
        st.markdown("<div style='background-color: var(--bg-surface); padding: 30px; border: 1px dashed var(--border-color); border-radius:8px; text-align: center; box-shadow: var(--shadow-subtle);'><span style='color:var(--text-muted); font-family:\"Rajdhani\", sans-serif; font-size:20px; letter-spacing:2px;'>[ TIDAK ADA UNIT MENUJU KM72. ]</span></div>", unsafe_allow_html=True)
    else:
        cols = st.columns(3)
        for i, unit in enumerate(armada_aktif):
            with cols[i % 3]:
                # Menggunakan container adaptif
                with st.container(border=True):
                    st.markdown(f"""
                    <div style="line-height: 1.4; text-align: left; padding-bottom: 8px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
                            <span style="font-family:'Rajdhani', sans-serif; font-size: 22px; font-weight: bold; color: var(--text-primary);">{unit['nopol']}</span>
                            <span style="font-size: 14px; font-weight: bold; color: var(--accent-cyan);">[ {unit['driver'][:12]} ]</span>
                        </div>
                        <div style="font-size: 14px; color: var(--text-primary);">
                            {unit['rute']} <br> 
                            <span style="font-size: 13px; color:var(--text-muted); font-weight:600;">JAM:</span> <span style="color:var(--accent-yellow); font-weight:bold;">{unit['jadwal']} WIB</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button("📡 CHECKOUT", key=f"btn_{unit['trip_id']}", use_container_width=True):
                        confirm_checkout_dialog(unit)

radar_dashboard()
