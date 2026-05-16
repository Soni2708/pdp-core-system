import streamlit as st
import hashlib

def hash_password(password: str) -> str:
    """Fungsi internal untuk men-generate hash SHA-256 dari input user"""
    return hashlib.sha256(password.encode()).hexdigest()

def require_auth(module_name, secret_dict_name):
    """
    Sistem Autentikasi Global (V2 - Enkripsi SHA-256).
    Menahan render halaman jika user belum login.
    """
    akses_key = f"akses_{module_name}"
    petugas_key = f"petugas_{module_name}"

    if akses_key not in st.session_state:
        st.session_state[akses_key] = False
        st.session_state[petugas_key] = ""

    if st.session_state[akses_key]:
        return True

    # --- UI RENDER: FORM LOGIN ---
    st.markdown("<br><br><h2 style='text-align:center; color:#00ffcc;'>🔒 SYSTEM LOGIN</h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center; color:#ffffff;'>Akses terbatas. Silakan masuk untuk mengakses modul <b>{module_name.upper()}</b>.</p>", unsafe_allow_html=True)
    
    with st.container():
        col_log1, col_log2, col_log3 = st.columns([1, 1.5, 1])
        with col_log2:
            with st.form(f"form_login_{module_name}"):
                # FIX: Input diubah ke .lower() agar kebal terhadap kesalahan huruf besar/kecil
                input_id = st.text_input("User ID").lower().strip()
                input_pass = st.text_input("Password", type="password").strip()
                submit_login = st.form_submit_button("Login")
                
                if submit_login:
                    try:
                        # FIX: Otomatis mapping semua kunci di database menjadi lowercase
                        user_db_raw = st.secrets[secret_dict_name]
                        user_db = {str(k).lower(): str(v) for k, v in user_db_raw.items()}
                    except KeyError:
                        st.error(f"Fatal Error: Database kredensial [{secret_dict_name}] hilang dari sistem!")
                        st.stop()

                    # ==========================================
                    # 🛡️ VALIDASI KREDENSIAL BERBASIS HASH
                    # ==========================================
                    if input_id in user_db:
                        stored_hash = user_db[input_id]
                        # Ubah password ketikan user menjadi hash
                        input_hash = hash_password(input_pass)
                        
                        # Cocokkan Hash vs Hash (Sistem tidak pernah tahu password asli)
                        if input_hash == stored_hash:
                            st.session_state[akses_key] = True
                            st.session_state[petugas_key] = input_id
                            st.rerun() 
                        else:
                            st.error("❌ Akses Ditolak! ID atau Password tidak valid.")
                    else:
                        st.error("❌ Akses Ditolak! ID atau Password tidak valid.")
    
    st.stop()

def logout_user(module_name):
    """Fungsi global untuk menghancurkan session login"""
    st.session_state[f"akses_{module_name}"] = False
    st.session_state[f"petugas_{module_name}"] = ""
    st.rerun()
