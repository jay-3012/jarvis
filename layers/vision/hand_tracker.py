import cv2
import pyautogui
import structlog
import time
import numpy as np

logger = structlog.get_logger()

class HandTracker:
    """
    SIMULATED Hand Tracker (Fallback Mode).
    Since MediaPipe is failing, we use the Mouse as the "Hand" 
    and keyboard 'SPACE' as the "Pinch" gesture.
    """
    def __init__(self):
        self.is_running = False
        try:
            self.screen_width, self.screen_height = pyautogui.size()
        except:
             self.screen_width, self.screen_height = 1920, 1080

    def start(self):
        """Start the simulated camera loop."""
        self.is_running = True
        logger.info("Hand Tracker (SIMULATION) Started. Move mouse to control.")
        self._loop()

    def _loop(self):
        """Main tracking loop."""
        # Create a blank black image to represent "Camera View"
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        
        while self.is_running:
            # 1. Get Mouse Position (Simulated Hand)
            mouse_x, mouse_y = pyautogui.position()
            
            # 2. Map Mouse to Window Coordinates (scaled down)
            win_x = int((mouse_x / self.screen_width) * 640)
            win_y = int((mouse_y / self.screen_height) * 480)
            
            # Reset Image
            img[:] = 0 
            
            # 3. Check for Pinch (Using Keyboard or Mouse Click)
            # We'll use cv2.waitKey to detect SPACE for pinch simulation visually
            key = cv2.waitKey(1)
            is_pinching = (key == 32) # Spacebar temporarily
            # OR check if actual mouse is down
            # is_pinching = pyautogui.mouseDown() check is hard without polling
            
            # Draw "Hand"
            color = (0, 255, 0) if is_pinching else (0, 0, 255) # Green=Pinch, Red=Open
            cv2.circle(img, (win_x, win_y), 15, color, cv2.FILLED)
            cv2.putText(img, "SIMULATION MODE", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(img, "Move Mouse = Move Hand", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
            
            # Show
            cv2.imshow("Jarvis Vision (Simulated)", img)
            
            if key & 0xFF == ord('q'):
                self.stop()
                break

    def stop(self):
        self.is_running = False
        cv2.destroyAllWindows()
