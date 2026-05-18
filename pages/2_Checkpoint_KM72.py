import streamlit as st
import base64 # Injeksi untuk Logo Adaptive
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh 

from components.ui_styles import apply_global_cyberpunk_theme
from core.auth import require_auth, logout_user
from db_utils import get_waktu_wib, fetch_mapped_data, execute_batch_update, safe_update_by_uuid
from services.engine_kalkulasi import get_sla_limit, normalize_time_format

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
                jadwal_aman = normalize_time_format(jadwal)
                jadwal_dt = datetime.strptime(jadwal_aman, "%H:%M")
                jadwal_real = waktu_sekarang.replace(hour=jadwal_dt.hour, minute=jadwal_dt.minute, second=0, microsecond=0)
                if (waktu_sekarang - jadwal_real).total_seconds() < -43200: 
                    jadwal_real -= timedelta(days=1)
                    
                lama_jalan = int((waktu_sekarang - jadwal_real).total_seconds() / 60)
                if lama_jalan < 0: lama_jalan = 0
                if lama_jalan > sla_limit: is_overdue = True
            except Exception as e:
                log.error(f"CORRUPTED TIME FORMAT DETECTED: {jadwal} pada Armada {nopol}. {e}")
                is_overdue = True  # Peringatan paksa agar operator sadar ada anomali
                lama_jalan = 999

            armada_aktif.append({
                "nopol": nopol, "rute": rute, "jadwal": jadwal, 
                "driver": driver, "baris": baris_data,
                "lama_jalan": lama_jalan, "sla_limit": sla_limit, "is_overdue": is_overdue,
                "trip_id": trip_id 
            })

armada_aktif.sort(key=lambda x: (not x['is_overdue'], -x['lama_jalan']))

waktu_refresh = 60000 if jumlah_armada_jalan > 0 else 300000
st_autorefresh(interval=waktu_refresh, key="refresh_km72_smart")

# ============================================================
# 🚀 ADAPTIVE BRANDING LOGO (FLEXBOX)
# ============================================================
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

# 💉 NEXUS PRIME REFACTOR: Vertical Alignment untuk Header Grid agar Tombol Sejajar Bawah
col_judul, col_spacer, col_sync, col_logout = st.columns([5, 2.5, 1.2, 1.3], vertical_alignment="bottom")

with col_judul:
    # 💉 NEXUS PRIME FIX: Menambahkan border-bottom agar selaras dengan halaman Home
    st.markdown("<h2 style='color: var(--text-primary); font-family: \"Rajdhani\", sans-serif; font-size: 32px; font-weight: 700; margin-top: -10px; margin-bottom: 5px; letter-spacing: 3px; border-bottom: 3px solid var(--accent-yellow); display: inline-block; padding-bottom: 6px;'>CHECKPOINT KM72</h2>", unsafe_allow_html=True)
    status_pulse = "<span style='color:var(--accent-yellow); font-weight:700;'>⚡  Active Tracking...</span>" if jumlah_armada_jalan > 0 else "<span style='color:var(--text-muted); font-weight:700;'>💤 Standby</span>"
    st.markdown(f"<p style='text-align: left; margin-top:-5px; font-size:13px; font-family:\"Inter\", sans-serif;'><span style='color:var(--text-muted);'>Sistem Pemantauan Checkpoint</span> | <span style='color:var(--accent-cyan); font-weight:bold;'>USER: {st.session_state.get('petugas_km72', '')}</span> | {status_pulse}</p>", unsafe_allow_html=True)

with col_sync:
    st.markdown('<div class="btn-sync">', unsafe_allow_html=True) # Margin manual dihapus
    if st.button("🔄 Refresh", width="stretch"): 
        fetch_mapped_data.clear() 
        st.rerun() 
    st.markdown('</div>', unsafe_allow_html=True)

with col_logout:
    st.markdown('<div class="btn-logout">', unsafe_allow_html=True) # Margin manual dihapus
    if st.button("Logout", width="stretch"): logout_user("km72")           
    st.markdown('</div>', unsafe_allow_html=True)

st.divider()

unit_overdue = sum(1 for u in armada_aktif if u['is_overdue'])
unit_aman = len(armada_aktif) - unit_overdue

# ============================================================
# 📊 METRICS PANEL (ADAPTIVE THEME)
# ============================================================
m1, m2, m3 = st.columns(3)
with m1: st.metric(label="Unit Terdeteksi", value=len(armada_aktif))
with m2: st.markdown(f"""<div style="background:var(--bg-surface); padding:15px; border:1px solid var(--border-color); border-radius:8px; border-left:4px solid var(--accent-cyan); text-align:center; box-shadow: var(--shadow-subtle);"><small style="color:var(--text-muted); font-weight:600; letter-spacing:1px;">On-Track</small><br><b style="font-size:28px; color:var(--accent-cyan);">{unit_aman}</b></div>""", unsafe_allow_html=True)
with m3: st.markdown(f"""<div style="background:var(--bg-surface); padding:15px; border:1px solid var(--border-color); border-radius:8px; border-left:4px solid var(--accent-red); text-align:center; box-shadow: var(--shadow-subtle);"><small style="color:var(--text-muted); font-weight:600; letter-spacing:1px;">Overdue</small><br><b style="font-size:28px; color:var(--accent-red);">{unit_overdue}</b></div>""", unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

if not armada_aktif:
    st.markdown("<div style='background-color: var(--bg-surface); padding: 20px; border: 1px solid var(--border-color); border-radius:8px; border-left: 4px solid var(--text-muted); text-align: center;'><span style='color:var(--text-muted); font-family:\"Rajdhani\", sans-serif; font-size:18px; letter-spacing:2px;'>[ Belum ada unit berangkat. ]</span></div>", unsafe_allow_html=True)
else:
    cols = st.columns(3)
    for index, unit in enumerate(armada_aktif):
        with cols[index % 3]:
            # 💉 NEXUS PRIME PATCH: Adaptive Variable Theme untuk Kartu Armada
            border_color = "var(--accent-red)" if unit['is_overdue'] else "var(--border-color)"
            accent_border = "var(--accent-red)" if unit['is_overdue'] else "var(--accent-cyan)"
            
            st.markdown(f"<div style='background-color:var(--bg-surface); border:1px solid {border_color}; border-left:4px solid {accent_border}; border-radius:8px; padding:15px; margin-bottom:15px; box-shadow: var(--shadow-subtle);'>", unsafe_allow_html=True)
            
            if unit['is_overdue']:
                kelebihan = unit['lama_jalan'] - unit['sla_limit']
                badge_html = f"<div class='badge-overdue' style='width:100%; text-align:center;'>🚨 OVERDUE (+{kelebihan} Mnt)</div>"
            else:
                badge_html = f"<div class='badge-normal' style='width:100%; text-align:center;'>⏱️ Durasi Perjalanan: {unit['lama_jalan']} / {unit['sla_limit']} MENIT</div>"

            # Teks warna diubah ke var(--text-primary) agar terbaca saat Light/Dark mode
            st.markdown(f"""
                <div style="line-height: 1.4; text-align: left; margin-bottom: 12px;">
                    <div style="display:flex; justify-content:space-between; align-items:baseline; border-bottom:1px solid var(--border-color); padding-bottom:8px; margin-bottom:8px;">
                        <span style="font-family:'Rajdhani', sans-serif; font-size: 22px; font-weight: 700; color: var(--text-primary); letter-spacing:1px;">{unit['nopol']}</span> 
                        <span style="font-size: 15px; font-weight: 700; color: var(--accent-cyan); letter-spacing:1px;">[ {unit['driver']} ]</span>
                    </div>
                    <div style="font-size: 13px; color: var(--text-muted); margin-bottom:3px; font-family:'Inter', sans-serif;">RUTE: <span style="color:var(--text-primary); font-weight:600;">{unit['rute']}</span></div>
                    <div style="font-size: 13px; color: var(--text-muted); font-family:'Inter', sans-serif;">JADWAL: <span style="color:var(--accent-yellow); font-weight:700;">{unit['jadwal']} WIB</span></div>
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
                        
                        fetch_mapped_data.clear()
                        st.rerun()
                    else:
                        # ❌ LOGGING ERROR
                        log.error(f"ERROR KM72: Gagal checkout {unit['nopol']}. Alasan: {pesan}")
                        st.toast(pesan, icon="⚠️")
                        
            st.markdown("</div>", unsafe_allow_html=True)
