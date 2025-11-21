import speech_recognition as sr
import pyttsx3
import threading

class SpeechTools:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.engine = pyttsx3.init()
        self._setup_voice()
        self.lock = threading.Lock()

    def _setup_voice(self):
        """Sets the voice to a female voice if available."""
        voices = self.engine.getProperty('voices')
        if len(voices) > 1:
            self.engine.setProperty('voice', voices[1].id)
        else:
            self.engine.setProperty('voice', voices[0].id)

    def speak(self, text: str):
        """Converts text to speech."""
        with self.lock:
            self.engine.say(text)
            self.engine.runAndWait()

    def listen(self, prompt: str = "Listening...") -> str:
        """Listens for a voice command and returns it as text."""
        with sr.Microphone() as source:
            print(prompt)
            try:
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)
                command = self.recognizer.recognize_google(audio, language='en-in')
                print(f"You said: {command}")
                return command.lower()
            except sr.UnknownValueError:
                return ""
            except sr.RequestError:
                print("Speech service down.")
                return ""
            except sr.WaitTimeoutError:
                return ""
