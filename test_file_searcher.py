import asyncio
import os
import shutil
from layers.skills.file_searcher import FileSearcher
from utils.logging import configure_logging

configure_logging()

async def main():
    print("--- Testing FileSearcher ---")
    
    # 1. Create dummy files
    test_dir = "test_search_dir"
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    os.makedirs(f"{test_dir}/subdir")
    
    with open(f"{test_dir}/file1.txt", "w") as f: f.write("test")
    with open(f"{test_dir}/file2.log", "w") as f: f.write("test")
    with open(f"{test_dir}/subdir/file3.txt", "w") as f: f.write("test")
    
    searcher = FileSearcher()
    
    # 2. Search for *.txt
    print(f"Searching for *.txt in {test_dir}...")
    # Command: "*.txt test_search_dir"
    res = await searcher.execute({"command": f"*.txt {test_dir}"})
    print(f"Result:\n{res}")
    
    if "file1.txt" in res and "file3.txt" in res and "file2.log" not in res:
        print("SUCCESS: Found expected files.")
    else:
        print("FAILURE: Search results incorrect.")

    # Cleanup
    shutil.rmtree(test_dir)

if __name__ == "__main__":
    asyncio.run(main())
