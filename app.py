import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import os
import sys

if getattr(sys, "frozen", False):
    app_folder = os.path.dirname(sys.executable)
else:
    app_folder = os.path.dirname(os.path.abspath(__file__))

ffmpeg_path = os.path.join(app_folder, "ffmpeg.exe")

BG = "#11141b"
PANEL = "#1d2330"
TEXT = "#f4f6fb"
MUTED = "#b8c1d1"
RED = "#e53945"
PURPLE = "#7554d9"
GREEN = "#2f9e72"

class DownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("YT Music & Video Downloader")
        self.root.geometry("720x600")
        self.root.minsize(620, 540)
        self.root.configure(bg=BG)
        self.output_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        self.busy = False

        tk.Label(root, text="YT Music & Video", font=("Segoe UI", 23, "bold"),
                 bg=BG, fg=TEXT).pack(pady=(18, 2))
        tk.Label(root, text="Download content you own or are authorized to save",
                 font=("Segoe UI", 10), bg=BG, fg=MUTED).pack(pady=(0, 14))

        panel = tk.Frame(root, bg=PANEL, padx=18, pady=16)
        panel.pack(fill="x", padx=22)

        tk.Label(panel, text="YouTube link", bg=PANEL, fg=TEXT,
                 font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.url = tk.Entry(panel, font=("Segoe UI", 11), relief="flat")
        self.url.pack(fill="x", pady=(7, 14), ipady=8)

        tk.Label(panel, text="Download type", bg=PANEL, fg=TEXT,
                 font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.kind = tk.StringVar(value="video")
        options = tk.Frame(panel, bg=PANEL)
        options.pack(fill="x", pady=(7, 12))
        tk.Radiobutton(options, text="Video (MP4)", variable=self.kind, value="video",
                       bg=PANEL, fg=TEXT, selectcolor=BG, activebackground=PANEL,
                       activeforeground=TEXT).pack(side="left", padx=(0, 20))
        tk.Radiobutton(options, text="Audio (MP3)", variable=self.kind, value="audio",
                       bg=PANEL, fg=TEXT, selectcolor=BG, activebackground=PANEL,
                       activeforeground=TEXT).pack(side="left")

        folderrow = tk.Frame(panel, bg=PANEL)
        folderrow.pack(fill="x")
        self.folder_label = tk.Label(folderrow, text=f"Save to: {self.output_dir}",
                                     bg=PANEL, fg=MUTED, anchor="w")
        self.folder_label.pack(side="left", fill="x", expand=True)
        tk.Button(folderrow, text="Choose folder", command=self.choose_folder,
                  bg="#343d4e", fg=TEXT, relief="flat", padx=10, pady=6).pack(side="right")

        self.authorized = tk.BooleanVar(value=False)
        tk.Checkbutton(root,
            text="I own this content or have permission to download it.",
            variable=self.authorized, bg=BG, fg=TEXT, selectcolor=PANEL,
            activebackground=BG, activeforeground=TEXT,
            font=("Segoe UI", 10)).pack(anchor="w", padx=26, pady=(14, 8))

        self.start_btn = tk.Button(root, text="Download", command=self.start_download,
            bg=RED, fg="white", activebackground=RED, activeforeground="white",
            font=("Segoe UI", 11, "bold"), relief="flat", padx=16, pady=10,
            cursor="hand2")
        self.start_btn.pack(fill="x", padx=22)

        self.progress = ttk.Progressbar(root, mode="indeterminate")
        self.progress.pack(fill="x", padx=22, pady=(12, 8))

        self.status = tk.StringVar(value="Ready.")
        tk.Label(root, textvariable=self.status, bg=BG, fg=TEXT,
                 anchor="w", wraplength=660, justify="left").pack(fill="x", padx=24)

        self.log = tk.Text(root, height=8, bg="#0b0d12", fg="#dce3ef",
                           insertbackground=TEXT, relief="flat", wrap="word",
                           font=("Consolas", 9))
        self.log.pack(fill="both", expand=True, padx=22, pady=(10, 18))
        self.log.insert("end", "Tip: Use this only for your own uploads or content whose creator permits downloading.\n")
        self.log.configure(state="disabled")

        if yt_dlp is None:
            self.status.set("Setup needed: install yt-dlp and FFmpeg (see README).")
            self.write_log("yt-dlp is not installed yet. Follow the README setup steps.")

    def choose_folder(self):
        folder = filedialog.askdirectory(initialdir=self.output_dir)
        if folder:
            self.output_dir = folder
            self.folder_label.configure(text=f"Save to: {self.output_dir}")

    def write_log(self, message):
        def append():
            self.log.configure(state="normal")
            self.log.insert("end", str(message) + "\n")
            self.log.see("end")
            self.log.configure(state="disabled")
        self.root.after(0, append)

    def set_status(self, message):
        self.root.after(0, lambda: self.status.set(message))

    def start_download(self):
        if yt_dlp is None:
            messagebox.showerror("Missing package",
                "yt-dlp is not installed.\n\nOpen CMD in this folder and run:\npython -m pip install -r requirements.txt")
            return
        url = self.url.get().strip()
        if not url.startswith(("https://", "http://")):
            messagebox.showwarning("Link needed", "Paste a valid video URL first.")
            return
        if not self.authorized.get():
            messagebox.showwarning("Permission required",
                "Please confirm that you own the content or have permission to download it.")
            return
        if self.busy:
            return

        self.busy = True
        self.start_btn.configure(state="disabled")
        self.progress.start(10)
        self.set_status("Starting download…")
        threading.Thread(target=self.download_worker, args=(url, self.kind.get()), daemon=True).start()

    def download_worker(self, url, kind):
        try:
            if kind == "audio":
                opts = {
                    "format": "bestaudio/best",
                    "outtmpl": os.path.join(self.output_dir, "%(title).180s.%(ext)s"),
                    "noplaylist": True,
                    "windowsfilenames": True,
                    "postprocessors": [{
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }],
                    "progress_hooks": [self.progress_hook],
                    "quiet": True,
                    "no_warnings": True,
                }
            else:
                opts = {
                    "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                    "merge_output_format": "mp4",
                    "outtmpl": os.path.join(self."outtmpl": os.path.join(
    os.path.expanduser("~"),
    "Downloads",
    "%(title)s.%(ext)s"
),
                    "noplaylist": True,
                    "windowsfilenames": True,
                    "progress_hooks": [self.progress_hook],
                    "quiet": True,
                    "no_warnings": True,
                }
            self.write_log("Starting: " + url)
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])
            self.set_status("Finished. Check the selected folder.")
            self.write_log("Download finished.")
        except Exception as exc:
            self.set_status("Download failed. See details below.")
            self.write_log("Error: " + str(exc))
        finally:
            def finish():
                self.progress.stop()
                self.start_btn.configure(state="normal")
                self.busy = False
            self.root.after(0, finish)

    def progress_hook(self, data):
        state = data.get("status")
        if state == "downloading":
            total = data.get("_total_bytes_str") or data.get("_percent_str") or "Downloading…"
            self.set_status("Downloading: " + str(total).strip())
        elif state == "finished":
            self.set_status("Processing file…")

def main():
    root = tk.Tk()
    DownloaderApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
