#!/usr/bin/env python3
"""
Script to run the Streamlit frontend for the Multi-Agent Document Chat System
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    """Run the Streamlit app"""
    # Get the directory where this script is located
    script_dir = Path(__file__).resolve().parent
    
    # Change to the script directory
    os.chdir(script_dir)
    
    # Check if .env file exists
    env_file = script_dir / ".env"
    if not env_file.exists():
        print("⚠️  Warning: .env file not found!")
        print("Please create a .env file with your API keys:")
        print("GOOGLE_API_KEY=your_google_api_key_here")
        print("GROQ_API_KEY=your_groq_api_key_here")
        print()
    
    # Run streamlit
    try:
        print("🚀 Starting Streamlit app...")
        print("📱 The app will open in your default web browser")
        print("🔗 If it doesn't open automatically, go to: http://localhost:8501")
        print("⏹️  Press Ctrl+C to stop the server")
        print()
        
        # Run streamlit with the app
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "streamlit_app.py",
            "--server.port", "8501",
            "--server.address", "localhost"
        ])
        
    except KeyboardInterrupt:
        print("\n👋 Streamlit app stopped by user")
    except Exception as e:
        print(f"❌ Error running Streamlit: {e}")
        print("Make sure you have installed the requirements:")
        print("pip install -r requirements.txt")

if __name__ == "__main__":
    main() 