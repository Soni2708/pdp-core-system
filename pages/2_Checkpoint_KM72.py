import streamlit as st
from datetime import datetime

# Menggunakan arsitektur tema Neo-Tokyo yang baru
from components.ui_styles import apply_neo_tokyo_corporate, render_neo_tokyo_header, render_logo
from components.navbar import render_navbar
from core.auth import require_auth
from db_utils import get_waktu_wib, fetch_mapped_data, safe_update_by_uuid
from core.logger import setup_logger

log = setup_logger("RADAR_KM72")

# Konfigurasi halaman
st.set_page_config(page_title="CHECKPOINT KM72", layout="wide", initial_sidebar_state="collapsed")
apply_neo_tokyo_corporate()
require_auth(module_name="km72", secret_dict_name="users_km72")
render_navbar("km72")

# ========== INIT STATE ==========
if 'last_checkout' not in st.session_state:
    st.session_state.last_checkout = None  # Simpan nopol terakhir yang di-checkout

# ✅ TAMBAHAN CTO: State untuk menyembunyikan unit sementara di layar ini
if 'local_checkout' not in st.session_state:
    st.session_state.local_checkout = set()

# ========== LOGO LINTAS ==========
render_logo(align="left", margin_bottom="5px")

# ==========================================
# 🛑 MODAL DIALOG KONFIRMASI CHECKOUT
# ==========================================
@st.dialog("KONFIRMASI CHECKOUT KM72", width="small")
def confirm_checkout_dialog(unit):
    st.markdown(f"<div class='nt-nopol' style='text-align: center; font-size: 28px;'>{unit['nopol']}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='nt-meta' style='text-align: center; margin-bottom: 20px;'>DRIVER: {unit['driver']}</div>", unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        st.caption("RUTE")
        st.write(f"**{unit['rute']}**")
    with c2:
        st.caption("JADWAL")
        st.write(f"**{unit['jadwal']}**")
    
    st.warning("Tandai armada ini sudah KELUAR dari Checkpoint KM72?")
    
    st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
    col_yes, col_no = st.columns(2)
    with col_yes:
        if 'sedang_checkout' not in st.session_state:
            st.session_state.sedang_checkout = False
            
        if st.button("✅ KONFIRMASI", type="primary", use_container_width=True, disabled=st.session_state.sedang_checkout):
            st.session_state.sedang_checkout = True
            with st.spinner("Memproses..."):
                waktu_wib = get_waktu_wib().strftime("%H:%M")
                sukses, pesan = safe_update_by_uuid(unit['trip_id'], {"jam_keluar_km72": waktu_wib})
                
                if sukses:
                    # ✅ OPTIMISTIC UPDATE: Masukkan trip_id ke filter lokal
                    st.session_state.local_checkout.add(unit['trip_id'])
                    
                    # Simpan data checkout terakhir untuk highlight
                    st.session_state.last_checkout = {
                        "nopol": unit['nopol'],
                        "waktu": waktu_wib,
                        "trip_id": unit['trip_id']
                    }
                    log.info(f"CHECKOUT KM72: {unit['nopol']} ({waktu_wib}).")
                    st.toast(f"✅ {unit['nopol']} Berhasil Checkout", icon="✅")
                    
                    # ✅ REFACTOR CTO: Hapus fetch_mapped_data.clear()
                    st.session_state.sedang_checkout = False
                    st.rerun()
                else:
                    log.error(f"ERROR KM72: Gagal checkout {unit['nopol']}. Alasan: {pesan}")
                    st.error(f"❌ GAGAL: {pesan}")
                    st.session_state.sedang_checkout = False
    with col_no:
        if st.button("❌ BATAL", use_container_width=True):
            st.rerun()


# ==========================================
# 🎨 UI HEADER STATIC & STATUS CENTER (REDUX)
# ==========================================
col_judul, col_status = st.columns([3, 1.5])
with col_judul:
    render_neo_tokyo_header(
        title="CHECKPOINT KM72", 
        subtitle="Sistem Pemantauan Radar Perjalanan Armada", 
        accent="var(--nt-cyan)",
        align="left"
    )

with col_status:
    petugas_aktif = st.session_state.get('petugas_km72', 'UNKNOWN')
    waktu_sekarang_dt = get_waktu_wib()
    tanggal_str = waktu_sekarang_dt.strftime("%d %B %Y")
    waktu_str = waktu_sekarang_dt.strftime("%H:%M:%S")

    st.markdown(f"""
    <div style="text-align: right; margin-top: 5px;">
        <div style='display: inline-block; background: rgba(0, 229, 255, 0.05); border: 1px solid rgba(0, 229, 255, 0.2); padding: 4px 12px; border-radius: 4px; font-size: 11px; font-weight: 700; color: var(--nt-text-muted); margin-bottom: 10px;'>
            <span style='color: #00E676;'>●</span> USER ACTIVE: <span style='color: var(--nt-cyan); letter-spacing: 0.5px;'>{petugas_aktif}</span>
        </div>
        <div style="margin-top: 2px; margin-bottom: 8px;">
            <span style="background: rgba(0, 230, 118, 0.15); color: #00E676; padding: 4px 12px; border-radius: 20px; font-size: 10px; font-weight: 800; letter-spacing: 0.5px; border: 1px solid rgba(0, 230, 118, 0.3);">SISTEM AKTIF</span>
        </div>
        <div style="font-size: 11px; color: #8B949E; margin-bottom: 12px; font-weight: 500;">
            {tanggal_str} | <span style="color: #F8F9FA;">{waktu_str} WIB</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Tombol refresh diposisikan sejajar di bawah status informasi kanan
    if st.button("🔄 REFRESH", use_container_width=True, type="primary"): 
        fetch_mapped_data.clear() 
        st.session_state.last_checkout = None
        st.rerun() 

st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True) 

# ==========================================
# ⚡ STREAMLIT FRAGMENT (Auto Radar Engine)
# ==========================================
@st.fragment(run_every=180)
def radar_dashboard():
    semua_data = fetch_mapped_data()
    armada_aktif = []

    if semua_data:
        for row in semua_data:
            trip_id = str(row.get('trip_id', ''))
            
            # ✅ OPTIMISTIC FILTER: Lewati unit yang barusan di-checkout agar langsung hilang dari radar
            if trip_id in st.session_state.get('local_checkout', set()):
                continue
                
            status = str(row.get('status', '')).strip().upper()
            jam_72 = str(row.get('jam_72', '')) 
            
            if status == "IN TRANSIT" and not jam_72:
                armada_aktif.append({
                    "nopol": str(row.get('nopol', '')), 
                    "rute": str(row.get('rute', '')), 
                    "jadwal": str(row.get('jadwal', '')), 
                    "driver": str(row.get('driver', '')), 
                    "trip_id": str(row.get('trip_id', ''))
                })

    armada_aktif.sort(key=lambda x: x['jadwal'])

    # HUD BAR (Ringkasan Cepat)
    st.markdown(f"""
    <div style='background: var(--nt-bg-sec); padding: 10px 20px; border-radius: 6px; border: 1px solid var(--nt-border); margin-bottom: 25px; display: flex; align-items: center; justify-content: space-between;'>
        <div style='display: flex; align-items: center; gap: 20px;'>
            <div>
                <span style='font-size: 11px; font-weight: 600; color: var(--nt-text-muted); letter-spacing: 0.5px;'>UNIT MENUJU KM72:</span>
                <span style='font-size: 20px; font-weight: 800; color: var(--nt-cyan); margin-left: 8px;'>{len(armada_aktif)}</span>
            </div>
            <div>
                <span style='font-size: 11px; font-weight: 600; color: var(--nt-text-muted); letter-spacing: 0.5px;'>STATUS:</span>
                <span style='font-size: 13px; font-weight: 700; color: var(--nt-success); margin-left: 8px;'>● ONLINE</span>
            </div>
        </div>
        <div style='font-size: 10px; color: var(--nt-text-muted);'>
            <i>AUTO-REFRESH (3 MENIT)</i>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Tampilkan notifikasi jika ada checkout terakhir
    if st.session_state.last_checkout:
        st.success(f"✅ Checkout terakhir: **{st.session_state.last_checkout['nopol']}** pada pukul {st.session_state.last_checkout['waktu']} WIB")
        # Hapus notifikasi setelah 5 detik (akan hilang saat next rerun)

    # Tabel List View
    if not armada_aktif:
        st.info("📭 TIDAK ADA UNIT MENUJU KM72")
    else:
        # Header Tabel
        st.markdown("<div style='border-bottom: 1px solid var(--nt-border); margin-bottom: 8px;'></div>", unsafe_allow_html=True)
        h1, h2, h3, h4, h5 = st.columns([1, 1.5, 2, 1.8, 1], vertical_alignment="center")
        with h1: st.markdown("<div style='color: var(--nt-text-muted); font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;'>JADWAL</div>", unsafe_allow_html=True)
        with h2: st.markdown("<div style='color: var(--nt-text-muted); font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;'>NOPOL</div>", unsafe_allow_html=True)
        with h3: st.markdown("<div style='color: var(--nt-text-muted); font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;'>RUTE</div>", unsafe_allow_html=True)
        with h4: st.markdown("<div style='color: var(--nt-text-muted); font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;'>DRIVER</div>", unsafe_allow_html=True)
        with h5: st.markdown("<div style='text-align: right; color: var(--nt-text-muted); font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;'>ACTION</div>", unsafe_allow_html=True)
        st.markdown("<div style='border-bottom: 1px solid var(--nt-border); margin-bottom: 12px;'></div>", unsafe_allow_html=True)

        # Baris Data
        for idx, unit in enumerate(armada_aktif):
            # Highlight baris yang baru di-checkout
            is_highlight = st.session_state.last_checkout and st.session_state.last_checkout['trip_id'] == unit['trip_id']
            highlight_style = "background: rgba(0, 230, 118, 0.1); border-radius: 6px; padding: 8px 0; margin: 4px 0;" if is_highlight else ""
            
            if highlight_style:
                st.markdown(f"<div style='{highlight_style}'>", unsafe_allow_html=True)
            
            c1, c2, c3, c4, c5 = st.columns([1, 1.5, 2, 1.8, 1], vertical_alignment="center")
            
            with c1: 
                st.markdown(f"<div style='font-family: monospace; font-weight: 600; color: var(--nt-cyan); font-size: 15px;'>{unit['jadwal']}</div>", unsafe_allow_html=True)
            with c2: 
                st.markdown(f"<div style='font-size: 17px; font-weight: 800; color: #F8F9FA; letter-spacing: 0.5px;'>{unit['nopol']}</div>", unsafe_allow_html=True)
            with c3: 
                st.markdown(f"<div style='font-size: 14px; color: var(--nt-text-primary);'>{unit['rute']}</div>", unsafe_allow_html=True)
            with c4: 
                st.markdown(f"<div style='font-size: 14px; color: var(--nt-text-muted);'>{unit['driver'][:20]}</div>", unsafe_allow_html=True)
            with c5:
                if st.button("🚀 CHECKOUT", key=f"btn_{unit['trip_id']}", use_container_width=True, type="primary"):
                    confirm_checkout_dialog(unit)
            
            if highlight_style:
                st.markdown("</div>", unsafe_allow_html=True)
            
            # Garis pemisah antar baris
            st.markdown("<div style='border-bottom: 1px solid rgba(255,255,255,0.04); margin: 6px 0 10px 0;'></div>", unsafe_allow_html=True)

# Jalankan dashboard
radar_dashboard()
