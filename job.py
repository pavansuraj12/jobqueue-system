import uuid
import json
from datetime import datetime
from enum import Enum

class JobState(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DEAD = "dead"

class Job:
    def __init__(self, id=None, command="", max_retries=3, state=JobState.PENDING, 
                 attempts=0, created_at=None, updated_at=None):
        self.id = id or str(uuid.uuid4())
        self.command = command
        self.state = state
        self.attempts = attempts
        self.max_retries = max_retries
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
    
    def to_dict(self):
        return {
            "id": self.id,
            "command": self.command,
            "state": self.state.value,
            "attempts": self.attempts,
            "max_retries": self.max_retries,
            "created_at": self.created_at.isoformat() + "Z",
            "updated_at": self.updated_at.isoformat() + "Z"
        }
    
    @classmethod
    def from_dict(cls, data):
        job = cls(
            id=data["id"],
            command=data["command"],
            max_retries=data.get("max_retries", 3),
            state=JobState(data["state"]),
            attempts=data["attempts"]
        )
        # Handle timestamp parsing
        created_at_str = data["created_at"].replace('Z', '+00:00')
        updated_at_str = data["updated_at"].replace('Z', '+00:00')
        job.created_at = datetime.fromisoformat(created_at_str)
        job.updated_at = datetime.fromisoformat(updated_at_str)
        return job
    
    def calculate_backoff(self):
        """Calculate exponential backoff delay in seconds"""
        return 2 ** self.attempts
    
    def can_retry(self):
        return self.attempts < self.max_retries and self.state == JobState.FAILED
    
    def mark_processing(self):
        self.state = JobState.PROCESSING
        self.updated_at = datetime.utcnow()
    
    def mark_completed(self):
        self.state = JobState.COMPLETED
        self.updated_at = datetime.utcnow()
    
    def mark_failed(self):
        self.attempts += 1
        if self.attempts >= self.max_retries:
            self.state = JobState.DEAD
        else:
            self.state = JobState.FAILED
        self.updated_at = datetime.utcnow()
    
    def retry(self):
        if self.state == JobState.DEAD and self.attempts <= self.max_retries:
            self.state = JobState.PENDING
            self.updated_at = datetime.utcnow()
            return True
        return False