# Help Desk Ticket Resolution Agent

An autonomous AI agent that triages and resolves customer support tickets, built with the [Claude API](https://docs.claude.com).

## The problem

Most support teams waste time on the same repetitive steps for every ticket: look up the customer, check if there's already an answer in the knowledge base, and figure out whether this is something that can be answered directly or needs a human. That triage work is repetitive but still requires judgment — a bad automated reply to a frustrated or billing-sensitive customer causes more damage than it saves.

## What this agent does

Given a ticket, the agent autonomously:

1. **Checks the customer's account** — looks up plan, order history, status
2. **Searches the knowledge base** — finds a relevant existing answer if one exists
3. **Decides how to respond:**
   - Drafts a grounded reply if it found a clear, confident answer
   - **Escalates to a human** if the issue is billing-sensitive, the customer sounds frustrated/angry, or no clear answer was found

The judgment about *when to escalate vs. resolve* lives in the system prompt, not hardcoded rules — this is the core difference between a simple chatbot and an agent: it reasons about the situation rather than following a fixed script.

## Example run

```
=== Ticket from jane@example.com ===
Message: Hi, my order #4471 arrived damaged. I'd like a refund please.

  -> called check_account({'email': 'jane@example.com'}) => Plan: Pro. Last order #4471, status: delivered Sept 12.
  -> called search_knowledge_base({'query': 'refund damaged order'}) => Refund policy: full refund within 30 days of delivery, no questions asked.
  -> called draft_reply({'message': '...'}) => [DRAFT REPLY SAVED]

Agent outcome: Resolved directly — refund approved per policy, reply drafted.

=== Ticket from sam@example.com ===
Message: I can't log in... this is the third time I'm emailing about this and I'm about to cancel.

  -> called check_account({'email': 'sam@example.com'}) => Plan: Free. No recent orders.
  -> called search_knowledge_base({'query': 'password reset not working'}) => Password resets: use the 'Forgot password' link on the login page.
  -> called escalate({'reason': 'Customer frustrated after repeated failed attempts, risk of churn'}) => [ESCALATED TO HUMAN]

Agent outcome: Escalated — recurring issue + churn risk, needs human judgment.
```

## How it works

- Built on the Anthropic Messages API with [tool use](https://docs.claude.com/en/docs/build-with-claude/tool-use) — the agent decides which of four tools to call and in what order
- Runs an agent loop: call the model → it requests a tool → execute the tool → return the result → repeat until it has enough information to act
- `check_account` and `search_knowledge_base` use mock data here so the demo runs standalone; in production these would call a real CRM/database and help-center API

## Setup

```bash
pip install anthropic
export ANTHROPIC_API_KEY=your_key_here
python agent.py
```

## Tech

- Python
- [Anthropic Claude API](https://docs.claude.com) (Claude Sonnet)
- Tool use / function calling
