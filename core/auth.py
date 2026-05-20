import streamlit as st
import bcrypt
import logging
import time
from streamlit_cookies_controller import CookieController

log = logging.getLogger("AUTH_SYSTEM")

# Inisialisasi Pengontrol Cookie Browser
controller = CookieController()

# ⚙️ KONFIGURASI KEAMANAN: Batas Waktu Idle / Inaktivitas
# 3 Jam = 3 x 60 x 60 = 10800 detik
IDLE_TIMEOUT_SECONDS = 10800 

def check_password(input_password: str, stored_hash: str) -> bool:
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
    akses_key = f"akses_{module_name}"
    petugas_key = f"petugas_{module_name}"
    waktu_key = f"last_active_{module_name}"
    timeout_msg_key = f"timeout_msg_{module_name}"

    waktu_sekarang = time.time()

    # Tampilkan notifikasi jika user baru saja terkena Auto-Logout
    if st.session_state.get(timeout_msg_key):
        st.warning("⏱️ Sesi Anda telah berakhir otomatis demi keamanan karena tidak ada aktivitas selama 3 Jam. Silakan login kembali.")
        st.session_state[timeout_msg_key] = False

    # 1. PERIKSA MEMORI RAM (User sedang aktif menggunakan aplikasi)
    if st.session_state.get(akses_key) == True:
        waktu_terakhir_aktif = st.session_state.get(waktu_key, waktu_sekarang)
        
        # Cek apakah sudah melebihi 3 Jam
        if waktu_sekarang - waktu_terakhir_aktif > IDLE_TIMEOUT_SECONDS:
            log.info(f"AUTO LOGOUT (RAM IDLE): Sesi {module_name} berakhir karena inaktivitas.")
            logout_user(module_name, is_timeout=True)
            st.stop()
        else:
            # Jika belum 3 jam, perbarui stempel waktunya ke detik ini
            st.session_state[waktu_key] = waktu_sekarang
            return True

    # 2. PERIKSA COOKIE BROWSER (Jika memori RAM hilang akibat tab ditutup/reload)
    cookie_akses = controller.get(akses_key)
    cookie_petugas = controller.get(petugas_key)
    cookie_waktu = controller.get(waktu_key)

    if str(cookie_akses) == "True" and cookie_petugas:
        # Mencegah error jika cookie waktu belum terbentuk di browser lama
        waktu_terakhir_cookie = float(cookie_waktu) if cookie_waktu is not None else waktu_sekarang
        
        # Cek apakah Cookie ini sudah 'basi' (lebih dari 3 jam ditinggalkan)
        if waktu_sekarang - waktu_terakhir_cookie > IDLE_TIMEOUT_SECONDS:
            log.info(f"AUTO LOGOUT (COOKIE IDLE): Sesi {module_name} usang, menghapus cookie.")
            logout_user(module_name, is_timeout=True)
            st.stop()
        else:
            # Pulihkan ingatan RAM Server dari Cookie Klien
            st.session_state[akses_key] = True
            st.session_state[petugas_key] = cookie_petugas
            st.session_state[waktu_key] = waktu_sekarang
            
            # Segarkan umur cookie waktu di browser
            controller.set(waktu_key, str(waktu_sekarang), max_age=604800)
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
                input_id = st.text_input("User ID (Case Insensitive)").lower().strip()
                input_pass = st.text_input("Password", type="password").strip()
                
                st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
                submit_login = st.form_submit_button("A U T H E N T I C A T E", type="primary", use_container_width=True)
                
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
                        
                        if check_password(input_pass, stored_hash):
                            # 1. Simpan di RAM beserta stempel waktu saat ini
                            waktu_login = time.time()
                            st.session_state[akses_key] = True
                            st.session_state[petugas_key] = input_id.upper() 
                            st.session_state[waktu_key] = waktu_login
                            
                            # 2. Tanamkan Cookie ke Browser
                            controller.set(akses_key, "True", max_age=604800)
                            controller.set(petugas_key, input_id.upper(), max_age=604800)
                            controller.set(waktu_key, str(waktu_login), max_age=604800)
                            
                            log.info(f"LOGIN SUCCESS: {input_id.upper()} mengakses {module_name.upper()}")
                            time.sleep(0.5) 
                            st.rerun() 
                        else:
                            st.error("❌ Akses Ditolak! Kredensial tidak valid.")
                    else:
                        st.error("❌ Akses Ditolak! Kredensial tidak valid.")
    
    st.stop()

def logout_user(module_name: str, is_timeout=False):
    """Fungsi global untuk menghancurkan session login dan membersihkan Cookie"""
    akses_key = f"akses_{module_name}"
    petugas_key = f"petugas_{module_name}"
    waktu_key = f"last_active_{module_name}"
    timeout_msg_key = f"timeout_msg_{module_name}"
    
    # 1. Hapus dari RAM
    st.session_state[akses_key] = False
    st.session_state[petugas_key] = ""
    st.session_state[waktu_key] = 0
    
    # 2. Hapus dari Cookie Browser
    controller.remove(akses_key)
    controller.remove(petugas_key)
    controller.remove(waktu_key)
    
    # 3. Tandai jika ini karena auto-logout
    if is_timeout:
        st.session_state[timeout_msg_key] = True
    
    time.sleep(0.5) 
    st.rerun()
