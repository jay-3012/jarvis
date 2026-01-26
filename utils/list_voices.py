import pyttsx3

def list_voices():
    try:
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        print(f"Found {len(voices)} voices:")
        for i, voice in enumerate(voices):
            print(f"ID: {voice.id}")
            print(f"Name: {voice.name}")
            print(f"Languages: {voice.languages}")
            print("-" * 30)
            
            # Check for Hindi
            if "hindi" in voice.name.lower() or "india" in voice.name.lower():
                 print(f"*** LIKELY HINDI VOICE FOUND: {voice.id} ***")
    except Exception as e:
        print(f"Error listing voices: {e}")

if __name__ == "__main__":
    list_voices()
