# Video Steganography Encoder & Decoder (V2)
A complete system for **encoding and decoding text inside a video** using visual signals.  
The project uses **4 parallel channels**, Morse-based encoding, and **red discs** displayed at the edges of the video frames.

This system is designed for experimentation in:
- Visual steganography
- Multi-channel communication
- Real-time video processing
- Signal detection & reconstruction
- Error correction (LanguageTool API)

---

## 🔥 Features

### ✅ **Encoding (VideoEncoderV2)**
- Splits the input text into **4 parallel channels**
- Converts text → Morse → signal sequence
- Encodes each channel using **red discs** (left/right)
- Generates a new video with embedded signals
- Adjustable parameters (radius, frames per dot/dash, speed, margins)
- Works with any input video (MP4 recommended)

### ✅ **Decoding (VideoDecoderV2)**
- Detects red discs in the video in real time
- Reconstructs 4 Morse streams simultaneously
- Converts Morse → text for each channel
- Rebuilds the **full message**
- Optional **API-based grammar correction**
- Real-time overlay: channels, signals, text, frame indicators
- Supports pause, save, mode switching

---

## 📂 Project Structure

