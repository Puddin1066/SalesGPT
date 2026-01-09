#!/usr/bin/env python3
"""
Simple service launcher for local development.
Starts all services and opens browser to dashboard.
"""
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

def check_dependencies():
    """Check if required packages are installed."""
    required = ['fastapi', 'uvicorn', 'streamlit', 'plotly', 'pandas']
    missing = []
    
    for package in required:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"❌ Missing dependencies: {', '.join(missing)}")
        print(f"Install with: pip3 install {' '.join(missing)}")
        return False
    return True

def start_service(name, command, log_file):
    """Start a service in the background."""
    print(f"🚀 Starting {name}...")
    try:
        with open(log_file, 'w') as log:
            process = subprocess.Popen(
                command,
                stdout=log,
                stderr=log,
                shell=True
            )
        print(f"   ✅ {name} started (PID: {process.pid})")
        return process
    except Exception as e:
        print(f"   ❌ Failed to start {name}: {e}")
        return None

def main():
    """Main launcher."""
    print("🚀 Starting SalesGPT Email Platform...")
    print()
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Create logs directory
    Path("logs").mkdir(exist_ok=True)
    
    # Change to project directory
    project_root = Path(__file__).parent
    import os
    os.chdir(project_root)
    
    # Set environment variables for mock APIs
    env = os.environ.copy()
    env.setdefault('APOLLO_API_URL', 'http://localhost:8001')
    env.setdefault('SMARTLEAD_API_URL', 'http://localhost:8001')
    env.setdefault('HUBSPOT_API_URL', 'http://localhost:8001')
    env.setdefault('USE_MOCK_APIS', 'true')
    
    processes = []
    
    # Start Mock API Server
    mock_api = start_service(
        "Mock API Server",
        "python3 mock_api_server.py",
        "logs/mock_api.log"
    )
    if mock_api:
        processes.append(('Mock API', mock_api))
    time.sleep(2)
    
    # Start Backend API
    backend = start_service(
        "Backend API",
        "python3 webhook_handler.py",
        "logs/backend.log"
    )
    if backend:
        processes.append(('Backend API', backend))
    time.sleep(2)
    
    # Start Dashboard
    dashboard = start_service(
        "Dashboard",
        "streamlit run dashboard/streamlit_app.py --server.port 8501 --server.address localhost",
        "logs/dashboard.log"
    )
    if dashboard:
        processes.append(('Dashboard', dashboard))
    time.sleep(5)
    
    print()
    print("✅ All services started!")
    print()
    print("📋 Service URLs:")
    print("   🌐 Dashboard:      http://localhost:8501")
    print("   🔌 Backend API:    http://localhost:8000")
    print("   📡 Mock API:       http://localhost:8001")
    print("   ❤️  Health Check:   http://localhost:8000/health")
    print()
    
    # Wait a bit for services to fully start
    print("⏳ Waiting for services to be ready...")
    time.sleep(5)
    
    # Check health
    import urllib.request
    print("🏥 Checking service health...")
    
    try:
        urllib.request.urlopen("http://localhost:8001/health", timeout=2)
        print("   ✅ Mock API: Healthy")
    except:
        print("   ❌ Mock API: Not responding")
    
    try:
        urllib.request.urlopen("http://localhost:8000/health", timeout=2)
        print("   ✅ Backend API: Healthy")
    except:
        print("   ⚠️  Backend API: Starting (may take a moment)")
    
    try:
        urllib.request.urlopen("http://localhost:8501/_stcore/health", timeout=2)
        print("   ✅ Dashboard: Healthy")
    except:
        print("   ⚠️  Dashboard: Starting (may take a moment)")
    
    print()
    print("🎉 Services are running!")
    print()
    print("📄 View logs:")
    print("   tail -f logs/mock_api.log")
    print("   tail -f logs/backend.log")
    print("   tail -f logs/dashboard.log")
    print()
    
    # Open browser
    print("🌐 Opening dashboard in browser...")
    time.sleep(2)
    try:
        webbrowser.open("http://localhost:8501")
        print("   ✅ Browser opened!")
    except:
        print("   ⚠️  Could not open browser automatically")
        print("   Please manually open: http://localhost:8501")
    
    print()
    print("Press Ctrl+C to stop all services...")
    
    # Keep running until interrupted
    try:
        while True:
            time.sleep(1)
            # Check if processes are still alive
            for name, proc in processes:
                if proc.poll() is not None:
                    print(f"⚠️  {name} stopped unexpectedly")
    except KeyboardInterrupt:
        print()
        print("🛑 Stopping all services...")
        for name, proc in processes:
            try:
                proc.terminate()
                proc.wait(timeout=5)
                print(f"   ✅ {name} stopped")
            except:
                proc.kill()
                print(f"   ⚠️  {name} force stopped")
        print("✅ All services stopped!")
        sys.exit(0)

if __name__ == "__main__":
    main()

