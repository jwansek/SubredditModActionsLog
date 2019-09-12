import modLogStream
from time import sleep

while True:
    #sleep(60 * 60 * 14)
    modLogStream.onceaday()
    sleep(60 * 60 * 24)
