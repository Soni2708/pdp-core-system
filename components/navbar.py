import streamlit as st
from core.auth import logout_user

def render_navbar(active_module: str):
    """
    Komponen Navigasi Utama & Tombol Logout (Neo-Tokyo Style)
    """
    # Menggunakan container agar rapi dan terisolasi
    with st.container():
        # Garis pembatas atas opsional
        # st.markdown("<div style='border-bottom: 1px solid var(--nt-border); padding-top: 10px;'></div>", unsafe_allow_html=True)
        
        col_nav, col_space, col_logout = st.columns([3, 2, 1], vertical_alignment="center")
        
        with col_nav:
            # Indikator Modul Aktif
            st.markdown(f"""
            <div style='font-size: 12px; font-weight: 700; color: var(--nt-text-muted); letter-spacing: 1px;'>
                SYSTEM / <span style='color: var(--nt-cyan);'>{active_module.upper()}</span>
            </div>
            """, unsafe_allow_html=True)
            
        with col_logout:
            # Tombol Logout (Menggunakan type secondary agar tidak bentrok dengan tombol Transmit)
            if st.button("LOGOUT", key=f"btn_logout_{active_module}", use_container_width=True):
                logout_user(active_module)
                
        # Garis pembatas bawah
        st.markdown("<div style='border-bottom: 1px solid var(--nt-border); margin-bottom: 15px; margin-top: 5px;'></div>", unsafe_allow_html=True)
