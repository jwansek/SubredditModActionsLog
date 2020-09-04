from time import sleep
import multiprocessing
import subprocess
import json

def theThread():
    subprocess.run(["python3", "subreddit.py"])

while True:
    thread = multiprocessing.Process(target=theThread, args=())
    thread.start()

    sleep(60*60*2)

    with open("sml.json", "r") as f:
        pid = json.load(f)
    
    subprocess.run(["kill", str(pid)])
    thread.terminate()
    print("Killed: ", pid)