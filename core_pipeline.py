import gradio as gr
import os
from dotenv import load_dotenv
from openai import OpenAI
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
import re
import json

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def is_exit_command(text):
    exit_words = {"exit", "quit", "stop", "end"}
    return text.strip().lower() in exit_words

def openai_validate(field_name, user_input):
    prompt_map = {
        # ... same validation prompts as before ...
        "full name": f"""
You are an expert validator.
Check if the following full name is valid (non-empty, realistic human name with alphabetic characters, no numbers or special chars): "{user_input}".
Reply with "VALID" if valid. Otherwise reply "INVALID: <reason>".
""",
        "email": f"""
You are an expert validator.
Check if the following email address is valid and well-formed: "{user_input}".
Reply with "VALID" if valid email format. Otherwise reply "INVALID: <reason>".
""",
        "phone": f"""
You are an expert validator.
Check if the following phone number is valid. It should contain only digits and be between 7 and 15 digits long: "{user_input}".
Reply with "VALID" if it meets these criteria. Otherwise reply "INVALID: <reason>".
""",
        "experience": f"""
You are an expert validator.
Check if the following years of experience input is valid. It should be a numeric value between 0 and 50: "{user_input}".
Reply with "VALID" if valid, else "INVALID: <reason>".
""",
        "position": f"""
You are an expert career counselor and input validator.
Check if the following input represents a realistic and valid job position or title.
It should be a commonly recognized job role or title in the tech industry or related professional fields.
Input: "{user_input}"
Reply with "VALID" if this is a plausible job position/title.
Otherwise reply "INVALID: <reason why this is not a job position>".
""",
        "location": f"""
You are an expert validator.
Check if the following current location input is valid.
It should be a real-world city, state, region, or country name (non-empty, alphabetic, reasonable place name).
Input: "{user_input}"
Reply with "VALID" if valid, else "INVALID: <reason>".
""",
        "tech stack": f"""
You are a tech expert and validator.
Check if the following comma-separated list contains valid and common programming languages, frameworks, databases, or developer tools:
"{user_input}".
Reply with "VALID" if all terms look like valid technologies.
Otherwise reply "INVALID: <list invalid or unknown terms>".
"""
    }

    prompt = prompt_map.get(field_name.lower())
    if not prompt:
        if user_input.strip():
            return True, ""
        else:
            return False, "Input cannot be empty."

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        reply = response.choices[0].message.content.strip()
        if reply.upper().startswith("VALID"):
            return True, ""
        else:
            if "INVALID:" in reply:
                return False, reply.split("INVALID:", 1)[1].strip()
            else:
                return False, "Invalid input."
    except Exception:
        return True, ""

def generate_technical_questions(tech_stack_list):
    tech_str = ", ".join(tech_stack_list)
    prompt = f"""
You are an experienced technical interviewer.
Generate 3 to 5 clear, concise technical interview questions for a candidate skilled in these technologies: {tech_str}.
Limit questions to intermediate level proficiency.
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant for interview preparation."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )
        content = response.choices[0].message.content.strip()
        questions = [q.strip("- ").strip() for q in content.split("\n") if q.strip()]
        return questions
    except Exception as e:
        return [f"Error generating questions: {str(e)}"]

def evaluate_answer_feedback(question, answer):
    prompt = f"""
You are a technical interviewer providing feedback on a candidate's answer.
Question: "{question}"
Candidate's answer: "{answer}"

Provide a short constructive feedback (1-2 sentences) on the quality of the answer.
Also, rate the answer quality on a scale of 1 to 5 (5 is excellent).
Reply in this JSON format ONLY:
{{"feedback": "<your feedback>", "score": <score_integer>}}
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        reply = response.choices[0].message.content.strip()
        data = json.loads(reply)
        feedback = data.get("feedback", "No feedback available.")
        score = data.get("score", 3)
        return feedback, score
    except Exception:
        return "Could not generate feedback.", 3

def make_hiring_decision(candidate_info, answers):
    experience = candidate_info.get("experience", 0)
    position = candidate_info.get("position", "").strip()
    tech_stack = candidate_info.get("tech_stack", [])

    if experience < 2:
        return False, "Candidate has less than 2 years of experience."

    if not position or not tech_stack:
        return False, "Position or tech stack information is incomplete."

    scores = [qa.get("score", 3) for qa in answers]
    avg_score = sum(scores) / len(scores) if scores else 0
    if avg_score < 3:
        return False, f"Candidate's answers show average score {avg_score:.2f} which is below expectation."

    return True, "Candidate meets the criteria and shows good technical knowledge."

def sanitize_filename(s):
    return re.sub(r'[^a-zA-Z0-9_-]', '_', s)

def save_report_pdf(candidate_info, answers, hire_decision, reason):
    reports_dir = "reports"
    os.makedirs(reports_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = sanitize_filename(candidate_info.get("full_name", "candidate"))
    filename = os.path.join(reports_dir, f"{safe_name}_{timestamp}.pdf")

    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    margin = inch
    y = height - margin

    def write_line(text, font="Helvetica", size=12):
        nonlocal y
        c.setFont(font, size)
        c.drawString(margin, y, text)
        y -= size + 6
        if y < margin:
            c.showPage()
            y = height - margin

    write_line("TalentScout Hiring Assistant Bot - Candidate Report", font="Helvetica-Bold", size=16)
    write_line(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    write_line(" ")

    write_line("Candidate Information:", font="Helvetica-Bold", size=14)
    for key in ["full_name", "email", "phone", "experience", "position", "location"]:
        write_line(f"{key.replace('_', ' ').title()}: {candidate_info.get(key, 'N/A')}")
    write_line(f"Tech Stack: {', '.join(candidate_info.get('tech_stack', []))}")
    write_line(" ")

    write_line("Interview Questions, Answers and Feedback:", font="Helvetica-Bold", size=14)
    for i, qa in enumerate(answers, 1):
        write_line(f"Q{i}: {qa['question']}", font="Helvetica-Bold", size=12)

        answer_lines = []
        max_line_length = 90
        ans = qa['answer']
        while len(ans) > max_line_length:
            split_at = ans.rfind(' ', 0, max_line_length)
            if split_at == -1:
                split_at = max_line_length
            answer_lines.append(ans[:split_at])
            ans = ans[split_at:].lstrip()
        answer_lines.append(ans)
        for line in answer_lines:
            write_line(f"A{i}: {line}", font="Helvetica", size=12)

        write_line(f"Feedback: {qa.get('feedback', 'N/A')}", font="Helvetica-Oblique", size=11)
        write_line(f"Score: {qa.get('score', 'N/A')}/5")
        write_line(" ")

    write_line("Hiring Recommendation:", font="Helvetica-Bold", size=14)
    if hire_decision:
        write_line("Recommended for hiring. Congratulations!")
    else:
        write_line(f"Not recommended for hiring.")
        write_line(f"Reason: {reason}")

    c.save()
    return filename

conversation_state = {
    "stage": "greeting",
    "candidate_info": {},
    "questions": [],
    "answers": [],
    "current_question_index": 0,
}

def chat_function(message, history):
    if history is None:
        history = []

    user_input = message.strip()

    if is_exit_command(user_input):
        history.append({"role": "user", "content": user_input})
        history.append({"role": "assistant", "content": "Thank you for your time! We will be in touch with the next steps. Have a great day!"})
        conversation_state["stage"] = "ended"
        return history, True

    if conversation_state["stage"] == "greeting":
        greeting = (
            "🤖 Hello! I’m the TalentScout Hiring Assistant Bot.\n"
            "I will help collect some information and then ask technical questions based on your tech stack.\n"
            "You can type 'exit' anytime to quit.\n\n"
            "What is your full name?"
        )
        conversation_state["stage"] = "collect_name"
        history.append({"role": "assistant", "content": greeting})
        return history, False

    elif conversation_state["stage"] == "collect_name":
        is_valid, err_msg = openai_validate("full name", user_input)
        if not is_valid:
            history.append({"role": "assistant", "content": f"{err_msg} Please provide your full name to continue."})
            return history, False
        conversation_state["candidate_info"]["full_name"] = user_input
        history.append({"role": "user", "content": user_input})
        history.append({"role": "assistant", "content": "Great! Please enter your email address:"})
        conversation_state["stage"] = "collect_email"
        return history, False

    elif conversation_state["stage"] == "collect_email":
        is_valid, err_msg = openai_validate("email", user_input)
        if not is_valid:
            history.append({"role": "assistant", "content": f"{err_msg} That doesn't look like a valid email. Please enter a valid email address:"})
            return history, False
        conversation_state["candidate_info"]["email"] = user_input
        history.append({"role": "user", "content": user_input})
        history.append({"role": "assistant", "content": "Please enter your phone number (digits only, 7-15 characters):"})
        conversation_state["stage"] = "collect_phone"
        return history, False

    elif conversation_state["stage"] == "collect_phone":
        is_valid, err_msg = openai_validate("phone", user_input)
        if not is_valid:
            history.append({"role": "assistant", "content": f"{err_msg} Invalid phone number. Please enter a valid phone number (7-15 digits):"})
            return history, False
        conversation_state["candidate_info"]["phone"] = user_input
        history.append({"role": "user", "content": user_input})
        history.append({"role": "assistant", "content": "How many years of experience do you have? (Enter a number between 0 and 50)"})
        conversation_state["stage"] = "collect_experience"
        return history, False

    elif conversation_state["stage"] == "collect_experience":
        is_valid, err_msg = openai_validate("experience", user_input)
        if not is_valid:
            history.append({"role": "assistant", "content": f"{err_msg} Please enter a valid number for your years of experience (0-50):"})
            return history, False
        conversation_state["candidate_info"]["experience"] = int(user_input)
        history.append({"role": "user", "content": user_input})
        history.append({"role": "assistant", "content": "What is your desired position(s)? Please avoid numbers or special characters."})
        conversation_state["stage"] = "collect_position"
        return history, False

    elif conversation_state["stage"] == "collect_position":
        is_valid, err_msg = openai_validate("position", user_input)
        if not is_valid:
            history.append({"role": "assistant", "content": f"{err_msg} Please enter valid desired position(s) (commonly recognized job titles, alphabetic only):"})
            return history, False
        conversation_state["candidate_info"]["position"] = user_input
        history.append({"role": "user", "content": user_input})
        history.append({"role": "assistant", "content": "Where are you currently located?"})
        conversation_state["stage"] = "collect_location"
        return history, False

    elif conversation_state["stage"] == "collect_location":
        is_valid, err_msg = openai_validate("location", user_input)
        if not is_valid:
            history.append({"role": "assistant", "content": f"{err_msg} Please enter a valid current location (real city, state, region, or country):"})
            return history, False
        conversation_state["candidate_info"]["location"] = user_input
        history.append({"role": "user", "content": user_input})
        history.append({"role": "assistant", "content":
            "Please list your tech stack (programming languages, frameworks, databases, tools) separated by commas.\n"
            "For example: Python, Django, React, PostgreSQL"
        })
        conversation_state["stage"] = "collect_tech_stack"
        return history, False

    elif conversation_state["stage"] == "collect_tech_stack":
        is_valid, err_msg = openai_validate("tech stack", user_input)
        if not is_valid:
            history.append({"role": "assistant", "content": f"{err_msg} That doesn't look like a valid tech stack. Please list your technologies separated by commas, for example: Python, Django, React, PostgreSQL."})
            return history, False

        tech_list = [t.strip() for t in user_input.split(",") if t.strip()]
        conversation_state["candidate_info"]["tech_stack"] = tech_list
        history.append({"role": "user", "content": user_input})

        history.append({"role": "assistant", "content": "Generating technical questions for you... Please wait."})
        questions = generate_technical_questions(tech_list)
        conversation_state["questions"] = questions
        conversation_state["answers"] = []
        conversation_state["current_question_index"] = 0

        history.append({"role": "assistant", "content": f"Question 1: {questions[0]}"})
        conversation_state["stage"] = "asking_questions"
        return history, False

    elif conversation_state["stage"] == "asking_questions":
        current_index = conversation_state["current_question_index"]

        feedback, score = evaluate_answer_feedback(
            conversation_state["questions"][current_index], user_input
        )

        conversation_state["answers"].append({
            "question": conversation_state["questions"][current_index],
            "answer": user_input,
            "feedback": feedback,
            "score": score
        })

        history.append({"role": "user", "content": user_input})
        history.append({"role": "assistant", "content": f"💡 Feedback: {feedback} (Score: {score}/5)"})

        current_index += 1
        if current_index < len(conversation_state["questions"]):
            conversation_state["current_question_index"] = current_index
            next_q = conversation_state["questions"][current_index]
            history.append({"role": "assistant", "content": f"Question {current_index + 1}: {next_q}"})
            return history, False
        else:
            candidate_info = conversation_state["candidate_info"]
            answers = conversation_state["answers"]
            hire_decision, reason = make_hiring_decision(candidate_info, answers)

            history.append({"role": "assistant", "content": "✅ Interview completed. Thank you for your answers!"})
            summary = "Here is the summary of your submitted information and answers:\n\n"
            summary += (
                f"Full Name: {candidate_info.get('full_name')}\n"
                f"Email: {candidate_info.get('email')}\n"
                f"Phone: {candidate_info.get('phone')}\n"
                f"Years of Experience: {candidate_info.get('experience')}\n"
                f"Desired Position(s): {candidate_info.get('position')}\n"
                f"Location: {candidate_info.get('location')}\n"
                f"Tech Stack: {', '.join(candidate_info.get('tech_stack', []))}\n\n"
            )
            for i, qa in enumerate(answers, 1):
                summary += f"Q{i}: {qa['question']}\nA{i}: {qa['answer']}\nFeedback: {qa['feedback']}\nScore: {qa['score']}/5\n\n"

            history.append({"role": "assistant", "content": summary})
            history.append({"role": "assistant", "content": "We will review your responses and get back to you soon. Goodbye!"})

            # Save detailed report PDF for hiring team
            pdf_path = save_report_pdf(candidate_info, answers, hire_decision, reason)
            print(f"[INFO] Candidate report saved: {pdf_path}")

            conversation_state["stage"] = "ended"
            return history, True

    else:
        history.append({"role": "assistant", "content": "The conversation has ended. Please refresh to start a new session."})
        return history, True

def build_gradio_interface():
    with gr.Blocks() as demo:
        gr.Markdown("# TalentScout Hiring Assistant Bot")
        chatbot = gr.Chatbot(type="messages", elem_id="chatbot")
        textbox = gr.Textbox(placeholder="Type here...")
        end_flag = gr.State(False)

        def update_chat(user_message, chat_history, ended):
            if ended:
                return chat_history, "", ended

            chat_history, ended = chat_function(user_message, chat_history)
            return chat_history, "", ended

        textbox.submit(update_chat, inputs=[textbox, chatbot, end_flag], outputs=[chatbot, textbox, end_flag])

        gr.Button("Exit").click(
            lambda: (
                [
                    {"role": "user", "content": "exit"},
                    {"role": "assistant", "content": "Thank you for your time! We will be in touch with the next steps. Have a great day!"}
                ], "", True),
            None,
            [chatbot, textbox, end_flag]
        )

    return demo

if __name__ == "__main__":
    interface = build_gradio_interface()
    interface.launch()
