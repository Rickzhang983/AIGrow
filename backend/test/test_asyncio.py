import asyncio
import time

start = time.time()


def tic():
    return 'at %1.1f seconds' % (time.time() - start)


async def gr1():
    #while True:
        try:
            # Busy waits for a second, but we don't want to stick around...
            print('gr1 started work: {}'.format(tic()))
            # 暂停两秒，但不阻塞时间循环，下同
            await asyncio.sleep(2)
            print('gr1 ended work: {}'.format(tic()))
        except KeyboardInterrupt:
            return


async def gr2():
    # Busy waits for a second, but we don't want to stick around...
    print('gr2 started work: {}'.format(tic()))
    await asyncio.sleep(2)
    print('gr2 Ended work: {}'.format(tic()))


async def gr3():
    print("Let's do some stuff while the coroutines are blocked, {}".format(tic()))
    await asyncio.sleep(1)
    print("Done!{}".format(tic()))

# 事件循环
ioloop = asyncio.get_event_loop()

# tasks中也可以使用asyncio.ensure_future(gr1())..
tasks = [
    ioloop.create_task(gr1()),
    ioloop.create_task(gr2()),
    ioloop.create_task(gr3())
]
ioloop.run_until_complete(asyncio.wait(tasks))
ioloop.close()

import asyncio
from threading import Thread


async def production_task():
    i = 0
    while True:
        # 将consumption这个协程每秒注册一个到运行在线程中的循环，thread_loop每秒会获得一个一直打印i的无限循环任务
        asyncio.run_coroutine_threadsafe(consumption(i),
                                         thread_loop)
        await asyncio.sleep(1)  # 必须加await
        i += 1


async def consumption(i):
    while True:
        print("我是第{}任务".format(i))
        await asyncio.sleep(1)


def start_loop(loop):
    #  运行事件循环， loop以参数的形式传递进来运行
    asyncio.set_event_loop(loop)
    loop.run_forever()
    print ("start_loop")


thread_loop = asyncio.new_event_loop()  # 获取一个事件循环
thread_loop.create_task(production_task())
run_loop_thread = Thread(target=start_loop, args=(thread_loop,))  # 将次事件循环运行在一个线程中，防止阻塞当前主线程
run_loop_thread.start()  # 运行线程，同时协程事件循环也会运行

#advocate_loop = asyncio.get_event_loop()  # 将生产任务的协程注册到这个循环中
#advocate_loop.run_until_complete(production_task())