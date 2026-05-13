import streamlit as st
# Mengimpor komponen dari folder yang baru kita buat
from components.ui_styles import apply_global_cyberpunk_theme, render_cyberpunk_header

# Konfigurasi Paling Awal
st.set_page_config(page_title="LINTAS COMMAND CENTER", page_icon="📡", layout="centered")

# Panggil fungsi CSS global
apply_global_cyberpunk_theme()

# Layout Logo & Header
col1, col2, col3 = st.columns([2, 1, 2])
with col2:
    try:
        # Perhatikan path-nya sekarang mengarah ke folder assets
        st.image("assets/logo.png", width="stretch") 
    except FileNotFoundError:
        st.warning("Logo tidak ditemukan di assets/logo.png")

render_cyberpunk_header("COMMAND CENTER", "LINTAS Sistem Operasi Terpadu", "#ff0055")

st.divider()
st.info("👈 Silakan pilih modul operasional di menu *sidebar* sebelah kiri untuk memulai.")