from time import sleep
import subprocess
import multiprocessing
import json

def thread_():
    subprocess.run(["python", "modLogStream.py"])

def main():
    while True:
        thread = multiprocessing.Process(target=thread_, args=())
        thread.start()

        sleep(60 * 15)

        with open("modLogStreamPID.json", "r") as f:
            pid = json.load(f)

        subprocess.run(["kill", pid])
        thread.terminate()

        print("Killed", pid, "\n")

if __name__ == "__main__":
    main()