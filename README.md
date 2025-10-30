# Sydney Voice Assistant

This is a Python-based voice assistant named Sydney that can perform various tasks based on voice commands.

## Features

-   **Web Browsing:** Open Google, LinkedIn, and YouTube.
-   **Music:** Play songs from a predefined library.
-   **News:** Fetch and read the latest news headlines.
-   **Jokes:** Tell a random joke.
-   **Web Search:** Search for a given query on Google.
-   **YouTube Control:** Pause, play, mute, and unmute YouTube videos.
-   **Wikipedia:** Search for a topic and get a summary.

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure the API key:**
    -   Rename the `config.py.template` file to `config.py`.
    -   Open `config.py` and replace `"YOUR_NEWS_API_KEY"` with your actual NewsAPI key.

4.  **Run the application:**
    ```bash
    python "mega project 1.py"
    ```

## Usage

-   Activate the assistant by saying "Sydney."
-   Once activated, you can give it a command, such as:
    -   "Open Google"
    -   "Play not like us"
    -   "Tell me a joke"
    -   "Search for Python tutorials"

## How to Add Music

1.  Open the `music.json` file.
2.  Add a new entry with the song name as the key and the YouTube link as the value.
    ```json
    {
      "new song name": "https://youtube.com/link-to-song"
    }
    ```
