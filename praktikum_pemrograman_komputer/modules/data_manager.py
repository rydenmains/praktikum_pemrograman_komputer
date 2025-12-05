import csv
import json
import os
import glob
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
LEADERBOARD_PATH = os.path.join(DATA_DIR, "leaderboard.json")
POWERUP_PATH = os.path.join(DATA_DIR, "powerups.csv")

os.makedirs(DATA_DIR, exist_ok=True)

def _read_csv_universal(filepath):
    if not os.path.exists(filepath): return []
    data_list = []
    try:
        with open(filepath, mode='r', encoding='utf-8-sig') as file:
            lines = file.readlines()
        if not lines: return []

        delimiter = ';' 
        header = lines[0].strip()
        if header.startswith('"') and header.endswith('"'): header = header[1:-1]
        if ';' in header: delimiter = ';'
        elif ',' in header: delimiter = ','
        
        headers = [h.strip().lower() for h in header.split(delimiter)]

        for line in lines[1:]:
            line = line.strip()
            if not line: continue
            if line.startswith('"') and line.endswith('"'): line = line[1:-1]
            values = line.split(delimiter)
            
            if len(values) >= len(headers):
                row_dict = {}
                for idx, key in enumerate(headers):
                    if idx < len(values): row_dict[key] = values[idx].strip()
                data_list.append(row_dict)
            else:
                row_dict = {}
                for idx, key in enumerate(headers):
                    val = values[idx].strip() if idx < len(values) else ""
                    row_dict[key] = val
                data_list.append(row_dict)
        return data_list
    except Exception as e:
        print(f"Error: {e}")
        return []

def load_data_csv(filepath=None):
    if filepath is None: filepath = get_valid_csv_path()
    if not filepath: return []
    raw_rows = _read_csv_universal(filepath)
    soal_list = []
    
    map_q = ['pertanyaan', 'question', 'soal', 'q']
    map_a = ['jawaban', 'answer', 'kunci', 'a']
    map_type = ['tipe', 'type']
    opt_keys = ["opsi a", "a", "opsi b", "b", "opsi c", "c", "opsi d", "d", "opsi e", "e"]

    for row in raw_rows:
        q = next((row.get(k) for k in map_q if row.get(k)), None)
        ans = next((row.get(k) for k in map_a if row.get(k)), None)
        tipe = next((row.get(k) for k in map_type if row.get(k)), "MC")
        if not q or not ans: continue
        tipe = tipe.strip().upper() or "MC"
        if tipe == "MATCH": continue 

        opts = [row.get(k) for k in opt_keys if row.get(k)]
        try:
            processed_ans = None
            if tipe == "MS":
                ans_chars = ans.split(";") if ";" in ans else ans.split(",")
                mapping = {'A':0, 'B':1, 'C':2, 'D':3, 'E':4}
                processed_ans = [mapping.get(x.strip().upper()) for x in ans_chars if x.strip()]
            elif tipe == "ESSAY":
                processed_ans = ans.lower().strip()
                opts = []
            else: 
                mapping = {'A':0, 'B':1, 'C':2, 'D':3, 'E':4}
                processed_ans = mapping.get(ans.strip().upper(), 0)

            soal_list.append({"type": tipe, "question": q.strip(), "options": opts, "answer": processed_ans})
        except: pass
    return soal_list

def load_powerups():
    default_pu = [{"code": "P01", "name": "Bonus Poin", "desc": "+50 Poin", "effect": "POINT_50", "weight": 100}]
    if not os.path.exists(POWERUP_PATH): return default_pu
    raw = _read_csv_universal(POWERUP_PATH)
    if not raw: return default_pu
    clean = []
    for r in raw:
        n = r.get('name')
        e = r.get('effect')
        w = r.get('weight') or '1'
        try: w = int(w)
        except: w = 1
        if n and e: clean.append({"name": n, "desc": r.get('desc', ''), "effect": e, "weight": w})
    return clean if clean else default_pu

def get_valid_csv_path():
    files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
    for f in files:
        if "powerup" not in f and "matematika" not in f and "leaderboard" not in f: return f
    return None

# --- UPDATE SAVE SCORE (SORT BY SKOR & WAKTU) ---
def save_score(name, score, filename, duration_seconds):
    data = get_leaderboard()
    
    # Format detik ke menit:detik (contoh: 65s -> 01:05)
    m, s = divmod(int(duration_seconds), 60)
    time_str = f"{m:02d}:{s:02d}"
    
    new_entry = {
        "name": name, 
        "score": score, 
        "time_str": time_str,     # Untuk ditampilkan
        "duration": duration_seconds, # Untuk sorting
        "file": filename
    }
    
    data.append(new_entry)
    
    # Sorting: 
    # 1. Skor Paling Besar (-x['score'])
    # 2. Durasi Paling Kecil (x['duration']) -> Makin cepat makin bagus
    data = sorted(data, key=lambda x: (-x['score'], x.get('duration', 9999)))[:10]
    
    try:
        with open(LEADERBOARD_PATH, 'w') as f: json.dump(data, f, indent=4)
    except: pass

def get_leaderboard():
    if not os.path.exists(LEADERBOARD_PATH): return []
    try:
        with open(LEADERBOARD_PATH, 'r') as f: return json.load(f)
    except: return []