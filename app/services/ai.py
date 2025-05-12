from abc import ABC, abstractmethod
import logging
import openai
from typing import Optional, Dict, Any, List
from app.config import settings

# Configure logging
logger = logging.getLogger(__name__)

class AIService(ABC):
    """Abstract base class for AI services"""

    @abstractmethod
    async def generate_response(self, message: str, context: Optional[List[Dict[str, str]]] = None) -> str:
        """Generate a response to a message"""
        pass

class OpenAIService(AIService):
    """OpenAI service implementation"""

    # System prompt for patient interviews
    PATIENT_INTERVIEW_PROMPT = """
    You are a medical assistant interviewing a patient.
    Focus on symptoms, medical history, and current concerns.
    Track question progress and inform the patient.
    After all 5 questions, summarize for the doctor:
    1. Chief complaint and symptoms
    2. Relevant medical history
    3. Current medications
    4. Symptom duration and severity
    5. Impact on daily activities
    Be professional, empathetic, and concise.

    Your messages should not exceed 15 words. Summary can be up to 75 words.
    Wait for patient response before asking the next question.

    After all the questions are done just return the summary to the patient don't add any advices.

    IMPORTANT: You must format your response as a valid JSON object with the following structure:
    {
        "message": "Your response text here",
        "isSummary": true/false
    }

    Set "isSummary" to true only when you are providing the final summary after all questions.
    For all other responses, set "isSummary" to false.
    """

    def __init__(self):
        """Initialize the OpenAI service"""
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL
        self.question_count = 0
        self.max_questions = 5
        self.summary_mode = False

        if not self.api_key:
            logger.warning("OpenAI API key not set. OpenAI service will not work.")
        else:
            openai.api_key = self.api_key

    async def generate_response(self, message: str, context: Optional[List[Dict[str, str]]] = None) -> str:
        """Generate a response using OpenAI"""
        if not self.api_key or self.api_key == "your_openai_api_key":
            logger.warning("OpenAI API key not set or using default value. Using mock response.")
            return self._generate_mock_response(message)

        try:
            # Prepare messages for the API
            messages = []

            # Add system prompt
            messages.append({"role": "system", "content": self.PATIENT_INTERVIEW_PROMPT})

            # Track question count and determine if we should generate a summary
            if context:
                # Count user messages to track question progress
                user_messages = [msg for msg in context if msg["role"] == "user"]
                self.question_count = len(user_messages)

                # Add context if provided
                messages.extend(context)

                # Check if we should generate a summary
                if self.question_count >= self.max_questions:
                    self.summary_mode = True

            # Add the current message
            messages.append({"role": "user", "content": message})
            self.question_count += 1

            logger.info(f"Sending request to OpenAI API with message: {message}")
            logger.info(f"Question count: {self.question_count}, Summary mode: {self.summary_mode}")

            # Call the OpenAI API with the updated client
            client = openai.OpenAI(api_key=self.api_key)

            # If in summary mode, explicitly ask for a summary
            if self.summary_mode:
                messages.append({
                    "role": "system",
                    "content": "Now generate a comprehensive summary of the patient's condition based on all the information gathered."
                })

            response = client.chat.completions.create(
                model=self.model,
                messages=messages
            )

            # Extract the response text
            response_text = response.choices[0].message.content
            logger.info(f"Received response from OpenAI API: {response_text[:100]}...")

            # Reset summary mode after generating a summary
            if self.summary_mode:
                self.summary_mode = False
                self.question_count = 0
                logger.info("Summary generated and state reset")

            # Try to parse the response as JSON
            try:
                import json
                response_json = json.loads(response_text)

                # Validate that the response has the expected format
                if "message" in response_json and "isSummary" in response_json:
                    logger.info(f"Successfully parsed JSON response: {response_json}")
                    return response_json
                else:
                    logger.warning(f"Response JSON missing required fields: {response_json}")
                    # Create a properly formatted response
                    return {
                        "message": response_text,
                        "isSummary": self.summary_mode
                    }
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse response as JSON: {response_text}")
                # If parsing fails, return a properly formatted response
                return {
                    "message": response_text,
                    "isSummary": self.summary_mode
                }

        except Exception as e:
            logger.error(f"Error generating response from OpenAI: {str(e)}")
            return f"Error generating AI response: {str(e)}"

    def _generate_mock_response(self, message: str) -> dict:
        """Generate a mock response for testing when no API key is available"""
        response_text = ""
        is_summary = False

        # Track question count
        if self.question_count >= self.max_questions:
            is_summary = True
            response_text = """
            Patient Summary:
            - Chief complaint: Flu-like symptoms including fever, sore throat, and fatigue
            - Medical history: No significant prior conditions
            - Current medications: None
            - Symptom duration: Started 2 days ago, gradually worsening
            - Impact: Difficulty working and sleeping due to symptoms

            Recommendation: Rest, hydration, and over-the-counter fever reducers. Consult doctor if symptoms worsen.
            """
        elif "symptoms" in message.lower() and "flu" in message.lower():
            response_text = "Common flu symptoms include fever, cough, sore throat, body aches, fatigue, headache, and sometimes vomiting and diarrhea."
        elif "treatment" in message.lower():
            response_text = "Treatment for most conditions involves rest, proper hydration, and medication appropriate for the specific condition."
        elif "hello" in message.lower() or "hi" in message.lower():
            response_text = "Hello! I'm your AI medical assistant. How can I help you today?"
        else:
            response_text = "I understand your question. As an AI medical assistant, I can provide general information."

        # Return JSON-formatted response
        return {
            "message": response_text.strip(),
            "isSummary": is_summary
        }

# Gemini implementation removed as per requirements

def get_ai_service() -> AIService:
    """Factory function to get the configured AI service"""
    provider = settings.AI_PROVIDER.lower()

    # Only OpenAI is supported as per requirements
    if provider != "openai":
        logger.warning(f"Provider {provider} is not supported. Using OpenAI as the default provider.")

    return OpenAIService()
