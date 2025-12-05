import os
import ctypes
import sys

def load_custom_font():
    """
    Mencari file font di assets/fonts/Feather Bold.ttf
    dan mendaftarkannya sementara ke sistem Windows agar bisa dipakai Tkinter.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    font_path = os.path.join(base_dir, "assets", "fonts", "Feather Bold.ttf")

    if not os.path.exists(font_path):
        return "Arial" 

    try:
        ctypes.windll.gdi32.AddFontResourceExW(font_path, 0x10, 0)
        return "Feather Bold" 
    except Exception:
        return "Arial"