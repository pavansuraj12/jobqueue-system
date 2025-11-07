import threading
import time
from typing import List, Optional
from job import Job, JobState
from storage import Storage

class QueueManager:
    def __init__(self, storage: Storage):
        self.storage = storage
        self.processing_lock = threading.Lock()
        self.active_workers = 0
        self.shutdown_flag = False
    
    def enqueue(self, command: str, max_retries: int = None) -> Job:
        """Enqueue a new job"""
        if max_retries is None:
            max_retries = int(self.storage.get_config("max_retries", 3))
        
        job = Job(command=command, max_retries=max_retries)
        self.storage.save_job(job)
        return job
    
    def get_next_pending_job(self) -> Optional[Job]:
        """Get next pending job atomically"""
        with self.processing_lock:
            pending_jobs = self.storage.get_jobs_by_state(JobState.PENDING)
            if not pending_jobs:
                return None
            
            # Also check for failed jobs that can be retried
            failed_jobs = self.storage.get_jobs_by_state(JobState.FAILED)
            retryable_jobs = [job for job in failed_jobs if job.can_retry()]
            
            all_available = pending_jobs + retryable_jobs
            if not all_available:
                return None
            
            # Sort by created_at to ensure FIFO
            all_available.sort(key=lambda x: x.created_at)
            job = all_available[0]
            
            # Mark as processing
            job.mark_processing()
            self.storage.save_job(job)
            return job
    
    def complete_job(self, job: Job):
        """Mark job as completed"""
        job.mark_completed()
        self.storage.save_job(job)
    
    def fail_job(self, job: Job):
        """Mark job as failed (with retry logic)"""
        job.mark_failed()
        self.storage.save_job(job)
    
    def get_stats(self) -> dict:
        """Get queue statistics"""
        all_jobs = self.storage.get_all_jobs()
        stats = {
            "total_jobs": len(all_jobs),
            "pending": 0,
            "processing": 0,
            "completed": 0,
            "failed": 0,
            "dead": 0,
            "active_workers": self.active_workers
        }
        
        for job in all_jobs:
            stats[job.state.value] += 1
        
        return stats
    
    def get_dlq_jobs(self) -> List[Job]:
        """Get all dead letter queue jobs"""
        return self.storage.get_jobs_by_state(JobState.DEAD)
    
    def retry_dlq_job(self, job_id: str) -> bool:
        """Retry a DLQ job"""
        job = self.storage.get_job(job_id)
        if job and job.state == JobState.DEAD:
            success = job.retry()
            if success:
                self.storage.save_job(job)
                return True
        return False