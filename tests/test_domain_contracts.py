from ai_comp.domain.exams import Exam, ExamLevel, PaperCategory
from ai_comp.domain.sources import CrawlPolicy


def test_paper_category_belongs_to_exam():
    category = PaperCategory("CAT1", "Question Paper", "EXAM1")
    assert category.exam_id == "EXAM1"


def test_crawl_policy_requires_safe_defaults():
    policy = CrawlPolicy(allowed=True)
    assert policy.respect_robots is True
    assert policy.respect_terms is True
