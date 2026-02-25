from config import llm
from utils.state import AgentState
from utils.helpers import (
    log_agent_action,
    create_error_message,
    validate_state_field,
    format_posts_for_review,
    log_activity
)
from langchain_core.messages import HumanMessage, SystemMessage

MAX_REVISION_CYCLES = 2

def critic_agent(state: AgentState) -> AgentState:
    log_agent_action("critic", "Starting message quality review")

    try:
        messages = state.get("messages", [])
        company_info = state.get("company_info", "")
        task = state.get("task", "")
        revision_count = state.get("revision_count", 0)

        if not messages:
            return {
                **state,
                "error": "Critic received no messages to review.",
                "current_agent": "critic"
            }

        if revision_count >= MAX_REVISION_CYCLES:
            log_agent_action(
                "critic",
                "Max revision cycles reached",
                f"Approving after {revision_count} revisions"
            )
            log_activity("Critic", f"Max revision cycles reached ({revision_count}) — auto-approving", "", "decision")
            return {
                **state,
                "approved": True,
                "current_agent": "scheduler",
                "error": None
            }

        formatted_messages = format_posts_for_review(messages)

        system_prompt = SystemMessage(content="""
You are the Critic Agent of ULTRON, an AI-powered social media agency.
You are a senior Telegram content strategist with 10 years of experience
growing brands on Telegram channels and groups.

Review each message against these criteria:
1. CHARACTER COUNT: Is it under 4096 characters? (PASS or FAIL)
2. HOOK STRENGTH: Does the opening grab attention instantly? (Score 1-10)
3. CLARITY: Is the message clear and easy to understand? (Score 1-10)
4. ENGAGEMENT POTENTIAL: Will it get reactions, replies, forwards? (Score 1-10)
5. BRAND ALIGNMENT: Does it match the company tone? (Score 1-10)
6. FORMATTING QUALITY: Is Markdown formatting used effectively? (Score 1-10)

Respond in EXACTLY this format:

OVERALL_SCORE: [average score out of 10]
APPROVED: [YES or NO]
FEEDBACK: [Specific feedback for each message that needs improvement]
STRENGTHS: [What was done well across the messages]

If ANY message fails the 4096 character check, APPROVED must be NO.
If OVERALL_SCORE is 7.5 or above AND all messages pass character check, set APPROVED to YES.
""")

        human_prompt = HumanMessage(content=f"""
Review these Telegram messages for the following brand:

COMPANY INFO: {company_info}

ORIGINAL TASK: {task}

MESSAGES TO REVIEW:
{formatted_messages}

Check character count for each message carefully.
Apply your highest Telegram content standards.
""")

        log_agent_action("critic", "Sending messages to Groq LLM for review")
        log_activity("Critic", f"Reviewing {len(messages)} messages on 6 quality criteria", "Hook, clarity, engagement, brand alignment, formatting, character count", "llm_call")

        response = llm.invoke([system_prompt, human_prompt])

        response_text = response.content

        approved, feedback, score = _parse_critic_response(response_text)

        log_agent_action(
            "critic",
            f"Review complete — Score: {score} — Approved: {approved}",
            feedback[:150]
        )

        if approved:
            log_activity("Critic", f"Score: {score}/10 — Content APPROVED ✅", "", "decision")
            log_activity("Critic", "Handing off to Scheduler", "", "handoff")
            return {
                **state,
                "approved": True,
                "feedback": "",
                "current_agent": "scheduler",
                "error": None
            }
        else:
            log_activity("Critic", f"Score: {score}/10 — Needs revision (cycle {revision_count + 1}/{MAX_REVISION_CYCLES})", f"Feedback: {feedback[:120]}...", "decision")
            log_activity("Critic", "Sending back to Content Creator with feedback", "", "handoff")
            return {
                **state,
                "approved": False,
                "feedback": feedback,
                "revision_count": revision_count + 1,
                "current_agent": "content_creator",
                "error": None
            }

    except Exception as e:
        error_msg = create_error_message("critic", e)
        print(error_msg)
        return {
            **state,
            "error": error_msg,
            "current_agent": "critic"
        }


def _parse_critic_response(text: str) -> tuple:
    approved = False
    feedback = ""
    score = "0"

    lines = text.strip().split("\n")
    current_section = None

    for line in lines:
        line = line.strip()

        if line.startswith("OVERALL_SCORE:"):
            score = line.replace("OVERALL_SCORE:", "").strip()

        elif line.startswith("APPROVED:"):
            approval_text = line.replace("APPROVED:", "").strip().upper()
            approved = approval_text == "YES"

        elif line.startswith("FEEDBACK:"):
            current_section = "feedback"
            feedback = line.replace("FEEDBACK:", "").strip()

        elif line.startswith("STRENGTHS:"):
            current_section = "strengths"

        elif current_section == "feedback" and line:
            feedback += " " + line

    return approved, feedback, score