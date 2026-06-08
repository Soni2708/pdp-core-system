import streamlit as st
import uuid
import base64
import json
from datetime import timedelta

# Import arsitektur visual Neo-Tokyo
from components.ui_styles import apply_neo_tokyo_corporate, render_neo_tokyo_header
from components.navbar import render_navbar
from db_utils import safe_append_reguler, get_waktu_wib, fetch_mapped_data
from services.jadwal_service import get_semua_rute, get_jadwal_dinamis
from core.logger import setup_logger
from core.auth import require_auth

log = setup_logger("PORTAL_AWAL")

st.set_page_config(page_title="PORTAL LINTAS", layout="centered")
apply_neo_tokyo_corporate()
require_auth(module_name="portal", secret_dict_name="users_portal")
render_navbar("portal")

# ========== INIT STATE MANAGEMENT ==========
if 'kunci_reset' not in st.session_state: 
    st.session_state.kunci_reset = 0

if 'pesan_sukses' not in st.session_state: 
    st.session_state.pesan_sukses = None

if 'tampilkan_referensi_jadwal' not in st.session_state:
    st.session_state.tampilkan_referensi_jadwal = False

if st.session_state.pesan_sukses:
    st.toast(st.session_state.pesan_sukses)
    st.session_state.pesan_sukses = None 

# ========== LOGO LINTAS ==========
try:
    with open("assets/logo.png", "rb") as img_file:
        img_b64 = base64.b64encode(img_file.read()).decode()
    st.markdown(f"""
        <div style='display: flex; justify-content: center; align-items: center; margin-bottom: 15px; width: 100%; padding-top: 10px;'>
            <img src='data:image/png;base64,{img_b64}' style='max-width: 140px; height: auto; object-fit: contain; filter: drop-shadow(0 0 10px rgba(255,255,255,0.1));'>
        </div>
    """, unsafe_allow_html=True)
except FileNotFoundError:
    pass

# ============================================================
# 🎨 UI HEADER DENGAN ADAPTIVE TOGGLE BUTTON (TOP RIGHT)
# ============================================================
col_judul, col_sched = st.columns([3, 1], vertical_alignment="bottom")
with col_judul:
    render_neo_tokyo_header("PORTAL KEBERANGKATAN", "Sistem Integrasi Feeder PDP", "var(--nt-cyan)")

with col_sched:
    st.markdown("<div style='margin-bottom: 24px;'></div>", unsafe_allow_html=True)
    # Tombol toggle persisten menggunakan Session State
    if st.button("INFORMASI JADWAL FEEDER", use_container_width=True):
        st.session_state.tampilkan_referensi_jadwal = not st.session_state.tampilkan_referensi_jadwal

# ============================================================
# 📅 REVENUE ENGINE: DYNAMIC 3-COLUMN SCHEDULE PANEL (RABU.JSON DLL)
# ============================================================
if st.session_state.tampilkan_referensi_jadwal:
    waktu_skr = get_waktu_wib()
    hari_eng_to_indo = {
        "Monday": "senin", "Tuesday": "selasa", "Wednesday": "rabu",
        "Thursday": "kamis", "Friday": "jumat", "Saturday": "sabtu", "Sunday": "minggu"
    }
    hari_ini_nama = hari_eng_to_indo[waktu_skr.strftime("%A")]
    path_json = f"data/{hari_ini_nama}.json"
    
    with st.container(border=True):
        st.markdown(f"<div class='nt-meta' style='color: var(--nt-violet); font-size: 13px; margin-bottom: 12px; font-weight: 700;'>| REFERENSI RUTE & JADWAL HARI INI ({hari_ini_nama.upper()})</div>", unsafe_allow_html=True)
        
        try:
            with open(path_json, "r", encoding="utf-8") as f_json:
                data_jadwal_hari_ini = json.load(f_json)
            
            # Membagi menjadi 3 kolom grid fungsional
            ch1, ch2, ch3 = st.columns(3)
            routes_list = data_jadwal_hari_ini.get("routes", [])
            
            # Mapping indeks rute agar pas ke 3 kolom secara rapi
            col_mapping = {
                "kopo": ch1,
                "jatinangor": ch2,
                "buahbatu": ch3
            }
            
            for r_data in routes_list:
                r_id = r_data.get("id")
                r_name = r_data.get("name", "")
                r_times = r_data.get("times", [])
                
                target_col = col_mapping.get(r_id, ch1)
                
                with target_col:
                    st.markdown(f"<div class='nt-meta' style='color:var(--nt-cyan); font-weight:700; margin-bottom: 6px;'>{r_name.upper()}</div>", unsafe_allow_html=True)
                    # Tampilkan waktu dalam format badge horizontal padat (Bloomberg Style)
                    times_html = "<div style='display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 15px; max-height: 150px; overflow-y: auto; padding-right: 4px;'>"
                    for t_val in r_times:
                        times_html += f"<div style='background: rgba(255,255,255,0.03); border: 1px solid var(--nt-border); padding: 2px 6px; border-radius: 4px; font-size: 11px; font-family: monospace;'>{t_val}</div>"
                    times_html += "</div>"
                    st.markdown(times_html, unsafe_allow_html=True)
                    
        except FileNotFoundError:
            st.error(f"SISTEM CRITICAL FAILURE: File {path_json} tidak ditemukan di folder data/.")
        except Exception as e:
            st.error(f"ERROR PARSING DATA JADWAL: {str(e)}")

st.markdown("<div style='margin-top: 5px;'></div>", unsafe_allow_html=True)

# ==========================================
# 🛑 MODAL DIALOG KONFIRMASI (NEO-TOKYO CORPORATE)
# ==========================================
@st.dialog("KONFIRMASI KEBERANGKATAN", width="small")
def show_confirm_dialog(data_konfirmasi):
    st.markdown(f"<div class='nt-nopol' style='text-align: center; font-size: 26px;'>{data_konfirmasi['nopol']}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='nt-meta' style='text-align: center; margin-bottom: 20px;'>DRIVER: {data_konfirmasi['driver']}</div>", unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        st.caption("RUTE")
        st.write(f"**{data_konfirmasi['rute']}**")
    with c2:
        st.caption("JADWAL")
        st.write(f"**{data_konfirmasi['jadwal']}**")
    
    st.divider()
    
    # Render Pax Metrics
    st.markdown("<div class='nt-meta' style='text-align: center; margin-bottom: 10px; color: var(--nt-cyan);'>JUMLAH PENUMPANG</div>", unsafe_allow_html=True)
    pax1, pax2, pax3 = st.columns(3)
    pax1.metric("MIM/BB", data_konfirmasi['pax_mim'])
    pax2.metric("KOPO", data_konfirmasi['pax_kopo'])
    pax3.metric("JTN", data_konfirmasi['pax_jtn'])
    
    # Render Paket Badges
    total_paket = data_konfirmasi['paket_dago'] + data_konfirmasi['paket_pdp'] + data_konfirmasi['paket_mim'] + data_konfirmasi['paket_bbt'] + data_konfirmasi['paket_kopo'] + data_konfirmasi['paket_jtn']
    if total_paket > 0:
        st.markdown("<div class='nt-meta' style='text-align: center; margin-top: 20px; margin-bottom: 10px; color: var(--nt-cyan);'>JUMLAH PAKET</div>", unsafe_allow_html=True)
        
        paket_html = "<div style='display: flex; flex-wrap: wrap; gap: 8px; justify-content: center;'>"
        paket_dict = {
            "DAGO": data_konfirmasi['paket_dago'], "PDP": data_konfirmasi['paket_pdp'],
            "MIM": data_konfirmasi['paket_mim'], "BBT": data_konfirmasi['paket_bbt'],
            "KOPO": data_konfirmasi['paket_kopo'], "JTN": data_konfirmasi['paket_jtn']
        }
        for pkt_name, pkt_val in paket_dict.items():
            if pkt_val > 0:
                paket_html += f"<div style='border: 1px solid var(--nt-border); padding: 4px 10px; border-radius: 4px; font-size: 12px;'><span style='color:var(--nt-text-muted);'>{pkt_name}:</span> <b style='color:var(--nt-warning);'>{pkt_val}</b></div>"
        paket_html += "</div>"
        st.markdown(paket_html, unsafe_allow_html=True)

    total_pax = data_konfirmasi['pax_mim'] + data_konfirmasi['pax_kopo'] + data_konfirmasi['pax_jtn']
    if total_pax == 0 and total_paket == 0:
        st.warning("UNIT KOSONG (TANPA PENUMPANG & PAKET)")
    
    st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
    
    col_yes, col_no = st.columns(2)
    with col_yes:
        if 'sedang_kirim' not in st.session_state:
            st.session_state.sedang_kirim = False

        if st.button("TRANSMIT", type="primary", use_container_width=True, disabled=st.session_state.sedang_kirim):
            st.session_state.sedang_kirim = True 
            
            with st.spinner("Transmisi ke database..."):
                waktu_wib = get_waktu_wib().strftime("%d-%b-%Y %H:%M:%S")
                trip_id = "TRP-" + uuid.uuid4().hex[:8].upper()
                
                payload_data = {
                    "timestamp": waktu_wib,
                    "rute": data_konfirmasi["rute"],
                    "jadwal": data_konfirmasi["jadwal"],
                    "driver_reguler": data_konfirmasi["driver"],
                    "nopol": data_konfirmasi["nopol"],
                    "status": "IN TRANSIT",
                    "trip_id": trip_id,
                    
                    "pax_mim_bbt": int(data_konfirmasi["pax_mim"]),
                    "pax_kopo": int(data_konfirmasi["pax_kopo"]),
                    "pax_jtn": int(data_konfirmasi["pax_jtn"]),
                    
                    "paket_dago": int(data_konfirmasi["paket_dago"]),
                    "paket_pdp": int(data_konfirmasi["paket_pdp"]),
                    "paket_mim": int(data_konfirmasi["paket_mim"]),
                    "paket_bbt": int(data_konfirmasi["paket_bbt"]),
                    "paket_kopo": int(data_konfirmasi["paket_kopo"]),
                    "paket_jtn": int(data_konfirmasi["paket_jtn"])
                }
                
                sukses, pesan = safe_append_reguler(payload_data)
                petugas_sekarang = st.session_state.get('petugas_portal', 'Unknown')
                
                if sukses:
                    log.info(f"TRANSMIT: {petugas_sekarang} - {data_konfirmasi['driver']} ({data_konfirmasi['nopol']}) rute {data_konfirmasi['rute']} jam {data_konfirmasi['jadwal']}")
                    fetch_mapped_data.clear()
                    st.session_state.kunci_reset += 1
                    st.session_state.pesan_sukses = f"{data_konfirmasi['nopol']} - Diberangkatkan"
                    st.session_state.sedang_kirim = False 
                    st.rerun() 
                else:
                    log.error(f"TRANSMIT GAGAL: {petugas_sekarang} - {data_konfirmasi['nopol']}. Error: {pesan}")
                    st.session_state.sedang_kirim = False 
                    st.error(f"Gagal mengirim data: {pesan}")

    with col_no:
        if st.button("BATAL", use_container_width=True):
            st.rerun()

# ==========================================
# 📋 FORM UTAMA (DATA OPERASIONAL)
# ==========================================
with st.container(border=True):
    st.markdown("<div class='nt-meta' style='margin-bottom: 16px; font-size: 13px; color: var(--nt-cyan); border-bottom: 1px solid var(--nt-border); padding-bottom: 8px;'>DATA OPERASIONAL</div>", unsafe_allow_html=True)
    
    list_rute_pilihan = get_semua_rute()
    col1, col2 = st.columns(2)
    with col1:
        pilihan_rute = st.selectbox("OUTLET / RUTE", options=list_rute_pilihan, key=f"rute_{st.session_state.kunci_reset}")
    with col2:
        opsi_jadwal = get_jadwal_dinamis(pilihan_rute) if pilihan_rute != "-- Pilih Rute --" else ["-- Pilih Rute Dulu --"]
        pilihan_jadwal = st.selectbox("JADWAL KEBERANGKATAN", options=opsi_jadwal, key=f"jadwal_{st.session_state.kunci_reset}")
    
    with st.expander("JADWAL TIDAK ADA DI DAFTAR? KLIK DISINI!"):
        pakai_jadwal_extra = st.checkbox("Gunakan Jadwal Extra", key=f"cek_extra_{st.session_state.kunci_reset}")
        jam_extra = st.time_input("Pilih Jam Keberangkatan", disabled=not pakai_jadwal_extra, key=f"jam_extra_{st.session_state.kunci_reset}")
    
    col_drv, col_npl = st.columns(2)
    with col_drv:
        nama_driver = st.text_input("NAMA DRIVER", placeholder="KETIK NAMA DRIVER...", max_chars=50, key=f"driver_{st.session_state.kunci_reset}").upper()
    with col_npl:
        nopol_reguler = st.text_input("NOMOR POLISI", placeholder="CONTOH: D 1234 ABC", max_chars=15, key=f"nopol_{st.session_state.kunci_reset}").upper()

st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)

# ==========================================
# 📦 SINGLE-VIEW GRID: PAX & PAKET
# ==========================================
with st.container(border=True):
    st.markdown("<div class='nt-meta' style='margin-bottom: 16px; font-size: 13px; color: var(--nt-cyan); border-bottom: 1px solid var(--nt-border); padding-bottom: 8px;'>PENUMPANG & PAKET</div>", unsafe_allow_html=True)
    
    st.caption("PENUMPANG TRANSIT (PAX)")
    col_mim, col_kopo, col_jtn = st.columns(3)
    with col_mim: 
        pax_mim = st.number_input("MIM / BUAH BATU", min_value=0, step=1, key=f"mim_{st.session_state.kunci_reset}")
    with col_kopo: 
        pax_kopo = st.number_input("KOPO", min_value=0, step=1, key=f"kopo_{st.session_state.kunci_reset}")
    with col_jtn: 
        pax_jtn = st.number_input("JATINANGOR", min_value=0, step=1, key=f"jtn_{st.session_state.kunci_reset}")
            
    st.markdown("<hr style='margin: 15px 0; border-color: var(--nt-border);'>", unsafe_allow_html=True)
    
    st.caption("PAKET")
    cp1, cp2, cp3 = st.columns(3)
    with cp1: pkt_dago = st.number_input("DAGO", min_value=0, step=1, key=f"pkt_dago_{st.session_state.kunci_reset}")
    with cp2: pkt_pdp = st.number_input("PDP (PASTEUR)", min_value=0, step=1, key=f"pkt_pdp_{st.session_state.kunci_reset}")
    with cp3: pkt_mim = st.number_input("MIM", min_value=0, step=1, key=f"pkt_mim_{st.session_state.kunci_reset}")
    
    cp4, cp5, cp6 = st.columns(3)
    with cp4: pkt_bbt = st.number_input("BUAH BATU", min_value=0, step=1, key=f"pkt_bbt_{st.session_state.kunci_reset}")
    with cp5: pkt_kopo = st.number_input("KOPO", min_value=0, step=1, key=f"pkt_kopo_{st.session_state.kunci_reset}")
    with cp6: pkt_jtn = st.number_input("JATINANGOR", min_value=0, step=1, key=f"pkt_jtn_{st.session_state.kunci_reset}")

# ==========================================
# 🛡️ ENGINE VALIDASI WAKTU
# ==========================================
jadwal_final = jam_extra.strftime("%H:%M") if pakai_jadwal_extra else pilihan_jadwal
tombol_terkunci = False

st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)

if pilihan_rute == "-- Pilih Rute --":
    tombol_terkunci = True
    st.warning("PILIH RUTE TERLEBIH DAHULU")
elif not nama_driver.strip():
    tombol_terkunci = True
    st.warning("MASUKKAN NAMA DRIVER")
elif not nopol_reguler.strip():
    tombol_terkunci = True
    st.warning("MASUKKAN NOMOR POLISI")
elif not pakai_jadwal_extra and pilihan_jadwal.startswith("--"):
    tombol_terkunci = True
    st.warning("JADWAL REGULER TIDAK TERSEDIA. SILAKAN TUNGGU ATAU GUNAKAN JADWAL EXTRA.")

if pakai_jadwal_extra:
    waktu_sekarang = get_waktu_wib()
    jam_extra_real = waktu_sekarang.replace(hour=jam_extra.hour, minute=jam_extra.minute, second=0, microsecond=0)
    
    if (jam_extra_real - waktu_sekarang).total_seconds() / 3600 > 20:
        jam_extra_real -= timedelta(days=1)
        
    selisih_menit = (jam_extra_real - waktu_sekarang).total_seconds() / 60
    
    if selisih_menit > 60:
        tombol_terkunci = True
        st.error("JADWAL EXTRA TIDAK BOLEH LEBIH DARI 1 JAM DI MASA DEPAN")
    elif selisih_menit < -120: 
        tombol_terkunci = True
        st.error("JADWAL EXTRA TERLALU LAMA TERLEWAT (MAKS 2 JAM)")

total_pax = pax_mim + pax_kopo + pax_jtn
total_pkt = pkt_dago + pkt_pdp + pkt_mim + pkt_bbt + pkt_kopo + pkt_jtn

if not tombol_terkunci and total_pax == 0 and total_pkt == 0:
    st.info("SISTEM MENDETEKSI ARMADA KOSONG (0 PENUMPANG & 0 PAKET)")

# ==========================================
# 🚀 TOMBOL TRANSMIT UTAMA
# ==========================================
st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
col_left, col_btn, col_right = st.columns([1, 2, 1])

with col_btn:
    if st.button("TRANSMIT DATA", disabled=tombol_terkunci, type="primary", use_container_width=True):
        data_siap_kirim = {
            "rute": pilihan_rute,
            "jadwal": jadwal_final,
            "driver": nama_driver.strip(),
            "nopol": nopol_reguler.strip(),
            "pax_mim": pax_mim,
            "pax_kopo": pax_kopo,
            "pax_jtn": pax_jtn,
            "paket_dago": pkt_dago,
            "paket_pdp": pkt_pdp,
            "paket_mim": pkt_mim,
            "paket_bbt": pkt_bbt,
            "paket_kopo": pkt_kopo,
            "paket_jtn": pkt_jtn
        }
        show_confirm_dialog(data_siap_kirim)
