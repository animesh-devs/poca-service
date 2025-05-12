import os
import openai
import logging
import sys
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Load environment variables
load_dotenv()

# Get OpenAI API key from environment
api_key = os.getenv("OPENAI_API_KEY")
model = os.getenv("OPENAI_MODEL", "gpt-4")

def test_openai_integration():
    """Test OpenAI integration directly"""
    if not api_key:
        logging.error("OpenAI API key not set. Please set the OPENAI_API_KEY environment variable.")
        return

    logging.info(f"Using OpenAI API key: {api_key[:5]}...{api_key[-5:]}")
    logging.info(f"Using model: {model}")

    try:
        # Initialize the OpenAI client
        logging.info("Initializing OpenAI client...")
        client = openai.OpenAI(api_key=api_key)

        # Test a simple completion
        logging.info("Sending request to OpenAI API...")
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful medical assistant."},
                {"role": "user", "content": "What are the symptoms of the flu?"}
            ]
        )

        # Print the response
        logging.info("Received response from OpenAI API")
        print("\nOpenAI API Response:")
        print(response.choices[0].message.content)
        print("\nTest completed successfully!")

    except Exception as e:
        logging.error(f"Error testing OpenAI integration: {str(e)}")

if __name__ == "__main__":
    test_openai_integration()
