import asyncio
from watchfiles import watch

# Example callback function
def my_callback(event_type, file_path):
    print(f"File {file_path} was {event_type}")

# Coroutine to watch the directory
async def watch_directory(directory, callback):
    async for changes in watch(directory):
        for event in changes:
            event_type, file_path = event
            callback(event_type, file_path)

# Main coroutine to run other tasks alongside watching the directory
async def main():
    directory_to_watch = '/path/to/directory'
    
    # Start watching the directory in the background
    watch_task = asyncio.create_task(watch_directory(directory_to_watch, my_callback))
    
    # Perform other tasks concurrently
    print("Performing other tasks while watching directory...")
    
    # Example: Simulating other tasks
    await asyncio.sleep(5)  # Simulating other work that takes 5 seconds
    print("Finished doing other tasks.")
    
    # Allow the watcher to continue running
    await watch_task  # This will keep the script running as the watcher is still active


class LocalDriveCrawler:
    def __init__(self, full_directory_path: str) -> None:
        self.full_directory_path = full_directory_path

    async def run(self):
        watch_task = asyncio.create_task(watch_directory(directory_to_watch, my_callback))
        
        # Perform other tasks concurrently
        print("Performing other tasks while watching directory...")
        
        # Example: Simulating other tasks
        await asyncio.sleep(5)  # Simulating other work that takes 5 seconds
        print("Finished doing other tasks.")
        
        # Allow the watcher to continue running
        await watch_task  # This will keep the script running as the watcher is still active

# Run the asyncio event loop
#asyncio.run(main())


# https://chatgpt.com/c/6740eff5-1c20-800f-85d4-2d0cc4b3158a