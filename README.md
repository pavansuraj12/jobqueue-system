# JobQueue System

A CLI-based background job queue system with worker processes, retry mechanism, and Dead Letter Queue (DLQ).

## 🚀 Features

- **Job Management**: Enqueue and manage background jobs
- **Worker Processes**: Multiple parallel workers
- **Retry Mechanism**: Exponential backoff for failed jobs  
- **Dead Letter Queue**: Permanent failure handling
- **JSON Specification**: Jobs follow exact JSON format
- **Persistent Storage**: Jobs survive restarts

## Demo

  [Output Demo](https://drive.google.com/file/d/1weoA_5rlPhQ4hTUd0lZmTU1oH6An2yu2/view?usp=sharing)


## 📦 Installation

```bash
# Clone repository
git clone https://github.com/pavansuraj12/jobqueue-system.git
cd jobqueue-system

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
