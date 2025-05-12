import os
import openai
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

def test_openai_simple():
    """Test OpenAI API directly with a simple request"""
    # Get API key from environment
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-4")
    
    if not api_key:
        logging.error("OpenAI API key not set. Please set the OPENAI_API_KEY environment variable.")
        return
    
    logging.info(f"Using OpenAI API key: {api_key[:5]}...{api_key[-5:]}")
    logging.info(f"Using model: {model}")
    
    try:
        # Initialize the OpenAI client
        logging.info("Initializing OpenAI client...")
        client = openai.OpenAI(api_key=api_key)
        
        # Test messages
        test_messages = [
            "Hello, I'm not feeling well today.",
            "I have a fever and a sore throat.",
            "What could be wrong with me?",
            "What treatment do you recommend?",
            "Thank you for your help."
        ]
        
        # Context for conversation
        messages = [
            {"role": "system", "content": "You are a helpful medical assistant."}
        ]
        
        # Send messages and get responses
        for i, message in enumerate(test_messages):
            logging.info(f"Sending message {i+1}/{len(test_messages)}: '{message}'")
            
            # Add user message to context
            messages.append({"role": "user", "content": message})
            
            # Generate response
            response = client.chat.completions.create(
                model=model,
                messages=messages
            )
            
            # Get assistant response
            assistant_response = response.choices[0].message.content
            logging.info(f"AI Response: {assistant_response}")
            
            # Add assistant response to context
            messages.append({"role": "assistant", "content": assistant_response})
        
        logging.info("OpenAI API test completed successfully!")
        
    except Exception as e:
        logging.error(f"Error testing OpenAI API: {str(e)}")

if __name__ == "__main__":
    test_openai_simple()
