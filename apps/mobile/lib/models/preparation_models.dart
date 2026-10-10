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
