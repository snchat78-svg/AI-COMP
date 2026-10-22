import 'dart:convert';

import 'package:http/http.dart' as http;

import '../models/preparation_models.dart';

class AiCompApiClient {
  AiCompApiClient({
    required String baseUrl,
    required this.learnerId,
    String accessToken = '',
    Future<String?> Function()? accessTokenProvider,
    http.Client? httpClient,
  })  : _baseUri = _normalizeBaseUri(baseUrl),
        _accessToken = accessToken.trim(),
        _accessTokenProvider = accessTokenProvider,
        _httpClient = httpClient ?? http.Client(),
        _ownsHttpClient = httpClient == null {
    if (learnerId.trim().isEmpty || learnerId != learnerId.trim()) {
      throw ArgumentError.value(learnerId, 'learnerId', 'Must be non-empty and trimmed.');
    }
  }

  final Uri _baseUri;
  final String learnerId;
  final String _accessToken;
  final Future<String?> Function()? _accessTokenProvider;
  final http.Client _httpClient;
  final bool _ownsHttpClient;

  static Uri _normalizeBaseUri(String value) {
    final parsed = Uri.tryParse(value.trim());
    if (parsed == null ||
        !parsed.hasAuthority ||
        (parsed.scheme != 'http' && parsed.scheme != 'https') ||
        parsed.userInfo.isNotEmpty ||
        parsed.query.isNotEmpty ||
        parsed.fragment.isNotEmpty) {
      throw ArgumentError.value(
        value,
        'baseUrl',
        'Use an absolute HTTP(S) API URL without credentials, query, or fragment.',
      );
    }
    final path = parsed.path == '/' ? '' : parsed.path.replaceFirst(RegExp(r'/+$'), '');
    return parsed.replace(path: path);
  }

  String get _learnerPath => '/api/v1/learners/${Uri.encodeComponent(learnerId)}';

  Uri _uri(String path, [Map<String, String>? query]) {
    final basePath = _baseUri.path;
    return _baseUri.replace(
      path: '${basePath == '/' ? '' : basePath}$path',
      queryParameters: query,
    );
  }

  Future<Map<String, String>> get _headers async {
    final headers = <String, String>{
      'Accept': 'application/json',
    };
    final suppliedToken = _accessTokenProvider == null
        ? _accessToken
        : (await _accessTokenProvider()) ?? '';
    final token = suppliedToken.trim();
    if (token.isNotEmpty) {
      headers['Authorization'] = 'Bearer $token';
    }
    return headers;
  }

  Future<Map<String, dynamic>> _send(
    String method,
    String path, {
    Map<String, String>? query,
    Map<String, Object?>? body,
  }) async {
    final uri = _uri(path, query);
    final headers = await _headers;
    if (body != null) {
      headers['Content-Type'] = 'application/json; charset=utf-8';
    }

    try {
      late final http.Response response;
      switch (method) {
        case 'GET':
          response = await _httpClient.get(uri, headers: headers);
          break;
        case 'POST':
          response = await _httpClient.post(
            uri,
            headers: headers,
            body: body == null ? null : jsonEncode(body),
          );
          break;
        default:
          throw StateError('Unsupported HTTP method: $method');
      }

      if (response.statusCode < 200 || response.statusCode >= 300) {
        throw ApiException.fromResponse(response.statusCode, response.body);
      }
      if (response.body.isEmpty) {
        return <String, dynamic>{};
      }
      final decoded = jsonDecode(utf8.decode(response.bodyBytes));
      if (decoded is! Map<String, dynamic>) {
        throw const ApiException(
          statusCode: 502,
          code: 'INVALID_API_RESPONSE',
          message: 'The API returned an unexpected response.',
        );
      }
      return decoded;
    } on ApiException {
      rethrow;
    } on FormatException {
      throw const ApiException(
        statusCode: 502,
        code: 'INVALID_API_RESPONSE',
        message: 'The API returned invalid JSON.',
      );
    } on http.ClientException {
      throw const ApiException(
        statusCode: 0,
        code: 'NETWORK_UNAVAILABLE',
        message: 'Could not reach the API. Check the URL and network connection.',
      );
    }
  }

  Future<AdaptiveRecommendation> recommendAdaptivePractice({
    int questionCount = 20,
    int durationSeconds = 1800,
    int maxConcepts = 8,
  }) async {
    final json = await _send(
      'POST',
      '$_learnerPath/preparation-recommendations',
      body: {
        'question_count': questionCount,
        'duration_seconds': durationSeconds,
        'max_concepts': maxConcepts,
      },
    );
    return AdaptiveRecommendation.fromJson(json);
  }

  Future<void> createMixedPracticeRequest({
    required int questionCount,
    required int durationSeconds,
    String? subjectId,
  }) async {
    final body = <String, Object?>{
      'title': subjectId == null ? 'Mixed practice test' : '$subjectId practice test',
      'question_count': questionCount,
      'duration_seconds': durationSeconds,
      'mode': 'MIXED',
      'concept_ids': <String>[],
    };
    if (subjectId != null && subjectId.trim().isNotEmpty) {
      body['subject_id'] = subjectId.trim();
    }
    await _send(
      'POST',
      '$_learnerPath/preparation-requests',
      body: body,
    );
  }

  Future<TestSessionSnapshot> createSession() async {
    final json = await _send('POST', '$_learnerPath/preparation-sessions');
    return TestSessionSnapshot.fromJson(json);
  }

  Future<TestSessionSnapshot> getSession(String sessionId) async {
    final json = await _send(
      'GET',
      '$_learnerPath/preparation-sessions/${Uri.encodeComponent(sessionId)}',
    );
    return TestSessionSnapshot.fromJson(json);
  }

  Future<TestSessionSnapshot> startSession(String sessionId) async {
    final json = await _send(
      'POST',
      '$_learnerPath/preparation-sessions/${Uri.encodeComponent(sessionId)}/start',
    );
    return TestSessionSnapshot.fromJson(json);
  }

  Future<CurrentQuestion> getCurrentQuestion(String sessionId) async {
    final json = await _send(
      'GET',
      '$_learnerPath/preparation-sessions/${Uri.encodeComponent(sessionId)}/current-question',
    );
    return CurrentQuestion.fromJson(json);
  }

  Future<TestSessionSnapshot> submitAnswer(
    String sessionId,
    String optionKey,
  ) async {
    final json = await _send(
      'POST',
      '$_learnerPath/preparation-sessions/${Uri.encodeComponent(sessionId)}/answer',
      body: {'option_key': optionKey},
    );
    return TestSessionSnapshot.fromJson(json);
  }

  Future<TestSessionSnapshot> navigateQuestion(
    String sessionId, {
    required String direction,
  }) async {
    if (!const {'next', 'previous', 'review'}.contains(direction)) {
      throw ArgumentError.value(direction, 'direction', 'Unsupported navigation.');
    }
    final json = await _send(
      'POST',
      '$_learnerPath/preparation-sessions/${Uri.encodeComponent(sessionId)}/$direction',
    );
    return TestSessionSnapshot.fromJson(json);
  }

  Future<SubmittedTest> submitSession(String sessionId) async {
    final json = await _send(
      'POST',
      '$_learnerPath/preparation-sessions/${Uri.encodeComponent(sessionId)}/submit',
    );
    return SubmittedTest.fromJson(json);
  }

  Future<AnswerReview> getAnswerReview(String sessionId) async {
    final json = await _send(
      'GET',
      '$_learnerPath/preparation-sessions/${Uri.encodeComponent(sessionId)}/answer-review',
    );
    return AnswerReview.fromJson(json);
  }

  Future<QuestionBankReadiness> getQuestionBankReadiness({String? subjectId}) async {
    final query = subjectId == null ? null : <String, String>{'subject_id': subjectId};
    final json = await _send('GET', '$_learnerPath/question-bank/readiness', query: query);
    return QuestionBankReadiness.fromJson(json);
  }

  Future<List<QuestionBankExamProfile>> getQuestionBankExamProfiles({
    int limit = 100,
  }) async {
    final json = await _send(
      'GET',
      '$_learnerPath/question-bank/exam-profiles',
      query: {'limit': '$limit'},
    );
    final raw = json['items'];
    if (raw is! List) return const [];
    return raw
        .whereType<Map<String, dynamic>>()
        .map(QuestionBankExamProfile.fromJson)
        .toList(growable: false);
  }

  Future<List<QuestionBankSubject>> getQuestionBankSubjects({String? examId}) async {
    final query = <String, String>{};
    if (examId != null && examId.trim().isNotEmpty) {
      query['exam_id'] = examId.trim();
    }
    final json = await _send(
      'GET',
      '$_learnerPath/question-bank/subjects',
      query: query.isEmpty ? null : query,
    );
    final raw = json['items'];
    if (raw is! List) return const [];
    return raw
        .whereType<Map<String, dynamic>>()
        .map(QuestionBankSubject.fromJson)
        .toList(growable: false);
  }

  Future<List<QuestionBankTopic>> getQuestionBankTopics(
    String subjectId, {
    String? examId,
    int limit = 100,
    int offset = 0,
  }) async {
    final query = <String, String>{
      'subject': subjectId,
      'limit': '$limit',
      'offset': '$offset',
    };
    if (examId != null && examId.trim().isNotEmpty) {
      query['exam_id'] = examId.trim();
    }
    final json = await _send(
      'GET',
      '$_learnerPath/question-bank/topics',
      query: query,
    );
    final raw = json['items'];
    if (raw is! List) return const [];
    return raw
        .whereType<Map<String, dynamic>>()
        .map(QuestionBankTopic.fromJson)
        .toList(growable: false);
  }

  Future<List<TopicOneLinerItem>> getTopicOneLiners(
    String conceptId, {
    int limit = 100,
    int offset = 0,
    String? languageCode,
  }) async {
    final query = <String, String>{
      'concept_id': conceptId,
      'limit': '$limit',
      'offset': '$offset',
    };
    if (languageCode != null && languageCode.trim().isNotEmpty) {
      query['language_code'] = languageCode.trim();
    }
    final json = await _send(
      'GET',
      '$_learnerPath/question-bank/one-liners',
      query: query,
    );
    final raw = json['items'];
    if (raw is! List) return const [];
    return raw
        .whereType<Map<String, dynamic>>()
        .map(TopicOneLinerItem.fromJson)
        .toList(growable: false);
  }

  Future<PreviousYearQuestionPage> getPreviousYearQuestionPage(
    String conceptId, {
    String? subjectId,
    String? examId,
    int? examYear,
    String? examShift,
    String? sourceDomain,
    int limit = 100,
    int offset = 0,
  }) async {
    final query = <String, String>{
      'concept_id': conceptId,
      'limit': '$limit',
      'offset': '$offset',
    };
    if (subjectId != null && subjectId.trim().isNotEmpty) {
      query['subject_id'] = subjectId.trim();
    }
    if (examId != null && examId.trim().isNotEmpty) {
      query['exam_id'] = examId.trim();
    }
    if (examYear != null) {
      query['exam_year'] = '$examYear';
    }
    if (examShift != null && examShift.trim().isNotEmpty) {
      query['exam_shift'] = examShift.trim();
    }
    if (sourceDomain != null && sourceDomain.trim().isNotEmpty) {
      query['source_domain'] = sourceDomain.trim();
    }
    final json = await _send(
      'GET',
      '$_learnerPath/question-bank/previous-papers',
      query: query,
    );
    return PreviousYearQuestionPage.fromJson(json);
  }

  Future<List<PreviousYearQuestion>> getPreviousYearQuestions(
    String conceptId, {
    String? subjectId,
    String? examId,
    int? examYear,
    String? examShift,
    String? sourceDomain,
    int limit = 100,
    int offset = 0,
  }) async {
    final page = await getPreviousYearQuestionPage(
      conceptId,
      subjectId: subjectId,
      examId: examId,
      examYear: examYear,
      examShift: examShift,
      sourceDomain: sourceDomain,
      limit: limit,
      offset: offset,
    );
    return page.items;
  }

  Future<TopicPracticeGenerationResult> generateSubjectPractice({
    required String subjectId,
    required int questionCount,
    required int durationSeconds,
    String languageCode = 'hi',
  }) async {
    final json = await _send(
      'POST',
      '$_learnerPath/question-bank/generate-practice',
      body: {
        'subject_id': subjectId,
        'question_count': questionCount,
        'duration_seconds': durationSeconds,
        'language_code': languageCode,
      },
    );
    return TopicPracticeGenerationResult.fromJson(json);
  }

  Future<LearnerAnalytics> getAnalytics() async {
    final json = await _send('GET', '$_learnerPath/preparation-results/analytics');
    return LearnerAnalytics.fromJson(json);
  }

  Future<ResultsSummary> getResultsSummary() async {
    final json = await _send('GET', '$_learnerPath/preparation-results/summary');
    return ResultsSummary.fromJson(json);
  }

  Future<List<TestHistoryItem>> getSessions({
    int limit = 10,
    int offset = 0,
    String? status,
  }) async {
    final query = <String, String>{'limit': '$limit', 'offset': '$offset'};
    if (status != null && status.isNotEmpty) query['status'] = status;
    final json = await _send(
      'GET',
      '$_learnerPath/preparation-sessions',
      query: query,
    );
    final raw = json['items'];
    if (raw is! List) return const [];
    return raw
        .whereType<Map<String, dynamic>>()
        .map(TestHistoryItem.fromJson)
        .toList(growable: false);
  }

  Future<List<TestHistoryItem>> getResults({int limit = 10, int offset = 0}) async {
    final json = await _send(
      'GET',
      '$_learnerPath/preparation-results',
      query: {'limit': '$limit', 'offset': '$offset'},
    );
    final raw = json['items'];
    if (raw is! List) {
      return const [];
    }
    return raw
        .whereType<Map<String, dynamic>>()
        .map(TestHistoryItem.fromJson)
        .toList(growable: false);
  }

  void close() {
    if (_ownsHttpClient) {
      _httpClient.close();
    }
  }
}
