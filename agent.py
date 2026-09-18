"""
Help Desk Ticket Resolution Agent

An autonomous agent that triages incoming support tickets: it looks up
the customer's account, searches a knowledge base for a relevant
answer, and either drafts a resolution or escalates to a human when
it's not confident (billing-sensitive issues, angry tone, or no clear
answer found).

In this demo, account lookup and the knowledge base are mocked with
sample data so it runs standalone with no external services. In a
real deployment, swap those two functions for calls to your actual
CRM/database and help-center API.

Install:
    pip install anthropic

Run:
    export ANTHROPIC_API_KEY=your_key_here
    python agent.py
"""

import anthropic
import json

client = anthropic.Anthropic()


# ---------------------------------------------------------------------
# Tools available to the agent. In production, replace the mock data
# in check_account() and search_knowledge_base() with real API calls.
# ---------------------------------------------------------------------

TOOLS = [
    {
        "name": "check_account",
        "description": "Look up a customer's account and recent order/subscription status by email.",
        "input_schema": {
            "type": "object",
            "properties": {"email": {"type": "string"}},
            "required": ["email"],
        },
    },
    {
        "name": "search_knowledge_base",
        "description": "Search the help-center knowledge base for an answer relevant to the ticket.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
    {
        "name": "draft_reply",
        "description": "Draft a resolution reply to send to the customer.",
        "input_schema": {
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "The reply text"}
            },
            "required": ["message"],
        },
    },
    {
        "name": "escalate",
        "description": "Escalate the ticket to a human agent instead of resolving it directly.",
        "input_schema": {
            "type": "object",
            "properties": {
                "reason": {"type": "string", "description": "Why this needs a human"}
            },
            "required": ["reason"],
        },
    },
]

MOCK_ACCOUNTS = {
    "jane@example.com": "Plan: Pro. Last order #4471, status: delivered Sept 12.",
    "sam@example.com": "Plan: Free. No recent orders.",
}

MOCK_KB = {
    "refund": "Refund policy: full refund within 30 days of delivery, no questions asked.",
    "password": "Password resets: use the 'Forgot password' link on the login page.",
    "shipping": "Standard shipping takes 5-7 business days; express is 2-3 days.",
}


def check_account(email: str) -> str:
    return MOCK_ACCOUNTS.get(email, "No account found for that email")


def search_knowledge_base(query: str) -> str:
    for keyword, answer in MOCK_KB.items():
        if keyword in query.lower():
            return answer
    return "No matching help-center article found."


def draft_reply(message: str) -> str:
    return f"[DRAFT REPLY SAVED]\n{message}"


def escalate(reason: str) -> str:
    return f"[ESCALATED TO HUMAN] Reason: {reason}"


TOOL_FUNCTIONS = {
    "check_account": check_account,
    "search_knowledge_base": search_knowledge_base,
    "draft_reply": draft_reply,
    "escalate": escalate,
}


# ---------------------------------------------------------------------
# Agent loop
# ---------------------------------------------------------------------

SYSTEM_PROMPT = (
    "You are a help desk ticket resolution agent. For every ticket: "
    "1) check the customer's account, 2) search the knowledge base for "
    "a relevant answer, then 3) either draft a reply grounded in what "
    "you found, or escalate to a human if the issue is billing-sensitive, "
    "the customer sounds angry/frustrated, or you can't find a clear answer. "
    "Always check the account before drafting a reply. Explain your "
    "final decision briefly after taking action."
)


def resolve_ticket(customer_email: str, ticket_text: str) -> str:
    messages = [
        {
            "role": "user",
            "content": f"Customer: {customer_email}\nTicket: {ticket_text}",
        }
    ]

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            final_text = "".join(
                block.text for block in response.content if block.type == "text"
            )
            return final_text

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                fn = TOOL_FUNCTIONS[block.name]
                result = fn(**block.input)
                print(f"  -> called {block.name}({block.input}) => {result}")
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    }
                )

        messages.append({"role": "user", "content": tool_results})


if __name__ == "__main__":
    sample_tickets = [
        (
            "jane@example.com",
            "Hi, my order #4471 arrived damaged. I'd like a refund please.",
        ),
        (
            "sam@example.com",
            "I can't log in, it says my password is wrong even after resetting twice. "
            "This is the third time I'm emailing about this and I'm about to cancel.",
        ),
    ]

    for email, ticket in sample_tickets:
        print(f"\n=== Ticket from {email} ===")
        print(f"Message: {ticket}\n")
        outcome = resolve_ticket(email, ticket)
        print(f"\nAgent outcome:\n{outcome}")
        print("=" * 60)
