import speech_recognition as sr
import webbrowser
import pyttsx3
import pyautogui
import wikipedia
import requests
import json
import config  # For API key

# --- INITIALIZATION ---
recognizer = sr.Recognizer()
engine = pyttsx3.init()
music_library = {}


# --- HELPER FUNCTIONS ---
def set_voice_to_female():
    """Sets the text-to-speech voice to a female voice if available."""
    voices = engine.getProperty('voices')
    if len(voices) > 1:
        engine.setProperty('voice', voices[1].id)
    else:
        print("Female voice not found, using default.")
        engine.setProperty('voice', voices[0].id)


def speak(text):
    """Converts text to speech."""
    engine.say(text)
    engine.runAndWait()


def listen_for_command(prompt="Listening..."):
    """Listens for a voice command and returns it as text."""
    with sr.Microphone() as source:
        print(prompt)
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
            command = recognizer.recognize_google(audio, language='en-in')
            print(f"You said: {command}")
            return command.lower()
        except sr.UnknownValueError:
            speak("Sorry, I did not understand that.")
            return None
        except sr.RequestError:
            speak("Sorry, my speech service is down.")
            return None
        except sr.WaitTimeoutError:
            print("Listening timed out.")
            return None


def load_music_library(filepath="music.json"):
    """Loads the music library from a JSON file."""
    global music_library
    try:
        with open(filepath, 'r') as f:
            music_library = json.load(f)
        print("Music library loaded successfully.")
    except FileNotFoundError:
        print(f"Error: {filepath} not found. Music playback will not work.")
    except json.JSONDecodeError:
        print(f"Error: Could not decode {filepath}. Check for syntax errors.")


# --- COMMAND HANDLERS ---
def open_google():
    """Opens Google in the web browser."""
    speak("Opening Google.")
    webbrowser.open("https://www.google.com")


def open_linkedin():
    """Opens LinkedIn in the web browser."""
    speak("Opening LinkedIn.")
    webbrowser.open("https://www.linkedin.com")


def search_youtube():
    """Asks for a query and searches it on YouTube."""
    speak("What would you like to search for on YouTube?")
    query = listen_for_command("Waiting for YouTube query...")
    if query:
        search_query = '+'.join(query.split())
        url = f"https://www.youtube.com/results?search_query={search_query}"
        webbrowser.open(url)
        speak(f"Searching for {query} on YouTube.")


def play_song(command):
    """Plays a song from the music library."""
    try:
        song_name = command.split(" ", 1)[1]
        link = music_library.get(song_name)
        if link:
            speak(f"Playing {song_name}.")
            webbrowser.open(link)
        else:
            speak(f"Sorry, I couldn't find {song_name} in my library.")
    except IndexError:
        speak("You need to tell me which song to play.")


def get_news():
    """Fetches and reads top news headlines."""
    speak("Fetching the latest news headlines.")
    try:
        url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={config.newsapi}"
        r = requests.get(url)
        r.raise_for_status()  # Raises an exception for bad status codes
        data = r.json()
        articles = data.get('articles', [])
        for i, article in enumerate(articles):
            if i >= 5:  # Limit to 5 articles
                break
            speak(article['title'])
    except requests.exceptions.RequestException as e:
        speak("Sorry, I couldn't fetch the news right now.")
        print(f"Error fetching news: {e}")


def tell_joke():
    """Tells a random joke."""
    try:
        response = requests.get("https://v2.jokeapi.dev/joke/Any?type=single")
        response.raise_for_status()
        joke_data = response.json()
        joke = joke_data.get('joke')
        if joke:
            speak(joke)
            print("Joke:", joke)
        else:
            speak("Sorry, I couldn't find a single-part joke.")
    except requests.exceptions.RequestException as e:
        speak("Sorry, something went wrong while fetching the joke.")
        print("Error:", e)


def search_web(command):
    """Searches the web for a given query."""
    try:
        query = command.replace("search", "").strip()
        if query:
            speak(f"Searching for {query} on the web.")
            url = f"https://www.google.com/search?q={'+'.join(query.split())}"
            webbrowser.open(url)
        else:
            speak("What would you like me to search for?")
    except Exception as e:
        speak("I encountered an error while trying to search.")
        print(e)


def control_youtube(action):
    """Controls YouTube playback (play, pause, mute, unmute)."""
    key_map = {'pause': 'k', 'play': 'k', 'mute': 'm', 'unmute': 'm'}
    if action in key_map:
        pyautogui.press(key_map[action])
        speak(f"Video {action}d.")


def search_wikipedia():
    """Asks for a topic and summarizes the Wikipedia page."""
    speak("What topic would you like to search for on Wikipedia?")
    topic = listen_for_command("Waiting for Wikipedia topic...")
    if topic:
        try:
            speak(f"Searching for {topic} on Wikipedia.")
            wikipedia.set_lang("en")
            summary = wikipedia.summary(topic, sentences=2)
            speak("Here's a summary:")
            speak(summary)
            print(summary)
        except wikipedia.exceptions.DisambiguationError as e:
            speak("There were multiple results. Please be more specific.")
            print(f"Options: {e.options[:5]}")
        except wikipedia.exceptions.PageError:
            speak(f"Sorry, I couldn't find a Wikipedia page for {topic}.")
        except Exception as e:
            speak("Sorry, an error occurred while searching Wikipedia.")
            print(e)


# --- COMMAND MAPPING ---
COMMANDS = {
    "open google": open_google,
    "open linkedin": open_linkedin,
    "search youtube": search_youtube,
    "play": play_song,  # Uses startswith
    "news": get_news,
    "tell me a joke": tell_joke,
    "search": search_web,  # Uses startswith
    "pause": lambda: control_youtube('pause'),
    "play video": lambda: control_youtube('play'),
    "resume video": lambda: control_youtube('play'),
    "mute": lambda: control_youtube('mute'),
    "unmute": lambda: control_youtube('unmute'),
    "wikipedia": search_wikipedia,
}


def process_command(command):
    """Processes the user command by matching it against the command map."""
    # Exact matches first
    if command in COMMANDS:
        COMMANDS[command]()
        return

    # Partial matches for commands like "play <song>" or "search <query>"
    for key, func in COMMANDS.items():
        if command.startswith(key):
            if key == "play" or key == "search":
                func(command)
            else:  # for cases like "pause video"
                func()
            return

    speak("Sorry, I don't know how to do that.")


# --- MAIN EXECUTION ---
if __name__ == "__main__":
    set_voice_to_female()
    load_music_library()
    speak("Initializing Sydney.")

    # Main loop to listen for activation word
    while True:
        r = sr.Recognizer()
        print("Recognizing...")
        try:
            with sr.Microphone() as source:
                print("Listening for activation word 'Sydney'...")
                audio = r.listen(source, timeout=5, phrase_time_limit=2)
            word = r.recognize_google(audio, language='en-in')

            if "sydney" in word.lower():
                speak("Yes Sir?")
                command = listen_for_command("I am now active...")
                if command:
                    process_command(command)

        except sr.WaitTimeoutError:
            # This is normal, just continue listening
            continue
        except Exception as e:
            # Catch other potential errors during activation listening
            print(f"An error occurred: {e}")
