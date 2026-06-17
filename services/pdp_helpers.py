# services/pdp_helpers.py
"""
Helper functions untuk modul Pasteur Drop Point (PDP)
"""

import streamlit as st
from db_utils import get_waktu_wib

def render_muatan_html(trip_id: str, semua_data: list) -> str:
    """
    Menampilkan muatan (PAX dan Paket) dalam format HTML.
    Digunakan di card Kanban PDP.
    """
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
    if p_mim > 0: 
        pax_parts.append(f"MIM/BBT: <b style='color: #00E5FF; font-weight:800; font-size:14px;'>{p_mim}</b>")
    if p_kopo > 0: 
        pax_parts.append(f"KOPO: <b style='color: #00E5FF; font-weight:800; font-size:14px;'>{p_kopo}</b>")
    if p_jtn > 0: 
        pax_parts.append(f"JTN: <b style='color: #00E5FF; font-weight:800; font-size:14px;'>{p_jtn}</b>")
    
    pkt_parts = []
    if pkt_dago > 0: 
        pkt_parts.append(f"DGO: <b style='color: #FFC400; font-weight:800; font-size:14px;'>{pkt_dago}</b>")
    if pkt_pdp > 0: 
        pkt_parts.append(f"PDP: <b style='color: #FFC400; font-weight:800; font-size:14px;'>{pkt_pdp}</b>")
    if pkt_mim > 0: 
        pkt_parts.append(f"MIM: <b style='color: #FFC400; font-weight:800; font-size:14px;'>{pkt_mim}</b>")
    if pkt_bbt > 0: 
        pkt_parts.append(f"BBT: <b style='color: #FFC400; font-weight:800; font-size:14px;'>{pkt_bbt}</b>")
    if pkt_kopo > 0: 
        pkt_parts.append(f"KOPO: <b style='color: #FFC400; font-weight:800; font-size:14px;'>{pkt_kopo}</b>")
    if pkt_jtn > 0: 
        pkt_parts.append(f"JTN: <b style='color: #FFC400; font-weight:800; font-size:14px;'>{pkt_jtn}</b>")
    
    html_output = "<div style='margin-top: 8px; padding-top: 8px; border-top: 1px solid rgba(255,255,255,0.1);'>"
    
    if pax_parts:
        html_output += f"<div class='nt-meta' style='color: #F8F9FA; margin-bottom: 4px;'>PAX: {' <b style=\"color: #334155; font-weight: normal;\">|</b> '.join(pax_parts)}</div>"
    if pkt_parts:
        html_output += f"<div class='nt-meta' style='color: #F8F9FA;'>PKT: {' <b style=\"color: #334155; font-weight: normal;\">|</b> '.join(pkt_parts)}</div>"
        
    if not pax_parts and not pkt_parts:
        html_output += "<div class='nt-meta' style='text-align:center; color: #8B949E;'>[ MUATAN KOSONG ]</div>"
        
    html_output += "</div>"
    return html_output


def add_activity_log(pesan: str, activity_log: list) -> list:
    """
    Menambahkan pesan ke activity log.
    Returns list baru yang sudah diupdate.
    """
    waktu = get_waktu_wib().strftime("%H:%M:%S")
    new_entry = f"<span style='color: #8B949E;'>[{waktu}]</span> {pesan}"
    
    # Insert di awal
    new_log = [new_entry] + activity_log
    
    # Batasi maksimal 50 entry (dari 10)
    return new_log[:50]


def render_activity_log_panel(activity_log: list):
    """
    Render activity log panel di sidebar atau expander.
    """
    log_html = "<div style='background: #0D0E12; border: 1px solid rgba(255,255,255,0.1); border-radius: 4px; padding: 12px; height: 200px; overflow-y: auto; font-family: monospace; font-size: 12px; line-height: 1.5;'>"
    if not activity_log:
        log_html += "<span style='color: #8B949E;'>Sistem bersiap. Belum ada aktivitas terekam pada sesi ini.</span>"
    else:
        for msg in activity_log:
            log_html += f"<div>{msg}</div>"
    log_html += "</div>"
    return log_html


def calculate_warning_level(wt_tertinggi: int) -> dict:
    """
    Menghitung level warning berdasarkan waktu tunggu tertinggi.
    Returns dict dengan keys: level, color, message
    """
    if wt_tertinggi >= 45:
        return {"level": "critical", "color": "#FF1744", "message": "🚨 CRITICAL OVERDUE"}
    elif wt_tertinggi >= 30:
        return {"level": "warning", "color": "#FFC400", "message": "⚠️ OVERDUE ALERT"}
    elif wt_tertinggi >= 15:
        return {"level": "notice", "color": "#00E5FF", "message": "⏳ MENDEKATI SLA"}
    else:
        return {"level": "normal", "color": "#00E676", "message": "✓ DALAM BATAS NORMAL"}
