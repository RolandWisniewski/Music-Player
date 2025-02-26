import logging
import json
import mpv
import yt_dlp
import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import re
import locale
from yt_dlp import YoutubeDL
from PIL import Image
import time
import random

locale.setlocale(locale.LC_NUMERIC, "C")

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H-%M:%S",
    filename="log.log"
    # filename=None
)

logger = logging.getLogger(__name__)

class FileHandling:
    def __init__(self, file):
        self.file = file
        with open(self.file) as f:
            try:
                self.data = dict(json.load(f))
                self.data = dict(sorted(self.data.items()))
            except:
                self.data = dict()

    def add_new(self, name, url):
        self.data[name] = url
        with open(self.file, 'w') as f:
            json.dump(self.data, f)

    def remove(self, pos):
        key_name = [k for i, k in enumerate(self.data) if i == pos]
        del self.data[key_name[0]]
        with open(self.file, 'w') as f:
            json.dump(self.data, f)
    
    def show(self):
        return self.data


class AppDisplay:
    def __init__(self, root, file):
        logger.info("Uruchomiono odtwarzacz")
        self.root = root
        # self.root.title("Odtwarzacz muzyki YouTube 🎶")
        self.root.title("MimiPlayer")
        small_icon = tk.PhotoImage(file="icon-16.png")
        large_icon = tk.PhotoImage(file="icon-32.png")
        self.root.iconphoto(False, large_icon, small_icon)

        window_width = 380
        window_height = 440
        self.screen_width = root.winfo_screenwidth()
        self.screen_height = root.winfo_screenheight()
        x = (self.screen_width/2) - (window_width/2)
        y = (self.screen_height/2) - (window_height/2)

        # self.root.geometry("380x380")
        self.root.geometry('%dx%d+%d+%d' % (window_width, window_height, x, y))
        self.root.resizable(False,False)

        self.boot_stl = "dark"
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
        self.filemenu.add_cascade(label="Zmień motyw", menu=self.changemenu)
        self.filemenu.add_separator()
        self.filemenu.add_command(label="Wyjście", command=root.quit)
        self.menubar.add_cascade(label="Plik", menu=self.filemenu)
        self.root.config(menu=self.menubar)

        self.right_click_menu = tk.Menu(root, tearoff=0)
        self.right_click_menu.add_command(label="Kopiuj")
        self.right_click_menu.add_separator()
        self.right_click_menu.add_command(label="Play/Pause")
        self.right_click_menu.add_separator()
        self.right_click_menu.add_command(label="Usuń")

        self.data = FileHandling(file)
        self.player = mpv.MPV(ytdl=True, video=False)
        self.player.observe_property("playback-time", self.check_end)

        self.gif_file = "music_gif.gif"
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

        self.text_info1 = tk.Label(self.header, text="Aktualnie puszczany utwór:")
        self.text_info1.grid(row=1, column=1, pady=2)

        self.title = "Wybierz coś"
        self.text_info2 = ttk.Label(self.header, text=self.title, bootstyle=f"inverse-{self.boot_stl}", font=("bold"), wraplength=350)
        self.text_info2.grid(row=2, column=1, pady=2)

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

        self.open_window_button = ttk.Button(self.list_space, text="Dodaj", bootstyle=self.boot_stl, takefocus=False, command=self.open_new_window)
        self.open_window_button.grid(row=0, column=2, pady=2)

        self.del_button = ttk.Button(self.list_space, text="Usuń", bootstyle=self.boot_stl, takefocus=False, command=self.delete_url)
        self.del_button.grid(row=1, column=2, pady=2)

        self.progress_bar = tk.Frame(root)
        self.progress_bar.grid(row=2, column=0, padx=5, pady=5)

        self.seeking = False
        self.start_progress = 0

        self.start_time = tk.Label(self.progress_bar, text="00:00")
        self.start_time.grid(row=0, column=0, padx=5, pady=5)

        self.progress_val = tk.IntVar(value=self.start_progress)
        self.progress_scale = ttk.Scale(self.progress_bar, variable=self.progress_val, bootstyle=self.boot_stl, orient=tk.HORIZONTAL, from_=0, to=100, length=240)
        self.progress_val.trace('w', self.trace_progress)
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

        self.stop_button = ttk.Button(self.buttons, text="⏹", bootstyle=self.boot_stl, takefocus=False, command=self.stop_audio)
        self.stop_button.grid(row=0, column=2, padx=5, pady=5)

        self.play_button = ttk.Button(self.buttons, text="▶️", bootstyle=self.boot_stl, takefocus=False, command=self.toggle_play_pause)
        self.play_button.grid(row=0, column=3, padx=5, pady=5)

        self.next_button = ttk.Button(self.buttons, text="⏭️", bootstyle=self.boot_stl, takefocus=False, command=self.play_next)
        self.next_button.grid(row=0, column=4, padx=5, pady=5)

        self.toggle_buttons = tk.Frame(root)
        self.toggle_buttons.grid(row=4, column=0, padx=5, pady=5)

        self.shuffle_button = ttk.Button(self.toggle_buttons, text="SHUFFLE OFF", bootstyle=self.boot_stl, takefocus=False, command=self.toggle_shuffle)
        self.shuffle_button.grid(row=0, column=0, padx=3, pady=5)

        self.play_mode_button = ttk.Button(self.toggle_buttons, text="NEXT MODE", bootstyle=self.boot_stl, takefocus=False, command=self.toggle_play_mode)
        self.play_mode_button.grid(row=0, column=1, padx=3, pady=5)

        self.volume_frame = tk.Frame(root)
        self.volume_frame.grid(row=5, column=0, padx=5, pady=5)

        self.mute_button = ttk.Button(self.volume_frame, text="MUTE OFF", bootstyle=self.boot_stl, takefocus=False, command=self.mute)
        self.mute_button.grid(row=0, column=0)
        self.volume_before_mute = 100
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

        self.shuffle_mode = False
        self.play_mode = "next"
        self.on_top = False

    def do_popup1(self, event=None):
        e_widget = event.widget
        self.mylist.event_generate('<Button-1>', x=event.x, y=event.y)
        self.right_click_menu.entryconfigure("Kopiuj", command=lambda: e_widget.event_generate("<<Copy>>"))
        self.right_click_menu.entryconfigure("Play/Pause", command=self.toggle_play_pause)
        self.right_click_menu.entryconfigure("Usuń", command=self.delete_url)
        self.right_click_menu.tk.call("tk_popup", self.right_click_menu, event.x_root, event.y_root)

    def do_popup2(self, event=None):
        e_widget = event.widget
        self.new_right_click_menu.entryconfigure("Wytnij", command=lambda: e_widget.event_generate("<<Cut>>"))
        self.new_right_click_menu.entryconfigure("Kopiuj", command=lambda: e_widget.event_generate("<<Copy>>"))
        self.new_right_click_menu.entryconfigure("Wklej", command=lambda: e_widget.event_generate("<<Paste>>"))
        self.new_right_click_menu.entryconfigure("Zaznacz wszystko", command=lambda: e_widget.select_range(0, 'end'))
        self.new_right_click_menu.tk.call("tk_popup", self.new_right_click_menu, event.x_root, event.y_root)

    def set_value(self, event=None):
        self.seeking = True
        self.progress_scale.event_generate('<Button-3>', x=event.x, y=event.y)
        return 'break'

    def update_progress(self):
        if self.player.time_pos is not None and self.player.duration is not None:
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
            if self.seeking == False:
                progress_percent = min((self.player.time_pos / self.player.duration) * 100, 100)
                self.progress_val.set(progress_percent)
        self.root.after(500, self.update_progress)

    def trace_progress(self, *args):
        self.trace_progress_val = int(self.progress_scale.get())

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
            self.new_window.title("Dodaj nowy utwór")
            window_width = 500
            window_height = 140
            self.screen_width = root.winfo_screenwidth()
            self.screen_height = root.winfo_screenheight()
            x = (self.screen_width/2) - (window_width/2)
            y = (self.screen_height/2) - (window_height/2)
            self.new_window.geometry('%dx%d+%d+%d' % (window_width, window_height, x, y))
            # self.new_window.geometry("440x140")
            self.new_window.resizable(False,False)

            self.new_right_click_menu = tk.Menu(root, tearoff=0)
            self.new_right_click_menu.add_command(label="Wytnij")
            self.new_right_click_menu.add_command(label="Kopiuj")
            self.new_right_click_menu.add_command(label="Wklej")
            self.new_right_click_menu.add_separator()
            self.new_right_click_menu.add_command(label="Zaznacz wszystko")

            self.url_entry = ttk.Label(self.new_window, bootstyle=self.boot_stl, text='Link do YouTube:').grid(row=0, column=0, sticky=tk.W, pady=2)
            self.name_entry = ttk.Label(self.new_window, bootstyle=self.boot_stl, text='Nazwa:').grid(row=1, column=0, sticky=tk.W, pady=2)
            self.e1 = ttk.Entry(self.new_window, bootstyle=self.boot_stl, width=40)
            self.check_button = ttk.Button(self.new_window, bootstyle=self.boot_stl, takefocus=False, text='Wyszukaj nazwę', command=self.get_video_title)
            self.check_button.grid(row=0, column=2, pady=2)
            self.entry_text = tk.StringVar()
            self.e2 = ttk.Entry(self.new_window, textvariable=self.entry_text, bootstyle=self.boot_stl, width=40)
            self.e1.grid(row=0, column=1, pady=2)
            self.e2.grid(row=1, column=1, pady=2)

            self.entry_text.trace("w", lambda *args: self.character_limit())

            self.e1.bind("<Button-3><ButtonRelease-3>", self.do_popup2)
            self.e2.bind("<Button-3><ButtonRelease-3>", self.do_popup2)

            self.add_button = ttk.Button(self.new_window, text="Dodaj", bootstyle=self.boot_stl, takefocus=False, command=self.add_new_url)
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
                self.error_sec_win.set("Niepoprawny link do YouTube")
                logger.info("Niepoprawny link do YouTube")
                return

            if url in self.data.show().values():
                self.error_sec_win.set(f"Podany link jest już na liście pod nazwą '{list(filter(lambda key: self.data.show()[key] == url, self.data.show()))[0]}'")
                logger.info(f"Podany link jest juz na liscie pod nazwa '{list(filter(lambda key: self.data.show()[key] == url, self.data.show()))[0]}'")
                return

            ydl_opts = {"quiet": True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                res = info.get("title", "Nieznany tytuł")
                self.e2.delete(0, tk.END)
                self.e2.insert(END, res)
        else:
            self.error_sec_win.set("Wprowadź URL")
            logger.info("Wprowadz URL")
            return

    def character_limit(self):
        if len(self.entry_text.get()) > 40:
            self.entry_text.set(self.entry_text.get()[:40])
            self.error_sec_win.set("Osiągnięto limit znaków")

    def add_new_url(self):
        url = self.e1.get().strip()        
        name = self.e2.get().strip()
        
        if not url:
            self.error_sec_win.set("Wprowadź URL")
            logger.info("Wprowadz URL")
            return

        youtube_regex = re.compile(r'^(https?://)?(www\.)?(youtube\.com|youtu\.?be)/.+$')
        if not youtube_regex.match(url):
            self.error_sec_win.set("Niepoprawny link do YouTube")
            logger.info("Niepoprawny link do YouTube")
            return

        if url in self.data.show().values():
            self.error_sec_win.set(f"Podany link jest już na liście pod nazwą '{list(filter(lambda key: self.data.show()[key] == url, self.data.show()))[0]}'")
            logger.info(f"Podany link jest juz na liscie pod nazwa '{list(filter(lambda key: self.data.show()[key] == url, self.data.show()))[0]}'")
            return

        if not name:
            self.error_sec_win.set("Wprowadź nazwę")
            logger.info("Wprowadz nazwe")
            return

        if name in self.data.show():
            self.error_sec_win.set(f"Nazwa '{name}' jest już na liście")
            logger.info(f"Nazwa '{name}' jest juz na liscie")
            return

        self.data.show()[name] = url
        with open('url.json', 'w') as f:
            json.dump(self.data.show(), f)

        self.error_sec_win.set("Pomyślnie dodano nowy utwór!")
        logger.info(f"Dodano '{name}' do listy")
        self.mylist.insert(tk.END, name)
        self.e1.delete(0, tk.END)
        self.e2.delete(0, tk.END)

    def delete_url(self):
        cs = self.mylist.curselection()
        if not cs:
            self.error.set("Nie wybrano żadnego utworu")
            logger.info("Nie wybrano zadnego utworu")
            return None
        res = tk.messagebox.askquestion("Usuwanie utworu", "Na pewno usunąć wybrany utwór?")
        if res == 'yes':
            self.error.set("Usunięto wybrany utwór z listy")
            logger.info(f"Usunieto '{list(self.data.show().keys())[cs[0]]}' z listy")
            self.data.remove(cs[0])
            self.mylist.delete(cs)

    def clear_error_text(self):
        self.error.set("")
        self.root.after(6000, self.clear_error_text)

    def clear_error_text_sec_win(self):
        self.error_sec_win.set("")
        self.root.after(6000, self.clear_error_text_sec_win)

    def fetch_audio_url(self):
        cs = self.mylist.curselection()
        if not cs:
            self.error.set("Nie wybrano żadnego utworu")
            logger.info("Nie wybrano zadnego utworu")
            return None
        url = self.data.show()[list(self.data.show().keys())[cs[0]]]
        logger.info(f"Link do video: {url}")
        logger.info(f"Odtwarzanie utworu: {list(self.data.show().keys())[cs[0]]}")
        options = {'format': 'bestaudio', 'quiet': True}
        with YoutubeDL(options) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                self.title = list(filter(lambda key: self.data.show()[key] == url, self.data.show()))[0]
                self.text_info2.config(text=self.title)
                return info.get('url', None)
            except Exception as e:
                self.error.set("Nie udało się pobrać audio")
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
        audio_url = self.fetch_audio_url()
        if audio_url:
            logger.info(f"Link do audio: {audio_url}")
            self.player.play(audio_url)
            self.animation(current_frame=0)
            logger.info("Rozpoczeto animacje gif")
            self.player.pause = False
            self.play_button.config(text="⏸")

    def pause_audio(self):
        logger.info("Wstrzymano odtwarzanie")
        self.player.pause = True
        self.stop_animation()
        self.play_button.config(text="▶️")

    def resume_audio(self):
        logger.info("Wznowiono odtwarzanie")
        self.player.pause = False
        self.animation(current_frame=0)
        logger.info("Rozpoczeto animacje gif")
        self.play_button.config(text="⏸")

    def toggle_play_mode(self):
        modes = ["repeat", "next", "stop"]
        mode_labels = {"repeat": "REPEAT MODE", "next": "NEXT MODE", "stop": "STOP MODE"}
        current_index = modes.index(self.play_mode)
        self.play_mode = modes[(current_index + 1) % len(modes)]
        logger.info(mode_labels[self.play_mode])
        self.play_mode_button.config(text=mode_labels[self.play_mode])

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
        new_text = "SHUFFLE ON" if self.shuffle_mode else "SHUFFLE OFF"
        logger.info(new_text)
        self.shuffle_button.config(text=new_text)

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
        self.player.volume = volume
        self.scale_lbl.config(text=volume)

    def set_volume(self, volume):
        volume = int(float(volume))
        self.player.volume = volume
        if self.player.mute and volume > 0:
            self.player.mute = False

    def mute(self):
        if self.player.mute:
            self.player.mute = False
            self.mute_button.config(text="MUTE OFF")
            logger.info("MUTE OFF")
            self.val.set(self.volume_before_mute)
            self.scale_lbl.config(text=self.volume_before_mute)
            self.change_volume()
        else:
            self.volume_before_mute = self.player.volume
            self.player.mute = True
            self.mute_button.config(text="MUTE ON")
            logger.info("MUTE ON")
            self.val.set(0)
            self.scale_lbl.config(text="0")
            self.change_volume()

    def check_end(self, _, time):
        if self.player.playback_time and self.player.duration:
            if self.player.playback_time >= self.player.duration - 1:
                self.on_track_end()

    def stop_audio(self):
        if self.player.playback_time:
            logger.info("Zatrzymano odtwarzanie")
            self.player.stop()
            self.player.pause = False
            self.text_info2.config(text="Wybierz coś")
            self.stop_animation()
            self.start_time.config(text="00:00")
            self.end_time.config(text="00:00")
            self.progress.set(0)
            self.play_button.config(text="▶️")

    def change_style(self, style):
        self.error.set(f"Zmieniono styl na {style.title()}")
        logger.info(f"Zmieniono styl na {style.title()}")
        self.text_info2.config(bootstyle=f"inverse-{style}")
        self.open_window_button.config(bootstyle=style)
        self.del_button.config(bootstyle=style)
        self.progress_scale.config(bootstyle=style)
        self.prev_button.config(bootstyle=style)
        self.stop_button.config(bootstyle=style)
        self.play_button.config(bootstyle=style)
        self.next_button.config(bootstyle=style)
        self.shuffle_button.config(bootstyle=style)
        self.play_mode_button.config(bootstyle=style)
        self.mute_button.config(bootstyle=style)
        self.volume_scale.config(bootstyle=style)


if __name__ == "__main__":
    file = "url.json"
    root = tk.Tk()
    app = AppDisplay(root, file)
    root.mainloop()
    logger.info("Zakonczono dzialanie programu")
