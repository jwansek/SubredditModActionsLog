import modLogStream
from time import sleep

while True:
    modLogStream.onceaday()
    sleep(60 * 60 * 24)
