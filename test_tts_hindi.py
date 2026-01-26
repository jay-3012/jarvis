import pyttsx3
import time

def test_hindi_voice():
    print("Initializing TTS Engine...")
    try:
        engine = pyttsx3.init()
    except Exception as e:
        print(f"Failed to init engine: {e}")
        return

    voices = engine.getProperty('voices')
    selected_voice = None
    search_term = "hindi"

    print(f"Scanning {len(voices)} voices for '{search_term}'...")

    for v in voices:
        # Check name and languages list
        if search_term.lower() in v.name.lower():
            selected_voice = v.id
            print(f"FOUND by name: {v.name}")
            break
            
        try:
            for lang in v.languages:
                if search_term.lower() in str(lang).lower():
                    selected_voice = v.id
                    print(f"FOUND by language: {v.name}")
                    break
        except: 
            pass
        if selected_voice: break

    if selected_voice:
        print(f"Setting voice to: {selected_voice}")
        engine.setProperty('voice', selected_voice)
        print("Speaking: Namaste, main Jarvis hoon.")
        engine.say("Namaste, main Jarvis hoon.")
        engine.runAndWait()
        print("Done.")
    else:
        print("No Hindi voice found. Speaking in default voice.")
        engine.say("I could not find a Hindi voice, but I am speaking.")
        engine.runAndWait()

if __name__ == "__main__":
    test_hindi_voice()
