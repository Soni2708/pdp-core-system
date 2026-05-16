from services.engine_kalkulasi import hitung_wt

def proses_kanban_pdp(semua_data, waktu_sekarang):
    hasil = {
        "portal_kiri": [],
        "km72_tengah": [],
        "monitor_antrean": [],
        "grup_tujuan": {"MIM / BUAHBATU": [], "KOPO": [], "JATINANGOR": []},
        "total_pax": {"MIM / BUAHBATU": 0, "KOPO": 0, "JATINANGOR": 0},
        "auto_selesai_updates": [],
        "jumlah_armada_jalan": 0
    }

    if not semua_data:
        return hasil

    for row in semua_data:
        status = str(row.get('status', '')).strip().upper()
        rute = str(row.get('rute', ''))
        nopol = str(row.get('nopol', ''))
        driver = str(row.get('driver', ''))
        jadwal = str(row.get('jadwal', ''))
        jam_72 = str(row.get('jam_72', ''))
        jam_tiba_pdp = str(row.get('jam_tiba_pdp', ''))
        baris_db = row.get('baris_db')
        trip_id = str(row.get('trip_id', ''))
        
        pax_mim = int(row.get('pax_mim', 0) if str(row.get('pax_mim', '')).isdigit() else 0)
        pax_kopo = int(row.get('pax_kopo', 0) if str(row.get('pax_kopo', '')).isdigit() else 0)
        pax_jtn = int(row.get('pax_jtn', 0) if str(row.get('pax_jtn', '')).isdigit() else 0)
        
        jam_out_mim = str(row.get('jam_out_mim', ''))
        jam_out_kopo = str(row.get('jam_out_kopo', ''))
        jam_out_jtn = str(row.get('jam_out_jtn', ''))

        if status != "IN TRANSIT":
            continue
        
        hasil["jumlah_armada_jalan"] += 1
        label_armada = f"[{rute}] {nopol}"

        pax_info = []
        semua_berangkat = False 
        ada_pax = False 

        # DISTRIBUSI KANBAN
        if jam_72 == "" and jam_tiba_pdp == "":
            hasil["portal_kiri"].append({
                "nopol": nopol, "driver": driver, "rute": rute, "jadwal": jadwal,
                "pax_mim": pax_mim, "pax_kopo": pax_kopo, "pax_jtn": pax_jtn,
                "baris_db": baris_db,
                "trip_id": trip_id
            })
            
        elif jam_72 != "" and jam_tiba_pdp == "":
            hasil["km72_tengah"].append({
                "nopol": nopol, "driver": driver, "rute": rute, "jadwal": jadwal,
                "pax_mim": pax_mim, "pax_kopo": pax_kopo, "pax_jtn": pax_jtn,
                "baris_db": baris_db,
                "trip_id": trip_id,
                "jam_72": jam_72  # <--- INI DIA TERSANGKANYA BRO! UDAH GUE TAMBAHIN!
            })
            
        elif jam_tiba_pdp != "":
            semua_berangkat = True 
            
            rutes = [
                ("MIM / BUAHBATU", pax_mim, jam_out_mim),
                ("KOPO", pax_kopo, jam_out_kopo),
                ("JATINANGOR", pax_jtn, jam_out_jtn)
            ]
            
            for tj, pax_count, jam_out in rutes:
                if pax_count > 0:
                    ada_pax = True
                    if jam_out == "":
                        semua_berangkat = False 
                        wt = hitung_wt(jam_tiba_pdp, waktu_sekarang)
                        
                        # Pengaturan Badge Warna Soft Neon Cyberpunk
                        badge = f"<span style='color:#ff4757; font-weight:bold; text-shadow: 0 0 5px rgba(255,71,87,0.4);'>🚨 {wt} menit</span>" if wt >= 30 else f"<span style='color:#feca57; text-shadow: 0 0 5px rgba(254, 202, 87, 0.4); font-weight:700;'>⏳ {wt} menit</span>"
                        
                        pax_info.append(f"<li>{tj}: <b style='color:#feca57;'>{pax_count} Pax</b> {badge}</li>")
                        hasil["grup_tujuan"][tj].append({"label": label_armada, "baris_db": baris_db, "trip_id": trip_id, "jam_tiba": jam_tiba_pdp})
                        hasil["total_pax"][tj] += pax_count
            
            if ada_pax and pax_info:
                hasil["monitor_antrean"].append({
                    "label": label_armada,
                    "driver": driver,
                    "tiba": jam_tiba_pdp,
                    "html": "".join(pax_info)
                })
            
            if semua_berangkat or not ada_pax:
                hasil["auto_selesai_updates"].append({
                    "baris": baris_db,
                    "updates": {"H": "SELESAI"}
                })

    return hasil
