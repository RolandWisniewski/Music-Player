# MusicPlayer

YouTube Player is a Python-based GUI application that allows you to stream and control audio playback from YouTube videos. It features a playlist system, media controls, and integration with mpv for smooth playback.

### 🌟 Features

* Play audio directly from YouTube using youtube-dl.
* Playlist Management: Add, remove, and select songs from a list.
* Media Controls: Play, pause, skip, repeat, shuffle.
* Volume Control: Adjust and mute volume via a slider.
* Live Progress Bar: Tracks the current song's progress.
* Keyboard Shortcuts:
 * Space → Play/Pause
 * Enter/Double Click → Play selected song

## 📦 Installation

### Prerequisites

* Python 3.8+
* `pip` installed
* `mpv` media player installed on your system

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run the Application

```bash
python main.py
```

## 🎉 Screenshots

Example:

<p align="center">
 <img src="https://github.com/user-attachments/assets/3b309093-ae32-4e82-9d7f-6c344349901c" width="600">
</p>

<p align="center">
 <img src="https://github.com/user-attachments/assets/6e5b83f5-51be-4c3f-9beb-ddb4b0f588a1" width="600">
</p>

## 🧩 How It Works

1. Fetching and Playing Audio:
* The application retrieves the YouTube URL from a JSON file.
* It extracts the best available audio format using youtube-dl.
* The extracted stream URL is then played using mpv.
2. Playlist Management:
* A Listbox widget displays available songs.
* Selecting a song and pressing Enter or double-clicking plays it.
* Songs can be removed from the list.
3. Playback Controls
* The user can control playback via buttons or keyboard shortcuts.
* The progress bar updates every 500ms to reflect song position.
4. Shuffle & Repeat Modes
* Shuffle: When enabled, songs play in random order.
* Repeat:
 * `Off` → Stops after last song
 * `One` → Repeats current song
 * `All` → Loops through the playlist

## 🛠️ FAQ

1. "The player doesn't start!"
* Ensure mpv is installed and accessible via the system path.
* Try running mpv manually to confirm it's working.
2. "Songs won't play, but they are in the list."
* Check if youtube-dl is up to date:
```bash
pip install --upgrade youtube-dl
```
* The video may have been removed from YouTube.

## 😊 Contribution

Contributions are welcome! If you have ideas for optimization or new features, feel free to fork the repository and submit a pull request.

## 👤 Author
* Created by [RolandWisniewski](https://github.com/RolandWisniewski)

## 📜 License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
