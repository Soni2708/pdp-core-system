import streamlit as st
from components.ui_styles import apply_global_cyberpunk_theme, render_cyberpunk_header

# Konfigurasi Paling Awal
st.set_page_config(page_title="PDP Mobility Dashboard", page_icon="📡", layout="centered")

# Panggil fungsi CSS global
apply_global_cyberpunk_theme()

# Layout Logo & Header
col1, col2, col3 = st.columns([2, 1, 2])
with col2:
    try:
        st.image("assets/logo.png", width="stretch") 
    except FileNotFoundError:
        pass

render_cyberpunk_header("TRANSIT HUB CORE SYSTEM", "PDP Mobility Dashboard - By : Soni Abbasy", "#ff0055")

st.divider()

# ==========================================
# 🚀 SHORTCUT MENU (QUICK ACCESS)
# ==========================================
st.markdown("<h3 style='text-align: center; color: #00d2d3; margin-bottom: 20px;'>QUICK ACCESS MENU</h3>", unsafe_allow_html=True)

# Bikin grid 2 kolom
c1, c2 = st.columns(2)

with c1:
    if st.button("🚐 1. PORTAL LINTAS", use_container_width=True):
        st.switch_page("pages/1_Portal_Lintas.py")
        
    if st.button("📍 3. PASTEUR DROP POINT", use_container_width=True):
        st.switch_page("pages/3_Pasteur_Drop_Point.py")

with c2:
    if st.button("📡 2. CHECKPOINT KM72", use_container_width=True):
        st.switch_page("pages/2_Checkpoint_KM72.py")
        
    # Catatan: Sesuaikan nama file "4_Laporan..." di bawah ini dengan nama file asli lu di dalam folder pages/
    if st.button("📊 4. LAPORAN", use_container_width=True):
        try:
            st.switch_page("pages/4_Laporan_Manajemen.py")
        except:
            st.switch_page("pages/4_Laporan.py") # Antisipasi kalau nama file lu pakai yang versi pendek
