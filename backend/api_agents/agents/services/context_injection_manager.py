"""
Context Injection Manager
-------------------------
Orchestrates the injection of all contextual information into agent prompts.
Combines system context (date, user) with app-specific guidance.
"""

import datetime
from typing import List, Dict, Any
from .app_context_library import get_contexts_for_connected_apps


class ContextInjectionManager:
    """
    Manages the complete context injection pipeline for agents.
    Combines system-level context with application-specific guidance.
    """

    def __init__(self):
        """Initialize the context manager"""
        pass

    def build_complete_context(
        self,
        user,
        agent_model,
        connected_apps: List[str] = None,
        include_app_guidance: bool = True,
        **kwargs
    ) -> str:
        """
        Build the complete context string to inject into agent prompt.

        Args:
            user: Django user instance
            agent_model: Agent model instance
            connected_apps: List of connected app names (e.g., ["GMAIL", "SLACK"])
            include_app_guidance: Whether to include app-specific guidance
            **kwargs: Additional parameters

        Returns:
            Complete formatted context string
        """
        context_parts = []

        # 1. System Context (Date, Time, User Identity)
        system_context = self._build_system_context(user)
        if system_context:
            context_parts.append(system_context)

        # 2. Operational Rules (Tool Usage, Autonomy)
        operational_rules = self._build_operational_rules()
        if operational_rules:
            context_parts.append(operational_rules)

        # 3. App-Specific Guidance
        if include_app_guidance and connected_apps:
            app_context = get_contexts_for_connected_apps(connected_apps)
            if app_context:
                context_parts.append(app_context)

        # 4. Additional Custom Context
        custom_context = kwargs.get('custom_context')
        if custom_context:
            context_parts.append(custom_context)

        if not context_parts:
            return ""

        return "\n".join(context_parts)

    def _build_system_context(self, user) -> str:
        """Build system-level context (date, time, user identity)"""
        now = datetime.datetime.now()
        current_time = now.strftime("%A, %B %d, %Y at %I:%M %p")
        current_date_short = now.strftime("%Y-%m-%d")
        day_of_week = now.strftime("%A")
        current_year = now.year

        # Build user identity string
        user_info_parts = [f"User ID: {user.id}"]

        if hasattr(user, 'username') and user.username:
            user_info_parts.append(f"Username: {user.username}")
        if hasattr(user, 'email') and user.email:
            user_info_parts.append(f"Email: {user.email}")
        if hasattr(user, 'first_name') and user.first_name:
            name = user.first_name
            if hasattr(user, 'last_name') and user.last_name:
                name += f" {user.last_name}"
            user_info_parts.append(f"Name: {name}")

        user_context = ", ".join(user_info_parts)

        return f"""
{'='*80}
🌍 SYSTEM CONTEXT
{'='*80}

📅 **CURRENT DATE & TIME**
• Full Date/Time: {current_time}
• ISO Date: {current_date_short}
• Day of Week: {day_of_week}
• Year: {current_year}
• ⚠️  IMPORTANT: When user mentions "today", "current", "latest", "now", or "this year", use these values!

👤 **USER IDENTITY**
• {user_context}
• 🔐 Authentication: You are already authenticated as this user for ALL connected services.
• ⚠️  NEVER ask the user for their account credentials, usernames, handles, or IDs.
• You have full authorized access to perform actions on their behalf.

{'='*80}
"""

    def _build_operational_rules(self) -> str:
        """Build operational and behavioral rules for the agent"""
        return """
🤖 OPERATIONAL RULES & BEST PRACTICES
{'='*80}

**1. AUTONOMOUS EXECUTION**
• Execute actions immediately without asking for permission.
• Don't ask "Would you like me to..." or "Should I..." - just do it.
• Only ask for clarification if CRITICAL information is missing (e.g., recipient email, file name).
• After completion, provide a brief confirmation of what was done.

**2. TOOL USAGE vs TEXT SIMULATION**
• ⚠️  CRITICAL: When you have a tool available, you MUST USE IT.
• ❌ NEVER write: "I'll send an email to..." or "Here's what I would post..."
• ✅ ALWAYS: Actually call the tool and let it execute.
• Example:
  • User: "Send email to john@example.com saying hello"
  • ❌ Wrong: "I'll send an email to john@example.com with the message 'Hello'"
  • ✅ Correct: [Calls GMAIL_SEND_EMAIL] → "Email sent successfully to john@example.com"

**3. VERIFICATION & IDEMPOTENCY**
• **Calendar Events**: Search for existing events BEFORE creating new ones (avoid duplicates).
• **Email/Messages**: After sending, assume success unless you get an error. Don't retry blindly.
• **Social Posts**: After posting, verify success. Never retry without confirmation (duplicate posts are bad UX).
• **File Operations**: Check if files exist before uploading to avoid duplicates.

**4. MULTI-STEP WORKFLOWS**
• Some tasks require multiple steps - execute them in sequence:
  • Example: "Email this Drive file" → Find file → Download → Attach → Send
  • Example: "Schedule meeting" → Check calendar for conflicts → Create event → Confirm
• Complete all steps without asking for approval between each step.

**5. ERROR HANDLING**
• If a tool returns an error, explain what happened and suggest a solution.
• Don't fail silently - always inform the user of errors.
• If you're unsure, it's better to ask than to guess wrong.

**6. CURRENT/LIVE DATA**
• If user asks for "current stock prices", "latest news", "today's weather", you need real-time data.
• Use web search tools if available, or explain you need a search tool for live data.
• Don't hallucinate or provide outdated information from your training data.

{'='*80}
"""


# Global instance for easy access
_context_manager_instance = None


def get_context_manager() -> ContextInjectionManager:
    """Get or create the global context manager instance"""
    global _context_manager_instance
    if _context_manager_instance is None:
        _context_manager_instance = ContextInjectionManager()
    return _context_manager_instance
