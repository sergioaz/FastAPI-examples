import asyncio
import random
from typing import Set, List
import time

# Simulated work function
async def process_task(task_id: int, duration: float = None) -> str:
    """Simulate processing a task with random duration"""
    if duration is None:
        duration = random.uniform(1, 3)  # Random duration between 1-3 seconds
    
    print(f"🚀 Task {task_id} started (will take {duration:.1f}s)")
    await asyncio.sleep(duration)
    result = f"Task {task_id} completed after {duration:.1f}s"
    print(f"✅ {result}")
    return result

class DynamicTaskManager:
    def __init__(self, max_concurrent_tasks: int = 3):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.running_tasks: Set[asyncio.Task] = set()
        self.task_counter = 0
        self.completed_tasks: List[str] = []
        self.total_tasks_to_process = 10  # Total number of tasks we want to process
        
    def create_new_task(self) -> asyncio.Task:
        """Create a new task with a unique ID"""
        self.task_counter += 1
        task = asyncio.create_task(
            process_task(self.task_counter),
            name=f"task_{self.task_counter}"
        )
        return task
        
    async def run_with_dynamic_tasks(self):
        """Run tasks with dynamic addition - add new task when old one completes"""
        print(f"🎯 Starting with {self.max_concurrent_tasks} concurrent tasks")
        print(f"📊 Will process {self.total_tasks_to_process} total tasks")
        print("-" * 60)
        
        # Start initial batch of tasks
        for _ in range(min(self.max_concurrent_tasks, self.total_tasks_to_process)):
            task = self.create_new_task()
            self.running_tasks.add(task)
            
        # Keep processing until all tasks are done
        while self.running_tasks and self.task_counter < self.total_tasks_to_process:
            # Wait for at least one task to complete
            done, pending = await asyncio.wait(
                self.running_tasks,
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Process completed tasks
            for task in done:
                try:
                    result = await task
                    self.completed_tasks.append(result)
                    print(f"📋 Completed tasks so far: {len(self.completed_tasks)}")
                except Exception as e:
                    print(f"❌ Task {task.get_name()} failed: {e}")
                
                # Remove completed task
                self.running_tasks.discard(task)
                
                # Add a new task if we haven't reached our limit
                if self.task_counter < self.total_tasks_to_process:
                    new_task = self.create_new_task()
                    self.running_tasks.add(new_task)
                    print(f"➕ Added new task {new_task.get_name()}")
            
            print(f"🔄 Currently running tasks: {len(self.running_tasks)}")
            print("-" * 30)
            
        # Wait for remaining tasks to complete
        if self.running_tasks:
            print("⏳ Waiting for remaining tasks to complete...")
            results = await asyncio.gather(*self.running_tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, Exception):
                    print(f"❌ Task failed: {result}")
                else:
                    self.completed_tasks.append(result)
        
        print(f"\n🎉 All tasks completed! Total: {len(self.completed_tasks)}")
        print (f"{self.completed_tasks=}")
        return self.completed_tasks

# Alternative approach using asyncio.as_completed()
async def dynamic_tasks_with_as_completed():
    """Alternative approach using as_completed for more granular control"""
    print("\n" + "="*60)
    print("🔄 Alternative approach using asyncio.as_completed()")
    print("="*60)
    
    tasks_to_create = 8
    max_concurrent = 3
    task_counter = 0
    active_tasks = set()
    completed_count = 0
    
    # Create initial batch
    for _ in range(min(max_concurrent, tasks_to_create)):
        task_counter += 1
        task = asyncio.create_task(process_task(task_counter))
        active_tasks.add(task)
    
    # Process tasks as they complete
    while active_tasks:
        for task in asyncio.as_completed(active_tasks):
            result = await task
            active_tasks.remove(task)
            completed_count += 1
            
            print(f"📊 Progress: {completed_count}/{tasks_to_create}")
            
            # Add new task if needed
            if task_counter < tasks_to_create:
                task_counter += 1
                new_task = asyncio.create_task(process_task(task_counter))
                active_tasks.add(new_task)
                print(f"➕ Added task {task_counter}")
            
            break  # Exit the for loop to re-evaluate active_tasks
    
    print(f"🎉 Alternative approach completed!")

# Example with a realistic use case - processing a queue
class TaskQueue:
    def __init__(self):
        self.queue = asyncio.Queue()
        self.results = []
    
    async def producer(self):
        """Simulate adding tasks to queue over time"""
        for i in range(12):
            await asyncio.sleep(0.5)  # Tasks arrive every 0.5 seconds
            await self.queue.put(f"item_{i+1}")
            print(f"📥 Added item_{i+1} to queue")
        
        # Signal completion
        await self.queue.put(None)
        print("🏁 Producer finished - added sentinel")
    
    async def worker(self, worker_id: int):
        """Worker that processes tasks from queue"""
        while True:
            item = await self.queue.get()
            
            if item is None:
                # Put sentinel back for other workers
                await self.queue.put(None)
                break
                
            print(f"👷 Worker {worker_id} processing {item}")
            await asyncio.sleep(random.uniform(1, 2))  # Simulate work
            result = f"Worker {worker_id} completed {item}"
            self.results.append(result)
            print(f"✅ {result}")
            self.queue.task_done()
    
    async def run_queue_processing(self):
        print("\n" + "="*60)
        print("📋 Queue-based task processing example")
        print("="*60)
        
        # Start producer and workers concurrently
        workers = [
            asyncio.create_task(self.worker(i)) 
            for i in range(3)  # 3 workers
        ]
        
        producer = asyncio.create_task(self.producer())
        
        # Wait for producer to finish and all tasks to be processed
        await producer
        await self.queue.join()  # Wait for all tasks to be processed
        
        # Cancel workers (they're in infinite loop)
        for worker in workers:
            worker.cancel()
        
        await asyncio.gather(*workers, return_exceptions=True)
        
        print(f"🎯 Queue processing completed! Processed {len(self.results)} items")

async def main():
    """Main function demonstrating different approaches"""
    start_time = time.time()

    '''
    # Approach 1: Using custom task manager
    print("Approach 1: Dynamic Task Manager")
    manager = DynamicTaskManager(max_concurrent_tasks=3)
    await manager.run_with_dynamic_tasks()

    '''
    # Approach 2: Using as_completed
    print("Approach 2: Using as_completed")
    await dynamic_tasks_with_as_completed()

    '''
    # Approach 3: Queue-based processing
    queue_processor = TaskQueue()
    await queue_processor.run_queue_processing()
    '''
    total_time = time.time() - start_time
    print(f"\n⏱️ Total execution time: {total_time:.1f} seconds")

if __name__ == "__main__":
    print("🚀 Starting dynamic task management examples...")
    asyncio.run(main())
