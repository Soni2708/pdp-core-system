import streamlit as st
import base64
from datetime import datetime
import pytz

from components.ui_styles import apply_global_cyberpunk_theme
from components.navbar import render_navbar

# ==========================================
# ⚙️ KONFIGURASI AWAL
# ==========================================
st.set_page_config(page_title="TRANSIT COMMAND CENTER", page_icon="🌐", layout="centered")
apply_global_cyberpunk_theme()
render_navbar("home")

# ==========================================
# 🎨 HEADER & LOGO (PREMIUM LAYOUT)
# ==========================================
st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

try:
    with open("assets/logo.png", "rb") as img_file:
        img_b64 = base64.b64encode(img_file.read()).decode()
    st.markdown(f"""
        <div style='display: flex; justify-content: center; align-items: center; margin-bottom: 25px; width: 100%;'>
            <img src='data:image/png;base64,{img_b64}' style='max-width: 180px; height: auto; filter: drop-shadow(0px 8px 16px rgba(0,0,0,0.15));'>
        </div>
    """, unsafe_allow_html=True)
except FileNotFoundError:
    pass

st.markdown("""
    <div style='text-align: center; margin-bottom: 30px;'>
        <h1 style='color: var(--text-primary); font-family: "Rajdhani", sans-serif; font-size: 38px; font-weight: 800; letter-spacing: 3px; margin: 0;'>TRANSIT HUB CORE SYSTEM</h1>
        <p style='color: var(--accent-cyan); font-family: "Inter", sans-serif; font-size: 15px; font-weight: 600; letter-spacing: 1px; margin-top: 5px;'>SISTEM OPERASIONAL FEEDER</p>
    </div>
""", unsafe_allow_html=True)

# ==========================================
# 🟢 SYSTEM HEALTH DASHBOARD (UX ENHANCEMENT)
# ==========================================
waktu_wib = datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%d %b %Y - %H:%M WIB")

st.markdown(f"""
    <div style='background-color: var(--bg-surface); border: 1px solid var(--border-color); border-radius: 8px; padding: 15px 20px; margin-bottom: 35px; box-shadow: var(--shadow-subtle); display: flex; justify-content: space-between; align-items: center;'>
        <div>
            <span style='font-size: 11px; color: var(--text-muted); font-weight: 700; letter-spacing: 1px;'>STATUS JARINGAN</span><br>
            <span style='font-size: 14px; font-weight: 700; color: #10b981;'>🟢 ONLINE SECURE (ENCRYPTED)</span>
        </div>
        <div style='text-align: right;'>
            <span style='font-size: 11px; color: var(--text-muted); font-weight: 700; letter-spacing: 1px;'>WAKTU SERVER (WIB)</span><br>
            <span style='font-size: 14px; font-weight: 700; color: var(--text-primary); font-family: "Rajdhani", sans-serif;'>{waktu_wib}</span>
        </div>
    </div>
""", unsafe_allow_html=True)

st.divider()

# ==========================================
# 🚀 MODUL OPERASIONAL (INTERACTIVE CARDS)
# ==========================================
st.markdown("<h3 style='text-align: center; color: var(--text-primary); font-family: \"Rajdhani\", sans-serif; letter-spacing: 2px; margin-bottom: 25px; font-size: 20px;'>🚦 PILIH MODUL OPERASIONAL</h3>", unsafe_allow_html=True)

c1, c2 = st.columns(2, gap="large")

with c1:
    with st.container(border=True):
        st.markdown("<h4 style='color: var(--text-primary); margin:0; font-family:\"Rajdhani\", sans-serif; font-size:20px;'><span style='font-size: 24px;'>🚐</span> PORTAL LINTAS</h4>", unsafe_allow_html=True)
        st.markdown("<p style='font-size:12px; color:var(--text-muted); line-height:1.4; margin-bottom:15px;'>Modul keberangkatan utama. Input data rute, jadwal, driver, dan manifest penumpang transit secara real-time.</p>", unsafe_allow_html=True)
        if st.button("BUKA PORTAL LINTAS", use_container_width=True, type="primary"):
            st.switch_page("pages/1_Portal_Lintas.py")

    st.markdown("<div style='margin-bottom:15px;'></div>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("<h4 style='color: var(--text-primary); margin:0; font-family:\"Rajdhani\", sans-serif; font-size:20px;'><span style='font-size: 24px;'>📍</span> PASTEUR DROP POINT</h4>", unsafe_allow_html=True)
        st.markdown("<p style='font-size:12px; color:var(--text-muted); line-height:1.4; margin-bottom:15px;'>Modul kendali kedatangan dan eksekusi Dispatch Feeder ke area MIM, Kopo, dan Jatinangor.</p>", unsafe_allow_html=True)
        if st.button("BUKA DASHBOARD PDP", use_container_width=True, type="primary"):
            st.switch_page("pages/3_Pasteur_Drop_Point.py")

with c2:
    with st.container(border=True):
        st.markdown("<h4 style='color: var(--text-primary); margin:0; font-family:\"Rajdhani\", sans-serif; font-size:20px;'><span style='font-size: 24px;'>📡</span> CHECKPOINT KM72</h4>", unsafe_allow_html=True)
        st.markdown("<p style='font-size:12px; color:var(--text-muted); line-height:1.4; margin-bottom:15px;'>Modul radar pemantauan unit in-transit. Catat waktu keluar armada dari Rest Area KM72 secara presisi.</p>", unsafe_allow_html=True)
        if st.button("BUKA RADAR KM72", use_container_width=True, type="primary"):
            st.switch_page("pages/2_Checkpoint_KM72.py")

    st.markdown("<div style='margin-bottom:15px;'></div>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("<h4 style='color: var(--text-primary); margin:0; font-family:\"Rajdhani\", sans-serif; font-size:20px;'><span style='font-size: 24px;'>📊</span> LAPORAN MANAJEMEN</h4>", unsafe_allow_html=True)
        st.markdown("<p style='font-size:12px; color:var(--text-muted); line-height:1.4; margin-bottom:15px;'>Modul ekstraksi data operasional. Unduh rekapitulasi data harian, bulanan, atau custom ke format Excel.</p>", unsafe_allow_html=True)
        if st.button("BUKA LAPORAN", use_container_width=True, type="primary"):
            st.switch_page("pages/4_Laporan.py")

# Footer
st.markdown("<hr style='margin-top: 40px; border-top: 1px solid var(--border-color);'>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: var(--text-muted); font-size: 11px; font-weight: 600; letter-spacing: 1px;'>© 2026 LINTAS SHUTTLE. SYSTEM ARCHITECTURE BY SONI ABBASY.</p>", unsafe_allow_html=True)
