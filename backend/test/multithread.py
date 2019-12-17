import asyncio
import time

import _thread
import time


def testThread( sec):
    while True:
        print("Hello from thread")
        time.sleep(sec)

_thread.start_new_thread(testThread, (2,))
while True:
    print ("----------")
    time.sleep(3)



async def run1(t):
    i = t
    while(1):
        print ("run1 %d"%i)
        i = i+1
        await  asyncio.sleep(2)
async def run2():
    while (1):
        print ("run2")
        await  asyncio.sleep(1)

async def main():
    while (1):
        print ("main run")
        await asyncio.sleep(1)

loop = asyncio.get_event_loop()
loop.create_task(run1(2))
loop.create_task(main())
#loop.create_task(run2())
#_thread.start_new_thread(run2(),())
#_thread.start_new_thread(run1(2),(1))
loop.run_forever()
loop.close()