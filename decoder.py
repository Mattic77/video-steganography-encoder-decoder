import cv2
import numpy as np
import requests
import time

class VideoDecoderV2:
    """Décode une vidéo avec 4 canaux parallèles + correction API"""
    
    MORSE_TO_TEXT = {
        '.-': 'A', '-...': 'B', '-.-.': 'C', '-..': 'D', '.': 'E', '..-.': 'F',
        '--.': 'G', '....': 'H', '..': 'I', '.---': 'J', '-.-': 'K', '.-..': 'L',
        '--': 'M', '-.': 'N', '---': 'O', '.--.': 'P', '--.-': 'Q', '.-.': 'R',
        '...': 'S', '-': 'T', '..-': 'U', '...-': 'V', '.--': 'W', '-..-': 'X',
        '-.--': 'Y', '--..': 'Z', '-----': '0', '.----': '1', '..---': '2',
        '...--': '3', '....-': '4', '.....': '5', '-....': '6', '--...': '7',
        '---..': '8', '----.': '9', '/': ' '
    }
    
    def __init__(self, video_path, disc_radius=5, disc_color=(0, 0, 255)):
        self.video_path = video_path
        self.disc_radius = disc_radius
        self.disc_color = disc_color
        
    def detect_disc(self, frame, x, y):
        """Détection rapide de disque par couleur"""
        margin = 8
        x1 = max(0, x - margin)
        x2 = min(frame.shape[1], x + margin)
        y1 = max(0, y - margin)
        y2 = min(frame.shape[0], y + margin)
        
        roi = frame[y1:y2, x1:x2]
        if roi.size == 0:
            return False
        
        hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        
        # Masque rouge
        lower_red1 = np.array([0, 100, 100])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([170, 100, 100])
        upper_red2 = np.array([180, 255, 255])
        
        mask1 = cv2.inRange(hsv_roi, lower_red1, upper_red1)
        mask2 = cv2.inRange(hsv_roi, lower_red2, upper_red2)
        mask = cv2.bitwise_or(mask1, mask2)
        
        color_percentage = (np.sum(mask > 0) / mask.size) * 100
        return color_percentage > 12  # Seuil abaissé pour petits disques
    
    def morse_to_text(self, morse_code):
        """Convertit Morse en texte"""
        if not morse_code.strip():
            return ""
        
        words = morse_code.split(' / ')
        result = []
        
        for word in words:
            letters = word.split(' ')
            decoded_word = ''
            for letter in letters:
                if letter in self.MORSE_TO_TEXT:
                    decoded_word += self.MORSE_TO_TEXT[letter]
            if decoded_word:
                result.append(decoded_word)
        
        return ' '.join(result)
    
    def correct_text_with_api(self, text):
        """
        Corrige le texte avec l'API LanguageTool
        
        Returns:
            tuple: (texte_corrigé, nombre_corrections)
        """
        if not text.strip():
            return text, 0
        
        try:
            url = "https://api.languagetoolplus.com/v2/check"
            params = {
                'text': text,
                'language': 'fr-FR'  # Français
            }
            
            response = requests.post(url, data=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                corrected_text = text
                corrections = 0
                
                # Appliquer les corrections en ordre inverse
                for match in reversed(data.get('matches', [])):
                    if match.get('replacements'):
                        replacement = match['replacements'][0]['value']
                        offset = match['offset']
                        length = match['length']
                        corrected_text = (corrected_text[:offset] + 
                                        replacement + 
                                        corrected_text[offset + length:])
                        corrections += 1
                
                return corrected_text, corrections
            else:
                return text, 0
                
        except Exception as e:
            print(f"⚠️  Erreur API: {e}")
            return text, 0
    
    def draw_overlay(self, frame, channels_data, full_text, full_text_corrected, show_corrected=False):
        """
        Dessine l'overlay avec les 4 canaux + texte complet
        
        Args:
            channels_data: Liste de dicts avec 'morse', 'text', 'text_corrected', 'left_det', 'right_det'
            full_text: Texte complet reconstitué (brut)
            full_text_corrected: Texte complet reconstitué (corrigé)
            show_corrected: Afficher la version corrigée ou brute
        """
        height, width = frame.shape[:2]
        
        # Fond semi-transparent plus grand pour inclure le texte complet
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (width, 380), (0, 0, 0), -1)
        frame = cv2.addWeighted(overlay, 0.75, frame, 0.25, 0)
        
        # Titre principal
        title = "DECODAGE V2 - 4 CANAUX PARALLELES"
        cv2.putText(frame, title, (20, 30),
                   cv2.FONT_HERSHEY_DUPLEX, 0.8, (0, 255, 255), 2)
        
        # Mode affichage
        mode = "AVEC CORRECTION API" if show_corrected else "SANS CORRECTION"
        mode_color = (0, 255, 0) if show_corrected else (255, 255, 0)
        cv2.putText(frame, mode, (width - 300, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, mode_color, 2)
        
        # Afficher chaque canal
        y_offset = 60
        for i, data in enumerate(channels_data):
            # Numéro du canal avec indicateurs
            left_color = (0, 255, 0) if data['left_det'] else (100, 100, 100)
            right_color = (0, 255, 0) if data['right_det'] else (100, 100, 100)
            
            cv2.putText(frame, f"C{i+1}:", (20, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
            
            # Indicateurs gauche/droite
            cv2.circle(frame, (55, y_offset - 5), 5, left_color, -1)
            cv2.circle(frame, (75, y_offset - 5), 5, right_color, -1)
            
            # Texte décodé
            text_to_show = data['text_corrected'] if show_corrected else data['text']
            max_chars = 70
            if len(text_to_show) > max_chars:
                text_to_show = text_to_show[:max_chars] + "..."
            
            cv2.putText(frame, text_to_show, (95, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            
            y_offset += 50
        
        # === TEXTE COMPLET RECONSTITUÉ ===
        y_offset += 10
        cv2.line(frame, (20, y_offset), (width - 20, y_offset), (100, 100, 100), 1)
        y_offset += 25
        
        cv2.putText(frame, "TEXTE COMPLET:", (20, y_offset),
                   cv2.FONT_HERSHEY_DUPLEX, 0.7, (255, 255, 0), 2)
        
        y_offset += 30
        
        # Afficher le texte complet sur plusieurs lignes si nécessaire
        text_to_display = full_text_corrected if show_corrected else full_text
        max_chars_per_line = 90
        
        # Découper en lignes
        words = text_to_display.split()
        lines = []
        current_line = ""
        
        for word in words:
            if len(current_line) + len(word) + 1 <= max_chars_per_line:
                current_line += word + " "
            else:
                if current_line:
                    lines.append(current_line.strip())
                current_line = word + " "
        
        if current_line:
            lines.append(current_line.strip())
        
        # Afficher max 2 lignes (les plus récentes)
        for line in lines[-2:]:
            cv2.putText(frame, line, (20, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 1)
            y_offset += 25
        
        # Compteur de mots
        word_count = len(text_to_display.split())
        cv2.putText(frame, f"Mots: {word_count}", (20, y_offset + 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        
        # Instructions
        instructions = [
            "Q: Quitter | ESPACE: Pause | C: Correction API ON/OFF",
            "S: Sauvegarder"
        ]
        y_inst = height - 45
        for inst in instructions:
            cv2.putText(frame, inst, (20, y_inst),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            y_inst += 20
        
        return frame
    
    def decode_video_live(self):
        """Décode la vidéo avec 4 canaux en direct"""
        cap = cv2.VideoCapture(self.video_path)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        
        # Positions des 8 disques
        margin = 10
        positions = [
            {'left': (margin, height // 4), 'right': (width - margin, height // 4)},
            {'left': (margin, height // 2 - height // 8), 'right': (width - margin, height // 2 - height // 8)},
            {'left': (margin, height // 2 + height // 8), 'right': (width - margin, height // 2 + height // 8)},
            {'left': (margin, 3 * height // 4), 'right': (width - margin, 3 * height // 4)},
        ]
        
        print("🚀 Décodage V2 en cours...")
        print("   4 canaux parallèles détectés")
        print("   Appuyez sur 'C' pour activer/désactiver la correction API\n")
        
        # État de chaque canal
        channels = [
            {
                'morse': '', 'text': '', 'text_corrected': '',
                'in_signal': False, 'signal_start': 0, 'last_signal_end': 0,
                'left_det': False, 'right_det': False
            }
            for _ in range(4)
        ]
        
        frame_count = 0
        paused = False
        show_corrected = False
        last_correction_time = 0
        correction_interval = 2.0  # Corriger toutes les 2 secondes
        
        delay = int(1000 / fps)
        
        while cap.isOpened():
            if not paused:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Détecter et décoder chaque canal
                for ch_idx in range(4):
                    pos = positions[ch_idx]
                    
                    # Détection
                    left_det = self.detect_disc(frame, pos['left'][0], pos['left'][1])
                    right_det = self.detect_disc(frame, pos['right'][0], pos['right'][1])
                    signal_detected = left_det and right_det
                    
                    channels[ch_idx]['left_det'] = left_det
                    channels[ch_idx]['right_det'] = right_det
                    
                    ch = channels[ch_idx]
                    
                    # Décodage Morse
                    if signal_detected:
                        if not ch['in_signal']:
                            ch['in_signal'] = True
                            ch['signal_start'] = frame_count
                            
                            if ch['last_signal_end'] > 0:
                                gap = ch['signal_start'] - ch['last_signal_end']
                                if gap > 10:
                                    ch['morse'] += " / "
                                elif gap > 5:
                                    ch['morse'] += " "
                    else:
                        if ch['in_signal']:
                            ch['in_signal'] = False
                            signal_duration = frame_count - ch['signal_start']
                            ch['last_signal_end'] = frame_count
                            
                            if signal_duration <= 6:
                                ch['morse'] += "."
                            else:
                                ch['morse'] += "-"
                            
                            # Décoder le texte
                            try:
                                ch['text'] = self.morse_to_text(ch['morse'])
                            except:
                                pass
                
                # Correction API périodique
                current_time = time.time()
                if show_corrected and (current_time - last_correction_time) > correction_interval:
                    for ch in channels:
                        if ch['text'] and not ch['text_corrected']:
                            corrected, num_corrections = self.correct_text_with_api(ch['text'])
                            ch['text_corrected'] = corrected
                            if num_corrections > 0:
                                print(f"✓ Canal corrigé: {num_corrections} corrections")
                    last_correction_time = current_time
                
                frame_count += 1
            
            # Affichage
            # Reconstituer le texte complet
            full_text = ' '.join([ch['text'] for ch in channels if ch['text']])
            full_text_corrected = ' '.join([ch.get('text_corrected', ch['text']) 
                                           for ch in channels if ch['text']])
            
            channels_data = [
                {
                    'morse': ch['morse'][-40:],
                    'text': ch['text'],
                    'text_corrected': ch.get('text_corrected', ch['text']),
                    'left_det': ch['left_det'],
                    'right_det': ch['right_det']
                }
                for ch in channels
            ]
            
            display_frame = self.draw_overlay(frame.copy(), channels_data, 
                                             full_text, full_text_corrected, 
                                             show_corrected)
            cv2.imshow('Decodage V2 - 4 Canaux', display_frame)
            
            # Gestion des touches
            key = cv2.waitKey(delay) & 0xFF
            if key == ord('q') or key == ord('Q'):
                print("\n❌ Arrêt demandé")
                break
            elif key == ord(' '):
                paused = not paused
                print(f"\n{'⏸️  PAUSE' if paused else '▶️  LECTURE'}")
            elif key == ord('c') or key == ord('C'):
                show_corrected = not show_corrected
                print(f"\n{'✅ Correction API ACTIVÉE' if show_corrected else '⚠️  Correction API DÉSACTIVÉE'}")
                # Forcer une correction immédiate
                if show_corrected:
                    last_correction_time = 0
            elif key == ord('s') or key == ord('S'):
                # Sauvegarder
                self.save_results(channels, show_corrected)
        
        cap.release()
        cv2.destroyAllWindows()
        
        # Résultats finaux
        print(f"\n{'='*70}")
        print(f"✅ DÉCODAGE TERMINÉ - RÉSULTATS")
        print(f"{'='*70}")
        
        for i, ch in enumerate(channels):
            print(f"\n📺 CANAL {i+1}:")
            print(f"   Morse: {ch['morse'][:100]}{'...' if len(ch['morse']) > 100 else ''}")
            print(f"   Texte brut: {ch['text']}")
            if show_corrected and ch.get('text_corrected'):
                print(f"   Texte corrigé: {ch['text_corrected']}")
        
        # Texte complet reconstitué
        print(f"\n{'='*70}")
        print(f"📝 TEXTE COMPLET RECONSTITUÉ:")
        print(f"{'='*70}")
        full_text_final = ' '.join([ch['text'] for ch in channels if ch['text']])
        print(f"\n{full_text_final}")
        
        if show_corrected:
            full_text_corrected_final = ' '.join([ch.get('text_corrected', ch['text']) 
                                                  for ch in channels if ch['text']])
            print(f"\n📝 TEXTE COMPLET CORRIGÉ:")
            print(f"{'='*70}")
            print(f"\n{full_text_corrected_final}")
        
        print(f"\n{'='*70}")
        print(f"📊 Statistiques:")
        print(f"   - Mots décodés: {len(full_text_final.split())}")
        print(f"   - Caractères: {len(full_text_final)}")
        print(f"{'='*70}\n")
        
        return channels
    
    def save_results(self, channels, with_correction):
        """Sauvegarde les résultats dans un fichier"""
        filename = "decoded_results_v2.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("RÉSULTATS DÉCODAGE V2 - 4 CANAUX PARALLÈLES\n")
            f.write("=" * 70 + "\n\n")
            
            for i, ch in enumerate(channels):
                f.write(f"CANAL {i+1}:\n")
                f.write(f"{'─' * 70}\n")
                f.write(f"Morse: {ch['morse']}\n\n")
                f.write(f"Texte brut:\n{ch['text']}\n\n")
                
                if with_correction and ch.get('text_corrected'):
                    f.write(f"Texte corrigé:\n{ch['text_corrected']}\n\n")
                
                f.write("\n")
            
            # Texte complet reconstitué
            f.write("=" * 70 + "\n")
            f.write("TEXTE COMPLET RECONSTITUÉ:\n")
            f.write("=" * 70 + "\n")
            
            full_text = ' '.join([ch['text_corrected' if with_correction else 'text'] 
                                  for ch in channels if ch['text']])
            f.write(full_text)
        
        print(f"\n💾 Résultats sauvegardés dans: {filename}")


def main():
    VIDEO_INPUT = "encoded_video_v2.mp4"
    
    print("🚀 Démarrage du décodeur V2...\n")
    
    decoder = VideoDecoderV2(
        video_path=VIDEO_INPUT,
        disc_radius=5,
        disc_color=(0, 0, 255)
    )
    
    channels = decoder.decode_video_live()
    
    print("\n✅ Décodage terminé!")


if __name__ == "__main__":
    main()