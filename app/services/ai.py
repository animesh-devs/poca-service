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

    @abstractmethod
    async def generate_suggested_response(self, patient_summary: str) -> str:
        """Generate a suggested medical response for a doctor based on patient summary"""
        pass

class OpenAIService(AIService):
    """OpenAI service implementation"""

    # System prompt for patient interviews
    # PATIENT_INTERVIEW_PROMPT = """
    # You are a medical assistant interviewing a patient.
    # Focus on symptoms, medical history, and current concerns.
    # Track question progress and inform the patient.
    # After all 5 questions, summarize for the doctor:
    # 1. Chief complaint and symptoms
    # 2. Relevant medical history
    # 3. Current medications
    # 4. Symptom duration and severity
    # 5. Impact on daily activities
    # Be professional, empathetic, and concise.

    # Your messages should not exceed 15 words. Summary can be up to 75 words.
    # Wait for patient response before asking the next question.

    # After all the questions are done just return the summary to the patient don't add any advices.

    # IMPORTANT: You must format your response as a valid JSON object with the following structure:
    # {
    #     "message": "Your response text here",
    #     "isSummary": true/false
    # }

    # Set "isSummary" to true only when you are providing the final summary after all questions.
    # For all other responses, set "isSummary" to false.
    # """

    PATIENT_INTERVIEW_PROMPT = """
    You are a doctor’s assistant, and patients are enrolled under you.

    Ask follow-up questions to help the doctor reach a more accurate diagnosis. Be concise. Cover:
	•	Severity of symptoms
	•	Duration
	•	Side effects (if any)
	•	Medications being taken
	•	Any relevant images or documents
    Keep questions crisp, avoid irrelevant questions, don’t emphatize with patient

	4.	Once responses are received, prepare a crisp bullet-point summary for the doctor to review quickly.

    Your messages should not exceed 15 words. Summary can be up to 75 words.
    Wait for patient response before asking the next question.


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
                    "content": "Now generate a comprehensive summary of the patient's condition based on all the information gathered. Give this summary as a first person."
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

    async def generate_suggested_response(self, patient_summary: str, discharge_summary: str = None) -> str:
        """Generate a suggested medical response for a doctor based on patient summary and optional discharge summary"""
        if not self.api_key or self.api_key == "your_openai_api_key":
            logger.warning("OpenAI API key not set or using default value. Using mock response.")
            return self._generate_mock_suggested_response(patient_summary, discharge_summary)

        try:
            # System prompt for doctor's suggested response
            doctor_prompt = """
            You are a senior physician from a reputed multispeciality hospital.
            Your role is to provide accurate and clear medical advice in the format of a formal prescription sheet, based on the summary of the patient’s medical issue.

            You will be provided with:

            A brief, summarized medical problem written by or on behalf of the patient

            (Optionally) A discharge summary or any relevant clinical history

            Your response must follow this structured prescription format:

            Diagnosis

            Medical Description: 2–4 lines explaining the diagnosis in layman’s terms

            Prescription in bullet points:

            Prescribed Medicines (with composition in parentheses)

            Dosage Instructions (e.g., Daily: 1-0-1, duration, timing like "After Meal", etc.)

            Drug Allergies: Default to "No known allergies" unless mentioned

            Lab Tests: Mention only if required

            Follow-up: Timeframe for next consultation

            Doctor's Advice: 3–5 specific, actionable bullet points
            """

            

            # Prepare the user message with patient summary and optional discharge summary
            user_content = f"Patient Summary: {patient_summary}"
            if discharge_summary:
                user_content += f"\n\nDischarge Summary: {discharge_summary}"

            messages = [
                {"role": "system", "content": doctor_prompt},
                {"role": "user", "content": user_content}
            ]

            logger.info(f"Generating suggested response for patient summary: {patient_summary[:100]}...")

            # Call the OpenAI API
            client = openai.OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,  # Slightly more creative for varied responses
                max_tokens=500    # Limit response length
            )

            # Extract the response text
            response_text = response.choices[0].message.content.strip()
            logger.info(f"Generated suggested response: {response_text[:100]}...")

            return response_text

        except Exception as e:
            logger.error(f"Error generating suggested response from OpenAI: {str(e)}")
            return f"Error generating suggested medical response: {str(e)}"

    def _generate_mock_suggested_response(self, patient_summary: str, discharge_summary: str = None) -> str:
        """Generate a mock suggested response for testing when no API key is available"""

        # Analyze the summary for key symptoms
        summary_lower = patient_summary.lower()

        # Include discharge summary information if available
        if discharge_summary:
            summary_lower += " " + discharge_summary.lower()

        if any(symptom in summary_lower for symptom in ["fever", "headache", "sore throat", "cough"]):
            return """
Based on the patient's presentation with fever, headache, sore throat, and cough, this appears consistent with a viral upper respiratory infection, possibly influenza.

Assessment:
- Viral syndrome most likely given the constellation of symptoms
- Consider bacterial pharyngitis if severe throat pain with exudate
- Monitor for complications such as pneumonia

Recommendations:
1. Symptomatic treatment with rest, fluids, and fever reducers (acetaminophen/ibuprofen)
2. Throat lozenges or warm salt water gargles for sore throat
3. Consider rapid strep test if bacterial pharyngitis suspected
4. Return if symptoms worsen, fever persists >3 days, or difficulty breathing develops

Follow-up: Routine unless symptoms deteriorate or patient develops concerning features.
            """.strip()

        elif any(symptom in summary_lower for symptom in ["chest pain", "shortness of breath"]):
            return """
The patient's presentation with chest pain and shortness of breath requires immediate evaluation to rule out serious cardiopulmonary conditions.

Assessment:
- Differential includes cardiac (MI, angina), pulmonary (PE, pneumonia), or other causes
- This presentation warrants urgent evaluation

Recommendations:
1. IMMEDIATE: Obtain vital signs, ECG, chest X-ray
2. Consider cardiac enzymes, D-dimer based on clinical suspicion
3. Oxygen saturation monitoring
4. Pain assessment and management as appropriate

RED FLAGS: Any signs of hemodynamic instability, severe respiratory distress, or cardiac symptoms require immediate emergency evaluation.

Follow-up: Urgent/emergent evaluation recommended.
            """.strip()

        else:
            return """
Based on the patient summary provided, a comprehensive evaluation is recommended.

Assessment:
- Further history and physical examination needed for accurate diagnosis
- Consider relevant differential diagnoses based on presenting symptoms

Recommendations:
1. Complete history and physical examination
2. Appropriate diagnostic testing based on clinical findings
3. Symptomatic management as indicated
4. Patient education regarding symptoms and when to seek care

Follow-up: As clinically indicated based on findings and patient response to treatment.
            """.strip()

# Gemini implementation removed as per requirements

def get_ai_service() -> AIService:
    """Factory function to get the configured AI service"""
    provider = settings.AI_PROVIDER.lower()

    # Only OpenAI is supported as per requirements
    if provider != "openai":
        logger.warning(f"Provider {provider} is not supported. Using OpenAI as the default provider.")

    return OpenAIService()
