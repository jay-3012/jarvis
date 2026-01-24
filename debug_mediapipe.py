import mediapipe
print("MediaPipe Path:", mediapipe.__file__)
print("Dir(mediapipe):", dir(mediapipe))
try:
    import mediapipe.solutions
    print("Success: import mediapipe.solutions")
except ImportError as e:
    print("Fail: import mediapipe.solutions ->", e)

try:
    from mediapipe.python.solutions import hands
    print("Success: from mediapipe.python.solutions import hands")
except ImportError as e:
    print("Fail: from mediapipe.python.solutions import hands ->", e)
