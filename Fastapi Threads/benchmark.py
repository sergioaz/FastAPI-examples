import time
import httpx
import asyncio

async def benchmark():
    """
    Runs benchmark requests to /no_thread and /yes_thread endpoints.
    """
    print("--- Starting benchmark ---")
    num_requests = 20

    # Set a longer timeout to accommodate the slow, blocking endpoint
    timeout = httpx.Timeout(60.0, connect=5.0)
    async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=timeout) as client:

        # Benchmark /thread
        print(f"Running {num_requests} requests to /thread...")
        start_time = time.time()
        tasks_yes_thread = [client.get("/thread") for _ in range(num_requests)]
        await asyncio.gather(*tasks_yes_thread)
        end_time = time.time()
        duration_yes_thread = end_time - start_time
        print(f"Batch of {num_requests} requests to /thread took: {duration_yes_thread:.4f} seconds")

        print("-" * 20)
        # Benchmark /generator
        print(f"Running {num_requests} requests to /generator...")
        start_time = time.time()
        tasks_generator = [client.get("/generator") for _ in range(num_requests)]
        await asyncio.gather(*tasks_generator)
        end_time = time.time()
        duration_generator = end_time - start_time
        print(f"Batch of {num_requests} requests to /generator took: {duration_generator:.4f} seconds")

        print("-" * 20)
        # Benchmark /cycle
        print(f"Running {num_requests} requests to /cycle...")
        start_time = time.time()
        tasks_cycle = [client.get("/cycle") for _ in range(num_requests)]
        await asyncio.gather(*tasks_cycle)
        end_time = time.time()
        duration_cycle = end_time - start_time
        print(f"Batch of {num_requests} requests to /cycle took: {duration_cycle:.4f} seconds")

        print("-" * 20)
        # Benchmark /cycle_sleep
        print(f"Running {num_requests} requests to /cycle_sleep...")
        start_time = time.time()
        tasks_cycle_sleep = [client.get("/cycle_sleep") for _ in range(num_requests)]
        await asyncio.gather(*tasks_cycle_sleep)
        end_time = time.time()
        duration_cycle_sleep = end_time - start_time
        print(f"Batch of {num_requests} requests to /cycle_sleep took: {duration_cycle_sleep:.4f} seconds")

        print("-" * 20)

        # background task
        # Benchmark /background
        print(f"Running {num_requests} requests to /background...")
        start_time = time.time()
        tasks_cycle_sleep = [client.get("/background") for _ in range(num_requests)]
        await asyncio.gather(*tasks_cycle_sleep)
        end_time = time.time()
        duration_cycle_sleep = end_time - start_time
        print(f"Batch of {num_requests} requests to /background took: {duration_cycle_sleep:.4f} seconds")

        print("-" * 20)

    print("--- Benchmark finished ---")

async def main():
    await benchmark()

if __name__ == "__main__":
    asyncio.run(main())