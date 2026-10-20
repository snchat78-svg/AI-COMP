from ai_comp.database.postgres_preparation_session import (
    PostgresPreparationTestSessionRepository,
)
from ai_comp.domain.material_generation import (
    AnswerVerificationStatus,
    GeneratedMCQ,
    GeneratedOption,
    GeneratedQuestionStatus,
    QuestionSourceKind,
)


def verified_history_question() -> GeneratedMCQ:
    return GeneratedMCQ(
        generated_question_id="verified-history:question-1",
        generation_id="verified-exam-history",
        material_id="verified-paper:question-1",
        stem="राजस्थान के क्षेत्रफल से संबंधित सही कथन कौन सा है?",
        options=(
            GeneratedOption("A", "विकल्प एक"),
            GeneratedOption("B", "सही विकल्प"),
            GeneratedOption("C", "विकल्प तीन"),
            GeneratedOption("D", "विकल्प चार"),
        ),
        correct_option_key="B",
        explanation="Matched to the official answer key.",
        fact_ids=(),
        concept_ids=("rajasthan-area",),
        difficulty="MEDIUM",
        importance_score=0.65,
        answer_verification=AnswerVerificationStatus.VERIFIED,
        answer_verification_evidence=(
            "Official paper: https://official.example/paper.pdf",
            "Official key: https://official.example/key.pdf",
        ),
        status=GeneratedQuestionStatus.ACCEPTED,
        quality_score=1.0,
        source_kind=QuestionSourceKind.VERIFIED_EXAM_HISTORY,
        source_url="https://official.example/paper.pdf",
        answer_key_source_url="https://official.example/key.pdf",
        exam_name="Rajasthan recruitment exam",
        exam_id="RAJ_EXAM",
        exam_year=2024,
        exam_shift="MORNING",
        exam_question_number=7,
        verified_appearance_count=3,
    )


def test_saved_test_snapshot_round_trips_official_history_provenance():
    question = verified_history_question()

    payload = PostgresPreparationTestSessionRepository._question_payload(question)
    restored = PostgresPreparationTestSessionRepository._question_from_payload(payload)

    assert restored == question
    assert payload["source_kind"] == "VERIFIED_EXAM_HISTORY"
    assert payload["source_url"] == "https://official.example/paper.pdf"
    assert payload["answer_key_source_url"] == "https://official.example/key.pdf"
    assert payload["exam_name"] == "Rajasthan recruitment exam"
    assert payload["exam_year"] == 2024
    assert payload["exam_shift"] == "MORNING"
    assert payload["exam_question_number"] == 7
    assert payload["verified_appearance_count"] == 3


def test_old_test_snapshots_without_provenance_remain_ai_generated():
    payload = PostgresPreparationTestSessionRepository._question_payload(
        GeneratedMCQ(
            generated_question_id="generated-question-1",
            generation_id="generation-1",
            material_id="material-1",
            stem="Choose the correct answer.",
            options=(
                GeneratedOption("A", "One"),
                GeneratedOption("B", "Two"),
                GeneratedOption("C", "Three"),
                GeneratedOption("D", "Four"),
            ),
            correct_option_key="A",
            explanation="Verified fixture explanation.",
            fact_ids=("fact-1",),
            concept_ids=("concept-1",),
            difficulty="MEDIUM",
            importance_score=0.9,
            answer_verification=AnswerVerificationStatus.VERIFIED,
            answer_verification_evidence=("Fixture verification evidence",),
            status=GeneratedQuestionStatus.ACCEPTED,
            quality_score=0.95,
        )
    )
    legacy_payload = {
        key: value
        for key, value in payload.items()
        if key not in {
            "source_kind",
            "source_url",
            "answer_key_source_url",
            "exam_name",
            "exam_id",
            "exam_year",
            "exam_shift",
            "exam_question_number",
            "verified_appearance_count",
        }
    }

    restored = PostgresPreparationTestSessionRepository._question_from_payload(
        legacy_payload
    )

    assert restored.source_kind is QuestionSourceKind.AI_GENERATED
    assert restored.source_url is None
    assert restored.verified_appearance_count == 0
