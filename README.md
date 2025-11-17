# Video Steganography Encoder & Decoder (V2)

A complete system for encoding and decoding text inside a video using
visual signals.\
The project uses **4 parallel channels**, Morse-based encoding, and
small **red discs** positioned at the edges of frames.

## 🚀 Features

### ▶️ Encoding (VideoEncoderV2)

-   Splits the input text into **4 parallel channels**
-   Converts text → Morse → visual signals
-   Encodes by showing/hiding red discs on each frame
-   Adjustable disc radius, frame speeds, margins, color
-   Generates a new video with embedded data

### ▶️ Decoding (VideoDecoderV2)

-   Real-time detection of red discs using HSV filtering
-   Reconstructs Morse sequences from timing
-   Converts Morse → text for each channel
-   Rebuilds the complete message
-   Optional **LanguageTool API** correction
-   Live overlay showing channels, indicators, decoded text

## 📁 Project Structure

    /VideoEncoderV2.py
    /VideoDecoderV2.py
    input_video.mp4
    encoded_video_v2.mp4
    message.txt
    decoded_results_v2.txt
    README.md

## 🛠 Installation

    pip install opencv-python numpy requests

## ▶️ Usage

### 🔵 Encode a message

    python VideoEncoderV2.py

### 🔴 Decode the video

    python VideoDecoderV2.py

### Keyboard controls:

  Key     Action
  ------- -----------------------
  Q       Quit
  Space   Pause / Resume
  C       Toggle API correction
  S       Save decoded results

## ⚙️ Configuration

    disc_radius=5
    frames_per_dot=3
    frames_per_dash=9
    frames_per_gap=3
    frame_rate=30
    disc_color=(0, 0, 255)

## 📜 License

MIT License -- free to use and modify.

## 👤 Author

**Younes Hadli**\
Master's student in Computer Science (France)\
AI • Video Processing • Backend Development
