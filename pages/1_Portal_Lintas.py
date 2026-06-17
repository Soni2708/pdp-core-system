import streamlit as st
import uuid
import json
from datetime import timedelta

# Import arsitektur visual Neo-Tokyo
from components.ui_styles import apply_neo_tokyo_corporate, render_neo_tokyo_header, render_logo
from components.navbar import render_navbar
from db_utils import safe_append_reguler, get_waktu_wib, fetch_mapped_data
from services.jadwal_service import get_semua_rute, get_jadwal_dinamis, get_jadwal_extra_info
from core.logger import setup_logger
from core.auth import require_auth

log = setup_logger("PORTAL_AWAL")

# Konfigurasi halaman
st.set_page_config(page_title="PORTAL LINTAS", layout="wide", initial_sidebar_state="collapsed")
apply_neo_tokyo_corporate()
require_auth(module_name="portal", secret_dict_name="users_portal")
render_navbar("portal")

# ========== INIT STATE MANAGEMENT ==========
if 'kunci_reset' not in st.session_state: 
    st.session_state.kunci_reset = 0

if 'pesan_sukses' not in st.session_state: 
    st.session_state.pesan_sukses = None

# ✅ REFACTOR CTO: AUTO-COMPLETE DRIVER LINTAS-OPERATOR (GLOBAL RAM CACHE)
@st.cache_resource
def get_global_driver_history():
    """Menyimpan memory history driver di RAM Server agar 18 operator tersinkronisasi tanpa hit DB."""
    return {} # format: {"RUTE": ["DRIVER1", "DRIVER2", ...]}

global_driver_history = get_global_driver_history()

if st.session_state.pesan_sukses:
    st.toast(st.session_state.pesan_sukses)
    st.session_state.pesan_sukses = None 

# ========== LOGO LINTAS ==========
render_logo(align="left", margin_bottom="5px")

# ============================================================
# 🎨 UI HEADER STATIC
# ============================================================
col_hdr, col_status = st.columns([3, 1.5])
with col_hdr:
    render_neo_tokyo_header(
        title="PORTAL KEBERANGKATAN", 
        subtitle="Sistem Integrasi Feeder & Transit LINTAS", 
        accent="var(--nt-cyan)", 
        align="left"
    )

with col_status:
    petugas_aktif = st.session_state.get('petugas_portal', 'UNKNOWN')
    waktu_sekarang_dt = get_waktu_wib()
    tanggal_str = waktu_sekarang_dt.strftime("%d %B %Y")
    waktu_str = waktu_sekarang_dt.strftime("%H:%M:%S")

    st.markdown(f"""
    <div style="text-align: right; margin-top: 5px;">
        <div style='display: inline-block; background: rgba(0, 229, 255, 0.05); border: 1px solid rgba(0, 229, 255, 0.2); padding: 4px 12px; border-radius: 4px; font-size: 11px; font-weight: 700; color: var(--nt-text-muted); margin-bottom: 10px;'>
            <span style='color: #00E676;'>●</span> USER ACTIVE: <span style='color: var(--nt-cyan); letter-spacing: 0.5px;'>{petugas_aktif}</span>
        </div>
        <div style="margin-top: 2px;">
            <span style="background: rgba(0, 230, 118, 0.15); color: #00E676; padding: 4px 12px; border-radius: 20px; font-size: 10px; font-weight: 800; letter-spacing: 0.5px; border: 1px solid rgba(0, 230, 118, 0.3);">SISTEM AKTIF</span>
        </div>
        <div style="font-size: 11px; color: #8B949E; margin-top: 6px; font-weight: 500;">
            {tanggal_str} | <span style="color: #F8F9FA;">{waktu_str} WIB</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)

# ============================================================
# 📅 REVENUE ENGINE: DYNAMIC SCHEDULE PANEL (DENGAN FALLBACK)
# ============================================================
with st.expander("📅 KLIK UNTUK MELIHAT REFERENSI JADWAL FEEDER HARI INI", expanded=False):
    waktu_skr = get_waktu_wib()
    hari_eng_to_indo = {
        "Monday": "senin", "Tuesday": "selasa", "Wednesday": "rabu",
        "Thursday": "kamis", "Friday": "jumat", "Saturday": "sabtu", "Sunday": "minggu"
    }
    hari_ini_nama = hari_eng_to_indo[waktu_skr.strftime("%A")]
    path_json = f"data/{hari_ini_nama}.json"
    
    data_jadwal_hari_ini = None
    
    # Coba load dari file JSON
    try:
        with open(path_json, "r", encoding="utf-8") as f_json:
            data_jadwal_hari_ini = json.load(f_json)
    except FileNotFoundError:
        # 🚀 FALLBACK: Ambil dari database Supabase
        try:
            from db_utils import fetch_master_config
            config = fetch_master_config()
            data_jadwal_hari_ini = {"routes": []}
            for rute, jadwal_list in config.get("JADWAL", {}).items():
                rute_id = rute.lower().replace(" ", "").replace("/", "")
                data_jadwal_hari_ini["routes"].append({
                    "id": rute_id,
                    "name": rute,
                    "times": jadwal_list
                })
            st.info("📡 MENGGUNAKAN DATA JADWAL DARI DATABASE (FALLBACK MODE)")
        except Exception as e:
            st.error(f"TIDAK DAPAT MEMUAT JADWAL FEEDER: {str(e)}")
            st.info("💡 SILAKAN GUNAKAN JADWAL EXTRA ATAU HUBUNGI ADMIN")
            data_jadwal_hari_ini = {"routes": []}
    except Exception as e:
        st.error(f"ERROR PARSING DATA JADWAL: {str(e)}")
        data_jadwal_hari_ini = {"routes": []}
    
    if data_jadwal_hari_ini and data_jadwal_hari_ini.get("routes"):
        ch1, ch2, ch3 = st.columns(3)
        routes_list = data_jadwal_hari_ini.get("routes", [])
        
        col_mapping = {"kopo": ch1, "jatinangor": ch2, "buahbatu": ch3}
        
        for r_data in routes_list:
            r_id = r_data.get("id")
            r_name = r_data.get("name", "")
            r_times = r_data.get("times", [])
            
            target_col = col_mapping.get(r_id, ch1)
            
            with target_col:
                st.markdown(f"<div class='nt-meta' style='color:var(--nt-cyan); font-weight:700; margin-bottom: 6px;'>{r_name.upper()}</div>", unsafe_allow_html=True)
                times_html = "<div style='display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 15px; max-height: 150px; overflow-y: auto; padding-right: 4px;'>"
                for t_val in r_times:
                    times_html += f"<div style='background: rgba(255,255,255,0.03); border: 1px solid var(--nt-border); padding: 4px 8px; border-radius: 4px; font-size: 12px; font-family: monospace; color: #F8F9FA;'>{t_val}</div>"
                times_html += "</div>"
                st.markdown(times_html, unsafe_allow_html=True)

st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)

# ==========================================
# 🛑 MODAL DIALOG KONFIRMASI (PENGAMAN TRANSMISI)
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
    pax3.metric("JATINANGOR", data_konfirmasi['pax_jtn'])
    
    # Render Paket
    total_paket = sum([data_konfirmasi[f"paket_{k}"] for k in ['dago','pdp','mim','bbt','kopo','jtn']])
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

        if st.button("KIRIM", type="primary", use_container_width=True, disabled=st.session_state.sedang_kirim):
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
                    # ✅ REFACTOR CTO: Simpan driver ke Global RAM History
                    rute = data_konfirmasi["rute"]
                    driver = data_konfirmasi["driver"]
                    if rute not in global_driver_history:
                        global_driver_history[rute] = []
                    if driver not in global_driver_history[rute]:
                        global_driver_history[rute].insert(0, driver)
                        # Batasi history maksimal 15 driver agar memori tetap ringan
                        global_driver_history[rute] = global_driver_history[rute][:15]
                    
                    log.info(f"TRANSMIT: {petugas_sekarang} - {data_konfirmasi['driver']} ({data_konfirmasi['nopol']}) rute {data_konfirmasi['rute']} jam {data_konfirmasi['jadwal']}")
                    
                    # ✅ REFACTOR CTO: Hapus fetch_mapped_data.clear() untuk menghentikan efek Thundering Herd mendadak
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
# 🔧 FUNGSI AUTO-COMPLETE DRIVER
# ==========================================
def get_driver_options(rute: str) -> list:
    """Mendapatkan daftar driver history tersinkronisasi lintas cabang"""
    if rute in global_driver_history:
        return global_driver_history[rute]
    return []


# ==========================================
# 🏛️ THE 3-PILLAR COMMAND DESK
# ==========================================
col_p1, col_p2, col_p3 = st.columns([1, 1, 1.2], gap="large")

# --- PILAR 1: ROUTING & SCHEDULE ---
with col_p1:
    with st.container(border=True):
        st.markdown("<div class='nt-meta' style='margin-bottom: 16px; font-size: 13px; color: var(--nt-cyan); border-bottom: 1px solid var(--nt-border); padding-bottom: 8px;'>[ 1 ] ROUTING & SCHEDULE</div>", unsafe_allow_html=True)
        
        list_rute_pilihan = get_semua_rute()
        pilihan_rute = st.selectbox("OUTLET / RUTE", options=list_rute_pilihan, key=f"rute_{st.session_state.kunci_reset}")
        
        # Gunakan fungsi jadwal yang sudah diperbaiki
        opsi_jadwal = get_jadwal_dinamis(pilihan_rute, is_extra_mode=False) if pilihan_rute != "-- Pilih Rute --" else ["-- Pilih Rute Dulu --"]
        pilihan_jadwal = st.selectbox("JADWAL KEBERANGKATAN", options=opsi_jadwal, key=f"jadwal_{st.session_state.kunci_reset}")
        
        with st.expander("📅 Jadwal tidak ada di daftar? Klik Disini!"):
            pakai_jadwal_extra = st.checkbox("Aktifkan Jadwal Extra", key=f"cek_extra_{st.session_state.kunci_reset}")
            jam_extra = st.time_input("Pilih Jam Keberangkatan", disabled=not pakai_jadwal_extra, key=f"jam_extra_{st.session_state.kunci_reset}")

# --- PILAR 2: VEHICLE & DRIVER (Dengan Auto-Complete) ---
with col_p2:
    with st.container(border=True):
        st.markdown("<div class='nt-meta' style='margin-bottom: 16px; font-size: 13px; color: var(--nt-cyan); border-bottom: 1px solid var(--nt-border); padding-bottom: 8px;'>[ 2 ] VEHICLE & DRIVER</div>", unsafe_allow_html=True)
        
        # 🚀 AUTO-COMPLETE DRIVER
        driver_options = get_driver_options(pilihan_rute) if pilihan_rute != "-- Pilih Rute --" else []
        
        if driver_options:
            selected_driver = st.selectbox(
                "NAMA DRIVER (HISTORY)", 
                options=["-- Ketik Manual --"] + driver_options,
                key=f"driver_select_{st.session_state.kunci_reset}"
            )
            if selected_driver == "-- Ketik Manual --":
                nama_driver = st.text_input("NAMA DRIVER (KETIK MANUAL)", placeholder="KETIK NAMA DRIVER...", max_chars=50, key=f"driver_manual_{st.session_state.kunci_reset}").upper()
            else:
                nama_driver = selected_driver.upper()
                st.success(f"✓ Menggunakan driver: {nama_driver}")
        else:
            nama_driver = st.text_input("NAMA DRIVER", placeholder="KETIK NAMA DRIVER...", max_chars=50, key=f"driver_{st.session_state.kunci_reset}").upper()
        
        st.markdown("<div style='margin-bottom: 5px;'></div>", unsafe_allow_html=True)
        nopol_reguler = st.text_input("NOMOR POLISI", placeholder="CONTOH: D 1234 ABC", max_chars=15, key=f"nopol_{st.session_state.kunci_reset}").upper()

# --- PILAR 3: MANIFEST ---
with col_p3:
    with st.container(border=True):
        st.markdown("<div class='nt-meta' style='margin-bottom: 16px; font-size: 13px; color: var(--nt-cyan); border-bottom: 1px solid var(--nt-border); padding-bottom: 8px;'>[ 3 ] MANIFEST</div>", unsafe_allow_html=True)
        
        st.caption("PENUMPANG TRANSIT (PAX)")
        pax_c1, pax_c2, pax_c3 = st.columns(3)
        with pax_c1: pax_mim = st.number_input("MIM/BBT", min_value=0, step=1, key=f"mim_{st.session_state.kunci_reset}")
        with pax_c2: pax_kopo = st.number_input("KOPO", min_value=0, step=1, key=f"kopo_{st.session_state.kunci_reset}")
        with pax_c3: pax_jtn = st.number_input("JATINANGOR", min_value=0, step=1, key=f"jtn_{st.session_state.kunci_reset}")
                
        st.markdown("<div style='margin-bottom: 8px;'></div>", unsafe_allow_html=True)
        
        # Paket (tetap di expander untuk menjaga UI tetap clean)
        with st.expander("📦 TAMBAH PAKET (OPSIONAL)", expanded=False):
            cp1, cp2, cp3 = st.columns(3)
            with cp1: pkt_dago = st.number_input("DAGO", min_value=0, step=1, key=f"pkt_dago_{st.session_state.kunci_reset}")
            with cp2: pkt_pdp = st.number_input("PDP", min_value=0, step=1, key=f"pkt_pdp_{st.session_state.kunci_reset}")
            with cp3: pkt_mim = st.number_input("MIM", min_value=0, step=1, key=f"pkt_mim_{st.session_state.kunci_reset}")
            
            cp4, cp5, cp6 = st.columns(3)
            with cp4: pkt_bbt = st.number_input("BUAH BATU", min_value=0, step=1, key=f"pkt_bbt_{st.session_state.kunci_reset}")
            with cp5: pkt_kopo = st.number_input("KOPO", min_value=0, step=1, key=f"pkt_kopo_{st.session_state.kunci_reset}")
            with cp6: pkt_jtn = st.number_input("JATINANGOR", min_value=0, step=1, key=f"pkt_jtn_{st.session_state.kunci_reset}")


# ==========================================
# 🛡️ ENGINE VALIDASI WAKTU (Menggunakan fungsi baru)
# ==========================================
jadwal_final = jam_extra.strftime("%H:%M") if pakai_jadwal_extra else pilihan_jadwal
tombol_terkunci = False

st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

if pilihan_rute == "-- Pilih Rute --":
    tombol_terkunci = True
    st.warning("⚠️ PILIH RUTE TERLEBIH DAHULU")
elif not nama_driver.strip():
    tombol_terkunci = True
    st.warning("⚠️ MASUKKAN NAMA DRIVER")
elif not nopol_reguler.strip():
    tombol_terkunci = True
    st.warning("⚠️ MASUKKAN NOMOR POLISI")
elif not pakai_jadwal_extra and pilihan_jadwal.startswith("--"):
    tombol_terkunci = True
    st.warning("⚠️ JADWAL REGULER TIDAK TERSEDIA. SILAKAN TUNGGU ATAU GUNAKAN JADWAL EXTRA.")

# 🚀 Validasi jadwal extra menggunakan fungsi baru
if pakai_jadwal_extra:
    jam_extra_str = jam_extra.strftime("%H:%M")
    validasi = get_jadwal_extra_info(pilihan_rute, jam_extra_str)
    
    if not validasi["is_valid"]:
        tombol_terkunci = True
        st.error(f"⚠️ {validasi['message']}")
    else:
        # Tampilkan info selisih waktu jika dalam batas wajar
        selisih = validasi["selisih_menit"]
        if selisih < 0:
            st.info(f"⏰ Jadwal extra terlewat {abs(selisih)} menit. Masih diperbolehkan.")
        elif selisih > 0:
            st.info(f"⏰ Jadwal extra dalam {selisih} menit ke depan.")

total_pax = pax_mim + pax_kopo + pax_jtn
total_pkt = pkt_dago + pkt_pdp + pkt_mim + pkt_bbt + pkt_kopo + pkt_jtn

if not tombol_terkunci and total_pax == 0 and total_pkt == 0:
    st.info("ℹ️ SISTEM MENDETEKSI ARMADA KOSONG (0 PENUMPANG & 0 PAKET)")

# ==========================================
# 🚀 TOMBOL TRANSMIT UTAMA
# ==========================================
col_sp1, col_btn_main, col_sp2 = st.columns([1, 1.5, 1])

with col_btn_main:
    if st.button("TRANSMIT DATA KE SISTEM PDP", disabled=tombol_terkunci, type="primary", use_container_width=True):
        data_siap_kirim = {
            "rute": pilihan_rute, "jadwal": jadwal_final, "driver": nama_driver.strip(), "nopol": nopol_reguler.strip(),
            "pax_mim": pax_mim, "pax_kopo": pax_kopo, "pax_jtn": pax_jtn,
            "paket_dago": pkt_dago, "paket_pdp": pkt_pdp, "paket_mim": pkt_mim,
            "paket_bbt": pkt_bbt, "paket_kopo": pkt_kopo, "paket_jtn": pkt_jtn
        }
        show_confirm_dialog(data_siap_kirim)
