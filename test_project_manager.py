import asyncio
import os
import shutil
from layers.skills.code_assistant import CodeAssistant
from layers.skills.git_controller import GitController
from utils.logging import configure_logging

configure_logging()

async def main():
    test_dir = "test_project_manager_dir"
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    os.makedirs(test_dir)
    
    # Change to test dir for git ops
    original_cwd = os.getcwd()
    os.chdir(test_dir)
    
    try:
        print("\n--- 1. Testing CodeAssistant (Create) ---")
        code = CodeAssistant()
        # "create filename content"
        res = await code.execute({"command": "create hello.py print('Hello World')"})
        print(f"Result: {res}")
        
        if os.path.exists("hello.py"):
            print("SUCCESS: File created.")
        else:
            print("FAILURE: File not created.")

        print("\n--- 2. Testing GitController (Init & Commit) ---")
        git_ctrl = GitController()
        
        # Init
        await git_ctrl.execute({"command": "init"})
        
        # Configure user if needed (local only)
        # We might need to run raw subprocess commands if GitController is restricted, 
        # but GitController just passes "git ...", so "config" works
        await git_ctrl.execute({"command": 'config user.email "jarvis@test.com"'})
        await git_ctrl.execute({"command": 'config user.name "Jarvis Test"'})
        
        # Add
        res = await git_ctrl.execute({"command": "add ."})
        print(f"Add Result: {res}")
        
        # Commit
        res = await git_ctrl.execute({"command": 'commit -m "Initial commit"'})
        print(f"Commit Result: {res}")
        
        if "Git Executed" in res or "successful" in res:
             print("SUCCESS: Git commit likely worked.")

        print("\n--- 3. Testing CodeAssistant (Read) ---")
        res = await code.execute({"command": "read hello.py"})
        print(f"Read Result: {res}")
        
        if "Hello World" in res:
            print("SUCCESS: Read content correctly.")

    finally:
        os.chdir(original_cwd)
        # Cleanup
        if os.path.exists(test_dir):
            try:
                shutil.rmtree(test_dir)
            except:
                pass

if __name__ == "__main__":
    asyncio.run(main())
