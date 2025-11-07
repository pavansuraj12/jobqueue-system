import subprocess
import threading
import time
import signal
import sys
from queue_manager import QueueManager
from job import Job

class Worker:
    def __init__(self, queue_manager: QueueManager, worker_id: int):
        self.queue_manager = queue_manager
        self.worker_id = worker_id
        self.running = False
        self.thread = None
        self.current_job = None
    
    def start(self):
        """Start the worker"""
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        self.queue_manager.active_workers += 1
    
    def stop(self):
        """Stop the worker gracefully"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        self.queue_manager.active_workers -= 1
    
    def _run(self):
        """Main worker loop"""
        while self.running:
            job = self.queue_manager.get_next_pending_job()
            if job:
                self.current_job = job
                self._process_job(job)
                self.current_job = None
            else:
                # No jobs available, sleep briefly
                time.sleep(1)
    
    def _process_job(self, job: Job):
        """Process a single job"""
        try:
            # Execute the command
            result = subprocess.run(
                job.command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                print(f"Worker {self.worker_id}: Job {job.id} completed successfully")
                self.queue_manager.complete_job(job)
            else:
                print(f"Worker {self.worker_id}: Job {job.id} failed with exit code {result.returncode}")
                print(f"Stderr: {result.stderr}")
                self.queue_manager.fail_job(job)
                
                # If not dead, schedule retry with backoff
                if job.state.value != "dead":
                    backoff_delay = job.calculate_backoff()
                    print(f"Worker {self.worker_id}: Scheduling retry in {backoff_delay} seconds")
                
        except subprocess.TimeoutExpired:
            print(f"Worker {self.worker_id}: Job {job.id} timed out")
            self.queue_manager.fail_job(job)
        except Exception as e:
            print(f"Worker {self.worker_id}: Job {job.id} failed with exception: {e}")
            self.queue_manager.fail_job(job)

class WorkerManager:
    def __init__(self, queue_manager: QueueManager):
        self.queue_manager = queue_manager
        self.workers = []
        self.shutdown_flag = False
        
        # Setup signal handling for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print("\nReceived shutdown signal, stopping workers gracefully...")
        self.shutdown_flag = True
        self.stop_all_workers()
        sys.exit(0)
    
    def start_workers(self, count: int = 1):
        """Start multiple workers"""
        for i in range(count):
            worker = Worker(self.queue_manager, len(self.workers) + 1)
            worker.start()
            self.workers.append(worker)
            print(f"Started worker {worker.worker_id}")
    
    def stop_all_workers(self):
        """Stop all workers gracefully"""
        print("Stopping all workers...")
        for worker in self.workers:
            worker.stop()
        self.workers.clear()
        print("All workers stopped")
    
    def get_active_count(self):
        """Get number of active workers"""
        return len([w for w in self.workers if w.running])