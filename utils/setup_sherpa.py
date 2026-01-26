import os
import urllib.request
import tarfile
import shutil
import sys

# Correct URL
MODEL_URL = "https://huggingface.co/csukuangfj/vits-mms-hin/resolve/main/vits-mms-hin.tar.bz2"
MODEL_FILENAME = "vits-mms-hin.tar.bz2"
DEST_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "models")

def setup_sherpa_model():
    print(f"DEBUG: DEST_DIR={DEST_DIR}")
    if not os.path.exists(DEST_DIR):
        os.makedirs(DEST_DIR)
        print("DEBUG: Created DEST_DIR")
    
    file_path = os.path.join(DEST_DIR, MODEL_FILENAME)
    extract_path = os.path.join(DEST_DIR, "vits-mms-hin")

    print(f"DEBUG: Downloading from {MODEL_URL}")
    print("DEBUG: This may take a minute...")
    sys.stdout.flush()

    try:
        # Download with headers to avoid 401/403
        req = urllib.request.Request(
            MODEL_URL, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        )
        with urllib.request.urlopen(req) as response:
            with open(file_path, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)
            
        print("\nDEBUG: Download complete.")
        sys.stdout.flush()
        
        print("DEBUG: Extracting...")
        if file_path.endswith("tar.bz2"):
            with tarfile.open(file_path, "r:bz2") as tar:
                tar.extractall(path=DEST_DIR)
        
        print(f"DEBUG: Model extracted to: {extract_path}")
        
        # Cleanup
        if os.path.exists(file_path):
            os.remove(file_path)
        print("DEBUG: Cleanup done. SUCCESS.")
        return extract_path
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    setup_sherpa_model()
