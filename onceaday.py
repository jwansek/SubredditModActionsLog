import modLogStream 
from time import sleep 
import threading

def dayThread():
    modLogStream.onceaday()

while True:
    # sleep(60 * 60 * 24)
    threading.Thread(target = dayThread, args=()).start()
    sleep(60 * 60 * 24)
