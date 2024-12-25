import speech_recognition as sr
import webbrowser
import pyttsx3
from forex_python.converter import CurrencyRates
import pyautogui
import wikipedia

import importlib
import musicLibrary
importlib.reload(musicLibrary)
import requests

recognizer = sr.Recognizer()
engine = pyttsx3.init()
newsapi = "1744842a4c0f4eb69e078c97f97c86ff"
def set_voice_to_female():
    voices = engine.getProperty('voices')
    if len(voices) > 1:
        engine.setProperty('voice', voices[1].id)
    else:
        print("female voice not found")
        engine.setProperty('voice', voices[0].id)
def processcommand(c):
    if "open google" in c.lower():
        webbrowser.open("https://www.google.com")
    elif "open linkedin" in c.lower():
        webbrowser.open("https://www.linkedin.com")
    elif "open youtube" in c.lower():
        webbrowser.open("https://www.youtube.com")
    elif c.lower().startswith("play"):
        song = c.lower().split(" ")[1]
        link=musicLibrary.music[song]
        webbrowser.open(link)
    elif "news" in c.lower():
        r=requests.get("https://newsapi.org/v2/top-headlines?country=us&apiKey=1744842a4c0f4eb69e078c97f97c86ff")
        if r.status_code == 200:
            data = r.json()
            articles = data.get('articles',[])
            for article in articles:
                speak(article['title'])
    elif "tell me a joke" in c.lower():
        tell_joke()
    elif "search" in c.lower():
        search_query = c.lower().replace("search", "").strip()
        if search_query:
            web_search(search_query)
    elif "open youtube" in c.lower():
        speak("What would you like to search for on YouTube?")
        with sr.Microphone() as source:
            audio = recognizer.listen(source)
        query = recognizer.recognize_google(audio)
        open_youtube(query)
    elif "pause" in c.lower():
        control_youtube('pause')
    elif "play" in c.lower():
        control_youtube('play')
    elif "mute" in c.lower():
        control_youtube('mute')
    elif "unmute" in c.lower():
        control_youtube('unmute')
    elif "wikipedia" in c.lower():
        speak("What topic would you like to search for on Wikipedia?")
        with sr.Microphone() as source:
            audio = recognizer.listen(source)
        topic = recognizer.recognize_google(audio)
        speak(f"Searching for {topic} on Wikipedia.")
        summary = summarize_wikipedia(topic)
        if summary:
            speak(f"Here's the summary: {summary}")
            print(summary)
        
def web_search(query):
    search_query = '+'.join(query.split())  # Convert spaces to '+' for the URL
    url = f"https://www.google.com/search?q={search_query}"
    webbrowser.open(url)
    speak(f"Searching for {query} on the web.")
    print(f"Web search: {query}")
def open_youtube(query):
    search_query = '+'.join(query.split())  # Convert spaces to '+' for URL
    url = f"https://www.youtube.com/results?search_query={search_query}"
    webbrowser.open(url)
    speak(f"Searching for {query} on YouTube.")
    print(f"Searching for {query} on YouTube.")

# Control YouTube (Play/Pause)
def control_youtube(action):
    if action == 'pause':
        pyautogui.press('k')  # YouTube shortcut for pause/play
        speak("Video paused.")
    elif action == 'play':
        pyautogui.press('k')  # YouTube shortcut for pause/play
        speak("Video playing.")
    elif action == 'mute':
        pyautogui.press('m')  # YouTube shortcut for mute/unmute
        speak("Video muted.")
    elif action == 'unmute':
        pyautogui.press('m')  # YouTube shortcut for mute/unmute
        speak("Video unmuted.")
    
def summarize_wikipedia(query):
    try:
        # Search for the article on Wikipedia
        wikipedia.set_lang("en")  # Set language to English
        page = wikipedia.page(query)
        
        # Get the summary of the article
        summary = page.summary
        
        # Return the summary
        return summary
    except wikipedia.exceptions.DisambiguationError as e:
        speak("There were multiple results for your query. Please be more specific.")
        print(e.options)
        return None
    except wikipedia.exceptions.HTTPTimeoutError:
        speak("There was an issue fetching the Wikipedia page. Please try again later.")
        return None
    except Exception as e:
        speak("Sorry, I couldn't find any information on that topic.")
        print(e)
        return None


def tell_joke():
    try:
        response = requests.get("https://v2.jokeapi.dev/joke/Any?type=single")
        if response.status_code == 200:
            joke_data = response.json()
            if joke_data['type'] == 'single':
                joke = joke_data['joke']
            else:
                joke = f"{joke_data['setup']} - {joke_data['delivery']}"
            speak(joke)
            print("Joke: ", joke)
        else:
            speak("Sorry, I couldn't fetch a joke at the moment.")
            print("Error fetching joke.")
    except Exception as e:
        speak("Sorry, something went wrong while fetching the joke.")
        print("Error:", e)



    
    
def speak(text):
    engine.say(text)
    engine.runAndWait()
if __name__ == "__main__":
    set_voice_to_female()
    speak("intializing Sydney...........")
    while True:
        r = sr.Recognizer()
        print("Reconizing........")
        try:
            with sr.Microphone() as source:
                print("Listening........")
                audio = r.listen(source,timeout=3,phrase_time_limit=2)
            word = r.recognize_google(audio,language='en-in')
            if (word.lower() == "sydney"):
                speak("Yes Sir")
                with sr.Microphone() as source:
                    print("I am Now Active.......")
                    audio = r.listen(source)
                    command = r.recognize_google(audio,language='en-in')
                    
                    processcommand(command)

        except Exception as e:
            print(e)
    
                    

