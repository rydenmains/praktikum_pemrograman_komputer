import tkinter as tk
from tkinter import messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import sys
import os
import logging
import pygame
import random

# Matikan log font matplotlib yang berisik
logging.getLogger('matplotlib.font_manager').setLevel(logging.ERROR)

# --- IMPORT MODUL ---
try:
    from modules.game_engine import GameEngine
    from modules.data_manager import save_score, load_powerups
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from modules.game_engine import GameEngine
    from modules.data_manager import save_score, load_powerups

# --- KONFIGURASI WARNA & FONT ---
BG_COLOR = "#f4f4f4"
ACCENT_COLOR = "#4CAF50" # HIJAU
WRONG_COLOR = "#D32F2F"  # MERAH
WARNING_COLOR = "#FF9800"
FONT_NAME = "Feather Bold"  
TIME_LIMIT = 20

class QuizWindow:
    def __init__(self, root, player_name="Pemain", filename="Unknown"):
        self.root = root
        self.player_name = player_name
        self.filename = filename 
        self.root.geometry("900x800")
        self.root.configure(bg=BG_COLOR)
        
        # Setup Path
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        if not os.path.exists(os.path.join(self.base_dir, "data")):
             self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        self.sfx_dir = os.path.join(self.base_dir, "assets", "sfx")
        self.is_muted = False
        
        # Init System
        self.init_audio_system()
        self.set_app_icon()
        
        # Load Game Engine
        try: 
            full_path = os.path.join(self.base_dir, "data", self.filename)
            self.engine = GameEngine(filepath=full_path)
            if self.engine.total_questions == 0:
                raise ValueError(f"File '{self.filename}' kosong.")
        except Exception as e:
            messagebox.showerror("Gagal", f"Error: {e}")
            self.root.destroy()
            return

        # State Variables
        self.powerup = None
        self.correct_count = 0
        self.wrong_count = 0
        self.time_left = TIME_LIMIT
        self.timer_job = None
        self.buttons = []
        self.input_locked = False
        self.history = []
        self.is_frozen = False
        self.score_multiplier = 1
        self.damage_multiplier = 1
        self.startup_msg = "" 

        self.play_bgm()
        self.show_gacha_screen()

    # --- SISTEM GACHA ---
    def show_gacha_screen(self):
        for w in self.root.winfo_children(): w.destroy()
        self.root.title(f"{self.player_name} - GACHA POWER UP")
        
        tk.Label(self.root, text="PILIH KARTU NASIBMU!", font=(FONT_NAME, 28, "bold"), bg=BG_COLOR, fg="#9C27B0").pack(pady=(40, 20))
        
        all_pu = load_powerups()
        choices = []
        pool = list(all_pu)
        
        for _ in range(3):
            if not pool: break
            weights = [p.get('weight', 1) for p in pool]
            picked = random.choices(pool, weights=weights, k=1)[0]
            choices.append(picked)
            pool.remove(picked)

        card_container = tk.Frame(self.root, bg=BG_COLOR)
        card_container.pack(pady=20)

        for pu in choices:
            w = pu.get('weight', 1)
            if w <= 5: border_col = "#FFD700" 
            elif w <= 25: border_col = "#C0C0C0" 
            else: border_col = "#cd7f32" 

            frm = tk.Frame(card_container, bg=border_col, bd=2)
            frm.pack(side="left", padx=15)
            
            btn = tk.Button(
                frm,
                text=f"{pu['name']}\n\n{pu['desc']}",
                font=("Arial", 11, "bold"), bg="white", fg="#333",
                width=18, height=8, relief="flat", cursor="hand2",
                command=lambda p=pu: self.start_quiz_flow(p)
            )
            btn.pack(padx=2, pady=2)

    # --- START GAME FLOW ---
    def start_quiz_flow(self, selected_powerup):
        self.powerup = selected_powerup
        self.root.title(f"Quiz - {self.player_name}")
        
        self.root.bind('1', lambda e: self.handle_keypress(0))
        self.root.bind('2', lambda e: self.handle_keypress(1))
        self.root.bind('3', lambda e: self.handle_keypress(2))
        self.root.bind('4', lambda e: self.handle_keypress(3))
        
        # Apply Powerup Effect
        raw_effect = self.powerup.get('effect', '')
        parts = raw_effect.split('_')
        jenis = parts[0].upper()
        
        if jenis == "POINT" and len(parts) > 1:
            poin_tambahan = int(parts[1])
            self.engine.score += poin_tambahan
            self.startup_msg = f"Bonus Awal: +{poin_tambahan} Poin Aktif!"
        else:
            self.startup_msg = "Game Dimulai!"

        self.setup_quiz_ui()
        self.load_question()

    def setup_quiz_ui(self):
        for w in self.root.winfo_children(): w.destroy()
        self.set_app_icon()

        self.header_frame = tk.Frame(self.root, bg=BG_COLOR); self.header_frame.pack(fill="x", padx=20, pady=(15, 5))
        left_frame = tk.Frame(self.header_frame, bg=BG_COLOR); left_frame.pack(side="left")
        
        self.btn_mute = tk.Button(left_frame, text="🔊", font=("Arial", 12), bg="#ddd", width=3, command=self.toggle_mute)
        self.btn_mute.pack(side="left", padx=(0, 10))
        
        self.lbl_progress = tk.Label(left_frame, text="Soal 1", font=(FONT_NAME, 14), bg=BG_COLOR, fg="#888")
        self.lbl_progress.pack(side="left")

        right_frame = tk.Frame(self.header_frame, bg=BG_COLOR); right_frame.pack(side="right")
        self.lbl_life = tk.Label(right_frame, text="❤️❤️❤️", font=("Segoe UI Emoji", 16), bg=BG_COLOR, fg="#D32F2F")
        self.lbl_life.pack(side="right", padx=(10, 0))
        
        self.lbl_score = tk.Label(right_frame, text=f"Skor: {self.engine.score}", font=(FONT_NAME, 14), bg=BG_COLOR, fg=ACCENT_COLOR)
        self.lbl_score.pack(side="right")

        self.timer_canvas = tk.Canvas(self.root, height=10, bg="#ddd", highlightthickness=0)
        self.timer_bar = self.timer_canvas.create_rectangle(0,0,0,0, fill=ACCENT_COLOR)

        self.main_frame = tk.Frame(self.root, bg="white", bd=2, relief="groove")
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.footer = tk.Frame(self.root, bg=BG_COLOR); self.footer.pack(fill="x", pady=10)
        self.btn_submit = tk.Button(self.footer, text="JAWAB", bg=ACCENT_COLOR, fg="white", font=(FONT_NAME, 12), command=self.submit_answer)

    def load_question(self):
        if self.score_multiplier == 1: self.main_frame.config(bg="white")
        q = self.engine.get_current_question()
        if not q: self.show_result(); return
        
        self.input_locked = False
        self.lbl_progress.config(text=f"Soal {self.engine.current_index+1}")
        
        txt_score = f"Skor: {self.engine.score}"
        self.lbl_score.config(text=txt_score)
        self.lbl_life.config(text="❤️" * max(0, self.engine.lives))
        
        self.timer_canvas.pack(fill="x", padx=20, pady=(0,10), before=self.main_frame)
        for w in self.main_frame.winfo_children(): w.destroy()
        self.btn_submit.pack_forget(); self.buttons = []
        
        if self.startup_msg:
            tk.Label(self.main_frame, text=self.startup_msg, font=(FONT_NAME, 12, "bold"), fg=ACCENT_COLOR, bg="white").pack(pady=(0, 10))
            self.startup_msg = "" 

        tk.Label(self.main_frame, text=q['question'], font=(FONT_NAME, 18), bg="white", wraplength=800).pack(pady=20)
        
        if q['type'] == "MC": self.render_mc(q['options'])
        elif q['type'] == "MS": self.render_ms(q['options'])
        elif q['type'] == "ESSAY": self.render_essay()
        self.start_timer()

    def render_mc(self, opts):
        f = tk.Frame(self.main_frame, bg="white"); f.pack(fill="both", expand=True, padx=50)
        for i, o in enumerate(opts):
            b = tk.Button(f, text=o, font=("Arial", 12), bg="#f0f0f0", height=2, command=lambda x=i: self.process_answer(x))
            b.pack(fill="x", pady=5); self.buttons.append(b)
            
    def render_ms(self, opts):
        f = tk.Frame(self.main_frame, bg="white"); f.pack(pady=10); self.ms_vars = []
        for o in opts: 
            v = tk.IntVar()
            tk.Checkbutton(f, text=o, variable=v, font=("Arial", 12), bg="white").pack(anchor="w", pady=2)
            self.ms_vars.append(v)
        self.btn_submit.pack(pady=5)
        
    def render_essay(self):
        self.entry_essay = tk.Entry(self.main_frame, font=("Arial", 14), width=30)
        self.entry_essay.pack(pady=20)
        self.btn_submit.pack(pady=5)

    def start_timer(self):
        if self.timer_job: self.root.after_cancel(self.timer_job)
        self.time_left = TIME_LIMIT; self.update_timer()
        
    def update_timer(self):
        if self.is_frozen: 
            self.timer_job = self.root.after(100, self.update_timer)
            return
            
        w = self.root.winfo_width()
        nw = (self.time_left / TIME_LIMIT) * (w - 40)
        self.timer_canvas.coords(self.timer_bar, 0, 0, nw, 10)
        
        col = ACCENT_COLOR if self.time_left > 10 else (WARNING_COLOR if self.time_left > 5 else WRONG_COLOR)
        self.timer_canvas.itemconfig(self.timer_bar, fill=col)
        
        if self.time_left > 0: 
            self.time_left -= 0.1
            self.timer_job = self.root.after(100, self.update_timer)
        else: 
            self.handle_wrong_answer(True)

    def submit_answer(self):
        q = self.engine.get_current_question(); tp = q['type']; ans = None
        if tp == "MS": ans = [i for i, v in enumerate(self.ms_vars) if v.get() == 1]
        elif tp == "ESSAY": ans = self.entry_essay.get()
        self.process_answer(ans)

    def handle_keypress(self, idx):
        if not self.input_locked and idx < len(self.buttons):
            if self.buttons[idx]['state'] != 'disabled': self.process_answer(idx)

    def process_answer(self, ans):
        if self.input_locked: return
        self.input_locked = True
        if self.timer_job: self.root.after_cancel(self.timer_job)
        
        is_corr = self.engine.check_answer(ans)
        
        # PEWARNAAN TOMBOL
        q = self.engine.get_current_question()
        if q['type'] == 'MC' and isinstance(ans, int):
            if 0 <= ans < len(self.buttons):
                if is_corr:
                    self.buttons[ans].config(bg=ACCENT_COLOR, fg="white")
                else:
                    self.buttons[ans].config(bg=WRONG_COLOR, fg="white")

        self.record_history(ans, is_corr)
        
        if is_corr:
            pts = 10 * self.score_multiplier
            self.engine.score += pts; self.engine.score -= 10
            self.correct_count += 1
            self.play_sound("correct.mp3")
            self.show_feedback(True, False, msg=f"BENAR! (+{pts})")
        else:
            self.handle_wrong_answer(False)

    def handle_wrong_answer(self, is_timeout):
        dmg = 1 * self.damage_multiplier
        self.engine.lives -= (dmg - 1 if not is_timeout else dmg)
        self.wrong_count += 1
        self.play_sound("wrong.mp3")
        self.highlight_correct_answer()
        
        # Teks disamakan sesuai request
        msg = f"SALAH! (-{dmg} ❤️)" if not is_timeout else f"WAKTU HABIS! (-{dmg} ❤️)"
        self.show_feedback(False, is_timeout, msg=msg)

    def highlight_correct_answer(self):
        try:
            c = self.engine.get_current_question()
            if c['type'] == 'MC':
                idx = c['answer']
                if 0 <= idx < len(self.buttons): 
                    self.buttons[idx].config(bg=ACCENT_COLOR, fg="white")
        except: pass

    def show_feedback(self, is_corr, is_to, msg=None):
        for w in self.main_frame.winfo_children():
            if isinstance(w, tk.Label) and w != self.btn_submit:
                w.config(text=msg, fg=ACCENT_COLOR if is_corr else WRONG_COLOR)
                break
        self.lbl_life.config(text="❤️" * max(0, self.engine.lives))
        self.timer_canvas.pack_forget()
        if self.engine.lives <= 0:
            self.play_sound("lose.mp3")
            self.root.after(2000, self.show_result)
        else:
            self.root.after(2000, self.next_step)

    def record_history(self, ans, is_corr):
        c = self.engine.get_current_question()
        if c: self.history.append({'question':c['question'],'user_ans':str(ans),'correct_ans':str(c['answer']),'status':'Benar' if is_corr else 'Salah'})

    def next_step(self):
        if self.engine.next_question(): self.load_question()
        else: self.show_result()

    def show_result(self):
        self.stop_bgm()
        
        # Hitung durasi
        duration = self.engine.get_duration()
        save_score(self.player_name, self.engine.score, self.filename, duration)
        
        for w in self.root.winfo_children(): w.destroy()
        self.set_app_icon()
        self.root.title("Laporan Hasil")
        
        max_s = self.engine.total_questions * 10
        val = (self.engine.score / max_s) * 100 if max_s > 0 else 0
        
        # Logic Menang/Kalah (Nyawa habis = Kalah)
        is_win = (val >= 80) and (self.engine.lives > 0)
        msg = "Luar Biasa!" if is_win else "Coba Lagi!"
        
        if is_win: self.play_sound("win.mp3")
        else: self.play_sound("lose.mp3")
        
        tk.Label(self.root, text="HASIL AKHIR", font=(FONT_NAME, 24), bg=BG_COLOR).pack(pady=20)
        
        sz = [self.correct_count, self.wrong_count]
        if sum(sz) == 0: sz = [1]
        
        fig, ax = plt.subplots(figsize=(4,3))
        ax.pie(sz, labels=['Benar','Salah'], colors=[ACCENT_COLOR,WRONG_COLOR], autopct='%1.1f%%')
        fig.patch.set_facecolor(BG_COLOR)
        can = FigureCanvasTkAgg(fig, master=self.root)
        can.draw()
        can.get_tk_widget().pack()
        
        # Tampilkan Durasi
        m, s = divmod(int(duration), 60)
        time_str = f"{m:02d}m {s:02d}s"
        
        tk.Label(self.root, text=f"Nilai: {val:.1f}", font=(FONT_NAME, 16), bg=BG_COLOR).pack()
        tk.Label(self.root, text=f"Waktu: {time_str}", font=(FONT_NAME, 12), bg=BG_COLOR, fg="#666").pack()
        tk.Label(self.root, text=msg, font=(FONT_NAME, 14, "bold"), fg=ACCENT_COLOR if is_win else WRONG_COLOR).pack(pady=10)
        
        tk.Button(self.root, text="TUTUP", bg="#333", fg="white", command=self.root.destroy).pack(pady=20)

    # --- SYSTEM UTILS (DIPISAH SUPAYA RAPI & ANTI ERROR) ---
    def init_audio_system(self):
        if not pygame.get_init():
            try:
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)
                pygame.init()
            except: pass

    def set_app_icon(self):
        i = os.path.join(self.base_dir, "assets", "logo.ico")
        if os.path.exists(i):
            try: self.root.iconbitmap(i)
            except: pass

    def toggle_mute(self):
        self.is_muted = not self.is_muted
        pygame.mixer.music.set_volume(0 if self.is_muted else 0.4)
        self.btn_mute.config(text="🔇" if self.is_muted else "🔊")

    def play_sound(self, f):
        if self.is_muted: return
        p = os.path.join(self.sfx_dir, f)
        if os.path.exists(p):
            try: pygame.mixer.Sound(p).play()
            except: pass

    def play_bgm(self):
        p = os.path.join(self.sfx_dir, "quiz.mp3")
        if os.path.exists(p):
            try:
                pygame.mixer.music.load(p)
                pygame.mixer.music.set_volume(0 if self.is_muted else 0.4)
                pygame.mixer.music.play(-1)
            except: pass

    def stop_bgm(self):
        try: pygame.mixer.music.stop()
        except: pass