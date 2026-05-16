import streamlit as st
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh 

from components.ui_styles import apply_global_cyberpunk_theme
from core.auth import require_auth, logout_user
from db_utils import get_waktu_wib, fetch_mapped_data, execute_batch_update, safe_update_by_uuid
from services.engine_kalkulasi import get_sla_limit

# INJEKSI LOGGER
from core.logger import setup_logger
log = setup_logger("RADAR_KM72")

st.set_page_config(page_title="CHECKPOINT KM72", page_icon="📡", layout="wide")
apply_global_cyberpunk_theme()
require_auth(module_name="km72", secret_dict_name="users_km72")

semua_data = fetch_mapped_data()
armada_aktif = []
jumlah_armada_jalan = 0
waktu_sekarang = get_waktu_wib()

if semua_data:
    for row in semua_data:
        baris_data = row.get('baris_db')
        rute = row.get('rute', '')
        jadwal = row.get('jadwal', '')
        status = row.get('status', '')
        jam_72 = row.get('jam_72', '')
        nopol = row.get('nopol', '')
        driver = row.get('driver', '')
        trip_id = row.get('trip_id', '') 

        sla_limit = get_sla_limit(rute)
        lama_jalan = 0
        is_overdue = False
            
        if "IN TRANSIT" in status and jam_72 == "":
            jumlah_armada_jalan += 1
            try:
                jadwal_dt = datetime.strptime(jadwal, "%H:%M")
                jadwal_real = waktu_sekarang.replace(hour=jadwal_dt.hour, minute=jadwal_dt.minute, second=0, microsecond=0)
                if (waktu_sekarang - jadwal_real).total_seconds() < -43200: 
                    jadwal_real -= timedelta(days=1)
                    
                lama_jalan = int((waktu_sekarang - jadwal_real).total_seconds() / 60)
                if lama_jalan < 0: lama_jalan = 0
                if lama_jalan > sla_limit: is_overdue = True
            except Exception: pass

            armada_aktif.append({
                "nopol": nopol, "rute": rute, "jadwal": jadwal, 
                "driver": driver, "baris": baris_data,
                "lama_jalan": lama_jalan, "sla_limit": sla_limit, "is_overdue": is_overdue,
                "trip_id": trip_id 
            })

armada_aktif.sort(key=lambda x: (not x['is_overdue'], -x['lama_jalan']))

waktu_refresh = 60000 if jumlah_armada_jalan > 0 else 300000
st_autorefresh(interval=waktu_refresh, key="refresh_km72_smart")

c1, c2, c3 = st.columns([4, 0.7, 4])
with c2:
    try: st.image("assets/logo.png", width="stretch")
    except: pass

col_judul, col_spacer, col_sync, col_logout = st.columns([5, 3, 1, 0.8])
with col_judul:
    st.markdown("<h2 style='color: #ffffff; font-family: \"Rajdhani\", sans-serif; font-size: 32px; font-weight: 700; margin-top: -10px; margin-bottom: 5px; letter-spacing: 3px; text-shadow: 0 0 10px rgba(0, 210, 211, 0.3);'>CHECKPOINT KM72</h2>", unsafe_allow_html=True)
    status_pulse = "<span style='color:#feca57; font-weight:700; text-shadow: 0 0 8px rgba(254, 202, 87, 0.4);'>📡  Active Tracking...</span>" if jumlah_armada_jalan > 0 else "<span style='color:#8b949e; font-weight:700;'>💤 Standby</span>"
    st.markdown(f"<p style='text-align: left; margin-top:-5px; font-size:13px; font-family:\"Inter\", sans-serif;'><span style='color:#8b949e;'>Sistem Pemantauan Checkpoint</span> | <span style='color:#00d2d3; font-weight:bold;'>USER: {st.session_state.get('petugas_km72', '')}</span> | {status_pulse}</p>", unsafe_allow_html=True)

with col_sync:
    st.markdown('<div class="btn-sync" style="margin-top:10px;">', unsafe_allow_html=True)
    if st.button("🔄 Refresh"): 
        st.cache_data.clear() 
        st.rerun() 
    st.markdown('</div>', unsafe_allow_html=True)

with col_logout:
    st.markdown('<div class="btn-logout" style="margin-top:10px;">', unsafe_allow_html=True)
    if st.button("Logout"): logout_user("km72")           
    st.markdown('</div>', unsafe_allow_html=True)

st.divider()

unit_overdue = sum(1 for u in armada_aktif if u['is_overdue'])
unit_aman = len(armada_aktif) - unit_overdue

m1, m2, m3 = st.columns(3)
with m1: st.metric(label="Unit Terdeteksi", value=len(armada_aktif))
with m2: st.markdown(f"""<div style="background:#161b22; padding:15px; border:1px solid #30363d; border-radius:8px; border-left:4px solid #00d2d3; text-align:center; box-shadow: 0 0 15px rgba(0, 210, 211, 0.1);"><small style="color:#8b949e; font-weight:500; letter-spacing:1px;">On-Track</small><br><b style="font-size:28px; color:#00d2d3; text-shadow: 0 0 10px rgba(0,210,211,0.3);">{unit_aman}</b></div>""", unsafe_allow_html=True)
with m3: st.markdown(f"""<div style="background:#161b22; padding:15px; border:1px solid #30363d; border-radius:8px; border-left:4px solid #ff4d6d; text-align:center; box-shadow: 0 0 15px rgba(255, 77, 109, 0.1);"><small style="color:#8b949e; font-weight:500; letter-spacing:1px;">Overdue</small><br><b style="font-size:28px; color:#ff4d6d; text-shadow: 0 0 10px rgba(255,77,109,0.3);">{unit_overdue}</b></div>""", unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

if not armada_aktif:
    st.markdown("<div style='background-color: #161b22; padding: 20px; border: 1px solid #30363d; border-radius:8px; border-left: 4px solid #8b949e; text-align: center;'><span style='color:#8b949e; font-family:\"Rajdhani\", sans-serif; font-size:18px; letter-spacing:2px;'>[ Belum ada unit berangkat. ]</span></div>", unsafe_allow_html=True)
else:
    cols = st.columns(3)
    for index, unit in enumerate(armada_aktif):
        with cols[index % 3]:
            # Soft Neon Card Layout
            border_color = "#ff4d6d" if unit['is_overdue'] else "#30363d"
            top_border = "#ff4d6d" if unit['is_overdue'] else "#00d2d3"
            shadow_color = "rgba(255, 77, 109, 0.15)" if unit['is_overdue'] else "rgba(0, 210, 211, 0.05)"
            
            st.markdown(f"<div style='background-color:#161b22; border:1px solid {border_color}; border-top:3px solid {top_border}; border-radius:8px; padding:15px; margin-bottom:15px; box-shadow: 0 4px 12px {shadow_color};'>", unsafe_allow_html=True)
            
            if unit['is_overdue']:
                kelebihan = unit['lama_jalan'] - unit['sla_limit']
                badge_html = f"<div class='badge-overdue' style='width:100%; text-align:center;'>🚨 OVERDUE (+{kelebihan} Mnt)</div>"
            else:
                badge_html = f"<div class='badge-normal' style='width:100%; text-align:center;'>⏱️ DURASI: {unit['lama_jalan']} / {unit['sla_limit']} MENIT</div>"

            st.markdown(f"""
                <div style="line-height: 1.4; text-align: left; margin-bottom: 12px;">
                    <div style="display:flex; justify-content:space-between; align-items:baseline; border-bottom:1px solid #30363d; padding-bottom:8px; margin-bottom:8px;">
                        <span style="font-family:'Rajdhani', sans-serif; font-size: 22px; font-weight: 700; color: #ffffff; letter-spacing:1px; text-shadow: 0 0 5px rgba(255,255,255,0.2);">{unit['nopol']}</span> 
                        <!-- UKURAN FONT DRIVER DINAIIKAN KE 15px -->
                        <span style="font-size: 15px; font-weight: 700; color: #00d2d3; letter-spacing:1px;">[ {unit['driver']} ]</span>
                    </div>
                    <div style="font-size: 13px; color: #8b949e; margin-bottom:3px; font-family:'Inter', sans-serif;">RUTE: <span style="color:#ebeef2; font-weight:600;">{unit['rute']}</span></div>
                    <div style="font-size: 13px; color: #8b949e; font-family:'Inter', sans-serif;">JAM: <span style="color:#feca57; font-weight:700; text-shadow: 0 0 5px rgba(254, 202, 87, 0.4);">{unit['jadwal']} WIB</span></div>
                </div>
                {badge_html}
            """, unsafe_allow_html=True)
            
            st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
            
            if st.button("CHECKOUT", key=f"btn_km72_{unit['trip_id']}", width="stretch"):
                with st.spinner("Mencatat target..."):
                    waktu_wib = get_waktu_wib().strftime("%H:%M")
                    sukses, pesan = safe_update_by_uuid(unit['trip_id'], {"J": waktu_wib})
                    
                    if sukses:
                        # ✅ LOGGING SUKSES
                        petugas = st.session_state.get('petugas_km72', 'Unknown')
                        log.info(f"CHECKOUT KM72: {unit['nopol']} ({unit['driver']}) dicheckout oleh {petugas}.")
                        
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        # ❌ LOGGING ERROR
                        log.error(f"ERROR KM72: Gagal checkout {unit['nopol']}. Alasan: {pesan}")
                        st.error(pesan)
                        
            st.markdown("</div>", unsafe_allow_html=True)
