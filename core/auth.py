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
    Otomatis mengekstrak Salt dari stored_hash dan melakukan validasi.
    """
    try:
        # Bcrypt membutuhkan format bytes
        return bcrypt.checkpw(input_password.encode('utf-8'), stored_hash.encode('utf-8'))
    except ValueError:
        # Menangkap error jika stored_hash bukan format Bcrypt yang valid
        log.error("Format hash tidak valid! Pastikan secrets.toml sudah menggunakan Bcrypt.")
        return False
    except Exception as e:
        log.error(f"Error autentikasi: {e}")
        return False

def generate_hash_for_new_user(password: str) -> str:
    """
    Fungsi utilitas (internal). Gunakan fungsi ini jika Anda ingin 
    mendaftarkan password baru untuk dimasukkan ke secrets.toml.
    """
    salt = bcrypt.gensalt(rounds=12) # Work factor 12 (Standar keamanan modern)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def require_auth(module_name: str, secret_dict_name: str):
    """
    Sistem Autentikasi Global (V4 - Bcrypt + Persistent Cookies).
    Kebal terhadap reload halaman (F5) dengan menyimpan identitas di Cookie browser.
    """
    akses_key = f"akses_{module_name}"
    petugas_key = f"petugas_{module_name}"

    # 1. PERIKSA MEMORI RAM (Paling Cepat)
    if st.session_state.get(akses_key) == True:
        return True

    # 2. PERIKSA COOKIE BROWSER (Jika memori RAM hilang akibat Reload)
    # Catatan: controller membutuhkan sedikit jeda untuk membaca browser klien pertama kali
    cookie_akses = controller.get(akses_key)
    cookie_petugas = controller.get(petugas_key)

    if str(cookie_akses) == "True" and cookie_petugas:
        # Pulihkan ingatan RAM Server dari Cookie Klien
        st.session_state[akses_key] = True
        st.session_state[petugas_key] = cookie_petugas
        return True

    # ==========================================
    # 🎨 UI RENDER: FORM LOGIN CYBERPUNK
    # ==========================================
    st.markdown("<div style='margin-top: 10vh;'></div>", unsafe_allow_html=True)
    st.markdown(
        "<h2 style='text-align:center; color:var(--accent-cyan); font-family:\"Rajdhani\", sans-serif; letter-spacing: 2px; text-shadow: 0 0 10px rgba(0,210,211,0.5);'>🔒 SYSTEM LOGIN</h2>", 
        unsafe_allow_html=True
    )
    st.markdown(
        f"<p style='text-align:center; color:var(--text-muted); font-family:\"Inter\", sans-serif; font-size:14px; margin-bottom: 25px;'>Akses terbatas. Otorisasi diperlukan untuk modul <b style='color:var(--text-primary);'>{module_name.upper()}</b>.</p>", 
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

                    # ==========================================
                    # 🛡️ VALIDASI KREDENSIAL BCRYPT
                    # ==========================================
                    if input_id in user_db:
                        stored_hash = user_db[input_id]
                        
                        # Bandingkan input user dengan hash di secrets.toml
                        if check_password(input_pass, stored_hash):
                            
                            # 1. Simpan di RAM
                            st.session_state[akses_key] = True
                            st.session_state[petugas_key] = input_id.upper() 
                            
                            # 2. 💾 TANAMKAN KTP DIGITAL KE COOKIE BROWSER (Masa aktif 7 Hari)
                            # max_age = 604800 detik (7 hari)
                            controller.set(akses_key, "True", max_age=604800)
                            controller.set(petugas_key, input_id.upper(), max_age=604800)
                            
                            log.info(f"LOGIN SUCCESS: {input_id.upper()} mengakses {module_name.upper()}")
                            time.sleep(0.5) # Memberi jeda bagi browser untuk menyimpan Cookie
                            st.rerun() 
                        else:
                            log.warning(f"LOGIN FAILED (Wrong Password): Attempt for user {input_id}")
                            st.error("❌ Akses Ditolak! Kredensial tidak valid.")
                    else:
                        log.warning(f"LOGIN FAILED (User Not Found): Attempt for user {input_id}")
                        st.error("❌ Akses Ditolak! Kredensial tidak valid.")
    
    st.stop()

def logout_user(module_name: str):
    """Fungsi global untuk menghancurkan session login dan membersihkan Cookie"""
    akses_key = f"akses_{module_name}"
    petugas_key = f"petugas_{module_name}"
    
    # 1. Hapus dari RAM
    st.session_state[akses_key] = False
    st.session_state[petugas_key] = ""
    
    # 2. Hapus dari Cookie Browser
    controller.remove(akses_key)
    controller.remove(petugas_key)
    
    time.sleep(0.5) # Memberi jeda bagi browser untuk menghapus Cookie
    st.rerun()
