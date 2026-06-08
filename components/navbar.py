import streamlit as st
from core.auth import logout_user

def render_navbar(active_module: str):
    """
    Render sidebar navigasi Neo-Tokyo Corporate.
    Zero-emoji, fokus pada tipografi dan indikator aktif.
    """
    with st.sidebar:
        try:
            st.image("assets/logo.png", width=140)
        except:
            st.markdown("<h2 style='color: var(--nt-text-primary); font-weight: 800; letter-spacing: 1px;'>LINTAS HUB</h2>", unsafe_allow_html=True)
        
        st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
        
        petugas_key = f"petugas_{active_module}"
        if petugas_key in st.session_state and st.session_state[petugas_key]:
            st.markdown(f"<div class='nt-meta' style='letter-spacing: 1.5px;'>USER ACTIVE</div><div style='color: var(--nt-cyan); font-weight: 800; font-size: 15px; letter-spacing: 1px;'>{st.session_state[petugas_key].upper()}</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='nt-meta' style='letter-spacing: 1.5px;'>USER ACTIVE</div><div style='color: var(--nt-cyan); font-weight: 800; font-size: 15px; letter-spacing: 1px;'>GUEST_SYSTEM</div>", unsafe_allow_html=True)
        
        st.divider()
        
        # Daftar halaman korporat
        pages = {
            "HOME DASHBOARD": ("0_Home.py", "home"),
            "PORTAL LINTAS": ("pages/1_Portal_Lintas.py", "portal"),
            "CHECKPOINT KM72": ("pages/2_Checkpoint_KM72.py", "km72"),
            "PASTEUR DROP POINT": ("pages/3_Pasteur_Drop_Point.py", "pdp"),
            "DATA & LAPORAN": ("pages/4_Laporan.py", "admin")
        }
        
        st.markdown("<div class='nt-meta' style='margin-bottom: 12px; letter-spacing: 1px;'>SYSTEM MODULES</div>", unsafe_allow_html=True)
        
        for label, (path, module) in pages.items():
            is_active = (active_module == module)
            if is_active:
                # Modul aktif diberikan garis pinggir menyala
                st.markdown(f"<div style='border-left: 3px solid var(--nt-cyan); padding-left: 10px; margin-bottom: 12px;'><b style='color: var(--nt-text-primary); letter-spacing: 1px; font-size: 14px;'>{label}</b></div>", unsafe_allow_html=True)
            else:
                st.page_link(path, label=label)
        
        st.divider()
        
        if st.button("TERMINATE SESSION", use_container_width=True):
            if active_module == "home":
                for key in list(st.session_state.keys()):
                    if key.startswith("akses_") or key.startswith("petugas_"):
                        del st.session_state[key]
                st.rerun()
            else:
                logout_user(active_module)
