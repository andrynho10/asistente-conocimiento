"""
Tests for Quiz Submission Endpoint (Story 4.3)

Validates the POST /api/ia/quiz/{quiz_id}/submit endpoint
with focus on AC9-AC20 requirements.
"""

import pytest
from sqlmodel import Session

from app.models.quiz import Quiz, QuizQuestion, QuizAttempt


class TestQuizSubmissionBasic:
    """Basic quiz submission tests (AC9-AC11)"""

    def test_submit_quiz_success(self, test_client, user_token, normal_user, test_db_session):
        """Test successful quiz submission with mixed correct/incorrect answers"""
        # Create test quiz for the user
        quiz = Quiz(
            document_id=1,
            user_id=normal_user.id,
            title="Test Quiz",
            difficulty="basic",
            num_questions=3
        )
        test_db_session.add(quiz)
        test_db_session.flush()
        quiz_id = quiz.id

        # Create 3 test questions
        for i in range(3):
            question = QuizQuestion(
                quiz_id=quiz_id,
                question=f"Question {i+1}?",
                options_json=["Option A", "Option B", "Option C", "Option D"],
                correct_answer="Option A",
                explanation=f"Explanation {i+1}",
                difficulty="basic"
            )
            test_db_session.add(question)
        test_db_session.commit()

        # Submit answers: 2 correct (A, A), 1 incorrect (B)
        answers = {"1": "A", "2": "A", "3": "B"}

        response = test_client.post(
            f"/api/ia/quiz/{quiz_id}/submit",
            json={"answers": answers},
            headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code == 200, f"Response: {response.json()}"
        data = response.json()

        # Verify AC10, AC11
        assert data["quiz_id"] == quiz_id
        assert data["score"] == 2
        assert data["total_questions"] == 3
        assert abs(data["percentage"] - 66.67) < 0.5
        assert data["passed"] is False
        assert "results" in data
        assert len(data["results"]) == 3

    def test_submit_quiz_all_correct(self, test_client, user_token, normal_user, test_db_session):
        """Test submission where all answers are correct (passed >= 70%)"""
        quiz = Quiz(
            document_id=1,
            user_id=normal_user.id,
            title="Easy Quiz",
            difficulty="basic",
            num_questions=2
        )
        test_db_session.add(quiz)
        test_db_session.flush()
        quiz_id = quiz.id

        for i in range(2):
            question = QuizQuestion(
                quiz_id=quiz_id,
                question=f"Q{i+1}",
                options_json=["Opt A", "Opt B", "Opt C", "Opt D"],
                correct_answer="Opt C",
                explanation="Expl",
                difficulty="basic"
            )
            test_db_session.add(question)
        test_db_session.commit()

        response = test_client.post(
            f"/api/ia/quiz/{quiz_id}/submit",
            json={"answers": {"1": "C", "2": "C"}},
            headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["score"] == 2
        assert data["percentage"] == 100.0
        assert data["passed"] is True


class TestQuizSubmissionResultsStructure:
    """Test results array contains required fields (AC11, AC13)"""

    def test_results_structure(self, test_client, user_token, normal_user, test_db_session):
        """Verify each result has required fields from AC11"""
        quiz = Quiz(
            document_id=1,
            user_id=normal_user.id,
            title="Struct Test",
            difficulty="basic",
            num_questions=1
        )
        test_db_session.add(quiz)
        test_db_session.flush()
        quiz_id = quiz.id

        question = QuizQuestion(
            quiz_id=quiz_id,
            question="What?",
            options_json=["Yes", "No", "Maybe", "Dont Know"],
            correct_answer="Yes",
            explanation="Because",
            difficulty="basic"
        )
        test_db_session.add(question)
        test_db_session.commit()

        response = test_client.post(
            f"/api/ia/quiz/{quiz_id}/submit",
            json={"answers": {"1": "A"}},
            headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 1

        result = data["results"][0]
        # AC11 required fields
        assert "question_number" in result
        assert "user_answer" in result
        assert "correct_answer" in result
        assert "is_correct" in result
        assert "explanation" in result
        # Enhancement: option text
        assert "user_answer_text" in result
        assert "correct_answer_text" in result


class TestQuizSubmissionValidation:
    """Test validation (AC17)"""

    def test_missing_answer_fails(self, test_client, user_token, normal_user, test_db_session):
        """Missing answer in submission should fail (AC17)"""
        quiz = Quiz(
            document_id=1,
            user_id=normal_user.id,
            title="Val Test",
            difficulty="basic",
            num_questions=2
        )
        test_db_session.add(quiz)
        test_db_session.flush()
        quiz_id = quiz.id

        for i in range(2):
            q = QuizQuestion(
                quiz_id=quiz_id,
                question=f"Q{i}",
                options_json=["A", "B", "C", "D"],
                correct_answer="A",
                explanation="Exp",
                difficulty="basic"
            )
            test_db_session.add(q)
        test_db_session.commit()

        # Only provide answer for Q1, missing Q2
        response = test_client.post(
            f"/api/ia/quiz/{quiz_id}/submit",
            json={"answers": {"1": "A"}},
            headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code == 400

    def test_invalid_answer_letter_fails(self, test_client, user_token, normal_user, test_db_session):
        """Invalid answer letter (not A-D) should fail"""
        quiz = Quiz(
            document_id=1,
            user_id=normal_user.id,
            title="Invalid Test",
            difficulty="basic",
            num_questions=1
        )
        test_db_session.add(quiz)
        test_db_session.flush()
        quiz_id = quiz.id

        q = QuizQuestion(
            quiz_id=quiz_id,
            question="Q",
            options_json=["A", "B", "C", "D"],
            correct_answer="A",
            explanation="E",
            difficulty="basic"
        )
        test_db_session.add(q)
        test_db_session.commit()

        response = test_client.post(
            f"/api/ia/quiz/{quiz_id}/submit",
            json={"answers": {"1": "Z"}},
            headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code == 400


class TestQuizSubmissionPersistence:
    """Test database persistence (AC15, AC20)"""

    def test_attempt_persisted_to_db(self, test_client, user_token, normal_user, test_db_session):
        """Quiz attempt must be saved to quiz_attempts table (AC15, AC20)"""
        quiz = Quiz(
            document_id=1,
            user_id=normal_user.id,
            title="Persist Test",
            difficulty="basic",
            num_questions=1
        )
        test_db_session.add(quiz)
        test_db_session.flush()
        quiz_id = quiz.id

        q = QuizQuestion(
            quiz_id=quiz_id,
            question="Q",
            options_json=["Opt A", "Opt B", "Opt C", "Opt D"],
            correct_answer="Opt A",
            explanation="Because",
            difficulty="basic"
        )
        test_db_session.add(q)
        test_db_session.commit()

        answers = {"1": "A"}
        response = test_client.post(
            f"/api/ia/quiz/{quiz_id}/submit",
            json={"answers": answers},
            headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code == 200

        # Verify in database
        from sqlmodel import select
        attempt = test_db_session.exec(
            select(QuizAttempt).where(
                QuizAttempt.quiz_id == quiz_id,
                QuizAttempt.user_id == normal_user.id
            )
        ).first()

        assert attempt is not None
        assert attempt.quiz_id == quiz_id
        assert attempt.user_id == normal_user.id
        assert attempt.score == 1
        assert attempt.total_questions == 1
        assert attempt.percentage == 100.0
        assert attempt.answers_json == answers
        assert attempt.timestamp is not None


class TestQuizSubmissionAuth:
    """Test authentication (AC1)"""

    def test_requires_authentication(self, test_client):
        """Submission endpoint requires JWT authentication"""
        response = test_client.post(
            "/api/ia/quiz/1/submit",
            json={"answers": {"1": "A"}}
        )
        assert response.status_code == 401

    def test_quiz_not_found(self, test_client, user_token):
        """Non-existent quiz should return 404"""
        response = test_client.post(
            "/api/ia/quiz/99999/submit",
            json={"answers": {"1": "A"}},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 404
