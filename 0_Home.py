import streamlit as st
from datetime import datetime
import pytz
import pandas as pd

from components.ui_styles import apply_neo_tokyo_corporate, render_logo
from db_utils import fetch_mapped_data, get_waktu_wib
from services.data_pipeline import proses_kanban_pdp
from services.engine_kalkulasi import hitung_wt

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="LINTAS SHUTTLE - Dashboard Operasional",
    page_icon="🚐",
    layout="wide",
    initial_sidebar_state="collapsed"
)

apply_neo_tokyo_corporate()

# ============================================================================
# CUSTOM CSS - COMPACT DASHBOARD
# ============================================================================
st.markdown("""
<style>
    /* Main container */
    .main .block-container {
        padding-top: 0.5rem;
        padding-bottom: 0.5rem;
        max-width: 1600px;
        margin: 0 auto;
    }
    
    /* Compact KPI Card */
    .compact-card {
        background: rgba(21, 23, 28, 0.8);
        border-radius: 10px;
        padding: 0.8rem;
        border: 1px solid rgba(255, 255, 255, 0.05);
        transition: all 0.2s ease;
    }
    
    .compact-card:hover {
        border-color: rgba(0, 229, 255, 0.3);
    }
    
    .card-value {
        font-size: 1.6rem;
        font-weight: 800;
        color: #00E5FF;
        margin: 0.2rem 0;
    }
    
    .card-label {
        font-size: 0.65rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #8B949E;
    }
    
    /* Section Header */
    .section-header {
        margin: 1rem 0 0.8rem 0;
        padding-bottom: 0.3rem;
        border-bottom: 1px solid rgba(0, 229, 255, 0.3);
    }
    
    .section-title {
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: #00E5FF;
    }
    
    /* Compact Row Item */
    .row-item {
        background: rgba(21, 23, 28, 0.5);
        border-radius: 6px;
        padding: 0.4rem 0.6rem;
        margin-bottom: 0.3rem;
        border-left: 2px solid #00E5FF;
        font-size: 0.75rem;
    }
    
    /* Status Badge */
    .badge {
        display: inline-block;
        padding: 0.15rem 0.5rem;
        border-radius: 20px;
        font-size: 0.6rem;
        font-weight: 600;
    }
    
    .badge-active { background: rgba(0, 230, 118, 0.15); color: #00E676; }
    .badge-warning { background: rgba(255, 196, 0, 0.15); color: #FFC400; }
    .badge-info { background: rgba(0, 229, 255, 0.15); color: #00E5FF; }
    
    /* Progress Bar */
    .progress-bar-bg {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 4px;
        height: 4px;
        overflow: hidden;
    }
    
    .progress-bar-fill {
        height: 4px;
        border-radius: 4px;
    }
    
    /* Header */
    .header-title {
        font-size: 1.2rem;
        font-weight: 700;
        margin: 0;
    }
    
    .header-subtitle {
        font-size: 0.6rem;
        color: #8B949E;
        margin: 0;
    }
    
    .status-text {
        font-size: 0.7rem;
        text-align: right;
    }
    
    /* Responsive */
    @media (max-width: 768px) {
        .card-value { font-size: 1.2rem; }
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# DATA FETCHING
# ============================================================================
@st.cache_data(ttl=30)
def fetch_dashboard_data():
    try:
        semua_data = fetch_mapped_data()
        waktu_sekarang = get_waktu_wib()
        
        if not semua_data:
            return None
        
        data_kanban = proses_kanban_pdp(semua_data, waktu_sekarang)
        
        metrics = {
            "unit_berangkat": len(data_kanban["portal_kiri"]),
            "unit_checkout": len(data_kanban["km72_tengah"]),
            "penumpang_menunggu": sum(data_kanban["total_pax"].values()),
            "penumpang_tiba_pdp": len(data_kanban["monitor_antrean"]),
            "pax_mim": data_kanban["total_pax"]["MIM / BUAHBATU"],
            "pax_kopo": data_kanban["total_pax"]["KOPO"],
            "pax_jtn": data_kanban["total_pax"]["JATINANGOR"],
            "total_armada": data_kanban["jumlah_armada_jalan"],
        }
        
        wt_list = [pax['waktu_tunggu'] for unit in data_kanban["monitor_antrean"] 
                   for pax in unit.get('pax_details', [])]
        metrics["rata_waktu_tunggu"] = int(sum(wt_list) / len(wt_list)) if wt_list else 0
        
        if wt_list:
            metrics["wt_tercepat"] = min(wt_list)
            metrics["wt_terlama"] = max(wt_list)
        else:
            metrics["wt_tercepat"] = 0
            metrics["wt_terlama"] = 0
        
        departure_data = []
        for row in data_kanban["portal_kiri"]:
            departure_data.append({
                "unit": row.get('nopol', '-'),
                "driver": row.get('driver', '-'),
                "waktu": row.get('jadwal', '-'),
                "tujuan": row.get('rute', '-'),
            })
        
        checkout_data = []
        for row in data_kanban["km72_tengah"]:
            checkout_data.append({
                "unit": row.get('nopol', '-'),
                "driver": row.get('driver', '-'),
                "waktu": row.get('jam_72', '-'),
            })
        
        arrived_data = []
        for row in semua_data:
            if row.get('jam_tiba_pdp'):
                arrived_data.append({
                    "unit": row.get('nopol', '-'),
                    "waktu": row.get('jam_tiba_pdp', '-'),
                    "asal": row.get('rute', '-'),
                    "pax": row.get('pax_mim', 0) + row.get('pax_kopo', 0) + row.get('pax_jtn', 0)
                })
        arrived_data = sorted(arrived_data, key=lambda x: x['waktu'], reverse=True)[:5]
        
        return {
            "metrics": metrics,
            "departure_data": departure_data,
            "checkout_data": checkout_data,
            "arrived_data": arrived_data,
        }
        
    except Exception:
        return None

# ============================================================================
# MESIN AUTO-REFRESH COMMAND CENTER (180 DETIK)
# ============================================================================
@st.fragment(run_every=180)
def live_command_center_board():
    # 1. TARIK DATA & WAKTU LOKAL
    dashboard_data = fetch_dashboard_data()
    waktu_sekarang_dt = get_waktu_wib()
    tanggal_str = waktu_sekarang_dt.strftime("%d %B %Y")
    waktu_str = waktu_sekarang_dt.strftime("%H:%M:%S")
    waktu_wib = waktu_sekarang_dt.strftime("%d %b %Y %H:%M:%S")

    # 2. CUSTOM NAVBAR & HEADER
    with st.container():
        st.markdown("""
            <div style='display: flex; justify-content: space-between; align-items: center; padding: 0.5rem 0; margin-bottom: 1rem; border-bottom: 1px solid rgba(255,255,255,0.08);'>
                <div style='display: flex; gap: 1.5rem;'>
                    <span style='color: #8B949E; font-size: 0.75rem; letter-spacing: 1px;'>SYSTEM / DASHBOARD</span>
                </div>
                <div style='display: flex; gap: 0.5rem;'>
                    <span style='color: #00E5FF; font-size: 0.7rem;'>● ONLINE</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

    col_logo, col_title, col_status = st.columns([1, 3, 2])

    with col_logo:
        render_logo(align="left", max_width="150px", margin_bottom="0px", padding_top="0px")

    with col_title:
        st.markdown("""
            <div>
                <div class="header-title">LINTAS SHUTTLE</div>
                <div class="header-subtitle">Sistem Informasi Operasional Feeder</div>
            </div>
        """, unsafe_allow_html=True)

    with col_status:
        st.markdown(f"""
            <div class="status-text">
                <div><span class="badge badge-active">SISTEM AKTIF</span></div>
                <div style="font-size: 0.6rem; color: #8B949E; margin-top: 4px;">{tanggal_str} | {waktu_str} WIB</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)

    # 3. QUICK ACCESS MODUL
    col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns([1.8, 1.8, 1.8, 1.8, 1.2])

    with col_m1:
        if st.button("🚪 PORTAL LINTAS", use_container_width=True):
            st.switch_page("pages/1_Portal_Lintas.py")

    with col_m2:
        if st.button("📡 CHECKPOINT KM72", use_container_width=True):
            st.switch_page("pages/2_Checkpoint_KM72.py")

    with col_m3:
        if st.button("🎯 PASTEUR DROP POINT", use_container_width=True):
            st.switch_page("pages/3_Pasteur_Drop_Point.py")

    with col_m4:
        if st.button("📊 LAPORAN", use_container_width=True):
            st.switch_page("pages/4_Laporan.py")

    with col_m5:
        if st.button("🔄 REFRESH", use_container_width=True, type="primary"):
            st.cache_data.clear() 
            st.rerun()

    st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)

    # 4. EXECUTIVE HUD PANEL (TOP HIGH-LEVEL METRICS)
    if dashboard_data:
        m = dashboard_data["metrics"]
        cols = st.columns(4)
        
        with cols[0]:
            st.markdown(f"""
                <div class='compact-card'>
                    <div class='card-label'>🚚 TOTAL ARMADA AKTIF</div>
                    <div class='card-value'>{m['total_armada']} UNIT</div>
                </div>
            """, unsafe_allow_html=True)
        
        with cols[1]:
            pax_color = "#FFC400" if m['penumpang_menunggu'] > 10 else "#00E5FF"
            st.markdown(f"""
                <div class='compact-card'>
                    <div class='card-label'>👥 PAX MENUNGGU DI PDP</div>
                    <div class='card-value' style='color: {pax_color};'>{m['penumpang_menunggu']} PAX</div>
                </div>
            """, unsafe_allow_html=True)
        
        with cols[2]:
            st.markdown(f"""
                <div class='compact-card'>
                    <div class='card-label'>⏱️ RATA-RATA WAKTU TUNGGU</div>
                    <div class='card-value'>{m['rata_waktu_tunggu']} MIN</div>
                </div>
            """, unsafe_allow_html=True)
        
        with cols[3]:
            wt_max_color = "#FF1744" if m['wt_terlama'] >= 30 else "#00E676"
            st.markdown(f"""
                <div class='compact-card' style='border-left: 3px solid {wt_max_color};'>
                    <div class='card-label'>🚨 WAKTU TUNGGU TERLAMA</div>
                    <div class='card-value' style='color: {wt_max_color};'>{m['wt_terlama']} MIN</div>
                </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom: 1.5rem;'></div>", unsafe_allow_html=True)

    # 5. LIVE TRANSIT PIPELINE
    st.markdown('<div class="section-header"><span class="section-title">📡 LIVE TRANSIT FLOW</span></div>', unsafe_allow_html=True)

    pipe_col1, pipe_col2, pipe_col3 = st.columns(3)

    with pipe_col1:
        st.markdown("<div style='font-size: 0.65rem; color: #00E5FF; font-weight: 700; margin-bottom: 5px;'>[ 1 ] BARU BERANGKAT</div>", unsafe_allow_html=True)
        if dashboard_data and dashboard_data['departure_data']:
            for unit in dashboard_data['departure_data'][:4]:
                st.markdown(f"""
                    <div class='row-item' style='border-left-color: #00E5FF;'>
                        <div style='display: flex; justify-content: space-between;'>
                            <span><b>{unit['unit']}</b> - {unit['tujuan']}</span>
                            <span class='badge badge-info'>{unit['waktu']}</span>
                        </div>
                        <div style='font-size: 0.65rem; color: #8B949E;'>Driver: {unit['driver']}</div>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.caption("📭 Tidak ada unit yang baru berangkat")

    with pipe_col2:
        st.markdown("<div style='font-size: 0.65rem; color: #FFC400; font-weight: 700; margin-bottom: 5px;'>[ 2 ] KELUAR DARI CHECKPOINT KM72</div>", unsafe_allow_html=True)
        if dashboard_data and dashboard_data['checkout_data']:
            for unit in dashboard_data['checkout_data'][:4]:
                st.markdown(f"""
                    <div class='row-item' style='border-left-color: #FFC400;'>
                        <div style='display: flex; justify-content: space-between;'>
                            <span><b>{unit['unit']}</b></span>
                            <span class='badge badge-warning'>{unit['waktu']}</span>
                        </div>
                        <div style='font-size: 0.65rem; color: #8B949E;'>Driver: {unit['driver']}</div>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.caption("📭 Belum ada unit yang keluar dari Km72")

    with pipe_col3:
        st.markdown("<div style='font-size: 0.65rem; color: #00E676; font-weight: 700; margin-bottom: 5px;'>[ 3 ] TIBA DI PDP (TERKINI)</div>", unsafe_allow_html=True)
        if dashboard_data and dashboard_data['arrived_data']:
            for p in dashboard_data['arrived_data'][:4]:
                st.markdown(f"""
                    <div class='row-item' style='border-left-color: #00E676;'>
                        <div style='display: flex; justify-content: space-between;'>
                            <span><b>{p['unit']}</b> - Dari {p['asal']}</span>
                            <span class='badge badge-active'>{p['waktu']}</span>
                        </div>
                        <div style='font-size: 0.65rem; color: #8B949E;'>{p['pax']} Penumpang</div>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.caption("📭 Belum ada unit yang tiba")

    st.markdown("<div style='margin-bottom: 1.5rem;'></div>", unsafe_allow_html=True)

    # 6. ANALYTICS PANEL
    an_col1, an_col2 = st.columns([1.2, 1])

    with an_col1:
        st.markdown('<div class="section-header"><span class="section-title">📊 PENUMPANG MENUNGGU PER TUJUAN</span></div>', unsafe_allow_html=True)
        if dashboard_data:
            m = dashboard_data["metrics"]
            destinations = [
                {"name": "MIM / BUAHBATU", "pax": m['pax_mim'], "color": "#00E5FF"},
                {"name": "KOPO", "pax": m['pax_kopo'], "color": "#FFC400"},
                {"name": "JATINANGOR", "pax": m['pax_jtn'], "color": "#9D4EDD"},
            ]
            max_pax = max(m['pax_mim'], m['pax_kopo'], m['pax_jtn'], 1)
            
            for dest in destinations:
                percentage = int((dest['pax'] / max_pax) * 100) if max_pax > 0 else 0
                st.markdown(f"""
                    <div style='margin-bottom: 0.6rem;'>
                        <div style='display: flex; justify-content: space-between; font-size: 0.7rem;'>
                            <span>{dest['name']}</span>
                            <span style='color: {dest["color"]}; font-weight: 700;'>{dest['pax']} PAX</span>
                        </div>
                        <div class='progress-bar-bg'>
                            <div class='progress-bar-fill' style='width: {percentage}%; background: {dest["color"]};'></div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

    with an_col2:
        st.markdown('<div class="section-header"><span class="section-title">📈 ANALISIS WAKTU TUNGGU</span></div>', unsafe_allow_html=True)
        if dashboard_data:
            m = dashboard_data["metrics"]
            st.markdown(f"""
                <div style='background: rgba(21, 23, 28, 0.4); border: 1px solid rgba(255,255,255,0.05); padding: 12px; border-radius: 6px; font-size: 13px;'>
                    <div style='display: flex; justify-content: space-between; margin-bottom: 8px;'>
                        <span style='color: #8B949E;'>Rata-rata Waktu Tunggu:</span>
                        <strong style='color: #F8F9FA;'>{m['rata_waktu_tunggu']} Menit</strong>
                    </div>
                    <div style='display: flex; justify-content: space-between; margin-bottom: 8px;'>
                        <span style='color: #8B949E;'>Durasi Tunggu Terendah:</span>
                        <strong style='color: #00E676;'>{m['wt_tercepat']} Menit</strong>
                    </div>
                    <div style='display: flex; justify-content: space-between;'>
                        <span style='color: #8B949E;'>Durasi Tunggu Terlama:</span>
                        <strong style='color: #FF1744;'>{m['wt_terlama']} Menit</strong>
                    </div>
                </div>
            """, unsafe_allow_html=True)

    # 7. FOOTER
    st.markdown(f"""
        <div style='margin-top: 1.5rem; padding: 0.5rem 0; border-top: 1px solid rgba(255,255,255,0.05); text-align: center; font-size: 0.6rem; color: #5A6573;'>
            Terakhir diperbarui: {waktu_wib} | Auto-refresh 3 menit | PDP TRANSIT SYSTEM
        </div>
    """, unsafe_allow_html=True)

# ============================================================================
# JALANKAN DASHBOARD
# ============================================================================
live_command_center_board()
