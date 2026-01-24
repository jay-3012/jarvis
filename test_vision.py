import structlog
from layers.vision.hand_tracker import HandTracker
from utils.logging import configure_logging

configure_logging()

def main():
    print("--- Testing Vision Layer ---")
    print("Press 'q' in the camera window to exit.")
    
    tracker = HandTracker()
    try:
        tracker.start()
    except Exception as e:
        print(f"Vision Error: {e}")

if __name__ == "__main__":
    main()
