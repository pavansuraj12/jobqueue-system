# JobQueue System - Background Job Queue Management

A CLI-based background job queue system with worker processes, retry mechanisms, and Dead Letter Queue (DLQ) support.

## 🚀 Features

- **Job Management**: Enqueue, monitor, and manage background jobs
- **Worker Processes**: Multiple parallel workers with graceful shutdown
- **Retry Mechanism**: Exponential backoff for failed jobs
- **Dead Letter Queue**: Permanent failure handling
- **Persistence**: Job data survives restarts
- **CLI Interface**: Easy-to-use command-line interface

## 📦 Installation

### Option 1: Direct Run
```bash
# Navigate to the project folder
cd jobqueue-system

# Install dependencies
pip install -r requirements.txt