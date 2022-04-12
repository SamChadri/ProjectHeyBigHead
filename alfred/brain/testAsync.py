import asyncio
import random
import time
from concurrent.futures import *

def worker(name, queue):
    print("worker starting...")
    # Get a "work item" out of the queue.
    sleep_for = queue.get_wait()

    # Sleep for the "sleep_for" seconds.
    time.sleep(sleep_for)

    # Notify the queue that the "work item" has been processed.
    queue.task_done()


    print(f'{name} has slept for {sleep_for:.2f} seconds')

def worker_callback(future):
    print("Worker finished task")


async def main():
    # Create a queue that we will use to store our "workload".
    queue = asyncio.Queue()
    worker_queue = asyncio.Queue()
    loop = asyncio.get_event_loop()
    executor = ThreadPoolExecutor(max_workers=1)
    # Generate random timings and put them into the queue.
    total_sleep_time = 0
    # Create three worker tasks to process the queue concurrently.
    tasks = []
    for i in range(3):
        #task = loop.create_task(worker(f'worker-{i}', queue))
        #tasks.append(task)
        #worker_queue.put_nowait(task)
        pass
    flag = True
    while flag:
        num = input("Please type in a number: ")
        num = int(num)
        print("Input received: " + str(num))
        if num == 0:
            flag = False
        sleep_for = random.uniform(0.05, num)
        total_sleep_time += sleep_for
        
        queue.put_nowait(sleep_for)
        #wker = await worker_queue.get()

        future = executor.submit(worker, f'worker-{num}', queue)
        future.add_done_callback(worker_callback)

        # Wait until the queue is fully processed.
        started_at = time.monotonic()
        #queue.join()
        total_slept_for = time.monotonic() - started_at
    # Cancel our worker tasks.

    executor.shutdown()
    for task in tasks:
        task.cancel()
    # Wait until all worker tasks are cancelled.
    await asyncio.gather(*tasks, return_exceptions=True)

    print('====')
    print(f'3 workers slept in parallel for {total_slept_for:.2f} seconds')
    print(f'total expected sleep time: {total_sleep_time:.2f} seconds')


loop = asyncio.get_event_loop()
loop.run_until_complete(main())