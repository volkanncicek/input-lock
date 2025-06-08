# Input Lock 🧼

A modern desktop application that temporarily locks your computer's input (keyboard and mouse) for a specified duration, perfect for taking cleaning breaks or preventing accidental input during maintenance tasks.

## Features

✨ **Modern UI** - Clean, intuitive interface with automatic dark/light theme detection  
⏱️ **Timed Lock** - Default 2-minute lock duration (configurable)  
🔓 **Emergency Unlock** - Customizable key combination (Shift + Alt + L by default)  
🌍 **Multi-language Support** - Automatic system language detection  
🖱️ **Complete Input Blocking** - Suppresses both keyboard and mouse input  
🪟 **Windows Integration** - Native Windows theming and title bar styling  
📱 **Fullscreen Overlay** - Immersive lock screen with countdown timer  

## Requirements

- Windows 10/11
- Python 3.7+
- Required Python packages (see Installation)

## Installation

### Option 1: Download Pre-built Executable (Recommended)

1. **Download the latest release**
   - Go to the [GitHub Releases](../../releases) page
   - Download the latest `input-lock.exe` file
   - No Python installation required!

2. **Run the application**
   - Double-click the downloaded `input-lock.exe` file
   - The application will start immediately

### Option 2: Run from Source

1. **Clone or download this repository**
   ```bash
   git clone <repository-url>
   cd input-lock
   ```

2. **Install required dependencies**
   ```bash
   pip install -r requirements.txt
   ```

   **Required packages:**
   - `tkinter` (usually included with Python)
   - `pynput` - For keyboard/mouse monitoring
   - `Pillow` - For image processing
   - `darkdetect` - For system theme detection
   - `sv-ttk` - For modern tkinter themes
   - `pywinstyles` - For Windows-specific styling

## Usage

### Basic Usage

1. **Run the application**
   ```bash
   python main.py
   ```

2. **Lock your system**
   - Click the "Lock" button
   - Your screen will be locked with a fullscreen overlay
   - Mouse and keyboard input will be suppressed

3. **Unlock methods**
   - **Wait for timer**: The system automatically unlocks after 2 minutes
   - **Emergency unlock**: Press `Shift + Alt + L` simultaneously

### Lock Process

The application follows a simple 3-step process:

1. **🔒 Lock** - Click to start the locking process
2. **🧼 Clean** - Clean your keyboard/screen while input is blocked
3. **✅ Done** - System automatically unlocks or use emergency combo

## Contributing

If you scrolled down to this section, you most likely appreciate open source. If you want to contribute, please feel free to submit issues, feature requests, or pull requests to improve the application.

## License
This project is completely open source under the MIT License. Feel free to use, modify, and distribute it as you wish. See [LICENSE](LICENSE) for more details.