import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import os
import shutil
import glob
import sys

# --- SETUP IMPORT MODUL ---
try:
    from modules.utils import load_custom_font
    from modules.ui_window import QuizWindow
    from modules.data_manager import get_leaderboard 
except ImportError:
    sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))
    from modules.utils import load_custom_font
    from modules.ui_window import QuizWindow
    from modules.data_manager import get_leaderboard

FONT_NAME = load_custom_font()

# --- FUNGSI-FUNGSI LOGIKA ---

def get_list_csv():
    """Mengambil semua file .csv di folder data untuk dropdown"""
    folder = "data"
    if not os.path.exists(folder): os.makedirs(folder)
    files = glob.glob(os.path.join(folder, "*.csv"))
    # Filter file sistem agar tidak muncul di pilihan soal
    return [os.path.basename(f) for f in files if "powerup" not in f and "leaderboard" not in f]

def refresh_dropdown():
    """Update isi dropdown kalau ada file baru"""
    files = get_list_csv()
    combo_soal['values'] = files
    if files:
        combo_soal.current(0) 
    else:
        combo_soal.set("Tidak ada file soal")

def jalankan_quiz():
    nama = entry_nama.get().strip()
    file_terpilih = combo_soal.get()

    if not nama:
        messagebox.showwarning("Peringatan", "Masukkan nama pemain dulu!")
        return
    
    if not file_terpilih or file_terpilih == "Tidak ada file soal":
        messagebox.showwarning("Peringatan", "Pilih file soal dulu!")
        return
    
    # Tutup menu utama & Buka Kuis
    root.destroy()
    quiz_root = tk.Tk()
    app = QuizWindow(quiz_root, player_name=nama, filename=file_terpilih) 
    quiz_root.mainloop()

def show_leaderboard_window():
    """Menampilkan Jendela Klasemen"""
    win = tk.Toplevel(root)
    win.title("Klasemen Tertinggi")
    win.geometry("600x500")
    win.config(bg="white")
    
    if os.path.exists("assets/logo.ico"):
        try: win.iconbitmap("assets/logo.ico")
        except: pass
    
    tk.Label(win, text="🏆 LEADERBOARD", font=(FONT_NAME, 20, "bold"), bg="white", fg="#FF9800").pack(pady=15)
    
    # Tabel Treeview
    cols = ("Rank", "Nama", "Skor", "Waktu", "Soal")
    tree = ttk.Treeview(win, columns=cols, show='headings', height=15)
    
    tree.heading("Rank", text="#")
    tree.heading("Nama", text="Pemain")
    tree.heading("Skor", text="Skor")
    tree.heading("Waktu", text="Durasi")
    tree.heading("Soal", text="File Soal")
    
    tree.column("Rank", width=40, anchor="center")
    tree.column("Nama", width=120)
    tree.column("Skor", width=60, anchor="center")
    tree.column("Waktu", width=100, anchor="center")
    tree.column("Soal", width=150)
    
    tree.pack(fill="both", expand=True, padx=20, pady=10)
    
    # Ambil data dari data_manager
    data = get_leaderboard()
    
    for i, d in enumerate(data):
        waktu = d.get('time_str', d.get('date', '-'))
        file = d.get('file', '-')
        tree.insert("", "end", values=(i+1, d['name'], d['score'], waktu, file))

def import_csv():
    """Import file CSV baru dengan aman"""
    s = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
    if s:
        try:
            os.makedirs("data", exist_ok=True)
            nama_asli = os.path.basename(s)
            tujuan = os.path.join("data", nama_asli)
            
            # Cek duplikasi path
            if os.path.abspath(s) == os.path.abspath(tujuan):
                messagebox.showinfo("Info", "File ini sudah ada di folder data.")
                return

            shutil.copy(s, tujuan)
            messagebox.showinfo("Sukses", f"File '{nama_asli}' berhasil dimasukkan!")
            refresh_dropdown() 
        except Exception as e: 
            messagebox.showerror("Gagal", f"Gagal Import: {str(e)}")

def download_contoh():
    """Membuat file contoh soal"""
    isi = """Tipe;Pertanyaan;Opsi A;Opsi B;Opsi C;Opsi D;Jawaban
MC;Siapa Presiden pertama Indonesia?;Soekarno;Hatta;Habibie;Jokowi;A
MC;2 + 2 = ?;3;4;5;6;B"""
    
    f = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")], initialfile="contoh_soal.csv")
    if f:
        try: 
            with open(f, 'w', encoding='utf-8') as file: file.write(isi)
            messagebox.showinfo("Sukses", "File contoh berhasil disimpan!")
        except Exception as e: messagebox.showerror("Gagal", str(e))

# --- GUI MAIN MENU ---
root = tk.Tk()
root.title("Quiz App - Main Menu")
root.geometry("500x700")
root.configure(bg="#f4f4f4")

if os.path.exists("assets/logo.ico"):
    try: root.iconbitmap("assets/logo.ico")
    except: pass

header_frame = tk.Frame(root, bg="#f4f4f4"); header_frame.pack(pady=30)
tk.Label(header_frame, text="QUIZ APP PYTHON", font=(FONT_NAME, 28, "bold"), bg="#f4f4f4", fg="#333").pack()
tk.Label(header_frame, text="Pilih Soal & Mainkan", font=(FONT_NAME, 12), bg="#f4f4f4", fg="#666").pack(pady=5)

# Input Nama
input_frame = tk.Frame(root, bg="#f4f4f4"); input_frame.pack(pady=10)
tk.Label(input_frame, text="Masukkan Nama:", font=(FONT_NAME, 10), bg="#f4f4f4").pack(anchor="w")
entry_nama = tk.Entry(input_frame, font=("Arial", 12), width=30)
entry_nama.pack(pady=5, ipady=3)

# Pilihan Soal (Dropdown)
tk.Label(input_frame, text="Pilih Paket Soal:", font=(FONT_NAME, 10), bg="#f4f4f4").pack(anchor="w", pady=(10,0))
combo_soal = ttk.Combobox(input_frame, font=("Arial", 11), width=28, state="readonly")
combo_soal.pack(pady=5, ipady=3)
refresh_dropdown() 

# Tombol Utama (Start & Leaderboard)
btn_frame = tk.Frame(root, bg="#f4f4f4"); btn_frame.pack(pady=20)

btn_start = tk.Button(btn_frame, text="MULAI KUIS", font=(FONT_NAME, 14), bg="#4CAF50", fg="white", width=20, height=2, relief="flat", cursor="hand2", command=jalankan_quiz)
btn_start.pack(pady=5)

btn_lead = tk.Button(btn_frame, text="🏆 LIHAT KLASEMEN", font=(FONT_NAME, 12), bg="#FFC107", fg="#333", width=20, relief="flat", cursor="hand2", command=show_leaderboard_window)
btn_lead.pack(pady=5)

# Tombol Aksi (Import & Contoh) - INI YANG TADI ERROR
action_frame = tk.Frame(root, bg="#f4f4f4"); action_frame.pack(pady=10)
tk.Button(action_frame, text="IMPORT SOAL", font=(FONT_NAME, 10), bg="#2196F3", fg="white", width=15, command=import_csv).pack(side="left", padx=5)
tk.Button(action_frame, text="CONTOH SOAL", font=(FONT_NAME, 10), bg="#607D8B", fg="white", width=15, command=download_contoh).pack(side="left", padx=5)

tk.Label(root, text="v9.0 - Full Features Restored", font=("Arial", 8), bg="#f4f4f4", fg="#aaa").pack(side="bottom", pady=20)

root.mainloop()