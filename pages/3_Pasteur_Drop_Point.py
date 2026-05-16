import streamlit as st
from streamlit_autorefresh import st_autorefresh

from components.ui_styles import apply_global_cyberpunk_theme
from core.auth import require_auth, logout_user
from db_utils import get_waktu_wib, fetch_mapped_data, execute_batch_update, safe_update_by_uuid, execute_batch_update_by_uuid

from services.data_pipeline import proses_kanban_pdp
from services.engine_kalkulasi import hitung_wt

# INJEKSI LOGGER
from core.logger import setup_logger
log = setup_logger("SYSTEM_PDP")

st.set_page_config(page_title="PASTEUR DROP POINT", page_icon="🚐", layout="wide")
apply_global_cyberpunk_theme()
require_auth(module_name="pdp", secret_dict_name="users_pdp") 

semua_data = fetch_mapped_data()
waktu_sekarang = get_waktu_wib()

if semua_data is None:
    # Ini baru error sungguhan (misal internet putus)
    st.error("Koneksi Database Terputus atau Sedang Sibuk.")
    st.stop()
elif not semua_data:
    # Ini kalau databasenya nyala, tapi emang lagi nggak ada armada (kosong)
    semua_data = [] 

data_kanban = proses_kanban_pdp(semua_data, waktu_sekarang)

armada_portal_kiri = data_kanban["portal_kiri"]
armada_km72_tengah = data_kanban["km72_tengah"]
monitor_antrean = data_kanban["monitor_antrean"]
grup_tujuan = data_kanban["grup_tujuan"]
total_pax_antre = data_kanban["total_pax"]
jumlah_armada_jalan = data_kanban["jumlah_armada_jalan"]

if data_kanban["auto_selesai_updates"]:
    sukses, _ = execute_batch_update(data_kanban["auto_selesai_updates"])
    if sukses: st.cache_data.clear()

waktu_refresh = 60000 if jumlah_armada_jalan > 0 else 300000
st_autorefresh(interval=waktu_refresh, key="auto_refresh_pdp_smart")

c1, c2, c3 = st.columns([4, 0.7, 4])
with c2:
    try: st.image("assets/logo.png", width="stretch")
    except: pass

col_judul, col_spacer, col_sync, col_logout = st.columns([5, 3, 1, 0.8])
with col_judul:
    st.markdown("<h2 style='color: #ffffff; font-family: \"Rajdhani\", sans-serif; font-size: 32px; font-weight: 700; margin-top: -10px; margin-bottom: 5px; letter-spacing: 3px; text-shadow: 0 0 10px rgba(0, 210, 211, 0.3);'>PASTEUR DROP POINT</h2>", unsafe_allow_html=True)
    status_pulse = "<span style='color:#feca57; font-weight:700; text-shadow: 0 0 8px rgba(0, 210, 211, 0.4);'>⚡ Active Tracking...</span>" if jumlah_armada_jalan > 0 else "<span style='color:#8b949e; font-weight:700;'>💤 Standby</span>"
    st.markdown(f"<p style='text-align: left; margin-top:-5px; font-size:13px; font-family:\"Inter\", sans-serif;'><span style='color:#8b949e;'>Sistem Feeder & Dispatch</span> | <span style='color:#00d2d3; font-weight:bold;'>USER: {st.session_state.get('petugas_pdp', '')}</span> | {status_pulse}</p>", unsafe_allow_html=True)

with col_sync:
    st.markdown('<div class="btn-sync" style="margin-top:10px;">', unsafe_allow_html=True)
    if st.button("🔄 Refresh"): st.cache_data.clear(); st.rerun()            
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
with m3: st.metric(label="Max Waktu Tunggu", value=f"{wt_tertinggi} Mnt")

st.markdown("<hr>", unsafe_allow_html=True)

col_kiri, col_tengah, col_kanan = st.columns([1, 1, 1.4])

# --- PANEL KIRI ---
with col_kiri:
    st.markdown("<div style='background-color:#161b22; border:1px solid #30363d; border-top:3px solid #e2e8f0; border-radius:6px; padding:10px; margin-bottom:15px; box-shadow: 0 4px 12px rgba(0,0,0,0.2);'><h4 style='color:#e2e8f0; font-size:15px; margin:0; text-align:center; font-family:\"Rajdhani\", sans-serif; letter-spacing:2px;'>🚐 KEBERANGKATAN</h4></div>", unsafe_allow_html=True)
    if not armada_portal_kiri:
        st.info("Belum ada unit berangkat.")
    else:
        for unit in armada_portal_kiri:
            st.markdown(f"""
            <div style="line-height: 1.4; text-align: left; padding: 5px;">
                <div style="margin-bottom: 5px;">
                    <span style="font-family:'Rajdhani', sans-serif; font-size: 20px; font-weight: bold; color: #ffffff; text-shadow: 0 0 5px rgba(255,255,255,0.2);">{unit['nopol']}</span> 
                    <span style="font-size: 15px; font-weight: bold; color: #00d2d3; letter-spacing:1px;">[ {unit['driver']} ]</span>
                </div>
                <div style="font-size: 15px; color: #8b949e; margin-bottom: 8px;">{unit['rute']} | JAM: <span style="color:#feca57; font-weight:bold; text-shadow: 0 0 5px rgba(254,202,87,0.3);">{unit['jadwal']}</span></div>
                <div style="font-size: 14px; color: #8b949e; background:#0d1117; padding:6px 12px; border-radius:4px; border:1px solid #30363d; display:inline-block; font-weight:600;">
                    MIM / BUAHBATU: <b style="color:#feca57;">{unit['pax_mim']}</b> &nbsp;|&nbsp; KOPO: <b style="color:#feca57;">{unit['pax_kopo']}</b> &nbsp;|&nbsp; JATINANGOR: <b style="color:#feca57;">{unit['pax_jtn']}</b>
                </div>
            </div><hr style="margin:10px 0; border-top: 1px dashed #30363d !important;">
            """, unsafe_allow_html=True)

# --- PANEL TENGAH ---
with col_tengah:
    st.markdown("<div style='background-color:#161b22; border:1px solid #30363d; border-top:3px solid #feca57; border-radius:6px; padding:10px; margin-bottom:15px; box-shadow: 0 4px 12px rgba(254, 202, 87, 0.1);'><h4 style='color:#feca57; text-shadow: 0 0 8px rgba(254, 202, 87, 0.4); font-size:15px; margin:0; text-align:center; font-family:\"Rajdhani\", sans-serif; letter-spacing:2px;'>📡 CHECKOUT KM72</h4></div>", unsafe_allow_html=True)
    if not armada_km72_tengah:
        st.info("Tidak ada unit yang keluar KM72.")
    else:
        for unit in armada_km72_tengah:
            with st.container():
                c_teks, c_tombol = st.columns([2.5, 1])
                with c_teks:
                    st.markdown(f"""
                    <div style="line-height: 1.4; text-align: left; padding: 5px;">
                        <div style="margin-bottom: 5px;">
                            <span style="font-family:'Rajdhani', sans-serif; font-size: 20px; font-weight: bold; color: #ffffff; text-shadow: 0 0 5px rgba(255,255,255,0.2);">{unit['nopol']}</span> 
                            <span style="font-size: 15px; font-weight: bold; color: #00d2d3; letter-spacing:1px;">[ {unit['driver']} ]</span>
                        </div>
                        <div style="font-size: 15px; color: #ffffff; margin-bottom: 7px;">
                            {unit['rute']} | JAM: <span style="color:#feca57; font-weight:bold; text-shadow: 0 0 5px rgba(254,202,87,0.3);">{unit['jadwal']}</span> | OUT KM72: <span style="color:#feca57; font-weight:bold; text-shadow: 0 0 5px rgba(0,210,211,0.3);">{unit.get('jam_72', '-')}</span>
                        </div>
                        <div style="font-size: 14px; color: #8b949e; background:#0d1117; padding:6px 12px; border-radius:4px; border:1px solid #30363d; display:inline-block; font-weight:600;">
                            MIM / BUAHBATU: <b style="color:#feca57;">{unit['pax_mim']}</b> &nbsp;|&nbsp; KOPO: <b style="color:#feca57;">{unit['pax_kopo']}</b> &nbsp;|&nbsp; JTN: <b style="color:#feca57;">{unit['pax_jtn']}</b>
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
                                # ✅ LOGGING TIBA
                                log.info(f"TIBA PDP: {unit['nopol']} ({unit['driver']}) tiba di Pasteur jam {waktu_tiba}.")
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                # ❌ LOGGING ERROR
                                log.error(f"ERROR PDP: Gagal mencatat kedatangan {unit['nopol']}. Alasan: {pesan}")
                                st.error(pesan)
            st.markdown("<hr style='margin:10px 0; border-top: 1px dashed #30363d !important;'>", unsafe_allow_html=True)

# --- PANEL KANAN ---
with col_kanan:
    st.markdown("<div style='background-color:#161b22; border:1px solid #30363d; border-top:3px solid #00d2d3; border-radius:6px; padding:10px; margin-bottom:15px; box-shadow: 0 4px 12px rgba(0, 210, 211, 0.1);'><h4 style='color:#00d2d3; text-shadow: 0 0 8px rgba(0, 210, 211, 0.4); font-size:15px; margin:0; text-align:center; font-family:\"Rajdhani\", sans-serif; letter-spacing:2px;'>📍 WAKTU TUNGGU PDP</h4></div>", unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; background-color: #161b22; padding: 15px; border-radius:8px; border: 1px solid #30363d; margin-bottom: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.2);">
        <div style="text-align: center; width: 33%; border-right: 1px solid #30363d;">
            <span style="color: #8b949e; font-size: 11px; font-weight: 700; letter-spacing:1px;">MIM / BUAHBATU</span><br>
            <span style="color: #00d2d3; font-size: 28px; font-weight: bold; font-family:'Rajdhani', sans-serif; text-shadow: 0 0 10px rgba(0,210,211,0.3);">{total_pax_antre['MIM / BUAHBATU']}</span> <span style="color: #8b949e; font-size: 12px;">PAX</span>
        </div>
        <div style="text-align: center; width: 33%; border-right: 1px solid #30363d;">
            <span style="color: #8b949e; font-size: 11px; font-weight: 700; letter-spacing:1px;">KOPO</span><br>
            <span style="color: #00d2d3; font-size: 28px; font-weight: bold; font-family:'Rajdhani', sans-serif; text-shadow: 0 0 10px rgba(0,210,211,0.3);">{total_pax_antre['KOPO']}</span> <span style="color: #8b949e; font-size: 12px;">PAX</span>
        </div>
        <div style="text-align: center; width: 33%;">
            <span style="color: #8b949e; font-size: 11px; font-weight: 700; letter-spacing:1px;">JATINANGOR</span><br>
            <span style="color: #00d2d3; font-size: 28px; font-weight: bold; font-family:'Rajdhani', sans-serif; text-shadow: 0 0 10px rgba(0,210,211,0.3);">{total_pax_antre['JATINANGOR']}</span> <span style="color: #8b949e; font-size: 12px;">PAX</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Bikin kotak yang bisa di-scroll dengan tinggi maksimal 400px
    html_antrean = "<div style='max-height: 400px; overflow-y: auto; padding-right: 5px; margin-bottom: 15px;'>"
    for unit in monitor_antrean:
        html_antrean += f"""
        <div style="line-height: 1.4; text-align: left; padding: 12px; background-color:#161b22; border-radius:6px; border: 1px solid #30363d; border-top: 3px solid #00d2d3; overflow: hidden; margin-bottom:12px; box-shadow: 0 2px 8px rgba(0,0,0,0.2);">
            <div style="display: flex; justify-content: space-between; align-items: baseline; border-bottom: 1px dashed #30363d; padding-bottom:8px; margin-bottom:8px;">
                <span>
                    <span style="font-family:'Rajdhani', sans-serif; font-size: 20px; font-weight: bold; color: #ffffff; text-shadow: 0 0 5px rgba(255,255,255,0.2);">{unit['label']}</span>
                    <span style="font-size: 15px; font-weight: bold; color: #00d2d3; letter-spacing:1px;"> [ {unit['driver']} ]</span>
                </span>
                <span style="font-size: 12px; color: #feca57; font-weight:700; text-shadow: 0 0 5px rgba(254, 202, 87, 0.4);">🕒 TIBA: {unit['tiba']}</span>
            </div>
            <ul style="margin: 4px 0 0 0; padding-left: 20px; font-size: 13px; color: #e2e8f0; list-style-type: square;">{unit['html']}</ul>
        </div>
        """
    html_antrean += "</div>"
    
    if monitor_antrean:
        st.markdown(html_antrean, unsafe_allow_html=True)

    st.markdown("<h4 style='color:#00d2d3; font-size:14px; margin: 25px 0 15px 0; border-bottom: 1px solid #30363d; padding-bottom: 5px; font-family:\"Rajdhani\", sans-serif; letter-spacing:1px;'>🚦 KEBERANGKATAN FEEDER 🚦</h4>", unsafe_allow_html=True)
    
    tujuan_dipilih = st.radio("Pilih Rute Tujuan:", ["MIM / BUAHBATU", "KOPO", "JATINANGOR"], horizontal=True)
    list_armada_ready = [item['label'] for item in grup_tujuan[tujuan_dipilih]]
    
    if not list_armada_ready:
        st.info(f"Belum ada penumpang untuk rute {tujuan_dipilih}.")
    else:
        if 'reset_form_feeder' not in st.session_state: st.session_state.reset_form_feeder = 0

        with st.form(key=f"form_dispatch_{tujuan_dipilih}_{st.session_state.reset_form_feeder}", clear_on_submit=False):
            pilihan_massal = st.multiselect(f"Pilih Penumpang dari Unit Reguler tujuan ke ({tujuan_dipilih}):", options=list_armada_ready)
            c1, c2 = st.columns(2)
            with c1: drv_f = st.text_input("Nama Driver Feeder")
            with c2: nopol_f = st.text_input("Nopol Feeder")
            
            with st.expander("📝 CATATAN KETERLAMBATAN (OPSIONAL)"):
                catatan_f = st.text_input("Catatan", placeholder="Wajib diisi jika WT >= 30 Menit", label_visibility="collapsed")
                
            if st.form_submit_button(f"BERANGKATKAN {tujuan_dipilih}"):
                if not pilihan_massal or not drv_f or not nopol_f:
                    st.error("Gagal: Harap lengkapi Nama Pengemudi, Nopol, dan pilihan unit.")
                else:
                    ada_pelanggaran = any(hitung_wt(next(i['jam_tiba'] for i in grup_tujuan[tujuan_dipilih] if i['label'] == p), waktu_sekarang) >= 30 for p in pilihan_massal)
                    
                    if ada_pelanggaran and not catatan_f.strip():
                        st.error("Peringatan: Terdapat waktu tunggu ≥ 30 Menit. Wajib mengisi Catatan Keterlambatan.")
                    else:
                        with st.spinner("Sinkronisasi keberangkatan Feeder..."):
                            jam_out = waktu_sekarang.strftime("%H:%M")
                            map_kolom = {"MIM / BUAHBATU": ["L", "M", "N", "O"], "KOPO": ["P", "Q", "R", "S"], "JATINANGOR": ["T", "U", "V", "W"]}[tujuan_dipilih]
                            c_drv, c_nopol, c_jam, c_wt = map_kolom
                            
                            uuid_updates = []
                            for p in pilihan_massal:
                                target_data = next(item for item in grup_tujuan[tujuan_dipilih] if item['label'] == p)
                                trip_id = target_data['trip_id']
                                wt_val = hitung_wt(target_data['jam_tiba'], waktu_sekarang)
                                
                                dict_update = {c_drv: drv_f.upper().strip(), c_nopol: nopol_f.upper().strip(), c_jam: jam_out, c_wt: wt_val}
                                if catatan_f.strip(): dict_update["X"] = catatan_f.strip()
                                    
                                uuid_updates.append({"trip_id": trip_id, "updates": dict_update})
                                    
                            if uuid_updates:
                                sukses, pesan = execute_batch_update_by_uuid(uuid_updates)
                                if sukses:
                                    # ✅ LOGGING DISPATCH FEEDER
                                    petugas = st.session_state.get('petugas_pdp', 'Unknown')
                                    log.info(f"DISPATCH: Petugas {petugas} memberangkatkan Feeder {nopol_f} ({drv_f}) rute {tujuan_dipilih}. Unit reguler: {pilihan_massal}.")
                                    
                                    st.session_state.reset_form_feeder += 1 
                                    st.cache_data.clear()
                                    st.rerun()            
                                else:
                                    # ❌ LOGGING ERROR
                                    log.error(f"ERROR DISPATCH: Gagal kirim feeder {tujuan_dipilih}. Alasan: {pesan}")
                                    st.error(pesan)
