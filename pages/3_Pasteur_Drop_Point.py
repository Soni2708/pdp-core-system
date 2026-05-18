import streamlit as st
import base64 # Injeksi untuk Logo Adaptive
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

if data_kanban["auto_selesai_updates"]:
    sukses, _ = execute_batch_update_by_uuid(data_kanban["auto_selesai_updates"])
    if sukses: 
        fetch_mapped_data.clear()
        st.rerun()

# 💉 VAKSINASI REFRESH OTOMATIS
if not st.session_state.modal_active:
    waktu_refresh = 60000 if jumlah_armada_jalan > 0 else 300000
    st_autorefresh(interval=waktu_refresh, key="auto_refresh_pdp_smart")

# ============================================================
# MODERN DIALOG DISPATCHER ENGINE (ANTI-RESET INPUT)
# ============================================================
@st.dialog("🚦 DISPATCH FEEDER", width="large")
def render_modal_dispatch(tujuan_target):
    st.markdown(f"Keberangkatan Feeder khusus rute: <b style='color:var(--accent-cyan);'>{tujuan_target}</b>", unsafe_allow_html=True)
    list_armada_ready = [item['label'] for item in grup_tujuan[tujuan_target]]
    
    if not list_armada_ready:
        st.warning(f"Belum ada antrian penumpang untuk rute {tujuan_target}.")
        if st.button("Tutup Panel"):
            st.session_state.modal_active = False
            st.rerun()
        return

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
    
    if st.button(f"BERANGKATKAN FEEDER {tujuan_target}", width="stretch", type="primary"):
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
                            st.session_state.modal_active = False 
                            fetch_mapped_data.clear()
                            st.rerun()            
                        else:
                            st.error(f"Kegagalan Transmisi Pipa Data: {pesan}")

# ============================================================
# RENDER TATA LETAK STRUKTUR HEADER (CINEMATIC ENTERPRISE)
# ============================================================
# 💉 NEXUS PRIME REFACTOR: Adaptive Flexbox Branding
try:
    with open("assets/logo.png", "rb") as img_file:
        img_b64 = base64.b64encode(img_file.read()).decode()
    st.markdown(f"""
        <div style='display: flex; justify-content: center; align-items: center; margin-bottom: 15px; width: 100%; padding-top: 10px;'>
            <img src='data:image/png;base64,{img_b64}' style='max-width: 160px; height: auto; object-fit: contain; filter: drop-shadow(0px 4px 6px rgba(0,0,0,0.1));'>
        </div>
    """, unsafe_allow_html=True)
except FileNotFoundError:
    pass

col_judul, col_spacer, col_sync, col_logout = st.columns([5, 2.5, 1.2, 1.3], vertical_alignment="bottom")

with col_judul:
    # 💉 NEXUS PRIME FIX: Menambahkan border-bottom agar selaras dengan halaman Home
    st.markdown("<h2 style='color: var(--text-primary); font-family: \"Rajdhani\", sans-serif; font-size: 32px; font-weight: 700; margin-top: -10px; margin-bottom: 5px; letter-spacing: 3px; border-bottom: 3px solid var(--accent-cyan); display: inline-block; padding-bottom: 6px;'>PASTEUR DROP POINT</h2>", unsafe_allow_html=True)
    status_pulse = "<span style='color:var(--accent-yellow); font-weight:700;'>⚡ Active Tracking...</span>" if jumlah_armada_jalan > 0 else "<span style='color:var(--text-muted); font-weight:700;'>💤 Standby</span>"
    st.markdown(f"<p style='text-align: left; margin-top:-5px; font-size:13px; font-family:\"Inter\", sans-serif;'><span style='color:var(--text-muted);'>Sistem Transit & Feeder</span> | <span style='color:var(--accent-cyan); font-weight:bold;'>USER: {st.session_state.get('petugas_pdp', '')}</span> | {status_pulse}</p>", unsafe_allow_html=True)

with col_sync:
    st.markdown('<div class="btn-sync">', unsafe_allow_html=True)
    if st.button("🔄 Refresh", width="stretch"): 
        fetch_mapped_data.clear()
        st.rerun()            
    st.markdown('</div>', unsafe_allow_html=True)

with col_logout:
    st.markdown('<div class="btn-logout">', unsafe_allow_html=True)
    if st.button("Logout", width="stretch"): 
        logout_user("pdp")           
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
# PANEL KANBAN UTAMA OPERASIONAL (ADAPTIVE THEME)
# ============================================================
col_kiri, col_tengah, col_kanan = st.columns([1, 1, 1.4])

with col_kiri:
    st.markdown("<div style='background-color:var(--bg-surface); border:1px solid var(--border-color); border-top:3px solid var(--text-primary); border-radius:6px; padding:10px; margin-bottom:15px; box-shadow: var(--shadow-subtle);'><h4 style='color:var(--text-primary); font-size:15px; margin:0; text-align:center; font-family:\"Rajdhani\", sans-serif; letter-spacing:2px;'>KEBERANGKATAN</h4></div>", unsafe_allow_html=True)
    if not armada_portal_kiri:
        st.info("Belum ada unit berangkat.")
    else:
        with st.container(height=550, border=False):
            for unit in armada_portal_kiri:
                st.markdown(f"""
                <div style="line-height: 1.4; text-align: left; padding: 5px;">
                    <div style="margin-bottom: 5px;">
                        <span style="font-family:'Rajdhani', sans-serif; font-size: 20px; font-weight: bold; color: var(--text-primary);">{unit['nopol']}</span> 
                        <span style="font-size: 15px; font-weight: bold; color: var(--accent-cyan);">[ {unit['driver']} ]</span>
                    </div>
                    <div style="font-size: 14px; color: var(--text-primary); margin-bottom: 8px;">
                        {unit['rute']} <span style="color:var(--text-muted);">|</span> JAM: <span style="color:var(--accent-yellow); font-weight:bold;">{unit['jadwal']}</span>
                    </div>
                    <div style="font-size: 14px; color: var(--text-primary); background:var(--expander-bg); padding:6px 12px; border-radius:4px; border:1px solid var(--border-color); display:inline-block; font-weight:600;">
                        MIM / BB: <b style="color:var(--accent-yellow);">{unit['pax_mim']}</b> &nbsp;|&nbsp; KOPO: <b style="color:var(--accent-yellow);">{unit['pax_kopo']}</b> &nbsp;|&nbsp; JTN: <b style="color:var(--accent-yellow);">{unit['pax_jtn']}</b>
                    </div>
                </div><hr style="margin:10px 0; border-top: 1px dashed var(--border-color) !important;">
                """, unsafe_allow_html=True)

with col_tengah:
    st.markdown("<div style='background-color:var(--bg-surface); border:1px solid var(--border-color); border-top:3px solid var(--accent-yellow); border-radius:6px; padding:10px; margin-bottom:15px; box-shadow: var(--shadow-subtle);'><h4 style='color:var(--accent-yellow); font-size:15px; margin:0; text-align:center; font-family:\"Rajdhani\", sans-serif; letter-spacing:2px;'>CHECKOUT KM72</h4></div>", unsafe_allow_html=True)
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
                                <span style="font-family:'Rajdhani', sans-serif; font-size: 20px; font-weight: bold; color: var(--text-primary);">{unit['nopol']}</span> 
                                <span style="font-size: 15px; font-weight: bold; color: var(--accent-cyan);">[ {unit['driver']} ]</span>
                            </div>
                            <div style="font-size: 14px; color: var(--text-primary); margin-bottom: 8px;">
                                {unit['rute']} <span style="color:var(--text-muted);">|</span> JAM: <span style="color:var(--accent-yellow); font-weight:bold;">{unit['jadwal']}</span> 
                                <span style="color:var(--text-muted);"> &nbsp;|&nbsp; </span> 
                                OUT KM72: <span style="color:var(--accent-yellow); font-weight:bold;">{unit['jam_72']}</span>
                            </div>
                            <div style="font-size: 14px; color: var(--text-primary); background:var(--expander-bg); padding:6px 12px; border-radius:4px; border:1px solid var(--border-color); display:inline-block; font-weight:600;">
                                MIM / BB: <b style="color:var(--accent-yellow);">{unit['pax_mim']}</b> &nbsp;|&nbsp; KOPO: <b style="color:var(--accent-yellow);">{unit['pax_kopo']}</b> &nbsp;|&nbsp; JTN: <b style="color:var(--accent-yellow);">{unit['pax_jtn']}</b>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    with c_tombol:
                        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
                        if st.button("TIBA", key=f"tiba_{unit['trip_id']}", width="stretch"):
                            with st.spinner("Proses..."):
                                waktu_tiba = waktu_sekarang.strftime("%H:%M")
                                sukses, pesan = safe_update_by_uuid(unit['trip_id'], {"K": waktu_tiba})
                                if sukses:
                                    log.info(f"TIBA PDP: {unit['nopol']} ({unit['driver']}) tiba di Pasteur jam {waktu_tiba}.")
                                    fetch_mapped_data.clear()
                                    st.rerun()
                                else:
                                    st.toast(pesan, icon="⚠️")
                st.markdown("<hr style='margin:10px 0; border-top: 1px dashed var(--border-color) !important;'>", unsafe_allow_html=True)

with col_kanan:
    st.markdown("<div style='background-color:var(--bg-surface); border:1px solid var(--border-color); border-top:3px solid var(--accent-cyan); border-radius:6px; padding:10px; margin-bottom:15px; box-shadow: var(--shadow-subtle);'><h4 style='color:var(--accent-cyan); font-size:15px; margin:0; text-align:center; font-family:\"Rajdhani\", sans-serif; letter-spacing:2px;'>WAKTU TUNGGU PDP</h4></div>", unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; background-color: var(--bg-surface); padding: 15px; border-radius:8px; border: 1px solid var(--border-color); margin-bottom: 20px; box-shadow: var(--shadow-subtle);">
        <div style="text-align: center; width: 33%; border-right: 1px solid var(--border-color);">
            <span style="color: var(--text-primary); font-size: 11px; font-weight: 700; letter-spacing:1px;">MIM / BUAHBATU</span><br>
            <span style="color: var(--accent-cyan); font-size: 28px; font-weight: bold; font-family:'Rajdhani', sans-serif;">{total_pax_antre['MIM / BUAHBATU']}</span> <span style="color: var(--text-muted); font-size: 12px;">PAX</span>
        </div>
        <div style="text-align: center; width: 33%; border-right: 1px solid var(--border-color);">
            <span style="color: var(--text-primary); font-size: 11px; font-weight: 700; letter-spacing:1px;">KOPO</span><br>
            <span style="color: var(--accent-cyan); font-size: 28px; font-weight: bold; font-family:'Rajdhani', sans-serif;">{total_pax_antre['KOPO']}</span> <span style="color: var(--text-muted); font-size: 12px;">PAX</span>
        </div>
        <div style="text-align: center; width: 33%;">
            <span style="color: var(--text-primary); font-size: 11px; font-weight: 700; letter-spacing:1px;">JATINANGOR</span><br>
            <span style="color: var(--accent-cyan); font-size: 28px; font-weight: bold; font-family:'Rajdhani', sans-serif;">{total_pax_antre['JATINANGOR']}</span> <span style="color: var(--text-muted); font-size: 12px;">PAX</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # ============================================================
    # 🚦 SMART WIDGET PLACEMENT: TOMBOL DISPATCH DITARIK KE ATAS
    # ============================================================
    st.markdown("<div style='background:var(--bg-surface); border: 1px dashed var(--accent-cyan); padding: 12px; border-radius: 8px; margin-bottom: 20px; box-shadow: var(--shadow-subtle);'>", unsafe_allow_html=True)
    st.markdown("<h4 style='color:var(--accent-cyan); font-size:12px; margin: 0 0 10px 0; text-align:center; font-family:\"Rajdhani\", sans-serif; letter-spacing:1px; text-transform:uppercase;'> KEBERANGKATAN FEEDER</h4>", unsafe_allow_html=True)
    
    col_b1, col_b2, col_b3 = st.columns(3)
    
    with col_b1:
        count_mim = len(grup_tujuan["MIM / BUAHBATU"])
        if st.button(f"MIM/BB ({count_mim})", width="stretch", disabled=(count_mim == 0), key="trg_mim"):
            st.session_state.modal_active = True
            render_modal_dispatch("MIM / BUAHBATU")
            
    with col_b2:
        count_kopo = len(grup_tujuan["KOPO"])
        if st.button(f"KOPO ({count_kopo})", width="stretch", disabled=(count_kopo == 0), key="trg_kop"):
            st.session_state.modal_active = True
            render_modal_dispatch("KOPO")
            
    with col_b3:
        count_jtn = len(grup_tujuan["JATINANGOR"])
        if st.button(f"JATINANGOR ({count_jtn})", width="stretch", disabled=(count_jtn == 0), key="trg_jtn"):
            st.session_state.modal_active = True
            render_modal_dispatch("JATINANGOR")
            
    st.markdown("</div>", unsafe_allow_html=True)

    # ============================================================
    # RENDER LIST ARMADA (Sekarang berada di bawah kendali Dispatch)
    # ============================================================
    if not monitor_antrean:
        st.info("Belum ada unit yang tiba di PDP.")
    else:
        with st.container(height=350, border=False):
            for unit in monitor_antrean:
                st.markdown(f"""
                <div style="line-height: 1.4; text-align: left; padding: 12px; background-color:var(--bg-surface); border-radius:6px; border: 1px solid var(--border-color); border-left: 4px solid var(--accent-cyan); margin-bottom:12px; box-shadow: var(--shadow-subtle);">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 1px dashed var(--border-color); padding-bottom:8px; margin-bottom:8px;">
                        <div>
                            <div style="font-size: 15px; color: var(--text-primary); font-weight: 600; letter-spacing: 1px; margin-bottom: 2px;">{unit['rute']}</div>
                            <span style="font-family:'Rajdhani', sans-serif; font-size: 22px; font-weight: bold; color: var(--text-primary);">{unit['nopol']}</span>
                            <span style="font-size: 14px; font-weight: bold; color: var(--accent-cyan);"> [ {unit['driver']} ]</span>
                        </div>
                        <div style="text-align: right;">
                            <span style="font-size: 15px; color: var(--text-muted); display:block; margin-bottom:2px; font-weight:700; letter-spacing:1px;">TIBA PDP</span>
                            <span style="font-size: 14px; color: var(--accent-yellow); font-weight:700;">🕒 {unit['tiba']}</span>
                        </div>
                    </div>
                    <div style="margin: 0; padding: 8px 10px; background-color: var(--expander-bg); border-radius: 4px; border: 1px solid var(--border-color); font-size: 13px;">
                        {unit['html']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
