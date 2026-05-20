import streamlit as st
from core.auth import logout_user

def render_navbar(active_module: str):
    """
    Render sidebar navigasi yang konsisten untuk semua halaman.
    active_module: 'home', 'portal', 'km72', 'pdp', 'admin'
    """
    with st.sidebar:
        try:
            st.image("assets/logo.png", width=120)
        except:
            st.markdown("### PDP Mobility")
        
        petugas_key = f"petugas_{active_module}"
        if petugas_key in st.session_state and st.session_state[petugas_key]:
            st.markdown(f"👤 **{st.session_state[petugas_key].upper()}**")
        else:
            st.markdown("👤 **Guest**")
        
        st.divider()
        
        # Daftar halaman dengan ikon dan path yang benar
        pages = {
            "🏠 HOME": ("0_Home.py", "home"),
            "🚐 PORTAL LINTAS": ("pages/1_Portal_Lintas.py", "portal"),
            "📡 CHECKPOINT KM72": ("pages/2_Checkpoint_KM72.py", "km72"),
            "📍 PASTEUR DROP POINT": ("pages/3_Pasteur_Drop_Point.py", "pdp"),
            "📊 LAPORAN": ("pages/4_Laporan.py", "admin")
        }
        
        for label, (path, module) in pages.items():
            # Tandai halaman aktif
            is_active = (active_module == module)
            if is_active:
                st.markdown(f"▶ **{label}**")
            else:
                st.page_link(path, label=label)
        
        st.divider()
        
        if st.button("🚪 LOGOUT", use_container_width=True):
            if active_module == "home":
                for key in list(st.session_state.keys()):
                    if key.startswith("akses_") or key.startswith("petugas_"):
                        del st.session_state[key]
                st.rerun()
            else:
                logout_user(active_module)
