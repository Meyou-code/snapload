<div align="center">
  
  <img src="./assets/logo.png" alt="SnapLoad Logo" width="200"/>
  
  <h1>✨ SnapLoad — Snapchat Memories Downloader ✨</h1>

  <p>
    <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white" alt="Python"/>
    <img src="https://img.shields.io/badge/Front-HTML%2FCSS%2FJS-0ea5e9?logo=html5&logoColor=white" alt="Frontend"/>
    <img src="https://img.shields.io/badge/UI-pywebview-6d28d9?logo=webassembly&logoColor=white" alt="UI"/>
    <img src="https://img.shields.io/badge/Metadata-ExifTool-f97316" alt="ExifTool"/>
    <img src="https://img.shields.io/badge/Media-ffmpeg-007808?logo=ffmpeg&logoColor=white" alt="ffmpeg"/>
    <img src="https://img.shields.io/badge/Platform-Windows-0078d4?logo=windows&logoColor=white" alt="Windows"/>
    <img src="https://img.shields.io/badge/License-MIT-green?logo=open-source-initiative&logoColor=white" alt="MIT License"/>
  </p>

  <p>
    SnapLoad is a desktop application designed as a <strong>friendly alternative to Snapchat's official tool for downloading Memories</strong>. 
    The official tool can be unintuitive or fail on large volumes of data. SnapLoad allows anyone to download Memories easily, with <strong>enhanced features</strong>
  </p>
</div>

---
## 📑 Table of Contents

- [🚀 Key Features](#-key-features)
- [🖥️ Quick Preview](#️-quick-preview)
- [⚡️ Getting Started](#️-getting-started)
- [🕷️ Known Issues](#️-known-issues)
- [🗺️ Roadmap](#️-roadmap)
- [🙏 Acknowledgments](#-acknowledgments)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)

---

## 🚀 Key Features

- 📥 **Parallel downloads** with automatic retry mechanism
- ♻️ **Automatic resume** using `download_state.json` (tracks success/failures) and full JSON recovery
- 🧠 **Stable speed & ETA** : dynamic averaging (files/s + MB/s) displayed in real-time
- 🧭 **Enhanced metadata** : localized dates + GPS coordinates written to EXIF/QuickTime tags via ExifTool (photos and videos)
- 🖥️ **Web/Desktop interface** : clean UI with progress bars, statistics, and Start/Stop controls
- 📂 **ZIP handling** : automatically unpacks and organizes Snapchat-provided ZIPs into clean folders
- 👶 **Beginner-friendly guide** : tutorial included for requesting your Snapchat data

---

## 🖥️ Quick Preview

<div align="center">
  <img src="./assets/screen1.png" alt="Main interface" width="800"/>
  <p><i>Memories retrieval guide interface</i></p>
</div>

<div align="center">
  <img src="./assets/screen.png" alt="Download in progress" width="800"/>
  <p><i>Main download interface</i></p>
</div>

---

## ⚡️ Getting Started

### 1️⃣ Installation

Download the setup executable from the [Releases](../../releases) page.

### 2️⃣ Windows SmartScreen Warning

The SnapLoad setup file is not verified by Windows SmartScreen, so you may see a warning about an unknown executable. Don't panic! Simply follow these two steps:

<div align="center">
  <img src="./assets/smartscreen.png" alt="SmartScreen warning" width="600"/>
  <p><i>Click "More info" then "Run anyway"</i></p>
</div>

1. Click on **"More info"**  
2. Click on **"Run anyway"**

### 3️⃣ Enjoy!

That's it! Start backing up your Snapchat memories.

---

## 🕷️ Known Issues

> 👻 **Snapchat-side bug**: Occasionally, requesting data from Snapchat may result in an empty export (issue observed during testing). Despite contacting support, I haven't received a response or solution.

> ⚠️ **Beta status**: The app is currently in beta and may have bugs. Please don't hesitate to report any issues you encounter!

---

## 🗺️ Roadmap

- Linux support
- Faster download

---

## 🙏 Acknowledgments

This project leverages several excellent open-source tools:

- **[ffmpeg](https://ffmpeg.org/)** - Multimedia framework for video/audio processing
- **[ExifTool](https://exiftool.org/)** - Metadata reading and writing
- **[devices.css](https://github.com/picturepan2/devices.css)** - Beautiful device mockups for the UI

---

## 🤝 Contributing

Contributions are welcome! Feel free to:
- 🐛 Report bugs
- 💡 Suggest new features
- 🔧 Submit pull requests

---

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

<div align="center">
  <p>Built with ❤️ by meyou to simplify backing up your Snapchat memories 👻 </p>
  <p>
    <a href="#-table-of-contents">⬆ Back to top</a>
  </p>
</div>