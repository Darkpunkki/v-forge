"""Simple questionnaire engine for MVP."""

from vibeforge_api.models.responses import QuestionResponse, QuestionOption


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

    def get_next_question(self, current_index: int) -> QuestionResponse | None:
        """Get the next question based on current index."""
        if current_index >= len(self.questions):
            return None

        q = self.questions[current_index]
        options = (
            [QuestionOption(**opt) for opt in q["options"]] if "options" in q else None
        )

        return QuestionResponse(
            question_id=q["question_id"],
            text=q["text"],
            question_type=q["question_type"],
            options=options,
            min_value=q.get("min_value"),
            max_value=q.get("max_value"),
            is_final=(current_index == len(self.questions) - 1),
        )

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


# Global questionnaire engine instance
questionnaire_engine = QuestionnaireEngine()
