import asyncio
import os
from layers.conversational.tts_sherpa import SherpaTTS

async def test_sherpa():
    print("Initializing Sherpa TTS...")
    tts = SherpaTTS()
    
    try:
        tts.initialize()
        print("Model Loaded.")
    except Exception as e:
        print(f"Failed to load model: {e}")
        return

    text = "Namaste. Main aapka assistant hoon. Yeh neural TTS offline chal raha hai."
    print(f"Speaking: {text}")
    
    await tts.synthesize(text)
    print("Done.")

if __name__ == "__main__":
    asyncio.run(test_sherpa())
