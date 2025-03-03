import logging
import json
import mpv
import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.tooltip import ToolTip
import os
import re
import locale
import yt_dlp
import yt_dlp as ydl
from PIL import Image
import time
import random
import threading

locale.setlocale(locale.LC_NUMERIC, "C")

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H-%M:%S",
    filename="log.log"
)

logger = logging.getLogger(__name__)

URL_FILE = "assets/url.json"
CACHE_FILE = "assets/song_cache.json"
SETTINGS_FILE = "assets/settings.json"
TRANSLATIONS_FILE = "assets/translations.json"
ICON_16 = "assets/icon-16.png"
ICON_32 = "assets/icon-32.png"
MUSIC_GIF = "assets/music_gif.gif"


class FileHandling:
    def __init__(self, URL_FILE):
        self.file = URL_FILE
        self.sort()

    def sort(self):
        with open(self.file, encoding="utf-8") as f:
            try:
                self.data = dict(json.load(f))
                self.data = dict(sorted(self.data.items()))
            except:
                self.data = dict()

    def add_new(self, name, url):
        self.data[name] = url
        with open(self.file, 'w', encoding="utf-8") as f:
            json.dump(self.data, f)
        self.sort()

    def remove(self, pos):
        key_name = [k for i, k in enumerate(self.data) if i == pos]
        del self.data[key_name[0]]
        with open(self.file, 'w', encoding="utf-8") as f:
            json.dump(self.data, f)
    
    def show(self):
        return self.data


class CacheHandling:
    def __init__(self, CACHE_FILE):
        self.file = CACHE_FILE
        self.cache = self.load_cache()

    def load_cache(self):
        if os.path.exists(self.file):
            with open(self.file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def save_cache(self):
        with open(self.file, "w", encoding="utf-8") as f:
            json.dump(self.cache, f, indent=4)

    def get_song_info(self, url):
        if url in self.cache:
            return self.cache[url]
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'format': 'bestaudio/best',
            'noplaylist': True,
            'extract_flat': True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        self.cache[url] = info
        self.save_cache()
        return info


class SettingsConfig:
    def __init__(self, SETTINGS_FILE):
        self.file = SETTINGS_FILE
        self.data = self.open_file()
        
    def open_file(self):
        with open(self.file, "r", encoding="utf-8") as f:
            return json.load(f)

    def overwrite_data(self, key, new_value):
        self.data[key] = new_value
        with open(self.file, "w", encoding="utf-8") as f:
            json.dump(self.data, f)

    def show(self):
        return self.data


class AppDisplay:
    def __init__(self, root, URL_FILE, CACHE_FILE, SETTINGS_FILE, TRANSLATIONS_FILE, ICON_16, ICON_32, MUSIC_GIF):
        logger.info("Uruchomiono odtwarzacz")
        self.root = root

        self.data = FileHandling(URL_FILE)
        self.cache_data = CacheHandling(CACHE_FILE)
        self.settings = SettingsConfig(SETTINGS_FILE)
        self.language = self.settings.show()["lang"]
        with open(TRANSLATIONS_FILE, "r", encoding="utf-8") as f:
            self.translations = json.load(f)
        self.root.title("Music Player")
        small_icon = tk.PhotoImage(file=ICON_16)
        large_icon = tk.PhotoImage(file=ICON_32)
        self.root.iconphoto(False, large_icon, small_icon)

        window_width = 380
        window_height = 440
        self.screen_width = root.winfo_screenwidth()
        self.screen_height = root.winfo_screenheight()
        x = (self.screen_width/2) - (window_width/2)
        y = (self.screen_height/2) - (window_height/2)

        self.root.geometry('%dx%d+%d+%d' % (window_width, window_height, x, y))
        self.root.resizable(False,False)

        self.boot_stl = self.settings.show()["theme"]
        self.menubar = tk.Menu(root)
        self.filemenu = tk.Menu(self.menubar, tearoff=0)
        self.changemenu = tk.Menu(self.filemenu, tearoff=0)
        self.changemenu.add_command(label="Primary", command=lambda: self.change_style("primary"))
        self.changemenu.add_command(label="Secondary", command=lambda: self.change_style("secondary"))
        self.changemenu.add_command(label="Success", command=lambda: self.change_style("success"))
        self.changemenu.add_command(label="Info", command=lambda: self.change_style("info"))
        self.changemenu.add_command(label="Warning", command=lambda: self.change_style("warning"))
        self.changemenu.add_command(label="Danger", command=lambda: self.change_style("danger"))
        self.changemenu.add_command(label="Light", command=lambda: self.change_style("light"))
        self.changemenu.add_command(label="Dark", command=lambda: self.change_style("dark"))
        self.filemenu.add_cascade(label=self.translations[self.language]["theme_change"], menu=self.changemenu)
        self.lanchange = tk.Menu(self.filemenu, tearoff=0)
        self.lanchange.add_command(label="en", command=lambda: self.change_language("en"))
        self.lanchange.add_command(label="pl", command=lambda: self.change_language("pl"))
        self.filemenu.add_cascade(label=self.translations[self.language]["lang_change"], menu=self.lanchange)
        self.filemenu.add_separator()
        self.filemenu.add_command(label=self.translations[self.language]["exit"], command=root.quit)
        self.menubar.add_cascade(label=self.translations[self.language]["file"], menu=self.filemenu)
        self.root.config(menu=self.menubar)

        self.right_click_menu = tk.Menu(root, tearoff=0)
        self.right_click_menu.add_command(label=self.translations[self.language]["copy"])
        self.right_click_menu.add_separator()
        self.right_click_menu.add_command(label=self.translations[self.language]["play_pause"])
        self.right_click_menu.add_separator()
        self.right_click_menu.add_command(label=self.translations[self.language]["del"])

        self.player = mpv.MPV(ytdl=True, video=False)
        self.player.command("set", "cache", "yes")
        self.player.command("set", "cache-secs", "10")
        self.player.command("set", "demuxer-readahead-secs", "5")
        self.player.command("set", "demuxer-max-bytes", "5000000")
        self.player.command("set", "demuxer-max-back-bytes", "5000000")
        self.player.observe_property("playback-time", self.check_end)

        self.gif_file = MUSIC_GIF
        self.info = Image.open(self.gif_file)

        self.header = tk.Frame(root)
        self.header.grid(row=0, column=0, padx=5, pady=5)

        self.frames = self.info.n_frames
        self.photoimage_objects = []
        for i in range(self.frames):
            self.obj = tk.PhotoImage(file=self.gif_file, format=f"gif -index {i}")
            self.photoimage_objects.append(self.obj.subsample(10))

        self.static_img = self.obj.subsample(10)

        self.gif_label = tk.Label(self.header, width=40, image=self.static_img)
        self.gif_label.grid(row=0, column=1, pady=2)

        self.text_info1 = tk.Label(self.header, text=self.translations[self.language]["now_playing"])
        self.text_info1.grid(row=1, column=1, pady=2)

        self.s_index = 0
        self.width = 30

        self.title = self.translations[self.language]["select"]
        self.text_info2 = ttk.Label(self.header, text=self.title, bootstyle=f"inverse-{self.boot_stl}", font=("bold"), wraplength=350)
        self.text_info2.grid(row=2, column=1, pady=2)
        ToolTip(self.text_info2, text=self.translations[self.language]["select"], bootstyle=self.boot_stl)

        self.list_space = tk.Frame(root)
        self.list_space.grid(row=1, column=0, padx=5, pady=5)

        self.mylist = tk.Listbox(self.list_space, width=50, height=5)
        for i, (k, v) in enumerate(self.data.show().items()):
            self.mylist.insert(i, k)
        self.mylist.bind('<Double-1>', self.play_audio)
        self.mylist.bind('<Return>', self.play_audio)
        self.mylist.bind('<space>', self.toggle_play_pause)
        self.mylist.bind("<Button-3><ButtonRelease-3>", self.do_popup1)
        self.mylist.grid(row=0, column=0, columnspan=2, rowspan=2, padx=5, pady=5)
        self.mylist.configure(highlightcolor="black")
        self.lListOver = [-1,None,None]
        self.mylist.bind('<Motion>', self.f_coord)
        self.mylist.bind('<Leave>', self.f_resetnListOver)
        self.mylist.bind('<Right>', "break")

        self.open_window_button = ttk.Button(self.list_space, text=self.translations[self.language]["add"], bootstyle=self.boot_stl, takefocus=False, command=self.open_new_window)
        self.open_window_button.grid(row=0, column=2, pady=2)
        ToolTip(self.open_window_button, text=self.translations[self.language]["add_new"], bootstyle=self.boot_stl)

        self.del_button = ttk.Button(self.list_space, text=self.translations[self.language]["del"], bootstyle=self.boot_stl, takefocus=False, command=self.delete_url)
        self.del_button.grid(row=1, column=2, pady=2)
        ToolTip(self.del_button, text=self.translations[self.language]["del_track"], bootstyle=self.boot_stl)

        self.progress_bar = tk.Frame(root)
        self.progress_bar.grid(row=2, column=0, padx=5, pady=5)

        self.seeking = False
        self.start_progress = 0

        self.start_time = tk.Label(self.progress_bar, text="00:00")
        self.start_time.grid(row=0, column=0, padx=5, pady=5)

        self.progress_val = tk.IntVar(value=self.start_progress)
        self.progress_scale = ttk.Scale(self.progress_bar, variable=self.progress_val, bootstyle=self.boot_stl, orient=tk.HORIZONTAL, from_=0, to=100, length=240)
        self.progress_scale.bind("<ButtonRelease-1>", self.change_progress)
        self.progress_scale.bind('<Button-1>', self.set_value)

        self.progress_scale.grid(row=0, column=1, padx=5, pady=5)

        self.end_time = tk.Label(self.progress_bar, text="00:00")
        self.end_time.grid(row=0, column=2, padx=5, pady=5)

        self.update_progress()

        self.buttons = tk.Frame(root)
        self.buttons.grid(row=3, column=0, padx=5, pady=5)

        self.prev_button = ttk.Button(self.buttons, text="⏮️", bootstyle=self.boot_stl, takefocus=False, command=self.play_previous)
        self.prev_button.grid(row=0, column=1, padx=5, pady=5)
        ToolTip(self.prev_button, text=self.translations[self.language]["previous"], bootstyle=self.boot_stl)

        self.stop_button = ttk.Button(self.buttons, text="⏹", bootstyle=self.boot_stl, takefocus=False, command=self.stop_audio)
        self.stop_button.grid(row=0, column=2, padx=5, pady=5)
        ToolTip(self.stop_button, text=self.translations[self.language]["stop"], bootstyle=self.boot_stl)

        self.play_button = ttk.Button(self.buttons, text="▶️", bootstyle=self.boot_stl, takefocus=False, command=self.toggle_play_pause)
        self.play_button.grid(row=0, column=3, padx=5, pady=5)
        ToolTip(self.play_button, text=self.translations[self.language]["play"], bootstyle=self.boot_stl)

        self.next_button = ttk.Button(self.buttons, text="⏭️", bootstyle=self.boot_stl, takefocus=False, command=self.play_next)
        self.next_button.grid(row=0, column=4, padx=5, pady=5)
        ToolTip(self.next_button, text=self.translations[self.language]["next"], bootstyle=self.boot_stl)

        self.toggle_buttons = tk.Frame(root)
        self.toggle_buttons.grid(row=4, column=0, padx=5, pady=5)

        if self.settings.show()["shuffle"] == 'shuffle_off':
            self.shuffle_mode = False
            self.toggle_shuffle_text = 'SHUFFLE OFF'
        else:
            self.shuffle_mode = True
            self.toggle_shuffle_text = 'SHUFFLE ON'

        self.shuffle_button = ttk.Button(self.toggle_buttons, text=self.toggle_shuffle_text, bootstyle=self.boot_stl, takefocus=False, command=self.toggle_shuffle)
        self.shuffle_button.grid(row=0, column=0, padx=3, pady=5)
        ToolTip(self.shuffle_button, text=self.translations[self.language][self.settings.show()["shuffle"]], bootstyle=self.boot_stl)

        if self.settings.show()["play_mode"] == 'repeat_mode':
            self.play_mode = "repeat"
            self.play_mode_text = 'REPEAT MODE'
        elif self.settings.show()["play_mode"] == 'next_mode':
            self.play_mode = "next"
            self.play_mode_text = 'NEXT MODE'
        else:
            self.play_mode = "stop"
            self.play_mode_text = 'STOP MODE'

        self.play_mode_button = ttk.Button(self.toggle_buttons, text=self.play_mode_text, bootstyle=self.boot_stl, takefocus=False, command=self.toggle_play_mode)
        self.play_mode_button.grid(row=0, column=1, padx=3, pady=5)
        ToolTip(self.play_mode_button, text=self.translations[self.language][self.settings.show()["play_mode"]], bootstyle=self.boot_stl)

        self.volume_frame = tk.Frame(root)
        self.volume_frame.grid(row=5, column=0, padx=5, pady=5)

        if self.settings.show()["mute"] == 'mute_off':
            self.player.mute = False
            self.mute_button_text = 'MUTE OFF'
        else:
            self.player.mute = True
            self.mute_button_text = 'MUTE ON'

        self.mute_button = ttk.Button(self.volume_frame, text=self.mute_button_text, bootstyle=self.boot_stl, takefocus=False, command=self.mute)
        self.mute_button.grid(row=0, column=0)
        ToolTip(self.mute_button, text=self.translations[self.language][self.settings.show()["mute"]], bootstyle=self.boot_stl)
        self.volume_before_mute = self.settings.show()["volume"]
        self.player.volume = self.volume_before_mute
        self.val = tk.IntVar(value=self.volume_before_mute)
        self.volume_scale = ttk.Scale(self.volume_frame, bootstyle=self.boot_stl, variable=self.val, from_=0, to=100, command=self.set_volume)
        self.volume_scale.set(self.player.volume)
        self.volume_scale.grid(row=0, column=1, padx=5, pady=5)
        self.val.trace('w', self.change_volume)
        self.scale_lbl = tk.Label(self.volume_frame, text=str(self.volume_before_mute))
        self.scale_lbl.grid(row=0, column=2, padx=5, pady=5)

        self.error = tk.StringVar()
        self.error.set("")
        self.label = tk.Label(textvariable=self.error, width=30, height=2)
        self.label.grid(row=7, column=0, columnspan=3, pady=2)
        self.clear_error_text()

        self.on_top = False

    def f_coord(self, *d):
        xEnrPos, yEnrPos = d[0].x, d[0].y
        idxOver = self.mylist.nearest(yEnrPos)
        tLast = self.mylist.bbox(self.mylist.size() - 1)
        if tLast is not None:
        	yDownLast = tLast[1] + tLast[3]
        	if yEnrPos > yDownLast:
        		if self.lListOver[1] is not None:
        			self.f_resetnListOver(None)
        		return None
        if idxOver != self.lListOver[0]:
        	sX, sY = str(self.root.winfo_pointerx() + 15), str(self.root.winfo_pointery() + 15)
        	if self.lListOver[1] is not None: self.lListOver[1].destroy()
        	self.lListOver[1] = tk.Toplevel(self.root)
        	self.lListOver[1].wm_geometry("+" + sX + "+" + sY)
        	self.lListOver[1].wm_overrideredirect(True)
        	ttk.Label(self.lListOver[1], text=[k for i, (k, v) in enumerate(self.data.show().items())][idxOver],
        			bootstyle=(self.boot_stl, INVERSE), justify=tk.LEFT).pack(padx=2, pady=2)
        	self.lListOver[0] = idxOver
        return None

    def f_resetnListOver(self, *d):
        if self.lListOver[1] is None: return None
        self.lListOver[0] = -1
        self.lListOver[1].destroy()
        self.lListOver[1] = None
        self.lListOver[2] = None
        return None

    def do_popup1(self, event=None):
        e_widget = event.widget
        self.mylist.event_generate('<Button-1>', x=event.x, y=event.y)
        try:
            self.right_click_menu.entryconfigure(self.translations[self.language]["copy"], command=lambda: e_widget.event_generate("<<Copy>>"))
        except:
            self.language = 'en'
            self.right_click_menu.entryconfigure(self.translations[self.language]["copy"], command=lambda: e_widget.event_generate("<<Copy>>"))
        self.right_click_menu.entryconfigure(self.translations[self.language]["play_pause"], command=self.toggle_play_pause)
        self.right_click_menu.entryconfigure(self.translations[self.language]["del"], command=self.delete_url)
        self.right_click_menu.tk.call("tk_popup", self.right_click_menu, event.x_root, event.y_root)

    def do_popup2(self, event=None):
        e_widget = event.widget
        self.new_right_click_menu.entryconfigure(self.translations[self.language]["cut"], command=lambda: e_widget.event_generate("<<Cut>>"))
        self.new_right_click_menu.entryconfigure(self.translations[self.language]["copy"], command=lambda: e_widget.event_generate("<<Copy>>"))
        self.new_right_click_menu.entryconfigure(self.translations[self.language]["paste"], command=lambda: e_widget.event_generate("<<Paste>>"))
        self.new_right_click_menu.entryconfigure(self.translations[self.language]["select_all"], command=lambda: e_widget.select_range(0, 'end'))
        self.new_right_click_menu.tk.call("tk_popup", self.new_right_click_menu, event.x_root, event.y_root)

    def set_value(self, event=None):
        self.seeking = True
        self.progress_scale.event_generate('<Button-3>', x=event.x, y=event.y)
        return 'break'

    def update_progress(self):
        if self.player.time_pos is None or self.player.duration is None:
            self.root.after(500, self.update_progress)
            return

        if abs(self.player.time_pos - self.player.duration) < 1:
            self.player.time_pos = self.player.duration

        if self.player.duration >= 3600:
            start = time.strftime("%H:%M:%S", time.gmtime(self.player.time_pos))
            end = time.strftime("%H:%M:%S", time.gmtime(self.player.duration))
        else:
            start = time.strftime("%M:%S", time.gmtime(self.player.time_pos))
            end = time.strftime("%M:%S", time.gmtime(self.player.duration))

        self.start_time.config(text=start)
        self.end_time.config(text=end)

        if not self.seeking:
            progress_percent = (self.player.time_pos / self.player.duration) * 100
            self.progress_val.set(progress_percent)

        self.root.after(500, self.update_progress)

    def change_progress(self, *args):
        self.seeking = True
        if self.player.duration:
            new_time = (self.progress_val.get() / 100) * self.player.duration
            self.player.seek(new_time, reference="absolute")

    def animation(self, current_frame=0):
        self.image = self.photoimage_objects[current_frame]
        self.gif_label.configure(image=self.image)
        current_frame = current_frame + 1
        if current_frame == self.frames:
            current_frame = 0
        self.loop = root.after(20, lambda: self.animation(current_frame))

    def stop_animation(self):
        if self.loop:
            logger.info("Zatrzymano animacje gif")
            self.root.after_cancel(self.loop)

    def set_flag(self, event=None):
        self.on_top = False

    def open_new_window(self):
        if not self.on_top:
            self.new_window = tk.Toplevel(root)
            self.new_window.title(self.translations[self.language]["add_new"])
            window_width = 500
            window_height = 140
            self.screen_width = root.winfo_screenwidth()
            self.screen_height = root.winfo_screenheight()
            x = (self.screen_width/2) - (window_width/2)
            y = (self.screen_height/2) - (window_height/2)
            self.new_window.geometry('%dx%d+%d+%d' % (window_width, window_height, x, y))
            self.new_window.resizable(False,False)

            self.new_right_click_menu = tk.Menu(root, tearoff=0)
            self.new_right_click_menu.add_command(label=self.translations[self.language]["cut"])
            self.new_right_click_menu.add_command(label=self.translations[self.language]["copy"])
            self.new_right_click_menu.add_command(label=self.translations[self.language]["paste"])
            self.new_right_click_menu.add_separator()
            self.new_right_click_menu.add_command(label=self.translations[self.language]["select_all"])

            self.url_entry = ttk.Label(self.new_window, bootstyle=self.boot_stl, text=self.translations[self.language]["yt_link"]).grid(row=0, column=0, sticky=tk.W, pady=2)
            self.name_entry = ttk.Label(self.new_window, bootstyle=self.boot_stl, text=self.translations[self.language]["name"]).grid(row=1, column=0, sticky=tk.W, pady=2)
            self.e1 = ttk.Entry(self.new_window, bootstyle=self.boot_stl, width=40)
            self.check_button = ttk.Button(self.new_window, bootstyle=self.boot_stl, takefocus=False, text=self.translations[self.language]["name_search"], command=self.get_video_title)
            self.check_button.grid(row=0, column=2, pady=2)
            self.entry_text = tk.StringVar()
            self.e2 = ttk.Entry(self.new_window, textvariable=self.entry_text, bootstyle=self.boot_stl, width=40)
            self.e1.grid(row=0, column=1, pady=2)
            self.e2.grid(row=1, column=1, pady=2)

            self.entry_text.trace("w", lambda *args: self.character_limit())

            self.e1.bind("<Button-3><ButtonRelease-3>", self.do_popup2)
            self.e2.bind("<Button-3><ButtonRelease-3>", self.do_popup2)

            self.add_button = ttk.Button(self.new_window, text=self.translations[self.language]["add"], bootstyle=self.boot_stl, takefocus=False, command=self.add_new_url)
            self.add_button.grid(row=2, column=1, pady=2)

            self.error_sec_win = tk.StringVar()
            self.error_sec_win.set("")

            self.label_sec_win = tk.Label(self.new_window, textvariable=self.error_sec_win, width=40, height=2)
            self.label_sec_win.grid(row=3, column=1, sticky=tk.S, pady=2)
            self.clear_error_text_sec_win()
            
            self.new_window.bind('<Destroy>', self.set_flag)

        self.on_top = True

    def get_video_title(self):
        url = self.e1.get().strip()
        if url:
            youtube_regex = re.compile(r'^(https?://)?(www\.)?(youtube\.com|youtu\.?be)/.+$')
            if not youtube_regex.match(url):
                self.error_sec_win.set(self.translations[self.language]["inc_yt_link"])
                logger.info("Niepoprawny link do YouTube")
                return

            if url in self.data.show().values():
                self.error_sec_win.set(self.translations[self.language]["already_under"])
                logger.info(f"Podany link jest juz na liscie pod nazwa '{list(filter(lambda key: self.data.show()[key] == url, self.data.show()))[0]}'")
                return

            ydl_opts = {"quiet": True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                res = info.get("title", self.translations[self.language]["unknown_title"])
                self.e2.delete(0, tk.END)
                self.e2.insert(END, res)
        else:
            self.error_sec_win.set(self.translations[self.language]["enter_url"])
            logger.info("Wprowadz URL")
            return

    def character_limit(self):
        if len(self.entry_text.get()) > 100:
            self.entry_text.set(self.entry_text.get()[:100])
            self.error_sec_win.set(self.translations[self.language]["char_limit"])

    def add_new_url(self):
        url = self.e1.get().strip()        
        name = self.e2.get().strip()
        
        if not url:
            self.error_sec_win.set(self.translations[self.language]["enter_url"])
            logger.info("Wprowadz URL")
            return

        youtube_regex = re.compile(r'^(https?://)?(www\.)?(youtube\.com|youtu\.?be)/.+$')
        if not youtube_regex.match(url):
            self.error_sec_win.set(self.translations[self.language]["inc_yt_link"])
            logger.info("Niepoprawny link do YouTube")
            return

        if url in self.data.show().values():
            self.error_sec_win.set(self.translations[self.language]["already_under"])
            logger.info(f"Podany link jest juz na liscie pod nazwa '{list(filter(lambda key: self.data.show()[key] == url, self.data.show()))[0]}'")
            return

        if not name:
            self.error_sec_win.set(self.translations[self.language]["enter_name"])
            logger.info("Wprowadz nazwe")
            return

        if name in self.data.show():
            self.error_sec_win.set(self.translations[self.language]["already_on"].format(name=name))
            logger.info(f"Nazwa '{name}' jest juz na liscie")
            return

        self.data.add_new(name, url)
        self.error_sec_win.set(self.translations[self.language]["new_track_added"])
        logger.info(f"Dodano '{name}' do listy")
        self.mylist.delete(0, tk.END)
        for i, (k, v) in enumerate(self.data.show().items()):
            self.mylist.insert(i, k)
        self.e1.delete(0, tk.END)
        self.e2.delete(0, tk.END)

    def delete_url(self):
        cs = self.mylist.curselection()
        if not cs:
            self.error.set(self.translations[self.language]["no_track_sel"])
            logger.info("Nie wybrano zadnego utworu")
            return None
        if not self.on_top:
            self.delete_window = tk.Toplevel(root)
            self.delete_window.title(self.translations[self.language]["track_del"])
            window_width = 240
            window_height = 100
            self.screen_width = root.winfo_screenwidth()
            self.screen_height = root.winfo_screenheight()
            x = (self.screen_width/2) - (window_width/2)
            y = (self.screen_height/2) - (window_height/2)
            self.delete_window.geometry('%dx%d+%d+%d' % (window_width, window_height, x, y))
            self.delete_window.resizable(False,False)

            self.question_label = tk.Label(self.delete_window, text=self.translations[self.language]["question1"], width=32)
            self.question_label.grid(row=0, column=0, columnspan=5, pady=10, padx=5)

            self.yes_button = ttk.Button(self.delete_window, text=self.translations[self.language]["yes"], bootstyle=self.boot_stl, takefocus=False, command=lambda: self.on_yes(cs))
            self.yes_button.grid(row=2, column=1, pady=5, padx=10)
            
            self.no_button = ttk.Button(self.delete_window, text=self.translations[self.language]["no"], bootstyle=self.boot_stl, takefocus=False, command=self.delete_window.destroy)
            self.no_button.grid(row=2, column=3, pady=5, padx=10)
            
            self.delete_window.bind('<Destroy>', self.set_flag)

        self.on_top = True

    def on_yes(self, cs):
        self.error.set(self.translations[self.language]["track_del_confirm"])
        logger.info(f"Usunieto '{list(self.data.show().keys())[cs[0]]}' z listy")
        self.data.remove(cs[0])
        self.mylist.delete(cs)
        self.on_top = False
        self.delete_window.destroy()
        self.result = False

    def update(self):
        double_text = self.title + '        ' + self.title
        display_text = double_text[self.s_index:self.s_index + self.width]
        self.text_info2.config(text=display_text)
        self.s_index += 1
        if self.s_index >= len(self.title) + 8:
            self.s_index = 0
            self.root.after(len(self.title)*80+5000, self.update)
        else:
            self.root.after(80, self.update)

    def clear_error_text(self):
        self.error.set("")
        self.root.after(6000, self.clear_error_text)

    def clear_error_text_sec_win(self):
        self.error_sec_win.set("")
        self.root.after(6000, self.clear_error_text_sec_win)

    def fetch_audio_url(self):
        cs = self.mylist.curselection()
        if not cs:
            self.error.set(self.translations[self.language]["no_track_sel"])
            logger.info("Nie wybrano zadnego utworu")
            return None
        url = self.data.show()[list(self.data.show().keys())[cs[0]]]
        logger.info(f"Link do video: {url}")
        logger.info(f"Odtwarzanie utworu: {list(self.data.show().keys())[cs[0]]}")
        try:
            info = self.cache_data.get_song_info(url)
            self.title = list(filter(lambda key: self.data.show()[key] == url, self.data.show()))[0]
            ToolTip(self.text_info2, text=self.title, bootstyle=self.boot_stl)
            self.text_info2.config(text=self.title[0:self.width])
            if len(self.title) > self.width:
                self.root.after(1000, self.update)
            else:
                self.text_info2.config(text=self.title)
            return info.get('url', None)
        except Exception as e:
            self.error.set(self.translations[self.language]["audio_download_fail"])
            logger.exception("Nie udalo sie pobrac audio")

    def toggle_play_pause(self, event=None):
        if self.player.pause:
            self.resume_audio()
        elif self.player.playback_time:
            self.stop_animation()
            self.pause_audio()
        else:
            self.play_audio()
    
    def play_audio(self, event=None):
        self.stop_audio()
        self.progress_val.set(0)
        audio_url = self.fetch_audio_url()
        if audio_url:
            logger.info(f"Link do audio: {audio_url}")
            self.player.play(audio_url)
            self.animation(current_frame=0)
            logger.info("Rozpoczeto animacje gif")
            self.player.pause = False
            self.play_button.config(text="⏸")
            ToolTip(self.play_button, text=self.translations[self.language]["pause"], bootstyle=self.boot_stl)

    def pause_audio(self):
        logger.info("Wstrzymano odtwarzanie")
        self.player.pause = True
        self.stop_animation()
        self.play_button.config(text="▶️")
        ToolTip(self.play_button, text=self.translations[self.language]["play"], bootstyle=self.boot_stl)

    def resume_audio(self):
        logger.info("Wznowiono odtwarzanie")
        self.player.pause = False
        self.animation(current_frame=0)
        logger.info("Rozpoczeto animacje gif")
        self.play_button.config(text="⏸")
        ToolTip(self.play_button, text=self.translations[self.language]["pause"], bootstyle=self.boot_stl)

    def toggle_play_mode(self):
        modes = ["repeat", "next", "stop"]
        mode_labels = {"repeat": "REPEAT MODE", "next": "NEXT MODE", "stop": "STOP MODE"}
        current_index = modes.index(self.play_mode)
        self.play_mode = modes[(current_index + 1) % len(modes)]
        logger.info(mode_labels[self.play_mode])
        self.play_mode_button.config(text=mode_labels[self.play_mode])
        self.settings.overwrite_data(key="play_mode", new_value=f'{self.play_mode}_mode')
        ToolTip(self.play_mode_button, text=self.translations[self.language][f'{self.play_mode}_mode'], bootstyle=self.boot_stl)

    def on_track_end(self):
        self.stop_animation()
        if self.play_mode == "repeat":
            self.play_audio()
        elif self.play_mode == "next":
            self.play_next()
        elif self.play_mode == "stop":
            self.stop_audio()

    def toggle_shuffle(self):
        self.shuffle_mode = not self.shuffle_mode
        shuffle_mode_text = "SHUFFLE ON" if self.shuffle_mode else "SHUFFLE OFF"
        logger.info(shuffle_mode_text)
        self.shuffle_button.config(text=shuffle_mode_text)
        if self.shuffle_mode:
            ToolTip(self.shuffle_button, text=self.translations[self.language]["shuffle_on"], bootstyle=self.boot_stl)
            self.settings.overwrite_data(key="shuffle", new_value="shuffle_on")
        else:
            ToolTip(self.shuffle_button, text=self.translations[self.language]["shuffle_off"], bootstyle=self.boot_stl)
            self.settings.overwrite_data(key="shuffle", new_value="shuffle_off")

    def play_next(self):
        logger.info("Nastepny utwor")
        cs = self.mylist.curselection()
        if not cs:
            return
        current_index = cs[0]
        if self.shuffle_mode:
            next_index = random.randint(0, self.mylist.size() - 1)
        else:
            next_index = (current_index + 1) % self.mylist.size()
        self.mylist.selection_clear(0, tk.END)
        self.mylist.selection_set(next_index)
        self.mylist.activate(next_index)
        self.play_audio()

    def play_previous(self, event=None):
        logger.info("Poprzedni utwor")
        cs = self.mylist.curselection()
        if not cs:
            return  
        current_index = cs[0]
        prev_index = (current_index - 1) % self.mylist.size()
        self.mylist.selection_clear(0, tk.END)
        self.mylist.selection_set(prev_index)
        self.mylist.activate(prev_index)
        self.play_audio()

    def change_volume(self, *args):        
        volume = int(self.volume_scale.get())
        self.settings.overwrite_data(key="volume", new_value=volume)
        self.player.volume = volume
        self.scale_lbl.config(text=volume)

    def set_volume(self, volume):
        volume = int(float(volume))
        self.player.volume = volume
        if self.player.mute and volume > 0:
            self.player.mute = False
            self.settings.overwrite_data(key="mute", new_value="mute_off")
            self.mute_button.config(text="MUTE OFF")
            logger.info("MUTE OFF")
            ToolTip(self.mute_button, text=self.translations[self.language]["mute_off"], bootstyle=self.boot_stl)

    def mute(self):
        if self.player.mute:
            self.player.mute = False
            self.settings.overwrite_data(key="mute", new_value="mute_off")
            self.mute_button.config(text="MUTE OFF")
            logger.info("MUTE OFF")
            ToolTip(self.mute_button, text=self.translations[self.language]["mute_off"], bootstyle=self.boot_stl)
            self.val.set(self.volume_before_mute)
            self.scale_lbl.config(text=self.volume_before_mute)
            self.change_volume()
        else:
            self.volume_before_mute = self.player.volume
            self.player.mute = True
            self.settings.overwrite_data(key="mute", new_value="mute_on")
            self.mute_button.config(text="MUTE ON")
            logger.info("MUTE ON")
            ToolTip(self.mute_button, text=self.translations[self.language]["mute_on"], bootstyle=self.boot_stl)
            self.val.set(0)
            self.scale_lbl.config(text="0")
            self.change_volume()

    def check_end(self, _, time):
        if self.player.duration is None or self.player.playback_time is None:
            return

        if self.player.playback_time >= self.player.duration - 0.5:
            self.on_track_end()

    def stop_audio(self):
        if self.player.playback_time:
            logger.info("Zatrzymano odtwarzanie")
            self.player.stop()
            self.player.pause = False
            self.text_info2.config(text=self.translations[self.language]["select"])
            ToolTip(self.text_info2, text=self.translations[self.language]["select"], bootstyle=self.boot_stl)
            self.stop_animation()
            self.start_time.config(text="00:00")
            self.end_time.config(text="00:00")
            self.progress_val.set(0)
            self.play_button.config(text="▶️")
            ToolTip(self.play_button, text=self.translations[self.language]["play"], bootstyle=self.boot_stl)

    def change_style(self, style):
        self.boot_stl = style
        self.settings.overwrite_data(key="theme", new_value=style)

        self.text_info2.config(bootstyle=f"inverse-{self.boot_stl}")
        self.open_window_button.config(bootstyle=self.boot_stl)
        self.del_button.config(bootstyle=self.boot_stl)
        self.progress_scale.config(bootstyle=self.boot_stl)
        self.prev_button.config(bootstyle=self.boot_stl)
        self.stop_button.config(bootstyle=self.boot_stl)
        self.play_button.config(bootstyle=self.boot_stl)
        self.next_button.config(bootstyle=self.boot_stl)
        self.shuffle_button.config(bootstyle=self.boot_stl)
        self.play_mode_button.config(bootstyle=self.boot_stl)
        self.mute_button.config(bootstyle=self.boot_stl)
        self.volume_scale.config(bootstyle=self.boot_stl)

        if not self.player.playback_time and not self.player.pause:
            ToolTip(self.text_info2, text=self.translations[self.language]["select"], bootstyle=self.boot_stl)
        else:
            ToolTip(self.text_info2, text=self.title, bootstyle=self.boot_stl)
        if self.player.pause == True:
            ToolTip(self.play_button, text=self.translations[self.language]["play"], bootstyle=self.boot_stl)
        else:
            ToolTip(self.play_button, text=self.translations[self.language]["pause"], bootstyle=self.boot_stl)
        ToolTip(self.stop_button, text=self.translations[self.language]["stop"], bootstyle=self.boot_stl)
        ToolTip(self.next_button, text=self.translations[self.language]["next"], bootstyle=self.boot_stl)
        ToolTip(self.prev_button, text=self.translations[self.language]["previous"], bootstyle=self.boot_stl)
        if self.player.mute == True:
            ToolTip(self.mute_button, text=self.translations[self.language]["mute_on"], bootstyle=self.boot_stl)
        else:
            ToolTip(self.mute_button, text=self.translations[self.language]["mute_off"], bootstyle=self.boot_stl)
        ToolTip(self.open_window_button, text=self.translations[self.language]["add_new"], bootstyle=self.boot_stl)
        ToolTip(self.del_button, text=self.translations[self.language]["del_track"], bootstyle=self.boot_stl)
        if self.shuffle_mode:
            ToolTip(self.shuffle_button, text=self.translations[self.language]["shuffle_on"], bootstyle=self.boot_stl)
        else:
            ToolTip(self.shuffle_button, text=self.translations[self.language]["shuffle_off"], bootstyle=self.boot_stl)
        ToolTip(self.play_mode_button, text=self.translations[self.language][f'{self.play_mode}_mode'], bootstyle=self.boot_stl)

        self.error.set(f"{self.translations[self.language]["theme_change_confirm"]} {style.title()}")
        logger.info(f"Zmieniono motyy na {style.title()}")

    def change_language(self, lang):
        self.language = lang
        self.settings.overwrite_data(key="lang", new_value=self.language)

        self.menubar.entryconfigure(0, label=self.translations[self.language]["file"])
        self.filemenu.entryconfigure(0, label=self.translations[self.language]["theme_change"])
        self.filemenu.entryconfigure(1, label=self.translations[self.language]["lang_change"])
        self.filemenu.entryconfigure(3, label=self.translations[self.language]["exit"])

        self.text_info1.config(text=self.translations[self.language]["now_playing"])
        if not self.player.playback_time and not self.player.pause:
            self.text_info2.config(text=self.translations[self.language]["select"])
            ToolTip(self.text_info2, text=self.translations[self.language]["select"], bootstyle=self.boot_stl)


        self.open_window_button.config(text=self.translations[self.language]["add"])
        self.del_button.config(text=self.translations[self.language]["del"])

        self.right_click_menu.entryconfigure(0, label=self.translations[self.language]["copy"])
        self.right_click_menu.entryconfigure(2, label=self.translations[self.language]["play_pause"])
        self.right_click_menu.entryconfigure(4, label=self.translations[self.language]["del"])

        if self.player.pause == True:
            ToolTip(self.play_button, text=self.translations[self.language]["play"], bootstyle=self.boot_stl)
        else:
            ToolTip(self.play_button, text=self.translations[self.language]["pause"], bootstyle=self.boot_stl)
        ToolTip(self.stop_button, text=self.translations[self.language]["stop"], bootstyle=self.boot_stl)
        ToolTip(self.next_button, text=self.translations[self.language]["next"], bootstyle=self.boot_stl)
        ToolTip(self.prev_button, text=self.translations[self.language]["previous"], bootstyle=self.boot_stl)
        if self.player.mute == True:
            ToolTip(self.mute_button, text=self.translations[self.language]["mute_on"], bootstyle=self.boot_stl)
        else:
            ToolTip(self.mute_button, text=self.translations[self.language]["mute_off"], bootstyle=self.boot_stl)
        ToolTip(self.open_window_button, text=self.translations[self.language]["add_new"], bootstyle=self.boot_stl)
        ToolTip(self.del_button, text=self.translations[self.language]["del_track"], bootstyle=self.boot_stl)
        if self.shuffle_mode:
            ToolTip(self.shuffle_button, text=self.translations[self.language]["shuffle_on"], bootstyle=self.boot_stl)
        else:
            ToolTip(self.shuffle_button, text=self.translations[self.language]["shuffle_off"], bootstyle=self.boot_stl)



if __name__ == "__main__":
    root = tk.Tk()
    app = AppDisplay(root, URL_FILE, CACHE_FILE, SETTINGS_FILE, TRANSLATIONS_FILE, ICON_16, ICON_32, MUSIC_GIF)
    root.mainloop()
    logger.info("Zakonczono dzialanie programu")
