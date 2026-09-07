import os
import sys
import tempfile
import json

sys.path.insert(0, os.path.abspath("."))
from extractor import extract_check_images

def test():
    test_file = "checkimage.pdf"
    if not os.path.exists(test_file):
        test_file = "CHECK # 11112 - Wells Fargo.pdf"
    
    print(f"Testing extract_check_images on: {test_file}")
    temp_dir = tempfile.mkdtemp()
    try:
        data = extract_check_images(
            test_file,
            temp_dir,
            use_history=True,
            parent_name="VRT Services",
            client_name="TEST"
        )
        print("RESULT:")
        print(json.dumps(data, indent=2, default=str))
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test()
