import streamlit as st
from streamlit_autorefresh import st_autorefresh

from components.ui_styles import apply_global_cyberpunk_theme
from core.auth import require_auth, logout_user
from db_utils import get_waktu_wib, fetch_mapped_data, safe_update_by_uuid, execute_batch_update_by_uuid
from services.data_pipeline import proses_kanban_pdp
from services.engine_kalkulasi import hitung_wt

# INJEKSI LOGGER
from core.logger import setup_logger
log = setup_logger("SYSTEM_PDP")

# --- KONFIGURASI HALAMAN PUSAT ---
st.set_page_config(page_title="PASTEUR DROP POINT", page_icon="🚐", layout="wide")
apply_global_cyberpunk_theme()
require_auth(module_name="pdp", secret_dict_name="users_pdp") 

# ============================================================
# INISIALISASI STATE & MANAJEMEN ANTI-INTERUPSI REFRESH
# ============================================================
if 'modal_active' not in st.session_state: st.session_state.modal_active = False
if 'reset_form_feeder' not in st.session_state: st.session_state.reset_form_feeder = 0

semua_data = fetch_mapped_data()
waktu_sekarang = get_waktu_wib()

# Fallback Aman Jaringan Terputus (Penyelarasan Operasi Fase 2)
if semua_data is None:
    st.error("🚨 KONEKSI CORE DATABASE TERPUTUS ATAU SIBUK. PANEL FALLBACK AKTIF.")
    st.stop()

data_kanban = proses_kanban_pdp(semua_data, waktu_sekarang)

armada_portal_kiri = data_kanban["portal_kiri"]
armada_km72_tengah = data_kanban["km72_tengah"]
monitor_antrean = data_kanban["monitor_antrean"]
grup_tujuan = data_kanban["grup_tujuan"]
total_pax_antre = data_kanban["total_pax"]
jumlah_armada_jalan = data_kanban["jumlah_armada_jalan"]

# Pemicu Rerun Instan untuk Mencegah Data Hantu (Optimasi Fase 3)
if data_kanban["auto_selesai_updates"]:
    sukses, _ = execute_batch_update_by_uuid(data_kanban["auto_selesai_updates"])
    if sukses: 
        fetch_mapped_data.clear()
        st.rerun()

# 💉 VAKSINASI REFRESH OTOMATIS: Mati total jika modal terbuka, aktif jika modal tutup
if not st.session_state.modal_active:
    waktu_refresh = 60000 if jumlah_armada_jalan > 0 else 300000
    st_autorefresh(interval=waktu_refresh, key="auto_refresh_pdp_smart")

# ============================================================
# MODERN DIALOG DISPATCHER ENGINE (ANTI-RESET INPUT)
# ============================================================
@st.dialog("🚦 DISPATCH FEEDER", width="large")
def render_modal_dispatch(tujuan_target):
    st.markdown(f"keberangkatan Feeder khusus rute: <b style='color:#00d2d3;'>{tujuan_target}</b>", unsafe_allow_html=True)
    list_armada_ready = [item['label'] for item in grup_tujuan[tujuan_target]]
    
    if not list_armada_ready:
        st.warning(f"Belum ada antrian penumpang untuk rute {tujuan_target}.")
        if st.button("Tutup Panel"):
            st.session_state.modal_active = False
            st.rerun()
        return

    # Seluruh key komponen diikat menggunakan kode reset form dinamis
    pilihan_massal = st.multiselect(
        f"Pilih Penumpang dari Unit Reguler tujuan ke ({tujuan_target}):", 
        options=list_armada_ready,
        key=f"sel_{tujuan_target}_{st.session_state.reset_form_feeder}"
    )
    
    c1, c2 = st.columns(2)
    with c1: 
        drv_f = st.text_input("Nama Driver Feeder", key=f"drv_{tujuan_target}_{st.session_state.reset_form_feeder}").upper()
    with c2: 
        nopol_f = st.text_input("Nopol Feeder", placeholder="Contoh: D 4321 XYZ", key=f"npl_{tujuan_target}_{st.session_state.reset_form_feeder}").upper()
    
    with st.expander("📝 CATATAN KETERLAMBATAN (OPSIONAL)"):
        catatan_f = st.text_input(
            "Catatan", placeholder="Wajib diisi jika Waktu Tunggu lebih dari 30 Menit", 
            label_visibility="collapsed", key=f"cat_{tujuan_target}_{st.session_state.reset_form_feeder}"
        )
        
    st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
    
    if st.button(f"BERANGKATKAN FEEDER {tujuan_target}", use_container_width=True, type="primary"):
        if not pilihan_massal or not drv_f.strip() or not nopol_f.strip():
            st.error("⚠️ Validasi Gagal: Lengkapi Nama Pengemudi, Nomor Polisi, dan minimal satu unit pilihan!")
        else:
            ada_pelanggaran = any(hitung_wt(next(i['jam_tiba'] for i in grup_tujuan[tujuan_target] if i['label'] == p), waktu_sekarang) >= 30 for p in pilihan_massal)
            
            if ada_pelanggaran and not catatan_f.strip():
                st.error("🚨 PERINGATAN: Waktu Tunggu melebihi batas SLA (WT ≥ 30 Menit). Kolom Catatan Keterlambatan Wajib Diisi!")
            else:
                with st.spinner("Sinkronisasi enkripsi manifes Feeder ke PostgreSQL Supabase..."):
                    jam_out = waktu_sekarang.strftime("%H:%M")
                    map_kolom = {"MIM / BUAHBATU": ["L", "M", "N", "O"], "KOPO": ["P", "Q", "R", "S"], "JATINANGOR": ["T", "U", "V", "W"]}[tujuan_target]
                    c_drv, c_nopol, c_jam, c_wt = map_kolom
                    
                    uuid_updates = []
                    for p in pilihan_massal:
                        target_data = next(item for item in grup_tujuan[tujuan_target] if item['label'] == p)
                        wt_val = hitung_wt(target_data['jam_tiba'], waktu_sekarang)
                        
                        dict_update = {c_drv: drv_f.strip(), c_nopol: nopol_f.strip(), c_jam: jam_out, c_wt: wt_val}
                        if catatan_f.strip(): dict_update["X"] = catatan_f.strip()
                            
                        uuid_updates.append({"trip_id": target_data['trip_id'], "updates": dict_update})
                            
                    if uuid_updates:
                        sukses, pesan = execute_batch_update_by_uuid(uuid_updates)
                        if sukses:
                            petugas = st.session_state.get('petugas_pdp', 'Unknown')
                            log.info(f"DISPATCH: Petugas {petugas} memberangkatkan Feeder {nopol_f} ({drv_f}) rute {tujuan_target}.")
                            
                            st.session_state.reset_form_feeder += 1 
                            st.session_state.modal_active = False # Buka gembok refresh otomatis kembali
                            fetch_mapped_data.clear()
                            st.rerun()            
                        else:
                            st.error(f"Kegagalan Transmisi Pipa Data: {pesan}")

# ============================================================
# RENDER TATA LETAK STRUKTUR HEADER (CINEMATIC ENTERPRISE)
# ============================================================
col1, col2, col3 = st.columns([4, 0.7, 4])
with col2:
    try: st.image("assets/logo.png", use_container_width=True)
    except: pass

col_judul, col_spacer, col_sync, col_logout = st.columns([5, 3, 1, 0.8])
with col_judul:
    st.markdown("<h2 style='color: #ffffff; font-family: \"Rajdhani\", sans-serif; font-size: 32px; font-weight: 700; margin-top: -10px; margin-bottom: 5px; letter-spacing: 3px;'>PASTEUR DROP POINT</h2>", unsafe_allow_html=True)
    status_pulse = "<span style='color:#feca57; font-weight:700;'>⚡ Active Tracking...</span>" if jumlah_armada_jalan > 0 else "<span style='color:#8b949e; font-weight:700;'>💤 Standby</span>"
    st.markdown(f"<p style='text-align: left; margin-top:-5px; font-size:13px; font-family:\"Inter\", sans-serif;'><span style='color:#8b949e;'>Sistem Feeder & Dispatch</span> | <span style='color:#00d2d3; font-weight:bold;'>USER: {st.session_state.get('petugas_pdp', '')}</span> | {status_pulse}</p>", unsafe_allow_html=True)

with col_sync:
    st.markdown('<div class="btn-sync" style="margin-top:10px;">', unsafe_allow_html=True)
    if st.button("🔄 Refresh"): fetch_mapped_data.clear(); st.rerun()            
    st.markdown('</div>', unsafe_allow_html=True)

with col_logout:
    st.markdown('<div class="btn-logout" style="margin-top:10px;">', unsafe_allow_html=True)
    if st.button("Logout"): logout_user("pdp")           
    st.markdown('</div>', unsafe_allow_html=True)

st.divider()

m1, m2, m3 = st.columns(3)
with m1: st.metric(label="Baru Berangkat", value=len(armada_portal_kiri))
with m2: st.metric(label="Menuju PDP (Keluar KM72)", value=len(armada_km72_tengah))
wt_list = [hitung_wt(item['jam_tiba'], waktu_sekarang) for tj in grup_tujuan for item in grup_tujuan[tj]]
wt_tertinggi = max(wt_list) if wt_list else 0
with m3: st.metric(label="Max Waktu Tunggu", value=f"{wt_tertinggi} Menit")

st.markdown("<hr>", unsafe_allow_html=True)

# ============================================================
# PANEL KANBAN UTAMA OPERASIONAL
# ============================================================
col_kiri, col_tengah, col_kanan = st.columns([1, 1, 1.4])

with col_kiri:
    st.markdown("<div style='background-color:#161b22; border:1px solid #30363d; border-top:3px solid #e2e8f0; border-radius:6px; padding:10px; margin-bottom:15px;'><h4 style='color:#e2e8f0; font-size:15px; margin:0; text-align:center; font-family:\"Rajdhani\", sans-serif; letter-spacing:2px;'>🚐 KEBERANGKATAN</h4></div>", unsafe_allow_html=True)
    if not armada_portal_kiri:
        st.info("Belum ada unit berangkat.")
    else:
        with st.container(height=550, border=False):
            for unit in armada_portal_kiri:
                st.markdown(f"""
                <div style="line-height: 1.4; text-align: left; padding: 5px;">
                    <div style="margin-bottom: 5px;">
                        <span style="font-family:'Rajdhani', sans-serif; font-size: 20px; font-weight: bold; color: #ffffff;">{unit['nopol']}</span> 
                        <span style="font-size: 15px; font-weight: bold; color: #00d2d3;">[ {unit['driver']} ]</span>
                    </div>
                    <div style="font-size: 14px; color: #ffffff; margin-bottom: 8px;">
                        {unit['rute']} <span style="color:#8b949e;">|</span> JAM: <span style="color:#feca57; font-weight:bold;">{unit['jadwal']}</span>
                    </div>
                    <div style="font-size: 14px; color: #ffffff; background:#0d1117; padding:6px 12px; border-radius:4px; border:1px solid #30363d; display:inline-block; font-weight:600;">
                        MIM / BUAHBATU: <b style="color:#feca57;">{unit['pax_mim']}</b> &nbsp;|&nbsp; KOPO: <b style="color:#feca57;">{unit['pax_kopo']}</b> &nbsp;|&nbsp; JATINANGOR: <b style="color:#feca57;">{unit['pax_jtn']}</b>
                    </div>
                </div><hr style="margin:10px 0; border-top: 1px dashed #30363d !important;">
                """, unsafe_allow_html=True)

with col_tengah:
    st.markdown("<div style='background-color:#161b22; border:1px solid #30363d; border-top:3px solid #feca57; border-radius:6px; padding:10px; margin-bottom:15px;'><h4 style='color:#feca57; font-size:15px; margin:0; text-align:center; font-family:\"Rajdhani\", sans-serif; letter-spacing:2px;'>📡 CHECKOUT KM72</h4></div>", unsafe_allow_html=True)
    if not armada_km72_tengah:
        st.info("Tidak ada unit yang keluar KM72.")
    else:
        with st.container(height=550, border=False):
            for unit in armada_km72_tengah:
                with st.container():
                    c_teks, c_tombol = st.columns([2.5, 1])
                    with c_teks:
                        st.markdown(f"""
                        <div style="line-height: 1.4; text-align: left; padding: 5px;">
                            <div style="margin-bottom: 5px;">
                                <span style="font-family:'Rajdhani', sans-serif; font-size: 20px; font-weight: bold; color: #ffffff;">{unit['nopol']}</span> 
                                <span style="font-size: 15px; font-weight: bold; color: #00d2d3;">[ {unit['driver']} ]</span>
                            </div>
                            <div style="font-size: 14px; color: #ffffff; margin-bottom: 8px;">
                                {unit['rute']} <span style="color:#8b949e;">|</span> JAM: <span style="color:#feca57; font-weight:bold;">{unit['jadwal']}</span> 
                                <span style="color:#8b949e;"> &nbsp;|&nbsp; </span> 
                                OUT KM72: <span style="color:#feca57; font-weight:bold;">{unit['jam_72']}</span>
                            </div>
                            <div style="font-size: 14px; color: #ffffff; background:#0d1117; padding:6px 12px; border-radius:4px; border:1px solid #30363d; display:inline-block; font-weight:600;">
                                MIM / BUAHBATU: <b style="color:#feca57;">{unit['pax_mim']}</b> &nbsp;|&nbsp; KOPO: <b style="color:#feca57;">{unit['pax_kopo']}</b> &nbsp;|&nbsp; JATINANGOR: <b style="color:#feca57;">{unit['pax_jtn']}</b>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    with c_tombol:
                        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
                        if st.button("TIBA", key=f"tiba_{unit['trip_id']}", use_container_width=True):
                            with st.spinner("Proses..."):
                                waktu_tiba = waktu_sekarang.strftime("%H:%M")
                                sukses, pesan = safe_update_by_uuid(unit['trip_id'], {"K": waktu_tiba})
                                if sukses:
                                    log.info(f"TIBA PDP: {unit['nopol']} ({unit['driver']}) tiba di Pasteur jam {waktu_tiba}.")
                                    fetch_mapped_data.clear()
                                    st.rerun()
                                else:
                                    st.toast(pesan, icon="⚠️")
                st.markdown("<hr style='margin:10px 0; border-top: 1px dashed #30363d !important;'>", unsafe_allow_html=True)

with col_kanan:
    st.markdown("<div style='background-color:#161b22; border:1px solid #30363d; border-top:3px solid #00d2d3; border-radius:6px; padding:10px; margin-bottom:15px;'><h4 style='color:#00d2d3; font-size:15px; margin:0; text-align:center; font-family:\"Rajdhani\", sans-serif; letter-spacing:2px;'>📍 WAKTU TUNGGU PDP</h4></div>", unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; background-color: #161b22; padding: 15px; border-radius:8px; border: 1px solid #30363d; margin-bottom: 20px;">
        <div style="text-align: center; width: 33%; border-right: 1px solid #30363d;">
            <span style="color: #ffffff; font-size: 11px; font-weight: 700; letter-spacing:1px;">MIM / BUAHBATU</span><br>
            <span style="color: #00d2d3; font-size: 28px; font-weight: bold; font-family:'Rajdhani', sans-serif;">{total_pax_antre['MIM / BUAHBATU']}</span> <span style="color: #ffffff; font-size: 12px;">PAX</span>
        </div>
        <div style="text-align: center; width: 33%; border-right: 1px solid #30363d;">
            <span style="color: #ffffff; font-size: 11px; font-weight: 700; letter-spacing:1px;">KOPO</span><br>
            <span style="color: #00d2d3; font-size: 28px; font-weight: bold; font-family:'Rajdhani', sans-serif;">{total_pax_antre['KOPO']}</span> <span style="color: #ffffff; font-size: 12px;">PAX</span>
        </div>
        <div style="text-align: center; width: 33%;">
            <span style="color: #ffffff; font-size: 11px; font-weight: 700; letter-spacing:1px;">JATINANGOR</span><br>
            <span style="color: #00d2d3; font-size: 28px; font-weight: bold; font-family:'Rajdhani', sans-serif;">{total_pax_antre['JATINANGOR']}</span> <span style="color: #ffffff; font-size: 12px;">PAX</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if not monitor_antrean:
        st.info("Belum ada unit yang tiba di PDP.")
    else:
        with st.container(height=350, border=False):
            for unit in monitor_antrean:
                st.markdown(f"""
                <div style="line-height: 1.4; text-align: left; padding: 12px; background-color:#161b22; border-radius:6px; border: 1px solid #21262d; border-left: 4px solid #00d2d3; margin-bottom:12px;">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 1px dashed #30363d; padding-bottom:8px; margin-bottom:8px;">
                        <div>
                            <div style="font-size: 15px; color: #ffffff; font-weight: 600; letter-spacing: 1px; margin-bottom: 2px;">{unit['rute']}</div>
                            <span style="font-family:'Rajdhani', sans-serif; font-size: 22px; font-weight: bold; color: #ffffff;">{unit['nopol']}</span>
                            <span style="font-size: 14px; font-weight: bold; color: #00d2d3;"> [ {unit['driver']} ]</span>
                        </div>
                        <div style="text-align: right;">
                            <span style="font-size: 15px; color: #ffffff; display:block; margin-bottom:2px; font-weight:700; letter-spacing:1px;">TIBA PDP</span>
                            <span style="font-size: 14px; color: #feca57; font-weight:700;">🕒 {unit['tiba']}</span>
                        </div>
                    </div>
                    <div style="margin: 0; padding: 8px 10px; background-color: #0d1117; border-radius: 4px; border: 1px solid #21262d; font-size: 13px;">
                        {unit['html']}
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # ============================================================
    # 🚦 KOMPONEN PEMICU MODAL DIALOG FEEDER (PENGGANTI FORM LAMA)
    # ============================================================
    st.markdown("<h4 style='color:#00d2d3; font-size:14px; margin: 25px 0 15px 0; border-bottom: 1px solid #30363d; padding-bottom: 5px; font-family:\"Rajdhani\", sans-serif; letter-spacing:1px;'>🚦 KEBERANGKATAN FEEDER</h4>", unsafe_allow_html=True)
    
    # Grid tombol modern untuk memicu modal dialog per rute tujuan
    col_b1, col_b2, col_b3 = st.columns(3)
    
    with col_b1:
        count_mim = len(grup_tujuan["MIM / BUAHBATU"])
        if st.button(f"MIM / BUAHBATU ({count_mim})", use_container_width=True, disabled=(count_mim == 0), key="trg_mim"):
            st.session_state.modal_active = True
            render_modal_dispatch("MIM / BUAHBATU")
            
    with col_b2:
        count_kopo = len(grup_tujuan["KOPO"])
        if st.button(f"KOPO ({count_kopo})", use_container_width=True, disabled=(count_kopo == 0), key="trg_kop"):
            st.session_state.modal_active = True
            render_modal_dispatch("KOPO")
            
    with col_b3:
        count_jtn = len(grup_tujuan["JATINANGOR"])
        if st.button(f"JATINANGOR ({count_jtn})", use_container_width=True, disabled=(count_jtn == 0), key="trg_jtn"):
            st.session_state.modal_active = True
            render_modal_dispatch("JATINANGOR")
