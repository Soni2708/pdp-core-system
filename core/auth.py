import streamlit as st
import bcrypt
import logging
import time
from datetime import datetime, timedelta

# Import Argon2 untuk Kriptografi Modern
try:
    from argon2 import PasswordHasher
    from argon2.exceptions import VerifyMismatchError
    ph = PasswordHasher()
except ImportError:
    ph = None
    logging.warning("Argon2 tidak tersedia, hanya Bcrypt yang akan digunakan")

log = logging.getLogger("AUTH_SYSTEM")

# Rate limiting
RATE_LIMIT_ATTEMPTS = 3
RATE_LIMIT_WINDOW = 60  # detik

def _get_parsed_credentials(secret_dict_name: str) -> dict:
    """Mengambil kredensial dari st.secrets"""
    try:
        user_db_raw = st.secrets[secret_dict_name]
        return {str(k).lower(): {"id_asli": str(k), "hash": str(v)} for k, v in user_db_raw.items()}
    except KeyError:
        log.error(f"Secret dict {secret_dict_name} tidak ditemukan")
        return {}

def check_password(input_password: str, stored_hash: str) -> bool:
    """Hybrid crypto: mendukung Bcrypt dan Argon2id"""
    if not input_password or not stored_hash:
        return False
        
    try:
        if stored_hash.startswith("$argon2"):
            if ph is None:
                log.error("Argon2 tidak tersedia!")
                return False
            ph.verify(stored_hash, input_password)
            return True
        elif stored_hash.startswith("$2b$") or stored_hash.startswith("$2a$"):
            return bcrypt.checkpw(input_password.encode('utf-8'), stored_hash.encode('utf-8'))
        else:
            log.error(f"Format hash tidak dikenali")
            return False
    except VerifyMismatchError:
        return False
    except (ValueError, TypeError) as e:
        log.warning(f"Password verification error: {e}")
        return False
    except Exception as e:
        log.error(f"Error Autentikasi Kritis: {e}")
        return False

def _is_rate_limited(module_name: str) -> tuple[bool, int]:
    """Cek rate limiting"""
    rate_key = f"rate_limit_{module_name}"
    attempts_key = f"rate_attempts_{module_name}"
    
    if rate_key not in st.session_state:
        return False, 0
        
    lock_until = st.session_state[rate_key]
    if datetime.now() < lock_until:
        remaining = int((lock_until - datetime.now()).total_seconds())
        return True, remaining
    
    # Lock expired, reset
    del st.session_state[rate_key]
    if attempts_key in st.session_state:
        del st.session_state[attempts_key]
    return False, 0

def _record_failed_attempt(module_name: str):
    """Mencatat percobaan login gagal"""
    attempts_key = f"rate_attempts_{module_name}"
    
    if attempts_key not in st.session_state:
        st.session_state[attempts_key] = 1
    else:
        st.session_state[attempts_key] += 1
        
    if st.session_state[attempts_key] >= RATE_LIMIT_ATTEMPTS:
        st.session_state[f"rate_limit_{module_name}"] = datetime.now() + timedelta(seconds=RATE_LIMIT_WINDOW)
        log.warning(f"Rate limit triggered for module {module_name}")

def _reset_rate_limit(module_name: str):
    """Reset rate limiting setelah login sukses"""
    attempts_key = f"rate_attempts_{module_name}"
    rate_key = f"rate_limit_{module_name}"
    
    if attempts_key in st.session_state:
        del st.session_state[attempts_key]
    if rate_key in st.session_state:
        del st.session_state[rate_key]

def require_auth(module_name: str, secret_dict_name: str):
    """
    Sistem Autentikasi (tanpa cookie, hanya session state)
    """
    akses_key = f"akses_{module_name}"
    petugas_key = f"petugas_{module_name}"

    # Cek apakah sudah login
    if st.session_state.get(akses_key) == True:
        return True

    # Cek rate limiting
    is_limited, remaining_seconds = _is_rate_limited(module_name)
    if is_limited:
        st.error(f"⛔ TERLALU BANYAK PERCOBAAN GAGAL. COBA LAGI DALAM {remaining_seconds} DETIK.")
        st.stop()

    # UI Login
    st.markdown("<div style='margin-top: 10vh;'></div>", unsafe_allow_html=True)
    st.markdown(
        "<h2 style='text-align:center; color:var(--nt-text-primary); font-weight:800; letter-spacing: 2px;'>🔒 SYSTEM LOGIN</h2>", 
        unsafe_allow_html=True
    )
    st.markdown(
        f"<p style='text-align:center; color:var(--nt-text-muted); font-size:13px; margin-bottom: 25px;'>Otorisasi diperlukan untuk mengakses modul <b style='color:var(--nt-cyan);'>{module_name.upper()}</b>.</p>", 
        unsafe_allow_html=True
    )
    
    with st.container():
        col_log1, col_log2, col_log3 = st.columns([1, 1.5, 1])
        with col_log2:
            with st.form(f"form_login_{module_name}"):
                input_id = st.text_input("User ID", placeholder="Masukkan username Anda").lower().strip()
                input_pass = st.text_input("Password", type="password", placeholder="Masukkan password").strip()
                
                st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
                submit_login = st.form_submit_button("LOGIN KE SISTEM", type="primary", use_container_width=True)
                
                if submit_login:
                    if not input_id or not input_pass:
                        st.warning("⚠️ Masukkan ID dan Password.")
                        st.stop()
                        
                    user_db = _get_parsed_credentials(secret_dict_name)
                    if not user_db:
                        st.error(f"🚨 FATAL: Database kredensial [{secret_dict_name}] hilang atau kosong!")
                        log.critical(f"Missing secret dict: {secret_dict_name}")
                        st.stop()

                    if input_id in user_db:
                        stored_hash = user_db[input_id]["hash"]
                        original_username = user_db[input_id]["id_asli"]
                        
                        if check_password(input_pass, stored_hash):
                            # Login sukses
                            st.session_state[akses_key] = True
                            st.session_state[petugas_key] = original_username.upper()
                            
                            _reset_rate_limit(module_name)
                            
                            log.info(f"LOGIN SUCCESS: {original_username.upper()} mengakses {module_name.upper()}")
                            time.sleep(0.3)
                            st.rerun() 
                        else:
                            _record_failed_attempt(module_name)
                            log.warning(f"LOGIN FAILED (Wrong Password): Attempt for user {original_username}")
                            st.error("❌ Akses Ditolak! Kredensial tidak valid.")
                    else:
                        _record_failed_attempt(module_name)
                        log.warning(f"LOGIN FAILED (User Not Found): Attempt for user {input_id}")
                        st.error("❌ Akses Ditolak! Kredensial tidak valid.")
    
    st.stop()

def logout_user(module_name: str):
    """Logout user dan membersihkan session state"""
    akses_key = f"akses_{module_name}"
    petugas_key = f"petugas_{module_name}"
    
    # Hapus session state keys
    keys_to_remove = [akses_key, petugas_key]
    
    # Hapus rate limiting keys
    for key in list(st.session_state.keys()):
        if key.startswith(f"rate_limit_{module_name}") or key.startswith(f"rate_attempts_{module_name}"):
            keys_to_remove.append(key)
        elif key.startswith(f"drv_g_") or key.startswith(f"npl_g_") or key.startswith(f"cat_g_"):
            keys_to_remove.append(key)
    
    for key in keys_to_remove:
        if key in st.session_state:
            del st.session_state[key]
    
    log.info(f"LOGOUT: User logout dari {module_name.upper()}")
    
    time.sleep(0.3)
    st.rerun()

def generate_hash_for_new_user(password: str) -> str:
    """Generate hash untuk user baru (Argon2id prefered)"""
    if ph:
        return ph.hash(password)
    else:
        salt = bcrypt.gensalt(rounds=12) 
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
