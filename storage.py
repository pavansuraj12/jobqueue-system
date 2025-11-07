import json
import os
import threading
from typing import List, Optional
from job import Job, JobState

class Storage:
    def __init__(self, data_file="jobqueue_data.json"):
        self.data_file = data_file
        self.lock = threading.Lock()
        self._ensure_data_file()
    
    def _ensure_data_file(self):
        """Create data file if it doesn't exist"""
        if not os.path.exists(self.data_file):
            with open(self.data_file, 'w') as f:
                json.dump({"jobs": {}, "config": {}}, f)
    
    def _read_data(self):
        """Read all data from file with locking"""
        with self.lock:
            try:
                with open(self.data_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return {"jobs": {}, "config": {}}
    
    def _write_data(self, data):
        """Write data to file with locking"""
        with self.lock:
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
    
    def save_job(self, job: Job):
        """Save or update a job"""
        data = self._read_data()
        data["jobs"][job.id] = job.to_dict()
        self._write_data(data)
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get a job by ID"""
        data = self._read_data()
        job_data = data["jobs"].get(job_id)
        if job_data:
            return Job.from_dict(job_data)
        return None
    
    def get_jobs_by_state(self, state: JobState) -> List[Job]:
        """Get all jobs with specified state"""
        data = self._read_data()
        jobs = []
        for job_data in data["jobs"].values():
            if job_data["state"] == state.value:
                jobs.append(Job.from_dict(job_data))
        return jobs
    
    def get_all_jobs(self) -> List[Job]:
        """Get all jobs"""
        data = self._read_data()
        return [Job.from_dict(job_data) for job_data in data["jobs"].values()]
    
    def delete_job(self, job_id: str):
        """Delete a job"""
        data = self._read_data()
        if job_id in data["jobs"]:
            del data["jobs"][job_id]
            self._write_data(data)
            return True
        return False
    
    def get_config(self, key: str, default=None):
        """Get configuration value"""
        data = self._read_data()
        return data.get("config", {}).get(key, default)
    
    def set_config(self, key: str, value):
        """Set configuration value"""
        data = self._read_data()
        if "config" not in data:
            data["config"] = {}
        data["config"][key] = value
        self._write_data(data)