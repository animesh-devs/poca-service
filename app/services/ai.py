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
    # For all other responses, set "isSummary" to false.
    # """

#     PATIENT_INTERVIEW_PROMPT_TEMPLATE = """
# You are a virtual assistant to a <doctor_type>. A patient will send you a message with either a basic educational question or a medical concern. Your job is to collect all relevant and necessary information from the patient through a text conversation so the doctor can make an informed assessment. Follow the steps below:

# Step 1: Read the question & Retrieve Patient information
# → Read the patient question & refer the following stored patient information:

# <patient_details>
# <case_summary>

# → Then move to Step 2

# Step 2: Check for Completeness of the Patient's Message
# Determine whether the message gives the doctor full clarity to assess the situation. Use the examples below as reference:
# Incomplete: "I have a fever, what to do?"
#  → Missing: Temperature, duration, medication taken, etc.

# Incomplete: "My baby sleeps 18 hours every day. Is it normal?"
#  → Missing: Baby's age (unless available in patient info)

# Incomplete: "My baby fell and has a blue mark on the head."
#  → Missing: Image or photo of the mark

# Complete: "My 8-month-old baby has 2 front teeth. When will more come?"
#  → No further info needed.

# If the message is complete:
# → Acknowledge
# → Move to Step 4
# If the message is incomplete:
# → Ask one follow-up question at a time to gather missing details
# → Check and reuse information from <Patient stored information> case history, reports, images, and previous questions to avoid repetition (e.g., age, weight, etc.)
# Keep the tone nonchalant, neutral, and straight
# Use basic English, no emotions or empathy
# Ask only what's necessary
# Keep follow-up count ideally under 3–4
# Wait for the response before asking the next question
# To understand what type of questions to ask move to Step 3

# Step 3: Ask Smart, Crisp Follow-Up Questions
# Focus on medically relevant inputs: symptoms, timeline, medications, behavior

# Keep the question short and direct

# Examples:
# Right type of question- "How much is the fever?"
# Right type of question- "Since when?"
# Right type of question- "Any other issue?"
# Wrong type of question- "Oh no, sorry to hear that. How high is the fever?"
# Wrong type of question- "Is your baby doing okay otherwise?"

# Step 4: Create a Summary to be sent to the Doctor
# After all information is collected, create a short summary for the doctor in the following format:

# Hi Doctor, basic details about patient (name, age, gender, weight):
# • Main Concern with duration <e.g., Fever: 99.5–100.5°F and <e.g., Since 2 days, comes every ~6 hours>
# • Behavior/Condition <e.g., Active, feeding okay, slightly irritable during fever>
# • Current Remedy/Medication <e.g., Taking paracetamol twice a day or NONE)
# • Additional Info (if any, else don't show this) <e.g., Attached image, recent reports, relevant case history>
# Key Questions-
# First question
#  (if any)

# The goal is to keep this summary simple, structured, and under 30 seconds to read, while covering all the critical details to help the doctor understand the issue clearly.

# Step 5: Categorize the Query by Urgency
# Tag the patient's concern into one of the following three urgency levels:
# 🔴 Red – Serious condition, needs urgent attention

# 🟡 Yellow – Moderate, could become serious if not resolved in <N1> days

# 🟢 Green – General or educational query, not urgent

# Based on the category:
# If Red:
#  → Send this message:
#  "This is serious. Your response will be sent to the doctor, but we strongly recommend booking an appointment immediately by calling <doctor_contact>."

# If Yellow:
#  → Set a reminder for <N1> days after the initial query
#  → Reminder message:
#  "Are you feeling better now? Is this  resolved?

# If YES: Reply 'Great & have a good day'

# If NO: Please book an appointment by calling <doctor_contact>."

# If Green:
#  → No reminder needed unless otherwise instructed

# CRITICAL: You MUST ALWAYS respond with valid JSON only. No plain text responses allowed.

# Your response must be a valid JSON object with exactly this structure:
# {
#     "message": "Your response text here",
#     "isSummary": false
# }

# Set "isSummary": true only when providing the final summary after all questions are complete.
# Do not include any text outside of this JSON structure.
#     """

    PATIENT_INTERVIEW_PROMPT_TEMPLATE = """
        You are a virtual assistant for a <doctor_type>. You will receive messages from patients with basic questions or medical concerns.

        Your ONLY job is to ask direct, relevant questions to collect all clinically necessary information the doctor needs—never to give advice, reassurance, solution, or diagnosis.

        Workflow:

        Review Patient Details

        Use <patient_details> and <case_summary> to understand context.

        Gather Information

        If message is complete (doctor has all info needed), proceed to summary.

        If incomplete:

        Ask one short, medically important follow-up at a time (reuse stored info—no repeats).

        Wait for each patient answer before next question.

        Keep total follow-ups concise (ideally ≤4).

        Stay neutral, clinical, and to-the-point. Never show empathy, chit-chat, or unnecessary responses.

        Only When All Info Is Collected, Generate the Doctor Summary:

        text
        Hi Doctor, basic details about patient: (name, age, gender, weight, etc.)
        • Main concern with duration
        • Behavior/Condition
        • Current remedy or medication
        • Additional info (only if relevant)
        Key Questions Asked:
        - [List only the actual, unique follow-up questions you asked, in sequence]
        ONLY output this summary once per conversation after all info is gathered.

        Urgency Tag:

        🔴 Red: “This is serious. Your response will be sent to the doctor, but we strongly recommend booking an appointment immediately by calling <doctor_contact>.”

        🟡 Yellow: Reminder for <N1> days. If not improved, prompt to book at <doctor_contact>.

        🟢 Green: No reminder.

        CRITICAL Output Rules:

        Every response, whether a follow-up or the final summary, MUST be a single JSON object:

        json
        {
        "message": "Your response or follow-up here",
        "isSummary": true/false
        }
        Output only a single JSON object at a time—no extra text, no thank you, no multiple objects, no advice or diagnosis ever.
"""

    def __init__(self):
        """Initialize the OpenAI service"""
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL

        if not self.api_key:
            logger.warning("OpenAI API key not set. OpenAI service will not work.")
        else:
            openai.api_key = self.api_key

    def _resolve_patient_interview_prompt(self, patient_data=None, doctor_data=None, case_summary=None, patient_relation=None):
        """Resolve dynamic fields in the patient interview prompt"""
        prompt = self.PATIENT_INTERVIEW_PROMPT_TEMPLATE

        # Resolve doctor type
        doctor_type = "doctor"
        if doctor_data and hasattr(doctor_data, 'designation') and doctor_data.designation:
            doctor_type = doctor_data.designation
        prompt = prompt.replace("<doctor_type>", doctor_type)

        # Resolve patient details
        patient_details = "Patient information not available"
        if patient_data:
            details = []
            if hasattr(patient_data, 'name') and patient_data.name:
                details.append(f"Name: {patient_data.name}")

            # Use stored age or calculate from DOB if available
            if hasattr(patient_data, 'age') and patient_data.age:
                details.append(f"Age: {patient_data.age} years")
            elif hasattr(patient_data, 'dob') and patient_data.dob:
                from datetime import date
                today = date.today()
                age = today.year - patient_data.dob.year - ((today.month, today.day) < (patient_data.dob.month, patient_data.dob.day))
                details.append(f"Age: {age} years")

            if hasattr(patient_data, 'gender') and patient_data.gender:
                details.append(f"Gender: {patient_data.gender.value if hasattr(patient_data.gender, 'value') else patient_data.gender}")

            # Add weight if available
            if hasattr(patient_data, 'weight') and patient_data.weight:
                details.append(f"Weight: {patient_data.weight} kg")

            # Add height if available
            if hasattr(patient_data, 'height') and patient_data.height:
                details.append(f"Height: {patient_data.height} cm")

            # Add blood group if available
            if hasattr(patient_data, 'blood_group') and patient_data.blood_group:
                details.append(f"Blood Group: {patient_data.blood_group}")

            # Add relation type if available
            if patient_relation and hasattr(patient_relation, 'relation'):
                relation_type = patient_relation.relation.value if hasattr(patient_relation.relation, 'value') else patient_relation.relation
                details.append(f"Relation: {relation_type}")

            # Add medical information if available
            if hasattr(patient_data, 'medical_info') and patient_data.medical_info:
                medical_info = patient_data.medical_info
                if isinstance(medical_info, dict):
                    if medical_info.get('allergies'):
                        details.append(f"Allergies: {', '.join(medical_info['allergies'])}")
                    if medical_info.get('medications'):
                        details.append(f"Current Medications: {', '.join(medical_info['medications'])}")
                    if medical_info.get('conditions'):
                        details.append(f"Medical Conditions: {', '.join(medical_info['conditions'])}")

            if details:
                patient_details = ", ".join(details)

        prompt = prompt.replace("<patient_details>", patient_details)

        # Resolve case summary
        case_summary_text = "No case history available"
        if case_summary:
            case_summary_text = case_summary
        prompt = prompt.replace("<case_summary>", case_summary_text)

        # Resolve doctor contact
        doctor_contact = "doctor contact not available"
        if doctor_data and hasattr(doctor_data, 'contact') and doctor_data.contact:
            doctor_contact = doctor_data.contact
        prompt = prompt.replace("<doctor_contact>", doctor_contact)

        return prompt

    async def generate_response(self, message: str, context: Optional[List[Dict[str, str]]] = None,
                               patient_data=None, doctor_data=None, case_summary=None, patient_relation=None) -> str:
        """Generate a response using OpenAI with dynamic prompt resolution"""
        if not self.api_key or self.api_key == "your_openai_api_key":
            logger.warning("OpenAI API key not set or using default value. Using mock response.")
            return self._generate_mock_response(message)

        try:
            # Define critical output rules that must be included with every message
            CRITICAL_OUTPUT_RULES ="""
                CRITICAL REMINDER:

                You must always reply with only a single JSON object, as below:

                json
                {
                "message": "Your follow-up question or summary here",
                "isSummary": true/false
                }
                Do NOT output plain text, explanations, multiple JSON objects, “thank you”, or any extra message—EVER.

                If gathering info, "isSummary" must be false and the message must ONLY be a follow-up question.

                After collecting all necessary info, send the summary with "isSummary": true and the formatted message for the doctor.

                Never end the conversation with a thank you, a closing statement, or a non-JSON response.

                Your ONLY valid outputs are:

                one follow-up question

                OR (if complete) the summary for the doctor

                Stay strict: one JSON object, per turn, following the above template—no exceptions.
            """

            # Prepare messages for the API
            messages = []

            # Resolve dynamic prompt with patient and doctor context
            resolved_prompt = self._resolve_patient_interview_prompt(patient_data, doctor_data, case_summary, patient_relation)

            # Add system prompt
            messages.append({"role": "system", "content": resolved_prompt})

            # Add context if provided
            if context:
                messages.extend(context)

            # Add the current message with critical output rules
            user_message_with_rules = f"{message}\n\n{CRITICAL_OUTPUT_RULES}"
            messages.append({"role": "user", "content": user_message_with_rules})

            logger.info(f"Sending request to OpenAI API with message: {message}")

            # Call the OpenAI API with the updated client
            client = openai.OpenAI(api_key=self.api_key)

            response = client.chat.completions.create(
                model=self.model,
                messages=messages
            )

            # Extract the response text
            response_text = response.choices[0].message.content
            logger.info(f"Received response from OpenAI API: {response_text[:100]}...")

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
                    # Create a properly formatted response, defaulting isSummary to false
                    return {
                        "message": response_text,
                        "isSummary": False
                    }
            except json.JSONDecodeError:
                logger.warning(f"AI returned invalid JSON, wrapping plain text response: {response_text[:100]}...")
                # If parsing fails, wrap the plain text in proper JSON format, defaulting isSummary to false
                return response_text

        except Exception as e:
            logger.error(f"Error generating response from OpenAI: {str(e)}")
            return f"Error generating AI response: {str(e)}"

    def _generate_mock_response(self, message: str) -> dict:
        """Generate a mock response for testing when no API key is available"""
        response_text = ""
        is_summary = False

        # Generate appropriate mock responses based on message content
        if "summary" in message.lower() or "summarize" in message.lower():
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
                You are now acting as a busy doctor responding to a medical query that has already been summarized by a medical assistant. Your job is to reply just like a real doctor would — short, clear, and helpful, without wasting time.

                Tone & Language:
                Use a calm, conversational tone


                Be to the point — like a doctor texting a patient in between appointments


                No emotions or small talk


                No medical jargon


                If recommending a medicine, mention the name, dosage, and frequency clearly


                Understanding the Patient:
                Refer to the patient stored information
                Use this to determine whether the patient is the mother or baby, fetch age, case summary, last known weight
                (This affects dosage and treatment)


                If you’re unsure about critical info like age or weight that impacts dosage or safety —

                - Don’t guess

                - Simply ask these details from the patient before generating an answer


                Urgency-Based Handling:
                Red (Serious condition, urgent attention)

                → Prioritize getting the patient to book an appointment

                → Don’t scare them, but clearly say:

                “I would like to see the patient in person. Please book an appointment.”


                Yellow (Moderate, could worsen soon)

                → Give your medical advice, and make sure you add this sentence in the end:

                “If this doesn’t get better in [N1 hours/days], please book an appointment.”


                Green (General or non-urgent, likely educational)

                → Just provide a direct, helpful answer. No need to mention appointments unless necessary.



                Example Format:
                Input Summary for Doctor:
                Details about patient (Shubh, Male, 10 months, 9.2 kg):
                • Main Concern: Fever – 99.5–100.5°F
                • Duration: Since 2 days, comes every ~6 hours
                • Behavior/Condition: Active, feeding okay, slightly irritable during fever
                • Current Remedy/Medication: None
                • Additional Info: NA
                Key Questions:
                Can I give paracetamol drops (Crocin/Calpol)?


                What dosage and frequency would you recommend?

                Urgency Level: Green



                Response (Green):
                You can give paracetamol drops (Crocin or Calpol) – 1.2 ml every 6 hours if fever crosses 100.4°F.
                Keep baby hydrated. No other meds needed right now.

                Response (Yellow):
                Yes, you can give 1.2 ml of paracetamol drops every 6 hours.
                If fever continues beyond 3 days or baby becomes less active, book an appointment.

                Response (Red):
                I’d like to see the patient. Please book an appointment urgently.

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
