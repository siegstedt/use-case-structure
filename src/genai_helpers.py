import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
import json
from pydantic import BaseModel


def _get_api_key() -> str:
    """
    Retrieves the Gemini API key from either a .env file or environment variables.
    """
    api_key = None    

    if os.path.exists('.env'):
        load_dotenv(dotenv_path='.env')
        api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        raise ValueError(
            "API key not found. Please set it in a .env file (in the script's directory) or as an environment variable GEMINI_API_KEY."
        )
    return api_key


class CaseSchema(BaseModel):
    problem: str
    solution: str
    stakeholders: str
    outcomes: str
    technology: str

SCHEMA_KEYS = {
    "problem": "Problem: Identified Opportunity or Challenge.",
    "solution": "Idea: Proposed Solution or Initiative.",
    "stakeholders": "People: Key Stakeholders, Users, and Beneficiaries.",
    "outcomes": "Outcome: Expected High-level Benefits and Value.",
    "technology": "How: Potential Core Functionality and Technologies Involved."
}    

def generate_help_response(instruction):
    client = genai.Client(api_key=_get_api_key())
    response = client.models.generate_content(
        model="gemini-2.0-flash-lite-001",
        contents=instruction,
    )
    return response.text


def generate_use_case(context, instruction, history):
    client = genai.Client(api_key=_get_api_key())
    model = "gemini-2.0-flash-lite-001"
    contents = types.Content(
        role="user",
        parts=[
            types.Part.from_text(text=history),
            types.Part.from_text(text=context),
            types.Part.from_text(text=instruction)
        ]
    ),
    generate_content_config = types.GenerateContentConfig(
        response_mime_type='application/json',
        response_schema=CaseSchema,
    )
    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=generate_content_config
    )
    return response.text


def llm_extraction(raw_file_input: str, chat_history_messages: list) -> tuple[dict, str]:
    """
    Extracts information using an LLM to populate a predefined schema (Python dictionary)
    and then formats this schema into a markdown string for display.

    Args:
        raw_file_input (str): Text content from the uploaded file.
        chat_history_messages (list): List of chat messages in OpenAI format
                                      (e.g., [{"role": "user", "content": "..."}, ...]).

    Returns:
        tuple[dict, str]: A tuple containing:
            - extracted_info_dict (dict): The populated schema as a Python dictionary.
            - display_text (str): A markdown formatted string of the extracted information.
    """
    full_text_for_extraction = """\n<CONTEXT>\n""" + raw_file_input + """\n</CONTEXT>\n"""
    chat_history_text = (
        """\n<CONVERSATION_HISTORY>\n""" + 
        " ".join(i['content'] for i in chat_history_messages) +
        """\n</CONVERSATION_HISTORY>\n"""
    )
    instruction = """
    <OBJECTIVE>
    You are a specialist in analysing use cases in the domains of digitalisation, cloud, data and AI. 
    You have just received information on a Use Case. You will extract the key information into a structured format.
    </OBJECTIVE>
    <TASK>
    Extract the data from the information above. Follow the following order and structure.
    1. Problem: Identify and briefly summarize the main problem, challenge, or opportunity being addressed. 
    2. Solution: From the text provided, describe the proposed solution, initiative, or idea.
    3. Stakeholders: Identify and list the key stakeholders, users, customers, or beneficiaries mentioned or implied in the text.
    4. Benefits: Summarize the expected high-level benefits, value proposition, or desired outcomes of this initiative as described in the text.
    5. Technology: List any potential core functionalities, systems, or technologies (e.g., AI, cloud, specific platforms) mentioned or suggested in the text for implementing the solution.
    If no information has been clearly stated, indicate that. 
    Make sure to capture all information. Synthesise information as you summarise it.
    </TASK>
    """
    extracted_info_dict = {}
    try:
        # Call the LLM with the combined text and schema-based instruction
        llm_response = generate_use_case(
            context=full_text_for_extraction,
            instruction=instruction,
            history=chat_history_text
        )

        # Attempt to parse the LLM response as JSON
        try:
            llm_output_dict = json.loads(llm_response)
            # Map the LLM output to our internal schema keys
            extracted_info_dict["problem"] = llm_output_dict.get("problem", "[LLM did not identify or an error occurred]")
            extracted_info_dict["solution"] = llm_output_dict.get("solution", "[LLM did not identify or an error occurred]")
            extracted_info_dict["stakeholders"] = llm_output_dict.get("stakeholders", "[LLM did not identify or an error occurred]")
            extracted_info_dict["outcomes"] = llm_output_dict.get("outcomes", "[LLM did not identify or an error occurred]")
            extracted_info_dict["technology"] = llm_output_dict.get("technology", "[LLM did not identify or an error occurred]")
        except json.JSONDecodeError as e:
            print(f"Error decoding LLM JSON response: {e}\nResponse was: {llm_response}") 
            for key in SCHEMA_KEYS.keys():
                extracted_info_dict[key] = f"[LLM output format error: {e}]"
    except Exception as e:
        print(f"Error during LLM call or processing: {e}")
        for key in SCHEMA_KEYS.keys():
            extracted_info_dict[key] = f"[LLM call or processing error: {e}]"

    display_text = ""
    for schema_key, display_label in SCHEMA_KEYS.items():
        # Get the extracted value, default to a message if key somehow missing (should not happen)
        value = extracted_info_dict.get(schema_key, "[Information not available for this section]")
        display_text += f"**{display_label}**\n\n{value}\n\n"

    return extracted_info_dict, display_text
