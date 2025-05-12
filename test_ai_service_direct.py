import asyncio
import logging
import sys
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Load environment variables
load_dotenv()

# Import the AI service
from app.services.ai import OpenAIService, get_ai_service

async def test_openai_service():
    """Test the OpenAI service directly"""
    logging.info("Testing OpenAI service directly...")
    
    # Get the AI service
    ai_service = get_ai_service()
    logging.info(f"Using AI service: {type(ai_service).__name__}")
    
    # Test messages
    test_messages = [
        "Hello, I'm not feeling well today.",
        "I have a fever and a sore throat.",
        "What could be wrong with me?",
        "What treatment do you recommend?",
        "Thank you for your help."
    ]
    
    # Context for conversation
    context = []
    
    # Send messages and get responses
    for i, message in enumerate(test_messages):
        logging.info(f"Sending message {i+1}/{len(test_messages)}: '{message}'")
        
        # Generate response
        response = await ai_service.generate_response(message, context)
        
        logging.info(f"AI Response: {response}")
        
        # Add to context for next message
        context.append({"role": "user", "content": message})
        context.append({"role": "assistant", "content": response})
    
    logging.info("OpenAI service test completed successfully!")

async def main():
    await test_openai_service()

if __name__ == "__main__":
    asyncio.run(main())
