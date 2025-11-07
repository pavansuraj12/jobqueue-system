#!/usr/bin/env python3
import os
import subprocess
import time

def run_command(cmd):
    """Run a CLI command and return output"""
    result = subprocess.run(f"python main.py {cmd}", shell=True, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr

def test_basic_commands():
    """Test basic CLI commands"""
    print("🧪 Testing Basic Commands")
    print("=" * 50)
    
    # Clean previous data
    if os.path.exists("jobqueue_data.json"):
        os.remove("jobqueue_data.json")
    
    # Test 1: Enqueue a simple job
    print("1. Testing enqueue command...")
    returncode, stdout, stderr = run_command('enqueue "echo Hello World"')
    print(f"   Output: {stdout.strip()}")
    if "Enqueued job" in stdout:
        print("   ✅ enqueue command working")
        job_id = stdout.split("Job ID: ")[1].strip() if "Job ID: " in stdout else None
    else:
        print("   ❌ enqueue command failed")
        return False
    
    # Test 2: Check status
    print("2. Testing status command...")
    returncode, stdout, stderr = run_command('status')
    print(f"   Output: {stdout.strip()}")
    if "Total Jobs: 1" in stdout:
        print("   ✅ status command working")
    else:
        print("   ❌ status command failed")
        return False
    
    # Test 3: List jobs
    print("3. Testing list command...")
    returncode, stdout, stderr = run_command('list')
    print(f"   Output: {stdout.strip()}")
    if job_id and job_id in stdout:
        print("   ✅ list command working")
    else:
        print("   ❌ list command failed")
        return False
    
    # Test 4: Enqueue with JSON
    print("4. Testing enqueue_json command...")
    returncode, stdout, stderr = run_command('enqueue_json \'{"command": "sleep 1", "max_retries": 2}\'')
    print(f"   Output: {stdout.strip()}")
    if "id" in stdout and "command" in stdout:
        print("   ✅ enqueue_json command working")
    else:
        print("   ❌ enqueue_json command failed")
        return False
    
    # Test 5: Export jobs
    print("5. Testing export command...")
    returncode, stdout, stderr = run_command('export')
    print(f"   Output: {stdout.strip()}")
    if "[" in stdout and "]" in stdout:
        print("   ✅ export command working")
    else:
        print("   ❌ export command failed")
        return False
    
    return True

def test_configuration():
    """Test configuration commands"""
    print("\n🧪 Testing Configuration Commands")
    print("=" * 50)
    
    # Test set config
    returncode, stdout, stderr = run_command('config set max-retries 5')
    print(f"Set config: {stdout.strip()}")
    
    # Test get config
    returncode, stdout, stderr = run_command('config get max-retries')
    print(f"Get config: {stdout.strip()}")
    
    if "max-retries = 5" in stdout:
        print("✅ Configuration commands working")
        return True
    else:
        print("❌ Configuration commands failed")
        return False

def test_dlq_commands():
    """Test DLQ commands"""
    print("\n🧪 Testing DLQ Commands")
    print("=" * 50)
    
    # Check DLQ (should be empty initially)
    returncode, stdout, stderr = run_command('dlq list')
    print(f"DLQ list: {stdout.strip()}")
    
    if "DLQ is empty" in stdout:
        print("✅ DLQ commands working")
        return True
    else:
        print("❌ DLQ commands failed")
        return False

def quick_demo():
    """Run a quick demo showing the system workflow"""
    print("\n🚀 Running Quick Demo")
    print("=" * 50)
    
    # Clean start
    if os.path.exists("jobqueue_data.json"):
        os.remove("jobqueue_data.json")
    
    print("Step 1: Enqueuing different types of jobs...")
    
    # Enqueue various jobs
    jobs = [
        "echo '✅ Quick success job'",
        "sleep 2",
        "exit 1",  # This will fail
        "dir",     # Directory listing
    ]
    
    for job in jobs:
        returncode, stdout, stderr = run_command(f'enqueue "{job}"')
        print(f"   {stdout.strip()}")
    
    print("\nStep 2: Checking initial status...")
    returncode, stdout, stderr = run_command('status')
    print(stdout)
    
    print("\nStep 3: Listing all jobs...")
    returncode, stdout, stderr = run_command('list')
    print(stdout)
    
    print("\nStep 4: Exporting jobs as JSON...")
    returncode, stdout, stderr = run_command('export')
    print("Jobs exported in JSON format ✓")
    
    print("\n🎯 Demo completed! Next steps:")
    print("1. Start workers: python main.py start --count 2")
    print("2. Watch jobs process in real-time")
    print("3. Check final status: python main.py status")

if __name__ == '__main__':
    print("JobQueue System - Comprehensive Test Suite")
    print("=" * 60)
    
    # Run tests
    basic_ok = test_basic_commands()
    config_ok = test_configuration()
    dlq_ok = test_dlq_commands()
    
    print("\n" + "=" * 60)
    if basic_ok and config_ok and dlq_ok:
        print("🎉 ALL TESTS PASSED! System is working correctly.")
        print("\nWould you like to run a quick demo? (y/n)")
        choice = input().strip().lower()
        if choice == 'y':
            quick_demo()
        else:
            print("\nYou can run the demo later with: python test_jobqueue.py")
    else:
        print("❌ Some tests failed. Please check the setup.")
    
    print("\nUseful commands to try:")
    print("  python main.py enqueue \"echo 'Hello World'\"")
    print("  python main.py enqueue_json '{\"command\": \"sleep 2\"}'")
    print("  python main.py status")
    print("  python main.py start --count 2")