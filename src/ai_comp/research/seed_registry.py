from ai_comp.domain.exams import ConductingBody, Exam, ExamLevel, PaperCategory
from ai_comp.domain.sources import CrawlPolicy, SourcePriority, SourceRecord, SourceType
from ai_comp.research.source_registry import SourceRegistry


def build_initial_registry() -> SourceRegistry:
    registry = SourceRegistry()

    rssb = ConductingBody(
        body_id="RSSB",
        name="Rajasthan Staff Selection Board",
        level=ExamLevel.STATE,
        state="Rajasthan",
    )
    rpsc = ConductingBody(
        body_id="RPSC",
        name="Rajasthan Public Service Commission",
        level=ExamLevel.STATE,
        state="Rajasthan",
    )
    registry.add_body(rssb)
    registry.add_body(rpsc)

    registry.add_exam(Exam(
        exam_id="RSSB_CET",
        name="Rajasthan CET",
        conducting_body_id="RSSB",
        level=ExamLevel.STATE,
        state="Rajasthan",
        categories=("COMMON_ENTRANCE",),
    ))
    registry.add_exam(Exam(
        exam_id="RPSC_GENERIC",
        name="RPSC Examinations",
        conducting_body_id="RPSC",
        level=ExamLevel.STATE,
        state="Rajasthan",
        categories=("RECRUITMENT",),
    ))

    registry.add_category(PaperCategory(
        category_id="RSSB_CET_QUESTION_PAPER",
        name="Question Paper",
        exam_id="RSSB_CET",
    ))
    registry.add_category(PaperCategory(
        category_id="RSSB_CET_ANSWER_KEY",
        name="Answer Key",
        exam_id="RSSB_CET",
    ))

    # Expand the Rajasthan exam registry additively. These IDs are the
    # canonical matching targets for explicit exam names in official archive
    # labels; a generic board archive alone is never enough to infer an exam.
    additional_exams = (
        ("RSSB_PATWAR", "Rajasthan Patwar Examination", "RSSB"),
        ("RSSB_LDC", "Rajasthan Lower Division Clerk Examination", "RSSB"),
        ("RSSB_VDO", "Rajasthan Village Development Officer Examination", "RSSB"),
        ("RSSB_JUNIOR_ASSISTANT", "Rajasthan Junior Assistant Examination", "RSSB"),
        ("RSSB_LAB_ASSISTANT", "Rajasthan Lab Assistant Examination", "RSSB"),
        ("RPSC_RAS", "Rajasthan State and Subordinate Services Combined Competitive Examination (RAS)", "RPSC"),
        ("RPSC_SI", "RPSC Sub Inspector Combined Competitive Examination", "RPSC"),
        ("RPSC_SCHOOL_LECTURER", "RPSC School Lecturer Examination", "RPSC"),
        ("RPSC_SENIOR_TEACHER", "RPSC Senior Teacher Examination", "RPSC"),
        ("RPSC_ASSISTANT_PROFESSOR", "RPSC Assistant Professor (College Education) Examination", "RPSC"),
    )
    for exam_id, exam_name, body_id in additional_exams:
        registry.add_exam(Exam(
            exam_id=exam_id,
            name=exam_name,
            conducting_body_id=body_id,
            level=ExamLevel.STATE,
            state="Rajasthan",
            categories=("QUESTION_PAPER", "ANSWER_KEY"),
        ))
        registry.add_category(PaperCategory(
            category_id=f"{exam_id}_QUESTION_PAPER",
            name="Question Paper",
            exam_id=exam_id,
        ))
        registry.add_category(PaperCategory(
            category_id=f"{exam_id}_ANSWER_KEY",
            name="Answer Key",
            exam_id=exam_id,
        ))

    registry.add_source(SourceRecord(
        source_id="RSSB_OFFICIAL",
        name="RSSB Official",
        base_url="https://rssb.rajasthan.gov.in/",
        source_type=SourceType.OFFICIAL_WEBSITE,
        priority=SourcePriority.OFFICIAL,
        conducting_body_id="RSSB",
        notes="Discovery must remain subject to robots.txt, terms and access restrictions.",
    ))
    registry.add_source(SourceRecord(
        source_id="RPSC_OFFICIAL",
        name="RPSC Official",
        base_url="https://rpsc.rajasthan.gov.in/",
        source_type=SourceType.OFFICIAL_WEBSITE,
        priority=SourcePriority.OFFICIAL,
        conducting_body_id="RPSC",
        notes="Discovery must remain subject to robots.txt, terms and access restrictions.",
    ))

    return registry


DEFAULT_CRAWL_POLICY = CrawlPolicy(
    allowed=True,
    respect_robots=True,
    respect_terms=True,
    rate_limit_seconds=1.0,
    max_depth=2,
)
