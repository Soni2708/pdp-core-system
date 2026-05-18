import streamlit as st
import base64
from components.ui_styles import apply_global_cyberpunk_theme, render_cyberpunk_header

# Konfigurasi Paling Awal
st.set_page_config(page_title="PDP Mobility Dashboard", page_icon="📡", layout="centered")

# Panggil fungsi CSS global (Mendukung Adaptive Light/Dark Mode)
apply_global_cyberpunk_theme()

# ==========================================
# 🚀 ADAPTIVE BRANDING LOGO (FLEXBOX)
# ==========================================
try:
    with open("assets/logo.png", "rb") as img_file:
        img_b64 = base64.b64encode(img_file.read()).decode()
    # 💉 PERBAIKAN: Menghapus margin-top negatif dan menggantinya dengan padding-top: 10px;
    st.markdown(f"""
        <div style='display: flex; justify-content: center; align-items: center; margin-bottom: 10px; width: 100%; padding-top: 10px;'>
            <img src='data:image/png;base64,{img_b64}' style='max-width: 150px; height: auto; object-fit: contain; filter: drop-shadow(0px 4px 6px rgba(0,0,0,0.1));'>
        </div>
    """, unsafe_allow_html=True)
except FileNotFoundError:
    pass

# Merender judul utama dengan teks asli milik Anda
render_cyberpunk_header("TRANSIT HUB CORE SYSTEM", "PDP Mobility Dashboard - By : Soni Abbasy", "var(--accent-cyan)")

st.divider()

# ==========================================
# 🚀 SHORTCUT MENU (QUICK ACCESS)
# ==========================================
# Mengembalikan teks judul komponen menu asli
st.markdown("<h3 style='text-align: center; color: var(--accent-cyan); margin-bottom: 25px; font-family: \"Rajdhani\", sans-serif; letter-spacing: 2px;'>QUICK ACCESS MENU</h3>", unsafe_allow_html=True)

# Grid 2 kolom dengan Bento Card container untuk pembungkus tombol agar lebih responsif
c1, c2 = st.columns(2)

with c1:
    with st.container(border=True):
        st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
        if st.button("1. PORTAL LINTAS", width="stretch"):
            st.switch_page("pages/1_Portal_Lintas.py")
        
    with st.container(border=True):
        st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
        if st.button("3. PASTEUR DROP POINT", width="stretch"):
            st.switch_page("pages/3_Pasteur_Drop_Point.py")

with c2:
    with st.container(border=True):
        st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
        if st.button("2. CHECKPOINT KM72", width="stretch"):
            st.switch_page("pages/2_Checkpoint_KM72.py")
        
    with st.container(border=True):
        st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
        # Logika switch_page try-except multi-nama file milik Anda tetap dipertahankan penuh
        if st.button("4. LAPORAN", width="stretch"):
            try:
                st.switch_page("pages/4_Laporan_Manajemen.py")
            except:
                st.switch_page("pages/4_Laporan.py")
