import os
import tkinter as tk
from tkinter import ttk, messagebox, PhotoImage
from googletrans import Translator, LANGUAGES
import speech_recognition as sr
from gtts import gTTS
from playsound import playsound
import threading

class VoiceTranslatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Voice Translator")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Initialize translator and speech recognizer
        self.translator = Translator()
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Language options
        self.languages = list(LANGUAGES.values())
        self.language_codes = list(LANGUAGES.keys())
        
        # GUI Setup
        self.setup_ui()
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Voice Translator", font=('Helvetica', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=10)
        
        # Source language selection
        ttk.Label(main_frame, text="Source Language:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.source_lang = ttk.Combobox(main_frame, values=self.languages, state="readonly")
        self.source_lang.grid(row=1, column=1, sticky=tk.EW, pady=5)
        self.source_lang.current(self.languages.index('english'))
        
        # Target language selection
        ttk.Label(main_frame, text="Target Language:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.target_lang = ttk.Combobox(main_frame, values=self.languages, state="readonly")
        self.target_lang.grid(row=2, column=1, sticky=tk.EW, pady=5)
        self.target_lang.current(self.languages.index('spanish'))
        
        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=3, column=0, columnspan=3, pady=10)
        
        # Record button
        self.record_btn = ttk.Button(buttons_frame, text="Record & Translate", command=self.start_recording)
        self.record_btn.pack(side=tk.LEFT, padx=5)
        
        # Play translation button
        self.play_btn = ttk.Button(buttons_frame, text="Play Translation", command=self.play_translation, state=tk.DISABLED)
        self.play_btn.pack(side=tk.LEFT, padx=5)
        
        # Clear button
        self.clear_btn = ttk.Button(buttons_frame, text="Clear", command=self.clear_text)
        self.clear_btn.pack(side=tk.LEFT, padx=5)
        
        # Text frames
        text_frame = ttk.Frame(main_frame)
        text_frame.grid(row=4, column=0, columnspan=3, sticky=tk.NSEW, pady=10)
        
        # Original text
        ttk.Label(text_frame, text="Original Text:").pack(anchor=tk.W)
        self.original_text = tk.Text(text_frame, height=8, wrap=tk.WORD)
        self.original_text.pack(fill=tk.BOTH, expand=True)
        
        # Translated text
        ttk.Label(text_frame, text="Translated Text:").pack(anchor=tk.W, pady=(10, 0))
        self.translated_text = tk.Text(text_frame, height=8, wrap=tk.WORD)
        self.translated_text.pack(fill=tk.BOTH, expand=True)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=5, column=0, columnspan=3, sticky=tk.EW)
        
        # Configure grid weights
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
    def start_recording(self):
        threading.Thread(target=self.record_and_translate, daemon=True).start()
    
    def record_and_translate(self):
        self.update_status("Listening... Speak now")
        self.record_btn.config(state=tk.DISABLED)
        
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source)
                audio = self.recognizer.listen(source, timeout=5)
            
            self.update_status("Processing speech...")
            
            # Get source language code
            source_lang_code = self.language_codes[self.languages.index(self.source_lang.get().lower())]
            
            # Recognize speech
            recognized_text = self.recognizer.recognize_google(audio, language=source_lang_code)
            self.original_text.delete(1.0, tk.END)
            self.original_text.insert(tk.END, recognized_text)
            
            # Translate text
            self.update_status("Translating...")
            target_lang_code = self.language_codes[self.languages.index(self.target_lang.get().lower())]
            translation = self.translator.translate(recognized_text, src=source_lang_code, dest=target_lang_code)
            
            self.translated_text.delete(1.0, tk.END)
            self.translated_text.insert(tk.END, translation.text)
            
            # Save translation to audio file
            self.translation_audio_file = "translation_output.mp3"
            tts = gTTS(text=translation.text, lang=target_lang_code)
            tts.save(self.translation_audio_file)
            
            self.play_btn.config(state=tk.NORMAL)
            self.update_status("Translation complete. Click 'Play Translation' to hear it.")
            
        except sr.WaitTimeoutError:
            self.update_status("No speech detected. Try again.")
        except sr.UnknownValueError:
            self.update_status("Could not understand audio. Try again.")
        except sr.RequestError:
            self.update_status("Speech recognition service unavailable. Check internet connection.")
        except Exception as e:
            self.update_status(f"Error: {str(e)}")
        finally:
            self.record_btn.config(state=tk.NORMAL)
    
    def play_translation(self):
        if hasattr(self, 'translation_audio_file') and os.path.exists(self.translation_audio_file):
            threading.Thread(target=self._play_audio, args=(self.translation_audio_file,), daemon=True).start()
    
    def _play_audio(self, audio_file):
        try:
            playsound(audio_file)
        except Exception as e:
            messagebox.showerror("Playback Error", f"Could not play audio: {str(e)}")
    
    def clear_text(self):
        self.original_text.delete(1.0, tk.END)
        self.translated_text.delete(1.0, tk.END)
        self.play_btn.config(state=tk.DISABLED)
        self.update_status("Ready")
        
        # Delete audio file if exists
        if hasattr(self, 'translation_audio_file') and os.path.exists(self.translation_audio_file):
            try:
                os.remove(self.translation_audio_file)
            except:
                pass
    
    def update_status(self, message):
        self.status_var.set(message)
        self.root.update_idletasks()

if __name__ == "__main__":
    root = tk.Tk()
    app = VoiceTranslatorApp(root)
    root.mainloop()