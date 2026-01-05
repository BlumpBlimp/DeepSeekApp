from typing import List, Dict, Tuple
import random
from datetime import datetime
from .deepseek_client import DeepSeekClient
import json


class QuizGenerator:
    """Generate quizzes from study materials"""

    def __init__(self):
        self.client = DeepSeekClient()

    def generate_questions(self, context: str, count: int = 5,
                           question_types: List[str] = None) -> List[Dict]:
        """Generate questions from study context"""
        if question_types is None:
            question_types = ["multiple_choice", "true_false", "short_answer"]

        prompt = f"""
        Based on the following study material, generate {count} questions.

        Study Material:
        {context}

        Requirements:
        1. Mix question types: {', '.join(question_types)}
        2. Include the correct answer for each
        3. For multiple choice: provide 4 options (A, B, C, D)
        4. For true/false: state clearly if true or false
        5. For short answer: provide expected key points

        Format as JSON with this structure:
        {{
            "questions": [
                {{
                    "type": "question_type",
                    "question": "question text",
                    "options": ["A", "B", "C", "D"],  # only for multiple_choice
                    "correct_answer": "correct answer",
                    "explanation": "brief explanation"
                }}
            ]
        }}
        """

        response = self.client.single_message(
            prompt,
            system_prompt="You are an expert educational content creator. Generate accurate, clear study questions."
        )

        try:
            # Extract JSON from response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            json_str = response[start_idx:end_idx]
            data = json.loads(json_str)
            return data.get("questions", [])
        except:
            # Fallback: parse manually
            return self._parse_questions_manually(response)

    def _parse_questions_manually(self, text: str) -> List[Dict]:
        """Manual parsing if JSON fails"""
        questions = []
        lines = text.split('\n')

        current_question = {}
        for line in lines:
            line = line.strip()
            if line.startswith("Q") or line.startswith("Question"):
                if current_question:
                    questions.append(current_question)
                current_question = {"type": "multiple_choice", "options": []}
                current_question["question"] = line
            elif line.startswith(("A.", "B.", "C.", "D.")):
                current_question["options"].append(line[2:].strip())
            elif "Answer:" in line or "Correct:" in line:
                current_question["correct_answer"] = line.split(":")[1].strip()
            elif "Explanation:" in line:
                current_question["explanation"] = line.split(":")[1].strip()

        if current_question:
            questions.append(current_question)

        return questions

    def conduct_quiz(self, questions: List[Dict]) -> Tuple[int, int, List[Dict]]:
        """Conduct interactive quiz"""
        print("\n" + "=" * 60)
        print("📚 STUDY QUIZ - Answer the following questions")
        print("=" * 60)

        score = 0
        results = []

        for i, q in enumerate(questions, 1):
            print(f"\nQuestion {i}/{len(questions)}")
            print(f"Type: {q.get('type', 'unknown').upper()}")
            print(f"\n{q['question']}")

            if q['type'] == 'multiple_choice' and 'options' in q:
                for j, option in enumerate(q['options']):
                    print(f"  {chr(65 + j)}. {option}")
                user_answer = input("\nYour answer (A/B/C/D): ").strip().upper()
            elif q['type'] == 'true_false':
                user_answer = input("\nYour answer (True/False): ").strip().lower()
            else:
                user_answer = input("\nYour answer: ").strip()

            correct = self._check_answer(user_answer, q['correct_answer'])

            if correct:
                score += 1
                print("✅ Correct!")
            else:
                print(f"❌ Incorrect. The correct answer is: {q['correct_answer']}")

            if 'explanation' in q:
                print(f"💡 Explanation: {q['explanation']}")

            results.append({
                "question": q['question'],
                "user_answer": user_answer,
                "correct_answer": q['correct_answer'],
                "correct": correct,
                "explanation": q.get('explanation', '')
            })

        return score, len(questions), results

    def _check_answer(self, user_answer: str, correct_answer: str) -> bool:
        """Check if answer is correct (fuzzy matching)"""
        user = user_answer.lower().strip()
        correct = correct_answer.lower().strip()

        # For multiple choice
        if len(user) == 1 and len(correct) == 1:
            return user == correct

        # For true/false
        if user in ['t', 'true'] and correct in ['t', 'true']:
            return True
        if user in ['f', 'false'] and correct in ['f', 'false']:
            return True

        # For short answers - simple containment check
        return user in correct or correct in user