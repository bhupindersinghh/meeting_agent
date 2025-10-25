#!/usr/bin/env python3
"""
Test script to verify the Smart Scheduler AI Agent setup
"""
import os
import sys
from dotenv import load_dotenv

def test_imports():
    """Test if all required modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        from fastapi import FastAPI
        print("✅ FastAPI imported successfully")
    except ImportError as e:
        print(f"❌ FastAPI import failed: {e}")
        return False
    
    try:
        from openai import OpenAI
        print("✅ OpenAI imported successfully")
    except ImportError as e:
        print(f"❌ OpenAI import failed: {e}")
        return False
    
    try:
        from google.oauth2.credentials import Credentials
        print("✅ Google Calendar API imported successfully")
    except ImportError as e:
        print(f"❌ Google Calendar API import failed: {e}")
        return False
    
    try:
        from services.conversation_engine import ConversationEngine
        print("✅ Conversation Engine imported successfully")
    except ImportError as e:
        print(f"❌ Conversation Engine import failed: {e}")
        return False
    
    return True

def test_environment():
    """Test environment configuration"""
    print("\n🔧 Testing environment...")
    
    load_dotenv()
    
    # Check OpenAI API key
    openai_key = os.getenv('OPENAI_API_KEY')
    if openai_key:
        print("✅ OpenAI API key found")
    else:
        print("❌ OpenAI API key not found")
        return False
    
    # Check Google Calendar credentials
    if os.path.exists('credentials.json'):
        print("✅ Google Calendar credentials found")
    else:
        print("⚠️  Google Calendar credentials not found (calendar features will be limited)")
    
    return True

def test_models():
    """Test if models can be instantiated"""
    print("\n🤖 Testing models...")
    
    try:
        from models.chatbot_models import ConversationContext, ConversationState
        context = ConversationContext(
            session_id="test",
            state=ConversationState.INITIAL
        )
        print("✅ Models instantiated successfully")
        return True
    except Exception as e:
        print(f"❌ Model instantiation failed: {e}")
        return False

def test_services():
    """Test if services can be instantiated"""
    print("\n⚙️  Testing services...")
    
    try:
        from services.llm_service import LLMService
        llm_service = LLMService()
        print("✅ LLM Service instantiated successfully")
    except Exception as e:
        print(f"❌ LLM Service instantiation failed: {e}")
        return False
    
    try:
        from services.voice_service import VoiceService
        voice_service = VoiceService()
        print("✅ Voice Service instantiated successfully")
    except Exception as e:
        print(f"❌ Voice Service instantiation failed: {e}")
        return False
    
    try:
        from services.time_parsing_service import TimeParsingService
        time_parser = TimeParsingService()
        print("✅ Time Parsing Service instantiated successfully")
    except Exception as e:
        print(f"❌ Time Parsing Service instantiation failed: {e}")
        return False
    
    return True

def main():
    """Run all tests"""
    print("🧪 Smart Scheduler AI Agent - Setup Test")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_environment,
        test_models,
        test_services
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The Smart Scheduler AI Agent is ready to run.")
        print("\n🚀 To start the server, run:")
        print("   python start.py")
        print("\n📱 Then visit: http://localhost:8000/static/index.html")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        print("\n💡 Common solutions:")
        print("   - Install dependencies: pip install -r requirements.txt")
        print("   - Set environment variables in .env file")
        print("   - Download Google Calendar credentials.json")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
