from ai_comp.database.postgres_question import PostgresQuestionRepository
from ai_comp.domain.questions import QuestionCandidate, QuestionKind, QuestionOption


class Result:
    def __init__(self, row=None, rows=()):
        self.row = row
        self.rows = list(rows)

    def fetchone(self):
        return self.row

    def fetchall(self):
        return self.rows


class Connection:
    def __init__(self):
        self.calls = []
        self.results = []

    def transaction(self):
        class Tx:
            def __enter__(self):
                return self
            def __exit__(self, exc_type, exc, tb):
                return False
        return Tx()

    def execute(self, sql, params=()):
        self.calls.append((sql, params))
        return self.results.pop(0) if self.results else Result()


def question():
    return QuestionCandidate(
        question_id="q1",
        document_id="doc1",
        document_sha256="a" * 64,
        question_number=1,
        stem="राजस्थान का उदाहरण?",
        options=(QuestionOption("A", "एक"), QuestionOption("B", "दो")),
        kind=QuestionKind.MCQ,
        raw_text="1. राजस्थान का उदाहरण?",
        start_line=1,
        end_line=3,
    )


def test_question_repository_writes_question_and_ordered_options():
    conn = Connection()
    repo = PostgresQuestionRepository(conn)

    repo.save(question())

    assert "INSERT INTO questions" in conn.calls[0][0]
    assert "question_options" in conn.calls[1][0]
    assert conn.calls[2][1] == ("q1", "A", "एक", 1)
    assert conn.calls[3][1] == ("q1", "B", "दो", 2)


def test_question_repository_reads_domain_question():
    conn = Connection()
    conn.results = [
        Result(row=("q1", "doc1", "a" * 64, 1, "राजस्थान?", "MCQ", "raw", 1, 3)),
        Result(rows=[("A", "एक"), ("B", "दो")]),
    ]
    loaded = PostgresQuestionRepository(conn).get("q1")

    assert loaded is not None
    assert loaded.question_id == "q1"
    assert loaded.options == (QuestionOption("A", "एक"), QuestionOption("B", "दो"))
