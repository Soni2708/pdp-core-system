import streamlit as st
import base64
from datetime import datetime
import pytz

# Menggunakan arsitektur tema Neo-Tokyo yang baru
from components.ui_styles import apply_neo_tokyo_corporate
from components.navbar import render_navbar

# ==========================================
# ⚙️ KONFIGURASI AWAL
# ==========================================
st.set_page_config(page_title="TRANSIT COMMAND CENTER", page_icon="🌐", layout="centered")
apply_neo_tokyo_corporate()
render_navbar("home")

# ==========================================
# 🎨 HEADER & LOGO (NEO-TOKYO CORPORATE)
# ==========================================
st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

try:
    with open("assets/logo.png", "rb") as img_file:
        img_b64 = base64.b64encode(img_file.read()).decode()
    st.markdown(f"""
        <div style='display: flex; justify-content: center; align-items: center; margin-bottom: 25px; width: 100%;'>
            <img src='data:image/png;base64,{img_b64}' style='max-width: 180px; height: auto; filter: drop-shadow(0 0 10px rgba(255,255,255,0.1));'>
        </div>
    """, unsafe_allow_html=True)
except FileNotFoundError:
    pass

st.markdown("""
    <div style='text-align: center; margin-bottom: 30px;'>
        <h1 style='color: var(--nt-text-primary); font-size: 32px; font-weight: 800; letter-spacing: 2px; margin: 0; text-shadow: 0 2px 10px rgba(0,0,0,0.5);'>
            TRANSIT HUB CORE
        </h1>
        <p style='color: var(--nt-cyan); font-size: 13px; font-weight: 600; letter-spacing: 3px; margin-top: 5px; text-transform: uppercase;'>
            Sistem Operasional Feeder
        </p>
    </div>
""", unsafe_allow_html=True)

# ==========================================
# 🟢 SYSTEM HEALTH DASHBOARD 
# ==========================================
waktu_wib = datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%d %b %Y - %H:%M WIB")

st.markdown(f"""
    <div style='background: var(--nt-bg-sec); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border: 1px solid var(--nt-border); border-radius: 8px; padding: 16px 24px; margin-bottom: 35px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); display: flex; justify-content: space-between; align-items: center;'>
        <div>
            <span style='font-size: 11px; color: var(--nt-text-muted); font-weight: 600; letter-spacing: 1.5px; text-transform: uppercase;'>STATUS JARINGAN</span><br>
            <span style='font-size: 14px; font-weight: 800; color: var(--nt-success); text-shadow: 0 0 8px rgba(0, 230, 118, 0.4);'>● SECURE CONNECTION</span>
        </div>
        <div style='text-align: right;'>
            <span style='font-size: 11px; color: var(--nt-text-muted); font-weight: 600; letter-spacing: 1.5px; text-transform: uppercase;'>WAKTU SERVER (WIB)</span><br>
            <span style='font-size: 14px; font-weight: 700; color: var(--nt-text-primary);'>{waktu_wib}</span>
        </div>
    </div>
""", unsafe_allow_html=True)

st.divider()

# ==========================================
# 🚀 MODUL OPERASIONAL (ZERO-ICON ARCHITECTURE)
# ==========================================
st.markdown("<h3 style='text-align: center; color: var(--nt-text-muted); font-weight: 600; margin-bottom: 25px; font-size: 12px; text-transform: uppercase; letter-spacing: 2px;'>| PILIH MODUL OPERASIONAL |</h3>", unsafe_allow_html=True)

c1, c2 = st.columns(2, gap="large")

with c1:
    with st.container(border=True):
        st.markdown("""
        <div style="padding: 10px 5px; text-align: center;">
            <div style="width: 30px; height: 3px; background-color: var(--nt-cyan); margin: 0 auto 15px auto; border-radius: 2px; box-shadow: 0 0 8px var(--nt-cyan-glow);"></div>
            <h4 style='color: var(--nt-text-primary); margin:0 0 15px 0; font-size:15px; font-weight: 700; letter-spacing: 1.5px;'>PORTAL LINTAS</h4>
        </div>
        """, unsafe_allow_html=True)
        if st.button("BUKA MODUL", key="btn_portal", use_container_width=True, type="primary"):
            st.switch_page("pages/1_Portal_Lintas.py")

    st.markdown("<div style='margin-bottom:15px;'></div>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("""
        <div style="padding: 10px 5px; text-align: center;">
            <div style="width: 30px; height: 3px; background-color: var(--nt-violet); margin: 0 auto 15px auto; border-radius: 2px; box-shadow: 0 0 8px rgba(157, 78, 221, 0.3);"></div>
            <h4 style='color: var(--nt-text-primary); margin:0 0 15px 0; font-size:15px; font-weight: 700; letter-spacing: 1.5px;'>PASTEUR DROP POINT</h4>
        </div>
        """, unsafe_allow_html=True)
        if st.button("BUKA MODUL", key="btn_pdp", use_container_width=True, type="primary"):
            st.switch_page("pages/3_Pasteur_Drop_Point.py")

with c2:
    with st.container(border=True):
        st.markdown("""
        <div style="padding: 10px 5px; text-align: center;">
            <div style="width: 30px; height: 3px; background-color: var(--nt-cyan); margin: 0 auto 15px auto; border-radius: 2px; box-shadow: 0 0 8px var(--nt-cyan-glow);"></div>
            <h4 style='color: var(--nt-text-primary); margin:0 0 15px 0; font-size:15px; font-weight: 700; letter-spacing: 1.5px;'>CHECKPOINT KM72</h4>
        </div>
        """, unsafe_allow_html=True)
        if st.button("BUKA MODUL", key="btn_km72", use_container_width=True, type="primary"):
            st.switch_page("pages/2_Checkpoint_KM72.py")

    st.markdown("<div style='margin-bottom:15px;'></div>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("""
        <div style="padding: 10px 5px; text-align: center;">
            <div style="width: 30px; height: 3px; background-color: var(--nt-text-muted); margin: 0 auto 15px auto; border-radius: 2px;"></div>
            <h4 style='color: var(--nt-text-primary); margin:0 0 15px 0; font-size:15px; font-weight: 700; letter-spacing: 1.5px;'>LAPORAN</h4>
        </div>
        """, unsafe_allow_html=True)
        if st.button("BUKA MODUL", key="btn_laporan", use_container_width=True, type="primary"):
            st.switch_page("pages/4_Laporan.py")

# Footer
st.markdown("<hr style='margin-top: 40px;'>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: var(--nt-text-muted); font-size: 11px; font-weight: 600; letter-spacing: 2px;'>© 2026 LINTAS SHUTTLE. SYSTEM ARCHITECTURE BY SONI ABBASY.</p>", unsafe_allow_html=True)
