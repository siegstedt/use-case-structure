import os
import tempfile
import gradio as gr
import gradio as gr
from src.file_reader import read_file_content
from src.genai_helpers import llm_extraction, generate_help_response
from src import aiku_theme


def process_initial_file_upload(file_input):
    """Processes initial file upload, runs LLM extraction, returns markdown and raw content."""
    raw_content = ""
    if file_input:
        raw_content = read_file_content(file_input) # From your src.file_reader
        if raw_content:
            # Initial extraction uses only file content, no chat history yet
            schema_dict, display_markdown = llm_extraction(raw_content, [])
            return (
                schema_dict,
                display_markdown,
                raw_input_state,
                schema_dict.get("problem", ""),
                schema_dict.get("solution", ""),
                schema_dict.get("stakeholders", ""),
                schema_dict.get("outcomes", ""),
                schema_dict.get("technology", ""),
            )
    return "", "Please upload a file to begin.", "", "", "", "", "", ""


def chat_response(user_message, chat_history_list, current_extracted_content):
    # Append user message to history
    chat_history_list.append({"role": "user", "content": user_message})
    # Generate LLM response
    chat_prompt_context = f"Current Use Case Draft (from document):\n{current_extracted_content}\n\nConversation so far:\n"
    for entry in chat_history_list[:-1]: # History before current user message
        chat_prompt_context += f"{entry['role'].capitalize()}: {entry['content']}\n"
    chat_prompt_context += f"User: {user_message}\nAssistant, please respond:"
    bot_response_content = generate_help_response(chat_prompt_context)
    # Append to history
    chat_history_list.append({"role": "assistant", "content": bot_response_content})
    return "", chat_history_list


def update_structured_display(current_extracted_content, current_chat_history):
    """
    Called by the 'Update Details' button.
    Re-runs llm_extraction with current raw file content and full chat history.
    """
    if not current_extracted_content and not current_chat_history:
        return "*(No content to process. Please upload a file or chat first.)*", {}

    schema_dict, display_markdown = llm_extraction(
        current_extracted_content if current_extracted_content else "",
        current_chat_history if current_chat_history else []
    )
    return (
        schema_dict,
        display_markdown,
        schema_dict.get("problem", ""),
        schema_dict.get("solution", ""),
        schema_dict.get("stakeholders", ""),
        schema_dict.get("outcomes", ""),
        schema_dict.get("technology", ""),
    )


def create_temp_markdown_file(extracted_info):
    """Creates a temporary markdown file with the extracted information."""
    markdown_content = format_extracted_info_for_download(extracted_info)
    if not markdown_content:  # Handle empty content
        return None

    with tempfile.NamedTemporaryFile(mode="w", prefix="use_cases_with_aiku_", suffix=".md", delete=False, encoding="utf-8") as temp_file:
        temp_file.write(markdown_content)
        return temp_file.name


def delete_temp_file(filepath):
    """Deletes the temporary file."""
    if filepath and os.path.exists(filepath):
        os.remove(filepath)


def format_extracted_info_for_download(extracted_info):
    """Formats the extracted information into a markdown string with a title and AI support notification."""
    if isinstance(extracted_info, dict):
        markdown_content = "# Use Case Description\n\n"
        for key, label in SCHEMA_KEYS.items():
            markdown_content += f"## {label}\n{extracted_info.get(key, '[Not Available]')}\n\n"
        markdown_content += "---\n\n"
        markdown_content += (
            "This use case was refined with the support of AI tools. "
            "For questions or further assistance, please visit [https://aiku.tech](https://aiku.tech).\n"
        )
        return markdown_content
    return ""  # Return empty string if extracted_info is not a dictionary


SCHEMA_KEYS = {
    "problem": "Problem: Identified Opportunity or Challenge.",
    "solution": "Idea: Proposed Solution or Initiative.",
    "stakeholders": "People: Key Stakeholders, Users, and Beneficiaries.",
    "outcomes": "Outcome: Expected High-level Benefits and Value.",
    "technology": "How: Potential Core Functionality and Technologies Involved."
}    

aiku_theme = aiku_theme.AikuTheme()

with gr.Blocks(theme=aiku_theme, title="Structure Use Cases with AI") as demo:
    # Store the raw input text persistently on this page using State
    raw_input_state = gr.State("")
    extracted_schema_state = gr.State({})
    uc_extracted_info_display = gr.State("")

    gr.Markdown("# ✨ Define you Use Case.")    
    with gr.Row():            
        with gr.Column(scale=6):
            gr.Markdown("Describe your IT initiative by uploading a document or describing it below. Use the chat to refine details.")
            gr.Markdown("This was written by [Aiku](https://aiku.tech). This is Open Source. Any questions? Reach out!")
            gr.Markdown(
                """
                <div style="display: flex; justify-content: left; align-items: center; gap: 10px;">
                    <a href="https://aiku.tech" target="_blank"><img src="https://img.shields.io/badge/Visit_our_homepage-Aiku-blue" alt="Aiku Website"></a>
                    <a href="https://github.com" target="_blank"><img src="https://img.shields.io/badge/Pull_the_source_code-GitHub-lightgrey" alt="Source Code"></a>
                    <a href="mailto:hi@aiku.tech"><img src="https://img.shields.io/badge/Send_us_an_Email-Contact-green" alt="Contact Us"></a>
                </div>
                """
            )
        with gr.Column(scale=3):
            download_button = gr.DownloadButton(
                label="⬇️ Download Use Case",
                value=lambda: create_temp_markdown_file(extracted_schema_state),
                size="lg"
            )

    gr.Markdown("---")
    gr.Markdown("")

    with gr.Row(variant="panel"):
        with gr.Column(scale=2):
            uc_file_input = gr.File(
                label="Upload a document (such as .txt, .md, .pdf, .docx, .csv, .json)",
                file_count='single',
                file_types=['.txt', '.md', '.pdf', '.docx', '.csv', '.json'],
            )

        with gr.Column(scale=4):
            if raw_input_state == "":                
                gr.Markdown(
                    "*(Extracted details will appear here after processing)*"
                )
            with gr.Row():
                problem_textbox = gr.Textbox(
                    label=SCHEMA_KEYS["problem"], value="", interactive=True
                )
            with gr.Row():
                solution_textbox = gr.Textbox(
                    label=SCHEMA_KEYS["solution"], value="", interactive=True
                )
            with gr.Row():
                stakeholders_textbox = gr.Textbox(
                    label=SCHEMA_KEYS["stakeholders"], value="", interactive=True
                )
            with gr.Row():
                outcomes_textbox = gr.Textbox(
                    label=SCHEMA_KEYS["outcomes"], value="", interactive=True
                )
            with gr.Row():
                technology_textbox = gr.Textbox(
                    label=SCHEMA_KEYS["technology"], value="", interactive=True
                )

            # Store textboxes in a dictionary for easier access in event handlers
            textbox_dict = {
                "problem": problem_textbox, 
                "solution": solution_textbox, 
                "stakeholders": stakeholders_textbox, 
                "outcomes": outcomes_textbox, 
                "technology": technology_textbox
            }

        with gr.Column(scale=3): 
            uc_chatbot = gr.Chatbot(
                type="messages",
                label="Detail out with AI Chat",
                min_height=450,
            )
            uc_chat_message = gr.Textbox(
                label="Your Message", 
                placeholder="Ask questions or add details..."
            )
            update_button = gr.Button(
                "🔄 Update Use Case",
                size="lg"
            )
        
    # Initial extraction when file is uploaded
    uc_file_input.upload(
        process_initial_file_upload, 
        inputs=[uc_file_input], 
        outputs=[
            extracted_schema_state, 
            uc_extracted_info_display, 
            raw_input_state, 
            *textbox_dict.values()
        ]
    )
    # Handle chat message submission (updates chat history only)
    uc_chat_message.submit(
        fn=chat_response,
        inputs=[uc_chat_message, uc_chatbot, uc_extracted_info_display],
        outputs=[uc_chat_message, uc_chatbot]
    )
    # Handle 'Update' button click
    update_button.click(
        fn=update_structured_display,
        inputs=[uc_extracted_info_display, uc_chatbot],
        outputs=[
            extracted_schema_state,
            uc_extracted_info_display,
            textbox_dict["problem"],
            textbox_dict["solution"],
            textbox_dict["stakeholders"],
            textbox_dict["outcomes"],
            textbox_dict["technology"],
        ]
    )

    # Event listener for download button - now calls a Python function to create the file
    download_button.click(
        create_temp_markdown_file,  # Call Python function to create file
        [extracted_schema_state],  # Input: extracted schema
        [download_button],  # Output: update the download button with the file path
    )

    # JavaScript to trigger the download (now separate from file creation)
    demo.js = """
        function triggerDownload(file_path) {
            if (file_path) {
                const link = document.createElement('a');
                link.href = file_path;
                link.download = 'innovation_use_cases_with_aiku.md';
                link.click();
            }
        }
    """

    gr.HTML(
        """
        <p style='text-align: center; margin-top: 20px;'>
        <a href='https://aiku.tech' target='_blank'>AI-powered Use Case Structuring by aiku.tech</a> | Open Source - Questions? Reach out!
        </p>
        """
    )

if __name__ == "__main__":
    demo.launch(favicon_path="assets/aiku-signet.png")
