import streamlit as st
import bcrypt
import logging
import time
from streamlit_cookies_controller import CookieController

log = logging.getLogger("AUTH_SYSTEM")

# Inisialisasi Pengontrol Cookie Browser
controller = CookieController()

def check_password(input_password: str, stored_hash: str) -> bool:
    """
    Sistem verifikasi standar industri menggunakan Bcrypt.
    """
    try:
        return bcrypt.checkpw(input_password.encode('utf-8'), stored_hash.encode('utf-8'))
    except ValueError:
        log.error("Format hash tidak valid! Pastikan secrets.toml sudah menggunakan Bcrypt.")
        return False
    except Exception as e:
        log.error(f"Error autentikasi: {e}")
        return False

def generate_hash_for_new_user(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12) 
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def require_auth(module_name: str, secret_dict_name: str):
    """
    Sistem Autentikasi Global (V4 - Bcrypt + Persistent Cookies).
    """
    akses_key = f"akses_{module_name}"
    petugas_key = f"petugas_{module_name}"

    if st.session_state.get(akses_key) == True:
        return True

    cookie_akses = controller.get(akses_key)
    cookie_petugas = controller.get(petugas_key)

    if str(cookie_akses) == "True" and cookie_petugas:
        st.session_state[akses_key] = True
        st.session_state[petugas_key] = cookie_petugas
        return True

    # ==========================================
    # 🎨 UI RENDER: FORM LOGIN MATERIAL FLAT
    # ==========================================
    st.markdown("<div style='margin-top: 10vh;'></div>", unsafe_allow_html=True)
    st.markdown(
        "<h2 style='text-align:center; color:var(--text-primary); font-family:\"Inter\", sans-serif; font-weight:700; letter-spacing: 1px;'>🔒 SYSTEM LOGIN</h2>", 
        unsafe_allow_html=True
    )
    st.markdown(
        f"<p style='text-align:center; color:var(--text-muted); font-family:\"Inter\", sans-serif; font-size:14px; margin-bottom: 25px;'>Otorisasi diperlukan untuk mengakses modul <b style='color:var(--accent-info);'>{module_name.upper()}</b>.</p>", 
        unsafe_allow_html=True
    )
    
    with st.container():
        col_log1, col_log2, col_log3 = st.columns([1, 1.5, 1])
        with col_log2:
            with st.form(f"form_login_{module_name}"):
                input_id = st.text_input("User ID").lower().strip()
                input_pass = st.text_input("Password", type="password").strip()
                
                st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
                submit_login = st.form_submit_button("Login", type="primary", use_container_width=True)
                
                if submit_login:
                    if not input_id or not input_pass:
                        st.warning("⚠️ Masukkan ID dan Password.")
                        st.stop()
                        
                    try:
                        user_db_raw = st.secrets[secret_dict_name]
                        user_db = {str(k).lower(): str(v) for k, v in user_db_raw.items()}
                    except KeyError:
                        st.error(f"🚨 FATAL: Database kredensial [{secret_dict_name}] hilang dari sistem!")
                        log.critical(f"Missing secret dict: {secret_dict_name}")
                        st.stop()

                    if input_id in user_db:
                        stored_hash = user_db[input_id]
                        if check_password(input_pass, stored_hash):
                            st.session_state[akses_key] = True
                            st.session_state[petugas_key] = input_id.upper() 
                            
                            controller.set(akses_key, "True", max_age=604800)
                            controller.set(petugas_key, input_id.upper(), max_age=604800)
                            
                            log.info(f"LOGIN SUCCESS: {input_id.upper()} mengakses {module_name.upper()}")
                            time.sleep(0.5) 
                            st.rerun() 
                        else:
                            log.warning(f"LOGIN FAILED (Wrong Password): Attempt for user {input_id}")
                            st.error("❌ Akses Ditolak! Kredensial tidak valid.")
                    else:
                        log.warning(f"LOGIN FAILED (User Not Found): Attempt for user {input_id}")
                        st.error("❌ Akses Ditolak! Kredensial tidak valid.")
    
    st.stop()

def logout_user(module_name: str):
    akses_key = f"akses_{module_name}"
    petugas_key = f"petugas_{module_name}"
    
    st.session_state[akses_key] = False
    st.session_state[petugas_key] = ""
    
    controller.remove(akses_key)
    controller.remove(petugas_key)
    
    time.sleep(0.5)
    st.rerun()
