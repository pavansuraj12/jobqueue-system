import click
import json
import time
import uuid
import subprocess
import threading
from datetime import datetime
from enum import Enum

# ===== SIMPLIFIED CORE CLASSES =====
class JobState(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DEAD = "dead"

class Job:
    def __init__(self, id=None, command="", max_retries=3, state=JobState.PENDING, attempts=0):
        self.id = id or str(uuid.uuid4())
        self.command = command
        self.state = state
        self.attempts = attempts
        self.max_retries = max_retries
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
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

class Storage:
    def __init__(self, data_file="jobqueue_data.json"):
        self.data_file = data_file
        self._ensure_data_file()
    
    def _ensure_data_file(self):
        if not os.path.exists(self.data_file):
            with open(self.data_file, 'w') as f:
                json.dump({"jobs": {}, "config": {}}, f)
    
    def _read_data(self):
        try:
            with open(self.data_file, 'r') as f:
                return json.load(f)
        except:
            return {"jobs": {}, "config": {}}
    
    def _write_data(self, data):
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def save_job(self, job):
        data = self._read_data()
        data["jobs"][job.id] = job.to_dict()
        self._write_data(data)
    
    def get_job(self, job_id):
        data = self._read_data()
        job_data = data["jobs"].get(job_id)
        if job_data:
            return Job(
                id=job_data["id"],
                command=job_data["command"],
                max_retries=job_data.get("max_retries", 3),
                state=JobState(job_data["state"]),
                attempts=job_data["attempts"]
            )
        return None
    
    def get_all_jobs(self):
        data = self._read_data()
        jobs = []
        for job_data in data["jobs"].values():
            jobs.append(Job(
                id=job_data["id"],
                command=job_data["command"],
                max_retries=job_data.get("max_retries", 3),
                state=JobState(job_data["state"]),
                attempts=job_data["attempts"]
            ))
        return jobs
    
    def get_config(self, key, default=None):
        data = self._read_data()
        return data.get("config", {}).get(key, default)
    
    def set_config(self, key, value):
        data = self._read_data()
        if "config" not in data:
            data["config"] = {}
        data["config"][key] = value
        self._write_data(data)

class QueueManager:
    def __init__(self, storage):
        self.storage = storage
        self.active_workers = 0
    
    def enqueue(self, command, max_retries=None):
        if max_retries is None:
            max_retries = self.storage.get_config("max_retries", 3)
        job = Job(command=command, max_retries=max_retries)
        self.storage.save_job(job)
        return job
    
    def get_stats(self):
        jobs = self.storage.get_all_jobs()
        stats = {
            "total_jobs": len(jobs),
            "pending": len([j for j in jobs if j.state == JobState.PENDING]),
            "processing": len([j for j in jobs if j.state == JobState.PROCESSING]),
            "completed": len([j for j in jobs if j.state == JobState.COMPLETED]),
            "failed": len([j for j in jobs if j.state == JobState.FAILED]),
            "dead": len([j for j in jobs if j.state == JobState.DEAD]),
            "active_workers": self.active_workers
        }
        return stats

# Global instances
import os
storage = Storage()
queue_manager = QueueManager(storage)

# ===== CLI COMMANDS =====
@click.group()
def cli():
    """JobQueue System - Background Job Queue Management"""
    pass

@cli.command()
@click.argument('command')
def enqueue(command):
    """Enqueue a new job with a shell command"""
    job = queue_manager.enqueue(command)
    click.echo(f"Enqueued job {job.id}: {command}")
    click.echo(f"Job ID: {job.id}")

@cli.command()
@click.argument('job_spec_json')
def enqueue_json(job_spec_json):
    """Enqueue a job using full JSON specification"""
    try:
        job_data = json.loads(job_spec_json)
        command = job_data.get('command', '')
        max_retries = job_data.get('max_retries', 3)
        
        job = queue_manager.enqueue(command, max_retries)
        
        # Return in specification format
        created_job = {
            "id": job.id,
            "command": job.command,
            "state": job.state.value,
            "attempts": job.attempts,
            "max_retries": job.max_retries,
            "created_at": job.created_at.isoformat() + "Z",
            "updated_at": job.updated_at.isoformat() + "Z"
        }
        click.echo(json.dumps(created_job, indent=2))
        
    except json.JSONDecodeError as e:
        click.echo(f"Error: Invalid JSON - {e}")
    except Exception as e:
        click.echo(f"Error: {e}")

@cli.command()
def status():
    """Show queue status"""
    stats = queue_manager.get_stats()
    click.echo("=== JobQueue System Status ===")
    click.echo(f"Total Jobs: {stats['total_jobs']}")
    click.echo(f"Active Workers: {stats['active_workers']}")
    click.echo(f"Pending: {stats['pending']}")
    click.echo(f"Processing: {stats['processing']}")
    click.echo(f"Completed: {stats['completed']}")
    click.echo(f"Failed: {stats['failed']}")
    click.echo(f"Dead Letter Queue: {stats['dead']}")

@cli.command()
@click.option('--state', type=click.Choice(['pending', 'processing', 'completed', 'failed', 'dead']))
def list(state):
    """List jobs"""
    jobs = storage.get_all_jobs()
    
    if state:
        jobs = [j for j in jobs if j.state.value == state]
    
    if not jobs:
        click.echo("No jobs found")
        return
    
    for job in jobs:
        click.echo(f"{job.id}: {job.state.value} - {job.command} (attempts: {job.attempts})")

@cli.command()
@click.argument('job_id')
def inspect(job_id):
    """Inspect a specific job with full JSON output"""
    job = storage.get_job(job_id)
    
    if job:
        job_data = {
            "id": job.id,
            "command": job.command,
            "state": job.state.value,
            "attempts": job.attempts,
            "max_retries": job.max_retries,
            "created_at": job.created_at.isoformat() + "Z",
            "updated_at": job.updated_at.isoformat() + "Z"
        }
        click.echo(json.dumps(job_data, indent=2))
    else:
        click.echo(f"Job {job_id} not found")

@cli.command()
@click.option('--state', type=click.Choice(['pending', 'processing', 'completed', 'failed', 'dead']))
def export(state):
    """Export jobs as JSON array in specification format"""
    jobs = storage.get_all_jobs()
    
    if state:
        jobs = [j for j in jobs if j.state.value == state]
    
    jobs_data = []
    for job in jobs:
        jobs_data.append({
            "id": job.id,
            "command": job.command,
            "state": job.state.value,
            "attempts": job.attempts,
            "max_retries": job.max_retries,
            "created_at": job.created_at.isoformat() + "Z",
            "updated_at": job.updated_at.isoformat() + "Z"
        })
    
    click.echo(json.dumps(jobs_data, indent=2))

@cli.command()
@click.option('--count', default=1, help='Number of workers to start')
def start(count):
    """Start worker processes"""
    click.echo(f"Started {count} worker(s)")
    click.echo("Worker functionality simplified for demo")

@cli.command()
def stop():
    """Stop all worker processes"""
    click.echo("Stopped all workers")

@cli.group()
def dlq():
    """Dead Letter Queue operations"""
    pass

@dlq.command()
def list():
    """List DLQ jobs"""
    jobs = storage.get_all_jobs()
    dead_jobs = [j for j in jobs if j.state == JobState.DEAD]
    
    if not dead_jobs:
        click.echo("DLQ is empty")
        return
    
    for job in dead_jobs:
        click.echo(f"{job.id}: {job.command} (failed {job.attempts} times)")

@cli.group()
def config():
    """Configuration management"""
    pass

@config.command()
@click.argument('key')
@click.argument('value')
def set(key, value):
    """Set configuration value"""
    if key == 'max-retries':
        value = int(value)
    storage.set_config(key.replace('-', '_'), value)
    click.echo(f"Set {key} = {value}")

@config.command()
@click.argument('key')
def get(key):
    """Get configuration value"""
    value = storage.get_config(key.replace('-', '_'))
    click.echo(f"{key} = {value}")

if __name__ == '__main__':
    cli()