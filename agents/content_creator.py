from config import llm
from utils.state import AgentState
from utils.helpers import (
    log_agent_action,
    create_error_message,
    validate_state_field,
    parse_numbered_list,
    log_activity
)
from langchain_core.messages import HumanMessage, SystemMessage

def content_creator_agent(state: AgentState) -> AgentState:
    log_agent_action("content_creator", "Starting Telegram message creation")

    try:
        task = state.get("task", "")
        company_info = state.get("company_info", "")
        research_results = state.get("research_results", "")
        feedback = state.get("feedback", "")
        existing_messages = state.get("messages", [])

        if not validate_state_field(state, "research_results", "content_creator"):
            return {
                **state,
                "error": "Content Creator needs research results but found none.",
                "current_agent": "content_creator"
            }

        is_revision = bool(feedback and existing_messages)

        if is_revision:
            log_agent_action(
                "content_creator",
                "Revision mode activated",
                f"Incorporating feedback: {feedback[:100]}..."
            )
            log_activity("Content Creator", "Revision mode — rewriting messages with Critic's feedback", f"Feedback: {feedback[:100]}...", "info")

        system_prompt = SystemMessage(content="""
You are the Content Creator Agent of ULTRON, an AI-powered social media agency.
You create world-class Telegram channel messages that drive engagement and grow brands.

CRITICAL TELEGRAM RULES:
- Each message must be UNDER 4096 characters including spaces and formatting
- Use Telegram Markdown formatting: *bold*, _italic_, `code`, [links](url)
- Messages can be longer and more detailed — leverage this for richer content
- Use emojis strategically to make messages visually appealing
- Strong hook in the first line — Telegram users see previews
- End with either a question, CTA, or powerful statement to drive engagement
- Hashtags can be used but are less important on Telegram — focus on content quality

MESSAGE FORMAT — follow this exactly for every message:
---MESSAGE START---
[Your message content here — must be under 4096 characters]
---MESSAGE END---

Rules:
- Each message must be completely unique with a different angle
- Make it feel human and conversational, not corporate
- Tailor tone to match the company's brand voice
- Use formatting (bold, italic, emojis) to improve readability
""")

        if is_revision:
            human_prompt = HumanMessage(content=f"""
You previously wrote messages that received this feedback from our Critic:

CRITIC FEEDBACK:
{feedback}

ORIGINAL MESSAGES THAT NEED REVISION:
{chr(10).join([f"MESSAGE {i+1}: {m}" for i, m in enumerate(existing_messages)])}

COMPANY INFO: {company_info}
RESEARCH BRIEF: {research_results}

Revise ALL messages addressing every point in the feedback.
CRITICAL: Every revised message must be under 4096 characters.
Return complete revised messages in the exact format specified.
""")
        else:
            human_prompt = HumanMessage(content=f"""
Create engaging Telegram channel messages based on this information:

TASK: {task}

COMPANY INFO: {company_info}

RESEARCH BRIEF:
{research_results}

CRITICAL REMINDER: Every single message must be under 4096 characters.
Use Telegram Markdown formatting for readability.
Follow the exact message format specified in your instructions.
Number each message clearly.
""")

        log_agent_action("content_creator", "Sending to Groq LLM for message generation")
        log_activity("Content Creator", "Generating messages with Llama 3.3 70B", "Using research brief + brand context" if not is_revision else "Applying Critic's feedback to revise", "llm_call")

        response = llm.invoke([system_prompt, human_prompt])

        response_text = response.content

        messages = _parse_messages(response_text)

        if not messages:
            log_agent_action("content_creator", "WARNING: Message parsing failed, using fallback parser")
            messages = parse_numbered_list(response_text)

        if not messages:
            return {
                **state,
                "error": "Content Creator could not generate valid messages.",
                "current_agent": "content_creator"
            }

        messages = [m[:4096] for m in messages]

        log_agent_action(
            "content_creator",
            "Message creation complete",
            f"Generated {len(messages)} messages"
        )
        avg_len = sum(len(m) for m in messages) // max(len(messages), 1)
        log_activity("Content Creator", f"Generated {len(messages)} messages (avg {avg_len:,} chars each)", "", "info")
        log_activity("Content Creator", "Handing off to Critic for quality review", "", "handoff")

        return {
            **state,
            "messages": messages,
            "feedback": "",
            "current_agent": "critic",
            "error": None
        }

    except Exception as e:
        error_msg = create_error_message("content_creator", e)
        print(error_msg)
        return {
            **state,
            "error": error_msg,
            "current_agent": "content_creator"
        }


def _parse_messages(text: str) -> list:
    messages = []

    sections = text.split("---MESSAGE START---")

    for section in sections:
        if "---MESSAGE END---" in section:
            message_content = section.split("---MESSAGE END---")[0]
            message_content = message_content.strip()
            if message_content:
                messages.append(message_content)

    return messages