import streamlit as st
import base64
import time

from components.ui_styles import apply_neo_tokyo_corporate, render_neo_tokyo_header
from components.navbar import render_navbar
from core.auth import require_auth
from db_utils import get_waktu_wib, fetch_mapped_data, safe_update_by_uuid, execute_batch_update_by_uuid
from services.data_pipeline import proses_kanban_pdp
from services.engine_kalkulasi import hitung_wt
from core.logger import setup_logger

log = setup_logger("SYSTEM_PDP")

st.set_page_config(page_title="PASTEUR DROP POINT", layout="wide")
apply_neo_tokyo_corporate()
require_auth(module_name="pdp", secret_dict_name="users_pdp")
render_navbar("pdp")

# ========== LOGO LINTAS ==========
try:
    with open("assets/logo.png", "rb") as img_file:
        img_b64 = base64.b64encode(img_file.read()).decode()
    st.markdown(f"""
        <div style='display: flex; justify-content: flex-start; align-items: center; margin-bottom: 5px; width: 100%; padding-top: 10px;'>
            <img src='data:image/png;base64,{img_b64}' style='max-width: 140px; height: auto; object-fit: contain; filter: drop-shadow(0 0 10px rgba(255,255,255,0.1));'>
        </div>
    """, unsafe_allow_html=True)
except FileNotFoundError:
    pass

# ========== INIT STATE ==========
if 'reset_form_feeder' not in st.session_state: 
    st.session_state.reset_form_feeder = 0

if 'modal_sedang_terbuka' not in st.session_state:
    st.session_state.modal_sedang_terbuka = False

# 🚀 INIT STATE: ACTIVITY LOG (JEJAK AUDIT)
if 'activity_log' not in st.session_state:
    st.session_state.activity_log = []

def add_activity_log(pesan: str):
    """Menambahkan jejak audit ke dalam Terminal Log (Maksimal 10 log terakhir)"""
    waktu = get_waktu_wib().strftime("%H:%M:%S")
    st.session_state.activity_log.insert(0, f"<span style='color: #8B949E;'>[{waktu}]</span> {pesan}")
    if len(st.session_state.activity_log) > 10:
        st.session_state.activity_log.pop()

# ============================================================
# 🛠️ HELPER ENGINE: DYNAMIC MUATAN (WARNA ABSOLUT)
# ==========================================
def render_dynamic_muatan_html(trip_id: str, semua_data: list) -> str:
    row = next((r for r in semua_data if r.get('trip_id') == trip_id), {})
    
    p_mim = row.get('pax_mim', 0)
    p_kopo = row.get('pax_kopo', 0)
    p_jtn = row.get('pax_jtn', 0)
    
    pkt_dago = row.get('paket_dago', 0)
    pkt_pdp = row.get('paket_pdp', 0)
    pkt_mim = row.get('paket_mim', 0)
    pkt_bbt = row.get('paket_bbt', 0)
    pkt_kopo = row.get('paket_kopo', 0)
    pkt_jtn = row.get('paket_jtn', 0)
    
    pax_parts = []
    if p_mim > 0: pax_parts.append(f"MIM: <b style='color: #00E5FF; font-weight:800; font-size:14px;'>{p_mim}</b>")
    if p_kopo > 0: pax_parts.append(f"KOPO: <b style='color: #00E5FF; font-weight:800; font-size:14px;'>{p_kopo}</b>")
    if p_jtn > 0: pax_parts.append(f"JTN: <b style='color: #00E5FF; font-weight:800; font-size:14px;'>{p_jtn}</b>")
    
    pkt_parts = []
    if pkt_dago > 0: pkt_parts.append(f"DGO: <b style='color: #FFC400; font-weight:800; font-size:14px;'>{pkt_dago}</b>")
    if pkt_pdp > 0: pkt_parts.append(f"PDP: <b style='color: #FFC400; font-weight:800; font-size:14px;'>{pkt_pdp}</b>")
    if pkt_mim > 0: pkt_parts.append(f"MIM: <b style='color: #FFC400; font-weight:800; font-size:14px;'>{pkt_mim}</b>")
    if pkt_bbt > 0: pkt_parts.append(f"BBT: <b style='color: #FFC400; font-weight:800; font-size:14px;'>{pkt_bbt}</b>")
    if pkt_kopo > 0: pkt_parts.append(f"KOPO: <b style='color: #FFC400; font-weight:800; font-size:14px;'>{pkt_kopo}</b>")
    if pkt_jtn > 0: pkt_parts.append(f"JTN: <b style='color: #FFC400; font-weight:800; font-size:14px;'>{pkt_jtn}</b>")
    
    html_output = "<div style='margin-top: 8px; padding-top: 8px; border-top: 1px solid rgba(255,255,255,0.1);'>"
    
    if pax_parts:
        html_output += f"<div class='nt-meta' style='color: #F8F9FA; margin-bottom: 4px;'>PAX: {' <b style=\"color: #334155; font-weight: normal;\">|</b> '.join(pax_parts)}</div>"
    if pkt_parts:
        html_output += f"<div class='nt-meta' style='color: #F8F9FA;'>PKT: {' <b style=\"color: #334155; font-weight: normal;\">|</b> '.join(pkt_parts)}</div>"
        
    if not pax_parts and not pkt_parts:
        html_output += "<div class='nt-meta' style='text-align:center; color: #8B949E;'>[ MUATAN KOSONG ]</div>"
        
    html_output += "</div>"
    return html_output

# ==========================================
# 🛑 MODAL DIALOG: GLOBAL DISPATCH FEEDER
# ==========================================
@st.dialog("KEBERANGKATAN FEEDER", width="medium")
def render_global_dispatch_modal():
    waktu_sekarang = get_waktu_wib()
    semua_data = fetch_mapped_data()
    if semua_data is None:
        st.error("GAGAL MENARIK DATA DARI SERVER.")
        return
        
    data_kanban = proses_kanban_pdp(semua_data, waktu_sekarang)
    grup_tujuan = data_kanban["grup_tujuan"]
    
    tujuan_target = st.selectbox("RUTE FEEDER", ["MIM / BUAHBATU", "KOPO", "JATINANGOR"])
    st.divider()
    
    armada_ready = grup_tujuan[tujuan_target]
    list_armada = [item['label'] for item in armada_ready]
    
    if not list_armada:
        st.warning(f"TIDAK ADA ANTRIAN UNTUK RUTE {tujuan_target}.")
        return

    pilihan_massal = st.multiselect(
        f"PILIH PENUMPANG (TUJUAN {tujuan_target})", 
        options=list_armada,
        key=f"sel_global_{st.session_state.reset_form_feeder}"
    )
    
    # 🚀 MODAL CALCULATOR
    if pilihan_massal:
        total_pax_terpilih = sum(next(item['pax_count'] for item in armada_ready if item['label'] == p) for p in pilihan_massal)
        if total_pax_terpilih <= 14:
            st.markdown(f"<div style='background: rgba(0, 230, 118, 0.1); border: 1px solid #00E676; padding: 8px 12px; border-radius: 4px; color: #00E676; font-weight: 700; font-size: 13px; margin-bottom: 15px;'>📊 TOTAL MUATAN TERPILIH: {total_pax_terpilih} PAX (KAPASITAS AMAN)</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='background: rgba(255, 23, 68, 0.1); border: 1px solid #FF1744; padding: 8px 12px; border-radius: 4px; color: #FF1744; font-weight: 700; font-size: 13px; margin-bottom: 15px;'>🚨 TOTAL MUATAN TERPILIH: {total_pax_terpilih} PAX (MELEBIHI KAPASITAS HIACE 14 PAX!)</div>", unsafe_allow_html=True)
    
    kunci_drv = f"drv_g_{st.session_state.reset_form_feeder}"
    kunci_npl = f"npl_g_{st.session_state.reset_form_feeder}"
    kunci_cat = f"cat_g_{st.session_state.reset_form_feeder}"
    
    if kunci_drv not in st.session_state: st.session_state[kunci_drv] = ""
    if kunci_npl not in st.session_state: st.session_state[kunci_npl] = ""
    if kunci_cat not in st.session_state: st.session_state[kunci_cat] = ""

    c1, c2 = st.columns(2)
    with c1: 
        st.text_input("NAMA DRIVER FEEDER", key=kunci_drv)
        drv_f = st.session_state[kunci_drv].upper()
    with c2: 
        st.text_input("NOPOL FEEDER", placeholder="CONTOH: D 4321 XYZ", key=kunci_npl)
        nopol_f = st.session_state[kunci_npl].upper()
    
    with st.expander("CATATAN KETERLAMBATAN (OPSIONAL)"):
        st.text_input(
            "ALASAN KETERLAMBATAN", placeholder="WAJIB DIISI JIKA MELEWATI SLA", 
            label_visibility="collapsed", key=kunci_cat
        )
        catatan_f = st.session_state[kunci_cat]
        
    st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
    
    if 'sedang_dispatch' not in st.session_state:
        st.session_state.sedang_dispatch = False

    if st.button(f"BERANGKATKAN FEEDER", use_container_width=True, type="primary", disabled=st.session_state.sedang_dispatch):
        ada_pelanggaran = any(hitung_wt(next(i['jam_tiba'] for i in armada_ready if i['label'] == p), waktu_sekarang) >= 30 for p in pilihan_massal)
        
        if not pilihan_massal or not drv_f.strip() or not nopol_f.strip():
            st.error("VALIDASI GAGAL: LENGKAPI NAMA DRIVER, NOPOL, DAN MINIMAL 1 UNIT PILIHAN.")
        elif ada_pelanggaran and not catatan_f.strip():
            st.error("PERINGATAN KRITIS: WAKTU TUNGGU MELEBIHI SLA. CATATAN WAJIB DIISI.")
        else:
            st.session_state.sedang_dispatch = True
            with st.spinner("Sinkronisasi enkripsi manifes..."):
                jam_out = waktu_sekarang.strftime("%H:%M")
                
                map_kolom = {
                    "MIM / BUAHBATU": ["driver_mim_buahbatu", "nopol_mim_buahbatu", "mim_bbt_out", "wt_mim_bbt"],
                    "KOPO": ["driver_kopo", "nopol_kopo", "kopo_out", "wt_kopo"],
                    "JATINANGOR": ["driver_jtn", "nopol_jtn", "jtn_out", "wt_jtn"]
                }[tujuan_target]
                
                c_drv, c_nopol, c_jam, c_wt = map_kolom
                uuid_updates = []
                
                for p in pilihan_massal:
                    target_data = next(item for item in armada_ready if item['label'] == p)
                    wt_val = hitung_wt(target_data['jam_tiba'], waktu_sekarang)
                    
                    dict_update = {
                        c_drv: drv_f.strip(), 
                        c_nopol: nopol_f.strip(), 
                        c_jam: jam_out, 
                        c_wt: wt_val
                    }
                    if catatan_f.strip(): 
                        dict_update["keterangan"] = catatan_f.strip() 
                        
                    uuid_updates.append({"trip_id": target_data['trip_id'], "updates": dict_update})
                        
                if uuid_updates:
                    sukses, pesan = execute_batch_update_by_uuid(uuid_updates)
                    if sukses:
                        petugas = st.session_state.get('petugas_pdp', 'Unknown')
                        log.info(f"DISPATCH: Petugas {petugas} memberangkatkan Feeder {nopol_f} ({drv_f}) rute {tujuan_target}.")
                    
                        st.toast(f"FEEDER {tujuan_target} BERHASIL DIBERANGKATKAN")
                        
                        # 🚀 INJEKSI KE ACTIVITY LOG
                        add_activity_log(f"<span style='color: #00E676; font-weight: bold;'>[DISPATCH]</span> Feeder <b>{nopol_f}</b> ({tujuan_target}) berhasil diberangkatkan membawa {total_pax_terpilih} PAX.")
                        
                        st.session_state.reset_form_feeder += 1 
                        fetch_mapped_data.clear()
                        st.session_state.sedang_dispatch = False
                        st.session_state["modal_sedang_terbuka"] = False
                        st.rerun()            
                    else:
                        st.session_state.sedang_dispatch = False
                        st.error(f"TRANSMISI GAGAL: {pesan}")

# ==========================================
# 🎨 UI HEADER STATIC & GLOBAL ACTIONS
# ==========================================
col_judul, col_spacer, col_dispatch, col_sync = st.columns([4.5, 1.0, 2.0, 1.2], vertical_alignment="bottom")
with col_judul:
    render_neo_tokyo_header(
        title="PASTEUR DROP POINT", 
        subtitle=f"SISTEM TRANSIT & FEEDER | USER: {st.session_state.get('petugas_pdp', 'UNKNOWN')}", 
        accent="var(--nt-violet)",
        align="left"
    )

with col_dispatch:
    if st.button("BERANGKATKAN FEEDER", type="primary", use_container_width=True):
        st.session_state["modal_sedang_terbuka"] = True
        render_global_dispatch_modal()
        
with col_sync:
    if st.button("REFRESH", use_container_width=True): 
        st.session_state["modal_sedang_terbuka"] = False
        fetch_mapped_data.clear()
        st.rerun()            

st.divider()

# 🚀 TACTICAL FILTER BAR & ACTIVITY LOG
cf1, cf2 = st.columns([3, 1])
with cf1:
    search_input = st.text_input("PENCARIAN KANBAN", placeholder="Ketik Nopol atau Nama Driver...", label_visibility="collapsed")
with cf2:
    st.markdown("<div style='color: #8B949E; font-size: 11px; margin-top: 10px; text-align: right;'><i>STATUS: AUTO-SYNC (30s)</i></div>", unsafe_allow_html=True)

# 🚀 RENDER TERMINAL ACTIVITY LOG (JEJAK AUDIT)
with st.expander("HISTORY ACTIVITY (10 Aktivitas Terakhir)", expanded=False):
    log_html = "<div style='background: #0D0E12; border: 1px solid rgba(255,255,255,0.1); border-radius: 4px; padding: 12px; height: 160px; overflow-y: auto; font-family: monospace; font-size: 13px; line-height: 1.6;'>"
    if not st.session_state.activity_log:
        log_html += "<span style='color: #8B949E;'>Sistem bersiap. Belum ada aktivitas terekam pada sesi ini.</span>"
    else:
        for msg in st.session_state.activity_log:
            log_html += f"<div>{msg}</div>"
    log_html += "</div>"
    st.markdown(log_html, unsafe_allow_html=True)

st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)

# ==========================================
# ⚡ STREAMLIT FRAGMENT (Auto Data Engine)
# ==========================================
@st.fragment(run_every=30)
def live_dashboard_board():
    waktu_sekarang = get_waktu_wib()
    semua_data = fetch_mapped_data()
    
    if semua_data is None:
        st.error("KONEKSI DATABASE TERPUTUS. SILAKAN CEK JARINGAN.")
        return

    data_kanban = proses_kanban_pdp(semua_data, waktu_sekarang)
    
    if data_kanban["auto_selesai_updates"]:
        sukses, _ = execute_batch_update_by_uuid(data_kanban["auto_selesai_updates"])
        if sukses: 
            fetch_mapped_data.clear()
            if not st.session_state.get("modal_sedang_terbuka", False):
                st.rerun() 

    # TERAPKAN FILTER PENCARIAN
    q_lower = search_input.lower()
    armada_portal_kiri = [u for u in data_kanban["portal_kiri"] if q_lower in u['nopol'].lower() or q_lower in u['driver'].lower()]
    armada_km72_tengah = [u for u in data_kanban["km72_tengah"] if q_lower in u['nopol'].lower() or q_lower in u['driver'].lower()]
    monitor_antrean = [u for u in data_kanban["monitor_antrean"] if q_lower in u['nopol'].lower() or q_lower in u['driver'].lower()]
    
    grup_tujuan = data_kanban["grup_tujuan"]
    total_pax_antre = data_kanban["total_pax"]

    # --- METRICS PANEL ---
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.metric("MENUJU KM72", len(armada_portal_kiri))
    with m2: st.metric("MENUJU PDP (OUT KM72)", len(armada_km72_tengah))
    
    wt_list = [hitung_wt(item['jam_tiba'], waktu_sekarang) for tj in grup_tujuan for item in grup_tujuan[tj]]
    wt_tertinggi = max(wt_list) if wt_list else 0
    with m3: 
        st.metric("MAX WAKTU TUNGGU", f"{wt_tertinggi} MNT", delta="OVERDUE" if wt_tertinggi >= 30 else "STANDBY", delta_color="inverse")
    with m4:
        total_semua = sum(total_pax_antre.values())
        st.metric("TOTAL PAX ANTRIAN", f"{total_semua} PAX", delta="MENUNGGU FEEDER" if total_semua > 0 else "CLEAR", delta_color="normal")

    st.markdown("<hr style='margin: 15px 0 25px 0; border-color: rgba(255,255,255,0.08);'>", unsafe_allow_html=True)

    col_kiri, col_tengah, col_kanan = st.columns([1, 1, 1.4])

    # ==========================================
    # KIRI: KEBERANGKATAN
    # ==========================================
    with col_kiri:
        st.markdown("<div class='nt-meta' style='text-align: center; margin-bottom: 16px; color: #F8F9FA; border-bottom: 2px solid #8B949E; padding-bottom: 8px;'>[ 01 ] KEBERANGKATAN</div>", unsafe_allow_html=True)
        
        if not armada_portal_kiri:
            st.info("BELUM ADA UNIT BERANGKAT")
        else:
            with st.container(height=580, border=False):
                for unit in armada_portal_kiri:
                    with st.container(border=True):
                        muatan_html = render_dynamic_muatan_html(unit['trip_id'], semua_data)
                        st.markdown(f"""
                        <div class='nt-nopol' style='color: #F8F9FA;'>{unit['nopol']}</div>
                        <div class='nt-meta' style='color: #8B949E; margin-top: 4px;'>
                            {unit['rute']} <b style='color: #334155; font-weight: normal; margin: 0 6px;'>|</b> JAM: <b style='color: #00E5FF; font-weight: 800; font-size: 13px;'>{unit['jadwal']} WIB</b>
                        </div>
                        <div class='nt-meta' style='color: #8B949E; margin-top: 4px;'>DRIVER: {unit['driver']}</div>
                        {muatan_html}
                        """, unsafe_allow_html=True)

    # ==========================================
    # TENGAH: CHECKOUT KM72
    # ==========================================
    with col_tengah:
        st.markdown("<div class='nt-meta' style='text-align: center; margin-bottom: 16px; color: #00E5FF; border-bottom: 2px solid #00E5FF; padding-bottom: 8px;'>[ 02 ] CHECKOUT KM72</div>", unsafe_allow_html=True)
        
        if not armada_km72_tengah:
            st.info("TIDAK ADA UNIT KELUAR KM72")
        else:
            with st.container(height=580, border=False):
                if 'sedang_tiba_pdp' not in st.session_state:
                    st.session_state.sedang_tiba_pdp = False

                for unit in armada_km72_tengah:
                    with st.container(border=True): 
                        muatan_html = render_dynamic_muatan_html(unit['trip_id'], semua_data)
                        st.markdown(f"""
                        <div class='nt-nopol' style='color: #F8F9FA;'>{unit['nopol']}</div>
                        <div class='nt-meta' style='color: #8B949E; margin-top: 4px;'>
                            {unit['rute']} <b style='color: #334155; font-weight: normal; margin: 0 6px;'>|</b> JAM: <b style='color: #00E5FF; font-weight: 800; font-size: 13px;'>{unit['jadwal']} WIB</b>
                        </div>
                        <div class='nt-meta' style='color: #8B949E; margin-top: 4px;'>DRIVER: {unit['driver']}</div>
                        <div class='nt-meta' style='margin-top: 8px; color: #F8F9FA;'>
                            OUT KM72: <b style='color: #00E5FF; font-weight: 800; font-size: 13px;'>{unit['jam_72']}</b>
                        </div>
                        {muatan_html}
                        """, unsafe_allow_html=True)
                        
                        st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
                        if st.button("TIBA DI PDP", key=f"tiba_{unit['trip_id']}", use_container_width=True, disabled=st.session_state.sedang_tiba_pdp):
                            st.session_state.sedang_tiba_pdp = True
                            with st.spinner("Proses..."):
                                waktu_tiba = get_waktu_wib().strftime("%H:%M")
                                sukses, pesan = safe_update_by_uuid(unit['trip_id'], {"jam_tiba_pdp": waktu_tiba})
                                if sukses:
                                    # 🚀 INJEKSI KE ACTIVITY LOG
                                    add_activity_log(f"<span style='color: #00E5FF; font-weight: bold;'>[TIBA]</span> Unit <b>{unit['nopol']}</b> ({unit['rute']}) telah tiba di PDP.")
                                    
                                    fetch_mapped_data.clear()
                                    st.session_state.sedang_tiba_pdp = False
                                    if not st.session_state.get("modal_sedang_terbuka", False):
                                        st.rerun()
                                else:
                                    st.session_state.sedang_tiba_pdp = False
                                    st.error(pesan)

    # ==========================================
    # KANAN: WAKTU TUNGGU PDP
    # ==========================================
    with col_kanan:
        st.markdown("<div class='nt-meta' style='text-align: center; margin-bottom: 16px; color: #9D4EDD; border-bottom: 2px solid #9D4EDD; padding-bottom: 8px;'>[ 03 ] WAKTU TUNGGU PDP</div>", unsafe_allow_html=True)
        
        st.markdown(f"""
        <div style="display: flex; justify-content: space-between; border: 1px solid rgba(255,255,255,0.08); border-radius: 6px; padding: 12px; margin-bottom: 16px; background: #15171C;">
            <div style="text-align: center; flex: 1; border-right: 1px solid rgba(255,255,255,0.08);">
                <div class="nt-meta">MIM/BB</div>
                <div style="font-size: 20px; font-weight: 800; color: #F8F9FA;">{total_pax_antre['MIM / BUAHBATU']}</div>
            </div>
            <div style="text-align: center; flex: 1; border-right: 1px solid rgba(255,255,255,0.08);">
                <div class="nt-meta">KOPO</div>
                <div style="font-size: 20px; font-weight: 800; color: #F8F9FA;">{total_pax_antre['KOPO']}</div>
            </div>
            <div style="text-align: center; flex: 1;">
                <div class="nt-meta">JTN</div>
                <div style="font-size: 20px; font-weight: 800; color: #F8F9FA;">{total_pax_antre['JATINANGOR']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if not monitor_antrean:
            st.info("BELUM ADA UNIT ANTRIAN DI PDP")
        else:
            with st.container(height=480, border=False): 
                for unit in monitor_antrean:
                    is_overdue_card = any(p['is_overdue'] for p in unit.get('pax_details', []))
                    bg_style = "background: rgba(255, 23, 68, 0.05); border-color: rgba(255, 23, 68, 0.4);" if is_overdue_card else ""
                    
                    with st.container(border=True):
                        if bg_style: 
                            st.markdown(f"<style>[data-testid='stVerticalBlockBorderWrapper']:has(div.overdue-{unit['nopol'].replace(' ', '')}) {{ {bg_style} }}</style>", unsafe_allow_html=True)
                            st.markdown(f"<div class='overdue-{unit['nopol'].replace(' ', '')}'></div>", unsafe_allow_html=True)

                        pax_info_html = ""
                        for pax in unit.get('pax_details', []):
                            tj = pax['tujuan']
                            pax_count = pax['jumlah']
                            wt = pax['waktu_tunggu']
                            
                            if pax['is_overdue']:
                                badge = f"<b style='color:#FF1744; font-weight:800; text-shadow: 0 0 8px rgba(255, 23, 68, 0.4); float:right;'>[{wt} MNT - OVERDUE]</b>"
                            else:
                                badge = f"<b style='color:#FFC400; font-weight:700; float:right;'>[{wt} MNT]</b>"
                                
                            pax_info_html += f"<div style='margin-bottom: 6px; border-left: 2px solid rgba(255,255,255,0.08); padding-left: 8px;'><span class='nt-meta'>{tj}:</span> <b style='color:#00E5FF; font-size: 14px;'>{pax_count} PAX</b> {badge}</div>"

                        st.markdown(f"""
                        <div style="display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 1px dashed rgba(255,255,255,0.08); padding-bottom: 8px; margin-bottom: 8px;">
                            <div>
                                <div class='nt-meta' style="color: #ffffff; margin-bottom: 2px;">{unit['rute']}</div>
                                <div class='nt-nopol' style="font-size: 18px; color: #F8F9FA;">{unit['nopol']}</div>
                                <div class='nt-meta' style="color: #8B949E;">DRIVER: {unit['driver']}</div>
                            </div>
                            <div style="text-align: right;">
                                <div class="nt-meta" style="color: #8B949E;">TIBA PDP</div>
                                <div style="font-size: 14px; color: #00E5FF; font-weight: 800;">{unit['tiba']}</div>
                            </div>
                        </div>
                        <div>
                            {pax_info_html}
                        </div>
                        """, unsafe_allow_html=True)

live_dashboard_board()
