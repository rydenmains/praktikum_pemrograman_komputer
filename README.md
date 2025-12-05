# 🧠 Quiz App Python 

Aplikasi kuis interaktif berbasis desktop yang dibangun menggunakan Python. Aplikasi ini mendukung sistem bank soal modular (CSV), fitur Gacha Power-up, dan Leaderboard lokal.



✨ Fitur Utama

* **Modular Question Bank**: Soal dibaca dari file `.csv` eksternal. Bisa ganti topik kuis dengan mudah (Matematika, IT, Pengetahuan Umum, dll).
* **Gacha Power-Up System**: Sistem undian kartu sebelum kuis dimulai dengan probabilitas (Weighted Random). Dapatkan bonus poin awal mulai dari "Receh" hingga "JACKPOT!".
* **Select Mode**: Pilih paket soal yang ingin dimainkan langsung dari menu utama.
* **Leaderboard**: Mencatat 10 skor tertinggi beserta durasi waktu pengerjaan tercepat.
* **Interactive UI**: Tombol interaktif dengan indikator warna (Hijau/Merah) saat menjawab.
* **Audio FX**: Efek suara untuk jawaban benar, salah, menang, dan kalah (menggunakan Pygame).


🛠️ Prasyarat (Requirements)

Pastikan kamu sudah menginstall Python 3.x.
Library tambahan yang diperlukan:

* `pygame` (Untuk audio)
* `matplotlib` (Untuk grafik hasil akhir)

Install dependencies dengan perintah:

```bash
pip install pygame matplotlib
