import time


class RetentionWorker:
    def __init__(self) -> None:
        self.running = False
        
    def start(self) -> None:
        self.running = True
        
    def stop(self) -> None:
        self.running = False
        
    def run_loop(self) -> None:
        while self.running:
            # Check for assets to delete
            time.sleep(60)
