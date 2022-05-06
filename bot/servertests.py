#!/usr/bin/env python3

import asyncio
import threading
import json
import time
import concurrent.futures
from time import sleep
import random
import time
from threading import Thread

KillThread = False


def worker(instance):
    global KillThread
    start = time.clock()
    time_taken = random.uniform(0, 10)
    print('thread %s starting' % (instance))
    while (time.clock() - start) < time_taken:
        sleep(.01)
        if KillThread:
            print('thread %s killed' % (instance))
            return
    print('thread %s : completed in %s sec' % (instance, time_taken))


for i in range(0, 10):
    Thread(target=worker, args=(i,)).start()

sleep(5)
KillThread = True

async def test(data):
    while True:
        try:
            print(str(data))
            sleep(data)
        except Exception as e:
            print(str(e))

            break

asyncio.run(test(1))


