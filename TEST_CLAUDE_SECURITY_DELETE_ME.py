# Test fixture: intentionally vulnerable. Delete with branch.
import pickle, subprocess

API_KEY = "sk-ant-1234567890abcdef"           # hardcoded secret

def load(blob):
    return pickle.loads(blob)                  # arbitrary code execution

def run(user_input):
    subprocess.run(f"echo {user_input}", shell=True)  # shell injection
