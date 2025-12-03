"""
Model Selection Strategy
------------------------
Dynamically selects the appropriate AI model based on task complexity.
Upgrades from gpt-4o-mini to gpt-4o for complex tasks.
"""

from typing import List, Dict
import re


class ModelSelectionStrategy:
    """
    Strategy for selecting the appropriate model based on task characteristics.
    Solves the "gpt-4o-mini can't handle complex tasks" problem.
    """

    def __init__(self):
        """Initialize with complexity detection rules"""
        self.complexity_indicators = self._build_complexity_indicators()
        self.default_model = "gpt-4o-mini"
        self.complex_model = "gpt-4o"

    def _build_complexity_indicators(self) -> Dict[str, List[str]]:
        """
        Build indicators that suggest task complexity.

        Returns:
            Dictionary mapping categories to indicator keywords/patterns
        """
        return {
            # Tasks that require deep analysis
            "analysis_tasks": [
                "analyze", "analysis", "deep dive", "investigate",
                "examine", "review", "assess", "evaluate",
                "compare", "contrast", "summarize long",
                "complex analysis"
            ],

            # Multi-step reasoning tasks
            "multi_step_reasoning": [
                "plan", "strategy", "multi-step", "multiple steps",
                "workflow", "process", "sequence", "orchestrate",
                "coordinate between", "integrate", "complex workflow"
            ],

            # Document processing
            "document_processing": [
                "pdf", "document", "read file", "parse document",
                "extract from", "summarize document", "analyze document",
                "report generation", "create presentation"
            ],

            # Code-related tasks
            "code_tasks": [
                "code review", "debug", "refactor", "implement",
                "algorithm", "optimize code", "github pull request",
                "analyze code", "write tests"
            ],

            # Calendar and scheduling (complex due to timezone/conflict handling)
            "scheduling_tasks": [
                "schedule multiple", "complex meeting", "recurring event",
                "coordinate schedules", "find available time",
                "calendar conflict", "timezone"
            ],

            # Data analysis and calculations
            "data_tasks": [
                "calculate complex", "financial analysis", "data analysis",
                "spreadsheet analysis", "pivot", "aggregate data",
                "statistical", "forecast", "predict"
            ],

            # Creative/generative tasks requiring quality
            "creative_tasks": [
                "write detailed", "compose long", "creative writing",
                "marketing copy", "professional email",
                "proposal", "presentation content"
            ],

            # Integration tasks (multiple services)
            "integration_tasks": [
                "sync between", "migrate from", "export and import",
                "backup and restore", "cross-platform"
            ]
        }

    def select_model(
        self,
        user_prompt: str,
        connected_apps: List[str] = None,
        chat_history: List[Dict[str, str]] = None
    ) -> str:
        """
        Select appropriate model based on task complexity.

        Args:
            user_prompt: The user's current message
            connected_apps: List of connected applications
            chat_history: Previous conversation history

        Returns:
            Model name to use ("gpt-4o-mini" or "gpt-4o")
        """
        complexity_score = self._calculate_complexity_score(
            user_prompt,
            connected_apps,
            chat_history
        )

        # Threshold for upgrading to gpt-4o
        # Lower threshold = more aggressive upgrading
        UPGRADE_THRESHOLD = 2

        if complexity_score >= UPGRADE_THRESHOLD:
            print(f"🚀 Upgrading to {self.complex_model} (complexity score: {complexity_score})")
            return self.complex_model
        else:
            print(f"⚡ Using {self.default_model} (complexity score: {complexity_score})")
            return self.default_model

    def _calculate_complexity_score(
        self,
        user_prompt: str,
        connected_apps: List[str] = None,
        chat_history: List[Dict[str, str]] = None
    ) -> int:
        """
        Calculate complexity score for the task.

        Returns:
            Integer score (0 = simple, higher = more complex)
        """
        score = 0
        prompt_lower = user_prompt.lower()

        # Check for complexity indicators in the prompt
        for category, indicators in self.complexity_indicators.items():
            for indicator in indicators:
                if indicator in prompt_lower:
                    score += 1
                    print(f"  📊 Complexity indicator found: '{indicator}' ({category})")
                    # Don't count multiple indicators from same category
                    break

        # Check for long prompts (usually more complex)
        if len(user_prompt) > 500:
            score += 1
            print(f"  📊 Long prompt detected ({len(user_prompt)} chars)")

        # Check for multiple apps (suggests integration task)
        if connected_apps and len(connected_apps) >= 3:
            score += 1
            print(f"  📊 Multiple apps connected ({len(connected_apps)} apps)")

        # Check for calendar app (historically problematic with mini)
        if connected_apps and "GOOGLECALENDAR" in [app.upper() for app in connected_apps]:
            if any(word in prompt_lower for word in ["schedule", "meeting", "event", "calendar"]):
                score += 1
                print(f"  📊 Calendar operation detected (requires precision)")

        # Check chat history for context (multi-turn conversations can be complex)
        if chat_history and len(chat_history) > 6:
            score += 1
            print(f"  📊 Long conversation history ({len(chat_history)} messages)")

        return score

    def should_use_complex_model_for_app(self, app_name: str) -> bool:
        """
        Determine if a specific app always requires the complex model.

        Args:
            app_name: Application name

        Returns:
            True if this app should always use complex model
        """
        # Apps that consistently need the complex model
        complex_apps = {
            "GOOGLECALENDAR",  # Calendar logic is complex (timezones, conflicts)
            "GITHUB",          # Code operations need precision
            "NOTION",          # Complex data structures
            "AIRTABLE",        # Database operations
        }

        return app_name.upper() in complex_apps


# Global instance
_model_selection_strategy_instance = None


def get_model_selection_strategy() -> ModelSelectionStrategy:
    """Get or create the global model selection strategy instance"""
    global _model_selection_strategy_instance
    if _model_selection_strategy_instance is None:
        _model_selection_strategy_instance = ModelSelectionStrategy()
    return _model_selection_strategy_instance
