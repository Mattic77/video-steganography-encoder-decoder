import cv2
import numpy as np
from pathlib import Path

class VideoEncoderV2:
    """Encode du texte dans une vidéo avec 4 canaux parallèles (4 mots simultanés)"""
    
    MORSE_CODE = {
        'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.',
        'G': '--.', 'H': '....', 'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..',
        'M': '--', 'N': '-.', 'O': '---', 'P': '.--.', 'Q': '--.-', 'R': '.-.',
        'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
        'Y': '-.--', 'Z': '--..', '0': '-----', '1': '.----', '2': '..---',
        '3': '...--', '4': '....-', '5': '.....', '6': '-....', '7': '--...',
        '8': '---..', '9': '----.', ' ': '/'
    }
    
    def __init__(self, video_path, text_path, output_path, 
                 disc_radius=5, frames_per_dot=3, frames_per_dash=9, 
                 frames_per_gap=3, frame_rate=30, disc_color=(0, 0, 255)):
        """
        Initialise l'encodeur V2 avec 4 canaux parallèles
        
        Args:
            disc_radius: Rayon réduit à 5 pixels
            frames_per_dot: Point = 3 frames (plus rapide)
            frames_per_dash: Tiret = 9 frames (3× point)
            frames_per_gap: Gap = 3 frames
        """
        self.video_path = video_path
        self.text_path = text_path
        self.output_path = output_path
        self.disc_radius = disc_radius
        self.frames_per_dot = frames_per_dot
        self.frames_per_dash = frames_per_dash
        self.frames_per_gap = frames_per_gap
        self.frame_rate = frame_rate
        self.disc_color = disc_color
        
    def text_to_morse(self, text):
        """Convertit le texte en code Morse"""
        morse = []
        for char in text.upper():
            if char in self.MORSE_CODE:
                morse.append(self.MORSE_CODE[char])
            elif char == ' ':
                morse.append('/')
        return ' '.join(morse)
    
    def create_morse_sequence(self, morse_code):
        """Crée une séquence de frames pour le code Morse"""
        sequence = []
        for char in morse_code:
            if char == '.':
                sequence.extend([True] * self.frames_per_dot)
                sequence.extend([False] * self.frames_per_gap)
            elif char == '-':
                sequence.extend([True] * self.frames_per_dash)
                sequence.extend([False] * self.frames_per_gap)
            elif char == ' ':
                sequence.extend([False] * (self.frames_per_gap * 2))
            elif char == '/':
                sequence.extend([False] * (self.frames_per_gap * 4))
        return sequence
    
    def split_text_into_chunks(self, text, num_channels=4):
        """
        Divise le texte en 4 parties pour encodage parallèle
        
        Returns:
            List de 4 listes de mots
        """
        words = text.split()
        chunk_size = len(words) // num_channels
        remainder = len(words) % num_channels
        
        chunks = []
        start = 0
        for i in range(num_channels):
            # Distribuer les mots restants
            extra = 1 if i < remainder else 0
            end = start + chunk_size + extra
            chunk_words = words[start:end]
            chunks.append(' '.join(chunk_words))
            start = end
        
        return chunks
    
    def draw_disc(self, frame, x, y, visible):
        """Dessine un petit disque coloré"""
        if visible:
            cv2.circle(frame, (x, y), self.disc_radius, self.disc_color, -1)
        return frame
    
    def encode_video(self):
        """Encode le texte avec 4 canaux parallèles"""
        # Charger le texte
        with open(self.text_path, 'r', encoding='utf-8') as f:
            text = f.read().strip()
        
        # Diviser en 4 chunks
        chunks = self.split_text_into_chunks(text, num_channels=4)
        
        print(f"📝 Texte à encoder: {text}")
        print(f"\n🔄 Division en 4 canaux:")
        for i, chunk in enumerate(chunks):
            print(f"   Canal {i+1}: {chunk[:50]}{'...' if len(chunk) > 50 else ''}")
        
        # Convertir chaque chunk en séquence Morse
        sequences = []
        max_length = 0
        for i, chunk in enumerate(chunks):
            morse = self.text_to_morse(chunk)
            sequence = self.create_morse_sequence(morse)
            sequences.append(sequence)
            max_length = max(max_length, len(sequence))
            print(f"   Canal {i+1} Morse: {len(sequence)} frames")
        
        # Égaliser les longueurs (padding)
        for seq in sequences:
            while len(seq) < max_length:
                seq.append(False)
        
        print(f"\n📊 Longueur maximale: {max_length} frames")
        print(f"⏱️  Durée estimée: {max_length / self.frame_rate:.1f} secondes")
        
        # Ouvrir la vidéo
        cap = cv2.VideoCapture(self.video_path)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Créer le writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(self.output_path, fourcc, fps, (width, height))
        
        # Positions des 8 disques (4 canaux × 2 côtés)
        margin = 10  # Très proche du bord
        positions = [
            # Canal 1 (haut gauche et haut droite)
            {'left': (margin, height // 4), 'right': (width - margin, height // 4)},
            # Canal 2 (milieu-haut gauche et droite)
            {'left': (margin, height // 2 - height // 8), 'right': (width - margin, height // 2 - height // 8)},
            # Canal 3 (milieu-bas gauche et droite)
            {'left': (margin, height // 2 + height // 8), 'right': (width - margin, height // 2 + height // 8)},
            # Canal 4 (bas gauche et bas droite)
            {'left': (margin, 3 * height // 4), 'right': (width - margin, 3 * height // 4)},
        ]
        
        frame_count = 0
        sequence_index = 0
        
        print(f"\n🎬 Encodage en cours...")
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Dessiner les disques pour chaque canal
            if sequence_index < max_length:
                for channel_idx in range(4):
                    show_disc = sequences[channel_idx][sequence_index]
                    
                    if show_disc:
                        pos = positions[channel_idx]
                        # Dessiner à gauche et à droite
                        frame = self.draw_disc(frame, pos['left'][0], pos['left'][1], True)
                        frame = self.draw_disc(frame, pos['right'][0], pos['right'][1], True)
                
                sequence_index += 1
            
            out.write(frame)
            frame_count += 1
            
            # Progression
            if frame_count % 30 == 0:
                progress = (frame_count / total_frames) * 100
                print(f"   Progression: {progress:.1f}%")
        
        cap.release()
        out.release()
        
        print(f"\n✅ Encodage terminé!")
        print(f"📁 Vidéo sauvegardée: {self.output_path}")
        print(f"📊 Total de frames: {frame_count}")
        print(f"🎯 Débit: ~{len(text.split()) / (max_length / fps):.1f} mots/seconde")


def main():
    VIDEO_INPUT = "input_video.mp4"
    TEXT_INPUT = "message.txt"
    VIDEO_OUTPUT = "encoded_video_v2.mp4"
    
    # Créer un texte long si nécessaire
    if not Path(TEXT_INPUT).exists():
        long_text = """LA PROGRAMMATION EST UNE FORME DART MODERNE QUI PERMET DE CREER DES SOLUTIONS INNOVANTES 
POUR RESOUDRE LES PROBLEMES COMPLEXES DU MONDE NUMERIQUE ACTUEL CHAQUE LIGNE DE CODE REPRESENTE UNE IDEE 
UNE LOGIQUE ET UNE VISION POUR TRANSFORMER LES DONNEES EN INFORMATIONS UTILES LE DEVELOPPEMENT LOGICIEL 
COMBINE CREATIVITE RIGUEUR ET METHODOLOGIE POUR CONSTRUIRE DES APPLICATIONS ROBUSTES ET PERFORMANTES 
QUI REPONDENT AUX BESOINS DES UTILISATEURS DANS UN ENVIRONNEMENT TECHNOLOGIQUE EN CONSTANTE EVOLUTION"""
        
        with open(TEXT_INPUT, 'w', encoding='utf-8') as f:
            f.write(' '.join(long_text.split()))
        print(f"✅ Fichier {TEXT_INPUT} créé avec un long message")
    
    # Encoder
    encoder = VideoEncoderV2(
        video_path=VIDEO_INPUT,
        text_path=TEXT_INPUT,
        output_path=VIDEO_OUTPUT,
        disc_radius=5,          # Disques très petits
        frames_per_dot=3,       # Rapide: 3 frames
        frames_per_dash=9,      # Rapide: 9 frames
        frames_per_gap=3,       # Rapide: 3 frames
        frame_rate=30,
        disc_color=(0, 0, 255)  # Rouge
    )
    
    encoder.encode_video()


if __name__ == "__main__":
    main()