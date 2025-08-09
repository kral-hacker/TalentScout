# TalentScout Hiring Assistant Chatbot

## Project Overview

The **TalentScout Hiring Assistant Chatbot** is an AI-powered conversational assistant designed to streamline the technical hiring process. It interacts with candidates in a natural, conversational manner to:

- Collect essential candidate information (full name, contact details, experience, desired role, location, and tech stack).
- Validate inputs using OpenAI's GPT model to ensure data accuracy and relevance.
- Generate tailored intermediate-level technical interview questions based on the candidate's declared tech stack.
- Collect candidate answers and provide feedback and scoring for each response.
- Store all candidate data and answers securely for review by hiring managers, including export to PDF.
- Maintain conversational context, enable graceful exits, and provide a smooth user experience.

---

## Installation Instructions

### Prerequisites

- Python 3.8+
- OpenAI API Key
- Virtual environment tool (optional but recommended)

### Setup Steps

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/talentscout-chatbot.git
   cd talentscout-chatbot
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv env
source env/bin/activate  
```
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create a .env file in the project root and add your OpenAI API key:
   ```bash
   OPENAI_API_KEY=your_openai_api_key_here
```
5. Run the chatbot application:
```bash
python core_pipeline.py
```

## Usage Guide
Launch the app and interact via the chat interface.

The chatbot will prompt you step-by-step to provide your personal and professional information.

Once your tech stack is provided, the chatbot generates personalized technical questions.

Answer the questions in sequence.

At the end, a summary of your inputs and answers is generated.

The candidate’s responses are saved for hiring managers to review along with scoring and feedback.

You can type commands like exit or quit anytime to end the conversation gracefully.

## Technical Details
Programming Language: Python 3.8+

Frontend UI: Gradio for a clean, interactive web-based chat interface.

Backend: OpenAI GPT-4o-mini model for dynamic prompt-based validation, question generation, and answer evaluation.

State Management: Conversation state is maintained in-memory during the session.

Data Storage: Candidate information and responses are saved as PDF reports for hiring team review.

Libraries Used:

gradio for UI

python-dotenv for environment variables

openai Python SDK for API communication

fpdf or reportlab (depending on implementation) for PDF generation

## Prompt Design
Prompts for input validation are crafted to explicitly instruct the model to evaluate the user input according to defined rules (e.g., valid email, phone number format, plausible job titles).

Technical question generation prompts specify the tech stack and request intermediate-level questions, ensuring relevance and clarity.

Answer evaluation prompts instruct the model to score answers on a 1-5 scale, give feedback, and provide explanations.

Prompts emphasize maintaining a professional, encouraging tone while being precise and concise.

The design ensures the chatbot maintains coherent, context-aware dialogues with smooth stage transitions.


## Challenges & Solutions
Challenge 1: Input Validation Without Hardcoding
Solution: Instead of using regex and fixed lists, all input validation is delegated to OpenAI GPT via carefully crafted validation prompts. This allows for flexible, adaptive validation that can handle diverse and unexpected inputs.

Challenge 2: Real-Time Interactive Chat with Context
Solution: Implemented a state machine approach to track conversation stages and data. Each user input is processed with context, allowing for smooth transitions and fallback when input is invalid.

Challenge 3: Providing Meaningful Answer Feedback and Scoring
Solution: Developed prompts that guide GPT to score and comment on candidate answers, providing actionable feedback for hiring managers while maintaining an encouraging user experience.

Challenge 4: Data Privacy and Secure Storage
Solution: Candidate data is stored only as PDF summaries for hiring managers. No sensitive data is exposed in the chatbot UI or logs. Environment variables keep API keys secure.

