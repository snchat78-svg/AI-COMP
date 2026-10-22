import 'dart:convert';

class ApiException implements Exception {
  const ApiException({
    required this.statusCode,
    required this.code,
    required this.message,
  });

  final int statusCode;
  final String code;
  final String message;

  factory ApiException.fromResponse(int statusCode, String body) {
    try {
      final decoded = jsonDecode(body);
      if (decoded is Map<String, dynamic>) {
        final error = decoded['error'];
        if (error is Map<String, dynamic>) {
          return ApiException(
            statusCode: statusCode,
            code: _string(error['code'], 'HTTP_$statusCode'),
            message: _string(error['message'], 'The request failed.'),
          );
        }
      }
    } on FormatException {
      // Keep the response details private; callers display this safe fallback.
    }
    return ApiException(
      statusCode: statusCode,
      code: 'HTTP_$statusCode',
      message: statusCode >= 500
          ? 'The service is unavailable. Please try again.'
          : 'The request could not be completed.',
    );
  }

  @override
  String toString() => '$code: $message';
}

class TopicPracticeGenerationResult {
  const TopicPracticeGenerationResult({
    required this.learnerId,
    required this.subjectId,
    required this.requestId,
    required this.requestedQuestionCount,
    required this.generatedAlternativeCount,
    required this.eligibleQuestionCount,
    required this.effectiveQuestionCount,
    required this.durationSeconds,
    required this.oneLinerSourceCount,
    required this.previousPaperSourceCount,
    required this.warnings,
    required this.message,
  });

  final String learnerId;
  final String subjectId;
  final String requestId;
  final int requestedQuestionCount;
  final int generatedAlternativeCount;
  final int eligibleQuestionCount;
  final int effectiveQuestionCount;
  final int durationSeconds;
  final int oneLinerSourceCount;
  final int previousPaperSourceCount;
  final List<String> warnings;
  final String message;

  factory TopicPracticeGenerationResult.fromJson(Map<String, dynamic> json) {
    return TopicPracticeGenerationResult(
      learnerId: _string(json['learner_id']),
      subjectId: _string(json['subject_id']),
      requestId: _string(json['request_id']),
      requestedQuestionCount: _integer(json['requested_question_count'], 1),
      generatedAlternativeCount: _integer(json['generated_alternative_count'], 0),
      eligibleQuestionCount: _integer(json['eligible_question_count'], 0),
      effectiveQuestionCount: _integer(json['effective_question_count'], 1),
      durationSeconds: _integer(json['duration_seconds'], 1800),
      oneLinerSourceCount: _integer(json['one_liner_source_count'], 0),
      previousPaperSourceCount: _integer(json['previous_paper_source_count'], 0),
      warnings: _stringList(json['warnings']),
      message: _string(json['message']),
    );
  }
}

class QuestionBankExamProfile {
  const QuestionBankExamProfile({
    required this.examId,
    required this.examName,
    required this.syllabusId,
    required this.syllabusTitle,
    required this.sourceUrl,
    required this.notificationNumber,
    required this.sourceStatus,
    required this.conceptCount,
    required this.mappedConceptCount,
    required this.excludedConceptCount,
    required this.unmappedConceptCount,
    required this.selectionReady,
  });

  final String examId;
  final String examName;
  final String syllabusId;
  final String syllabusTitle;
  final String sourceUrl;
  final String notificationNumber;
  final String sourceStatus;
  final int conceptCount;
  final int mappedConceptCount;
  final int excludedConceptCount;
  final int unmappedConceptCount;
  final bool selectionReady;

  factory QuestionBankExamProfile.fromJson(Map<String, dynamic> json) {
    return QuestionBankExamProfile(
      examId: _string(json['exam_id']),
      examName: _string(json['exam_name']),
      syllabusId: _string(json['syllabus_id']),
      syllabusTitle: _string(json['syllabus_title']),
      sourceUrl: _string(json['source_url']),
      notificationNumber: _string(json['notification_number']),
      sourceStatus: _string(json['source_status'], 'REVIEW_PENDING'),
      conceptCount: _integer(json['concept_count'], 0),
      mappedConceptCount: _integer(json['mapped_concept_count'], 0),
      excludedConceptCount: _integer(json['excluded_concept_count'], 0),
      unmappedConceptCount: _integer(json['unmapped_concept_count'], 0),
      selectionReady: json['selection_ready'] == true,
    );
  }
}

class QuestionBankSubject {
  const QuestionBankSubject({
    required this.subjectId,
    required this.subjectLabel,
    required this.conceptCount,
  });

  final String subjectId;
  final String subjectLabel;
  final int conceptCount;

  factory QuestionBankSubject.fromJson(Map<String, dynamic> json) {
    return QuestionBankSubject(
      subjectId: _string(json['subject_id']),
      subjectLabel: _string(json['subject_label']),
      conceptCount: _integer(json['concept_count'], 0),
    );
  }
}

class QuestionBankTopic {
  const QuestionBankTopic({
    required this.conceptId,
    required this.label,
    required this.subject,
    required this.topic,
    required this.subtopic,
    required this.verifiedOneLinerCount,
  });

  final String conceptId;
  final String label;
  final String subject;
  final String? topic;
  final String? subtopic;
  final int verifiedOneLinerCount;

  factory QuestionBankTopic.fromJson(Map<String, dynamic> json) {
    return QuestionBankTopic(
      conceptId: _string(json['concept_id']),
      label: _string(json['label']),
      subject: _string(json['subject']),
      topic: _optionalString(json['topic']),
      subtopic: _optionalString(json['subtopic']),
      verifiedOneLinerCount: _integer(json['verified_one_liner_count'], 0),
    );
  }
}

class TopicOneLinerItem {
  const TopicOneLinerItem({
    required this.oneLinerId,
    required this.conceptId,
    required this.questionText,
    required this.answerText,
    required this.languageCode,
    required this.sourceUrl,
    required this.sourceEvidence,
    required this.verificationStatus,
    required this.importanceScore,
  });

  final String oneLinerId;
  final String conceptId;
  final String questionText;
  final String answerText;
  final String languageCode;
  final String? sourceUrl;
  final String sourceEvidence;
  final String verificationStatus;
  final double importanceScore;

  factory TopicOneLinerItem.fromJson(Map<String, dynamic> json) {
    return TopicOneLinerItem(
      oneLinerId: _string(json['one_liner_id']),
      conceptId: _string(json['concept_id']),
      questionText: _string(json['question_text']),
      answerText: _string(json['answer_text']),
      languageCode: _string(json['language_code'], 'hi'),
      sourceUrl: _optionalString(json['source_url']),
      sourceEvidence: _string(json['source_evidence']),
      verificationStatus: _string(json['verification_status']),
      importanceScore: _double(json['importance_score']),
    );
  }
}

class QuestionBankPageInfo {
  const QuestionBankPageInfo({
    required this.limit,
    required this.offset,
    required this.returned,
    required this.totalCount,
    required this.hasMore,
  });

  final int limit;
  final int offset;
  final int returned;
  final int totalCount;
  final bool hasMore;

  factory QuestionBankPageInfo.fromJson(Map<String, dynamic> json) {
    return QuestionBankPageInfo(
      limit: _integer(json['limit'], 1),
      offset: _integer(json['offset'], 0),
      returned: _integer(json['returned'], 0),
      totalCount: _integer(json['total_count'], 0),
      hasMore: json['has_more'] == true,
    );
  }
}

class PreviousYearQuestion {
  const PreviousYearQuestion({
    required this.questionId,
    required this.stem,
    required this.options,
    required this.correctOptionKey,
    required this.explanation,
    required this.examName,
    required this.examId,
    required this.examYear,
    required this.examShift,
    required this.examQuestionNumber,
    required this.sourceUrl,
    required this.answerKeySourceUrl,
    required this.verifiedAppearanceCount,
    required this.conceptIds,
  });

  final String questionId;
  final String stem;
  final List<QuestionOption> options;
  final String correctOptionKey;
  final String explanation;
  final String examName;
  final String examId;
  final int examYear;
  final String? examShift;
  final int examQuestionNumber;
  final String sourceUrl;
  final String answerKeySourceUrl;
  final int verifiedAppearanceCount;
  final List<String> conceptIds;

  String get correctOptionText {
    for (final option in options) {
      if (option.key.toUpperCase() == correctOptionKey.toUpperCase()) {
        return option.text;
      }
    }
    return 'Verified answer key: $correctOptionKey';
  }

  factory PreviousYearQuestion.fromJson(Map<String, dynamic> json) {
    final rawOptions = json['options'];
    final options = rawOptions is List
        ? rawOptions
            .whereType<Map<String, dynamic>>()
            .map(QuestionOption.fromJson)
            .toList(growable: false)
        : const <QuestionOption>[];
    return PreviousYearQuestion(
      questionId: _string(json['question_id']),
      stem: _string(json['stem']),
      options: options,
      correctOptionKey: _string(json['correct_option_key']),
      explanation: _string(json['explanation']),
      examName: _string(json['exam_name']),
      examId: _string(json['exam_id']),
      examYear: _integer(json['exam_year'], 0),
      examShift: _optionalString(json['exam_shift']),
      examQuestionNumber: _integer(json['exam_question_number'], 0),
      sourceUrl: _string(json['source_url']),
      answerKeySourceUrl: _string(json['answer_key_source_url']),
      verifiedAppearanceCount: _integer(json['verified_appearance_count'], 0),
      conceptIds: _stringList(json['concept_ids']),
    );
  }
}

class PreviousYearQuestionPage {
  const PreviousYearQuestionPage({
    required this.items,
    required this.pagination,
  });

  final List<PreviousYearQuestion> items;
  final QuestionBankPageInfo pagination;

  factory PreviousYearQuestionPage.fromJson(Map<String, dynamic> json) {
    final raw = json['items'];
    final items = raw is List
        ? raw
            .whereType<Map<String, dynamic>>()
            .map(PreviousYearQuestion.fromJson)
            .toList(growable: false)
        : const <PreviousYearQuestion>[];
    final paginationJson = json['pagination'];
    return PreviousYearQuestionPage(
      items: items,
      pagination: QuestionBankPageInfo.fromJson(
        paginationJson is Map<String, dynamic>
            ? paginationJson
            : const <String, dynamic>{},
      ),
    );
  }
}

class QuestionBankReadiness {
  const QuestionBankReadiness({
    required this.questionPoolLimit,
    required this.eligibleQuestionCount,
    required this.verifiedHistoryQuestionCount,
    required this.acceptedGeneratedQuestionCount,
    required this.practiceTestAvailable,
    required this.sourceCountsScope,
    this.subjectId,
  });

  final int questionPoolLimit;
  final int eligibleQuestionCount;
  final int verifiedHistoryQuestionCount;
  final int acceptedGeneratedQuestionCount;
  final bool practiceTestAvailable;
  final String sourceCountsScope;
  final String? subjectId;

  factory QuestionBankReadiness.fromJson(Map<String, dynamic> json) {
    return QuestionBankReadiness(
      questionPoolLimit: _integer(json['question_pool_limit'], 1),
      eligibleQuestionCount: _integer(json['eligible_question_count'], 0),
      verifiedHistoryQuestionCount: _integer(
        json['verified_history_question_count'],
        0,
      ),
      acceptedGeneratedQuestionCount: _integer(
        json['accepted_generated_question_count'],
        0,
      ),
      practiceTestAvailable: json['practice_test_available'] == true,
      sourceCountsScope: _string(
        json['source_counts_scope'],
        'configured_eligible_pool',
      ),
      subjectId: _optionalString(json['subject_id']),
    );
  }
}

class AdaptiveRecommendation {
  const AdaptiveRecommendation({
    required this.requestId,
    required this.title,
    required this.mode,
    required this.questionCount,
    required this.durationSeconds,
    required this.focusConceptIds,
    required this.revisionQuestionIds,
    required this.requestedQuestionCount,
    required this.eligibleQuestionCount,
    required this.questionCountAdjusted,
  });

  final String requestId;
  final String title;
  final String mode;
  final int questionCount;
  final int durationSeconds;
  final List<String> focusConceptIds;
  final List<String> revisionQuestionIds;
  final int requestedQuestionCount;
  final int eligibleQuestionCount;
  final bool questionCountAdjusted;

  factory AdaptiveRecommendation.fromJson(Map<String, dynamic> json) {
    final recommendation = _map(json['recommendation']);
    return AdaptiveRecommendation(
      requestId: _string(json['request_id']),
      title: _string(json['title'], 'Adaptive practice'),
      mode: _string(json['mode'], 'ADAPTIVE'),
      questionCount: _integer(json['question_count'], 1),
      durationSeconds: _integer(json['duration_seconds'], 1800),
      focusConceptIds: _stringList(recommendation['focus_concept_ids']),
      revisionQuestionIds: _stringList(recommendation['revision_question_ids']),
      requestedQuestionCount: _integer(
        recommendation['requested_question_count'],
        _integer(json['question_count'], 1),
      ),
      eligibleQuestionCount: _integer(
        recommendation['eligible_question_count_in_configured_pool'],
        _integer(json['question_count'], 1),
      ),
      questionCountAdjusted:
          recommendation['question_count_adjusted'] == true,
    );
  }
}

class TestSessionSnapshot {
  const TestSessionSnapshot({
    required this.sessionId,
    required this.testId,
    required this.status,
    required this.questionCount,
    required this.questionIds,
    required this.currentQuestionNumber,
    required this.answeredQuestionCount,
    required this.reviewQuestionCount,
    required this.reviewQuestionIds,
    this.remainingSeconds,
    this.preparationRequestId,
    this.mode,
    this.focusConceptIds = const [],
    this.revisionQuestionIds = const [],
  });

  final String sessionId;
  final String testId;
  final String status;
  final int questionCount;
  final List<String> questionIds;
  final int currentQuestionNumber;
  final int answeredQuestionCount;
  final int reviewQuestionCount;
  final List<String> reviewQuestionIds;
  final double? remainingSeconds;
  final String? preparationRequestId;
  final String? mode;
  final List<String> focusConceptIds;
  final List<String> revisionQuestionIds;

  factory TestSessionSnapshot.fromJson(Map<String, dynamic> json) {
    return TestSessionSnapshot(
      sessionId: _string(json['session_id']),
      testId: _string(json['test_id']),
      status: _string(json['status'], 'CREATED'),
      questionCount: _integer(json['question_count'], 0),
      questionIds: _stringList(json['question_ids']),
      currentQuestionNumber: _integer(json['current_question_number'], 1),
      answeredQuestionCount: _integer(json['answered_question_count'], 0),
      reviewQuestionCount: _integer(json['review_question_count'], 0),
      reviewQuestionIds: _stringList(json['review_question_ids']),
      remainingSeconds: _optionalDouble(json['remaining_seconds']),
      preparationRequestId: _optionalString(json['preparation_request_id']),
      mode: _optionalString(json['mode']),
      focusConceptIds: _stringList(json['focus_concept_ids']),
      revisionQuestionIds: _stringList(json['revision_question_ids']),
    );
  }
}

class CurrentQuestion {
  const CurrentQuestion({
    required this.sessionId,
    required this.questionNumber,
    required this.questionCount,
    required this.questionId,
    required this.stem,
    required this.options,
    required this.reviewMarked,
    required this.remainingSeconds,
    this.selectedOptionKey,
    this.sourceKind = 'AI_GENERATED',
    this.sourceUrl,
    this.answerKeySourceUrl,
    this.examName,
    this.examId,
    this.examYear,
    this.examShift,
    this.examQuestionNumber,
    this.verifiedAppearanceCount = 0,
  });

  final String sessionId;
  final int questionNumber;
  final int questionCount;
  final String questionId;
  final String stem;
  final List<QuestionOption> options;
  final bool reviewMarked;
  final double remainingSeconds;
  final String? selectedOptionKey;
  final String sourceKind;
  final String? sourceUrl;
  final String? answerKeySourceUrl;
  final String? examName;
  final String? examId;
  final int? examYear;
  final String? examShift;
  final int? examQuestionNumber;
  final int verifiedAppearanceCount;

  factory CurrentQuestion.fromJson(Map<String, dynamic> json) {
    final rawOptions = json['options'];
    return CurrentQuestion(
      sessionId: _string(json['session_id']),
      questionNumber: _integer(json['question_number'], 1),
      questionCount: _integer(json['question_count'], 1),
      questionId: _string(json['question_id']),
      stem: _string(json['stem']),
      options: rawOptions is List
          ? rawOptions
              .whereType<Map<String, dynamic>>()
              .map(QuestionOption.fromJson)
              .toList(growable: false)
          : const [],
      reviewMarked: json['review_marked'] == true,
      remainingSeconds: _double(json['remaining_seconds']),
      selectedOptionKey: _optionalString(json['selected_option_key']),
      sourceKind: _string(json['source_kind'], 'AI_GENERATED'),
      sourceUrl: _optionalString(json['source_url']),
      answerKeySourceUrl: _optionalString(json['answer_key_source_url']),
      examName: _optionalString(json['exam_name']),
      examId: _optionalString(json['exam_id']),
      examYear: json['exam_year'] == null ? null : _integer(json['exam_year'], 0),
      examShift: _optionalString(json['exam_shift']),
      examQuestionNumber: json['exam_question_number'] == null
          ? null
          : _integer(json['exam_question_number'], 0),
      verifiedAppearanceCount: _integer(json['verified_appearance_count'], 0),
    );
  }
}

class QuestionOption {
  const QuestionOption({required this.key, required this.text});

  final String key;
  final String text;

  factory QuestionOption.fromJson(Map<String, dynamic> json) => QuestionOption(
        key: _string(json['key']),
        text: _string(json['text']),
      );
}

class TestResult {
  const TestResult({
    required this.testId,
    required this.sessionId,
    required this.status,
    required this.totalQuestions,
    required this.attemptedQuestions,
    required this.correctAnswers,
    required this.incorrectAnswers,
    required this.unattemptedQuestions,
    required this.rawScore,
    required this.maxScore,
    required this.percentage,
    required this.accuracy,
    required this.timedOut,
  });

  final String testId;
  final String sessionId;
  final String status;
  final int totalQuestions;
  final int attemptedQuestions;
  final int correctAnswers;
  final int incorrectAnswers;
  final int unattemptedQuestions;
  final double rawScore;
  final double maxScore;
  final double percentage;
  final double accuracy;
  final bool timedOut;

  factory TestResult.fromJson(Map<String, dynamic> json) => TestResult(
        testId: _string(json['test_id']),
        sessionId: _string(json['session_id']),
        status: _string(json['status']),
        totalQuestions: _integer(json['total_questions'], 0),
        attemptedQuestions: _integer(json['attempted_questions'], 0),
        correctAnswers: _integer(json['correct_answers'], 0),
        incorrectAnswers: _integer(json['incorrect_answers'], 0),
        unattemptedQuestions: _integer(json['unattempted_questions'], 0),
        rawScore: _double(json['raw_score']),
        maxScore: _double(json['max_score']),
        percentage: _double(json['percentage']),
        accuracy: _double(json['accuracy']),
        timedOut: json['timed_out'] == true,
      );
}

class SubmittedTest {
  const SubmittedTest({required this.result, required this.session});

  final TestResult result;
  final TestSessionSnapshot session;

  factory SubmittedTest.fromJson(Map<String, dynamic> json) => SubmittedTest(
        result: TestResult.fromJson(_map(json['result'])),
        session: TestSessionSnapshot.fromJson(_map(json['session'])),
      );
}

class AnswerReview {
  const AnswerReview({
    required this.title,
    required this.status,
    required this.result,
    required this.summary,
    required this.questions,
  });

  final String title;
  final String status;
  final TestResult result;
  final Map<String, dynamic> summary;
  final List<ReviewQuestion> questions;

  factory AnswerReview.fromJson(Map<String, dynamic> json) {
    final rawQuestions = json['questions'];
    return AnswerReview(
      title: _string(json['title'], 'Test review'),
      status: _string(json['status']),
      result: TestResult.fromJson(_map(json['result'])),
      summary: _map(json['summary']),
      questions: rawQuestions is List
          ? rawQuestions
              .whereType<Map<String, dynamic>>()
              .map(ReviewQuestion.fromJson)
              .toList(growable: false)
          : const [],
    );
  }
}

class ReviewQuestion {
  const ReviewQuestion({
    required this.number,
    required this.stem,
    required this.outcome,
    required this.selectedOptionText,
    required this.correctOptionText,
    required this.explanation,
  });

  final int number;
  final String stem;
  final String outcome;
  final String? selectedOptionText;
  final String? correctOptionText;
  final String explanation;

  factory ReviewQuestion.fromJson(Map<String, dynamic> json) => ReviewQuestion(
        number: _integer(json['question_number'], 0),
        stem: _string(json['stem']),
        outcome: _string(json['outcome']),
        selectedOptionText: _optionalString(json['selected_option_text']),
        correctOptionText: _optionalString(json['correct_option_text']),
        explanation: _string(json['explanation']),
      );
}

class ResultsSummary {
  const ResultsSummary({
    required this.completedTestCount,
    required this.averagePercentage,
    required this.bestPercentage,
    required this.correctAnswers,
    required this.incorrectAnswers,
  });

  final int completedTestCount;
  final double averagePercentage;
  final double bestPercentage;
  final int correctAnswers;
  final int incorrectAnswers;

  factory ResultsSummary.fromJson(Map<String, dynamic> json) => ResultsSummary(
        completedTestCount: _integer(json['completed_test_count'], 0),
        averagePercentage: _double(json['average_percentage']),
        bestPercentage: _double(json['best_percentage']),
        correctAnswers: _integer(json['correct_answers'], 0),
        incorrectAnswers: _integer(json['incorrect_answers'], 0),
      );
}

class LearnerAnalytics {
  const LearnerAnalytics({
    required this.weakTopics,
    required this.completedTestCount,
    required this.latestPercentage,
    required this.averagePercentage,
  });

  final List<WeakTopicSummary> weakTopics;
  final int completedTestCount;
  final double? latestPercentage;
  final double? averagePercentage;

  factory LearnerAnalytics.fromJson(Map<String, dynamic> json) {
    final summary = _map(json['summary']);
    final rawWeakTopics = json['weak_topics'];
    return LearnerAnalytics(
      weakTopics: rawWeakTopics is List
          ? rawWeakTopics
              .whereType<Map<String, dynamic>>()
              .map(WeakTopicSummary.fromJson)
              .toList(growable: false)
          : const [],
      completedTestCount: _integer(summary['completed_test_count'], 0),
      latestPercentage: _optionalDouble(summary['latest_percentage']),
      averagePercentage: _optionalDouble(summary['average_percentage']),
    );
  }
}

class WeakTopicSummary {
  const WeakTopicSummary({
    required this.conceptId,
    required this.performance,
    required this.trend,
    required this.accuracyPercentage,
    required this.priorityScore,
  });

  final String conceptId;
  final String performance;
  final String trend;
  final double accuracyPercentage;
  final double priorityScore;

  factory WeakTopicSummary.fromJson(Map<String, dynamic> json) =>
      WeakTopicSummary(
        conceptId: _string(json['concept_id']),
        performance: _string(json['performance'], 'WEAK'),
        trend: _string(json['trend'], 'UNKNOWN'),
        accuracyPercentage: _double(json['accuracy_percentage']),
        priorityScore: _double(json['priority_score']),
      );
}

class TestHistoryItem {
  const TestHistoryItem({
    required this.sessionId,
    required this.title,
    required this.status,
    required this.createdAt,
    this.percentage,
  });

  final String sessionId;
  final String title;
  final String status;
  final String createdAt;
  final double? percentage;

  factory TestHistoryItem.fromJson(Map<String, dynamic> json) {
    final result = json['result'];
    final resultMap = result is Map<String, dynamic> ? result : const <String, dynamic>{};
    return TestHistoryItem(
      sessionId: _string(json['session_id']),
      title: _string(json['title'], 'Practice test'),
      status: _string(json['status']),
      createdAt: _string(json['created_at']),
      percentage: _optionalDouble(resultMap['percentage']),
    );
  }
}

Map<String, dynamic> _map(Object? value) =>
    value is Map<String, dynamic> ? value : <String, dynamic>{};

String _string(Object? value, [String fallback = '']) =>
    value is String ? value : fallback;

String? _optionalString(Object? value) =>
    value is String && value.isNotEmpty ? value : null;

int _integer(Object? value, int fallback) =>
    value is num ? value.toInt() : fallback;

double _double(Object? value) =>
    value is num ? value.toDouble() : 0.0;

double? _optionalDouble(Object? value) =>
    value is num ? value.toDouble() : null;

List<String> _stringList(Object? value) =>
    value is List ? value.whereType<String>().toList(growable: false) : const [];
