import os
import sys
sys.path.insert(0, os.path.abspath("."))
from extractor import extract_check_images

def test():
    print("Testing check extraction import...")
    sample_files = []
    for root, dirs, files in os.walk("."):
        if ".git" in root or "venv" in root or ".gemini" in root:
            continue
        for f in files:
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.pdf')) and ('check' in f.lower() or 'chk' in f.lower()):
                sample_files.append(os.path.join(root, f))
    
    print("Sample check files found:", sample_files)

if __name__ == "__main__":
    test()
