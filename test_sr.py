import sys
try:
    import speech_recognition
    print("SUCCESS: speech_recognition is installed")
except ImportError as e:
    print(f"FAILURE: {e}")
except Exception as e:
    print(f"ERROR: {e}")
