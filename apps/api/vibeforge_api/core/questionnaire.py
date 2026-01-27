"""Simple questionnaire engine for MVP (legacy — kept for orchestration internals)."""


# MVP: Hardcoded question bank
QUESTION_BANK = [
    {
        "question_id": "q1_audience",
        "text": "Who is the primary audience for this application?",
        "question_type": "radio",
        "options": [
            {"value": "general", "label": "General public"},
            {"value": "developers", "label": "Developers/technical users"},
            {"value": "business", "label": "Business professionals"},
            {"value": "students", "label": "Students/learners"},
        ],
    },
    {
        "question_id": "q2_platform",
        "text": "What platform should the application target?",
        "question_type": "radio",
        "options": [
            {"value": "web", "label": "Web application"},
            {"value": "mobile", "label": "Mobile app"},
            {"value": "desktop", "label": "Desktop application"},
            {"value": "cli", "label": "Command-line tool"},
        ],
    },
    {
        "question_id": "q3_complexity",
        "text": "What is the desired complexity level?",
        "question_type": "radio",
        "options": [
            {"value": "simple", "label": "Simple (1-3 screens)"},
            {"value": "moderate", "label": "Moderate (4-7 screens)"},
            {"value": "complex", "label": "Complex (8+ screens)"},
        ],
    },
]


class QuestionnaireEngine:
    """Manages questionnaire flow and validation."""

    def __init__(self):
        self.questions = QUESTION_BANK

    def get_next_question(self, current_index: int) -> dict | None:
        """Get the next question based on current index.

        Returns a plain dict (previously returned QuestionResponse Pydantic model,
        removed as part of legacy session cleanup).
        """
        if current_index >= len(self.questions):
            return None

        q = self.questions[current_index]
        return {
            "question_id": q["question_id"],
            "text": q["text"],
            "question_type": q["question_type"],
            "options": q.get("options"),
            "min_value": q.get("min_value"),
            "max_value": q.get("max_value"),
            "is_final": (current_index == len(self.questions) - 1),
        }

    def validate_answer(self, question_id: str, answer: any) -> bool:
        """Validate an answer against the question definition."""
        question = next((q for q in self.questions if q["question_id"] == question_id), None)
        if not question:
            return False

        if question["question_type"] in ["radio", "select"]:
            valid_values = [opt["value"] for opt in question["options"]]
            return answer in valid_values

        if question["question_type"] == "checkbox":
            if not isinstance(answer, list):
                return False
            valid_values = [opt["value"] for opt in question["options"]]
            return all(a in valid_values for a in answer)

        return True

    def is_questionnaire_complete(self, current_index: int) -> bool:
        """Check if questionnaire is complete."""
        return current_index >= len(self.questions)

    def finalize(self, session_id: str, answers: dict[str, any]) -> dict:
        """
        Finalize questionnaire and generate IntentProfile.

        Converts questionnaire answers to a schema-validated IntentProfile.
        """
        from datetime import datetime, timezone

        # Map answers to IntentProfile structure
        # For MVP, we'll use simple mappings from the 3 questions

        # Map audience (q1_audience)
        audience_value = answers.get("q1_audience", "general")
        audience_map = {
            "general": {"targetUser": "PUBLIC", "userCount": "MANY"},
            "developers": {"targetUser": "TEAM", "userCount": "FEW"},
            "business": {"targetUser": "SMALL_BUSINESS", "userCount": "MANY"},
            "students": {"targetUser": "PUBLIC", "userCount": "MANY"},
        }
        audience = audience_map.get(audience_value, {"targetUser": "SELF", "userCount": "ONE"})

        # Map platform (q2_platform)
        platform_value = answers.get("q2_platform", "web")
        platform_map = {
            "web": "WEB_APP",
            "mobile": "WEB_APP",  # MVP: treat mobile as web
            "desktop": "DESKTOP_APP",
            "cli": "CLI_APP",
        }
        platform_preference = platform_map.get(platform_value, "WEB_APP")

        # Map complexity (q3_complexity)
        complexity_value = answers.get("q3_complexity", "simple")
        complexity_map = {
            "simple": {"complexity": 30, "featureBudget": "TINY", "timeBudget": 30},
            "moderate": {"complexity": 60, "featureBudget": "SMALL", "timeBudget": 60},
            "complex": {"complexity": 85, "featureBudget": "MEDIUM", "timeBudget": 120},
        }
        complexity_info = complexity_map.get(complexity_value, complexity_map["simple"])

        # Build IntentProfile
        intent_profile = {
            "version": "1.0",
            "sessionId": session_id,
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "audience": audience,
            "platformPreference": platform_preference,
            "domains": ["PRODUCTIVITY"],  # MVP: default domain
            "vibe": {
                "seriousness": 50,  # MVP: neutral
                "visualStyle": "MODERN",  # MVP: default
                "complexity": complexity_info["complexity"],
                "randomness": "MEDIUM",  # MVP: default
            },
            "constraints": {
                "offlinePreferred": False,
                "authAllowed": True,
                "dataSensitivity": "LOW",
                "networkAccessDuringBuild": "ALLOW",
            },
            "scope": {
                "timeBudgetMinutes": complexity_info["timeBudget"],
                "featureBudget": complexity_info["featureBudget"],
            },
        }

        return intent_profile


# Global questionnaire engine instance
questionnaire_engine = QuestionnaireEngine()
