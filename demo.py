#!/usr/bin/env python3
"""
Demo script for the Smart Scheduler AI Agent
Shows various conversation scenarios and capabilities
"""
import asyncio
import json
from datetime import datetime, timedelta
from services.conversation_engine import ConversationEngine
from models.chatbot_models import MessageRequest, ConversationState

class SmartSchedulerDemo:
    def __init__(self):
        self.engine = ConversationEngine()
        self.session_id = "demo_session"
    
    async def run_demo_scenario(self, scenario_name: str, messages: list):
        """Run a demo scenario with multiple messages"""
        print(f"\n🎭 Demo Scenario: {scenario_name}")
        print("=" * 60)
        
        for i, message in enumerate(messages, 1):
            print(f"\n👤 User: {message}")
            
            request = MessageRequest(
                user_query=message,
                session_id=self.session_id,
                is_voice=False
            )
            
            try:
                response = await self.engine.process_message(request)
                print(f"🤖 Agent: {response.response}")
                print(f"📊 State: {response.conversation_state.value}")
                
                if response.requires_clarification:
                    print("❓ Requires clarification")
                
                if response.suggested_actions:
                    print(f"💡 Suggestions: {', '.join(response.suggested_actions)}")
                
            except Exception as e:
                print(f"❌ Error: {e}")
            
            # Small delay for readability
            await asyncio.sleep(1)
    
    async def demo_basic_scheduling(self):
        """Demo basic meeting scheduling"""
        messages = [
            "I need to schedule a meeting",
            "1 hour",
            "Tuesday afternoon",
            "Option 1"
        ]
        await self.run_demo_scenario("Basic Meeting Scheduling", messages)
    
    async def demo_complex_time_parsing(self):
        """Demo complex time expression parsing"""
        messages = [
            "I need a 45-minute meeting sometime before my flight that leaves on Friday at 6 PM",
            "That works",
            "Yes, please schedule it"
        ]
        await self.run_demo_scenario("Complex Time Parsing", messages)
    
    async def demo_conflict_resolution(self):
        """Demo conflict resolution and alternatives"""
        messages = [
            "I need to schedule a 2-hour meeting for tomorrow morning",
            "Actually, my colleague needs to join, so we'll need a full hour. Are any of those times still available for an hour?",
            "How about afternoon times?",
            "That works"
        ]
        await self.run_demo_scenario("Conflict Resolution", messages)
    
    async def demo_voice_capabilities(self):
        """Demo voice conversation capabilities"""
        print(f"\n🎤 Demo: Voice Capabilities")
        print("=" * 60)
        print("Voice features include:")
        print("✅ Speech-to-Text conversion using OpenAI Whisper")
        print("✅ Text-to-Speech generation with multiple voice options")
        print("✅ Real-time WebSocket communication")
        print("✅ Audio quality analysis and feedback")
        print("✅ Low-latency voice conversations (<800ms)")
        print("\n💡 To test voice features, use the web interface at:")
        print("   http://localhost:8000/static/index.html")
    
    async def demo_smart_features(self):
        """Demo smart features and capabilities"""
        print(f"\n🧠 Demo: Smart Features")
        print("=" * 60)
        
        features = [
            "🎯 Context Awareness: Remembers conversation state and user preferences",
            "⏰ Smart Time Parsing: Understands 'sometime next week', 'after my 5 PM meeting'",
            "🔄 Conflict Resolution: Suggests alternatives when times are unavailable",
            "🗣️ Voice Integration: Natural voice conversations with TTS/STT",
            "📅 Calendar Integration: Checks Google Calendar availability and creates events",
            "🔍 Advanced Search: Finds events by title and uses them as references",
            "⚡ Real-time Processing: WebSocket support for instant responses",
            "🎨 Multiple Interfaces: REST API, WebSocket, and web interface"
        ]
        
        for feature in features:
            print(feature)
            await asyncio.sleep(0.5)
    
    async def demo_api_usage(self):
        """Demo API usage examples"""
        print(f"\n🔌 Demo: API Usage")
        print("=" * 60)
        
        print("REST API Endpoints:")
        print("POST /message/ - Send message to chatbot")
        print("GET /message/context/{session_id} - Get conversation context")
        print("DELETE /message/context/{session_id} - Clear context")
        
        print("\nWebSocket Endpoints:")
        print("WS /ws/chat/{session_id} - Text and voice chat")
        print("WS /ws/voice/{session_id} - Voice-only conversation")
        
        print("\nExample Usage:")
        print("""
# Python example
import requests

response = requests.post("http://localhost:8000/message/", json={
    "user_query": "I need to schedule a meeting",
    "session_id": "user123",
    "is_voice": False
})

print(response.json()["response"])
        """)
    
    async def run_all_demos(self):
        """Run all demo scenarios"""
        print("🚀 Smart Scheduler AI Agent - Demo")
        print("=" * 60)
        print("This demo showcases the capabilities of the Smart Scheduler AI Agent")
        print("including natural language processing, voice integration, and calendar management.")
        
        # Run demo scenarios
        await self.demo_basic_scheduling()
        await self.demo_complex_time_parsing()
        await self.demo_conflict_resolution()
        await self.demo_voice_capabilities()
        await self.demo_smart_features()
        await self.demo_api_usage()
        
        print(f"\n🎉 Demo Complete!")
        print("=" * 60)
        print("The Smart Scheduler AI Agent is ready for production use!")
        print("\n🚀 To start the server:")
        print("   python start.py")
        print("\n📱 Web interface:")
        print("   http://localhost:8000/static/index.html")
        print("\n📚 API documentation:")
        print("   http://localhost:8000/docs")

async def main():
    """Main demo function"""
    demo = SmartSchedulerDemo()
    await demo.run_all_demos()

if __name__ == "__main__":
    asyncio.run(main())
