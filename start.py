#!/usr/bin/env python3
"""
Startup script for the Smart Scheduler AI Agent
"""
import os
import sys
import uvicorn
from dotenv import load_dotenv

def main():
    # Load environment variables
    load_dotenv()
    
    # Check for required environment variables
    required_vars = ['OPENAI_API_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these variables in your .env file or environment")
        sys.exit(1)
    
    # Check if Google Calendar credentials exist
    if not os.path.exists('credentials.json'):
        print("⚠️  Google Calendar credentials not found.")
        print("Please download credentials.json from Google Cloud Console")
        print("The app will work for text conversations but calendar features will be limited")
    
    print("🚀 Starting Smart Scheduler AI Agent...")
    print("📱 Web interface: http://localhost:8000/static/index.html")
    print("🔗 API docs: http://localhost:8000/docs")
    print("🎤 Voice features: Use the web interface for voice conversations")
    
    # Start the server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()
