import 'dart:convert';

import 'package:ai_comp_mobile/api/ai_comp_api_client.dart';
import 'package:ai_comp_mobile/models/preparation_models.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

void main() {
  test('adaptive recommendation posts settings with bearer authentication', () async {
    late http.Request received;
    final mock = MockClient((request) async {
      received = request;
      return http.Response(
        jsonEncode({
          'request_id': 'request-1',
          'learner_id': 'learner-1',
          'status': 'ACTIVE',
          'test_id': 'adaptive-test-1',
          'title': 'Adaptive practice',
          'question_count': 6,
          'duration_seconds': 900,
          'scoring': {
            'correct_marks': 1.0,
            'incorrect_marks': -0.25,
            'unattempted_marks': 0.0,
          },
          'mode': 'ADAPTIVE',
          'concept_ids': ['geography'],
          'exclude_question_ids': [],
          'shuffle_questions': false,
          'shuffle_seed': null,
          'exam_id': null,
          'subject_id': null,
          'created_at': '2026-10-10T00:00:00Z',
          'updated_at': '2026-10-10T00:00:00Z',
          'recommendation': {
            'strategy': 'WEAK_TOPICS_THEN_REPEATED_CONCEPTS_THEN_PREVIOUS_MISTAKES',
            'source': 'PERSISTED_LEARNER_TEST_HISTORY',
            'focus_concept_ids': ['geography'],
            'focus_reasons': {'geography': ['WEAK_TOPIC']},
            'revision_question_ids': ['old-question'],
            'completed_test_count': 2,
            'weak_topic_count': 1,
            'repeated_concept_count': 0,
            'requested_question_count': 10,
            'eligible_question_count_in_configured_pool': 6,
            'effective_question_count': 6,
            'question_count_adjusted': true,
            'availability_scope': 'configured_accepted_question_pool',
          },
        }),
        201,
        headers: {'content-type': 'application/json'},
      );
    });
    addTearDown(mock.close);
    final api = AiCompApiClient(
      baseUrl: 'https://api.example.test',
      learnerId: 'learner-1',
      accessToken: 'test-token',
      httpClient: mock,
    );

    final response = await api.recommendAdaptivePractice(
      questionCount: 10,
      durationSeconds: 900,
      maxConcepts: 4,
    );

    expect(received.method, 'POST');
    expect(
      received.url.path,
      '/api/v1/learners/learner-1/preparation-recommendations',
    );
    expect(received.headers['authorization'], 'Bearer test-token');
    final posted = jsonDecode(received.body) as Map<String, dynamic>;
    expect(posted['question_count'], 10);
    expect(posted['duration_seconds'], 900);
    expect(posted['max_concepts'], 4);
    expect(response.questionCount, 6);
    expect(response.questionCountAdjusted, isTrue);
  });

  test('API conflict exposes stable error code without losing status', () async {
    final mock = MockClient((_) async => http.Response(
          jsonEncode({
            'error': {
              'code': 'NO_ADAPTIVE_PRACTICE_SIGNAL',
              'message': 'Complete a test first.',
            },
          }),
          409,
        ));
    addTearDown(mock.close);
    final api = AiCompApiClient(
      baseUrl: 'https://api.example.test/',
      learnerId: 'learner-1',
      accessToken: 'token',
      httpClient: mock,
    );

    await expectLater(
      api.recommendAdaptivePractice(),
      throwsA(
        isA<ApiException>()
            .having((error) => error.statusCode, 'status', 409)
            .having((error) => error.code, 'code', 'NO_ADAPTIVE_PRACTICE_SIGNAL'),
      ),
    );
  });

  test('current-question URL supports prefixed API deployments', () async {
    final mock = MockClient((request) async {
      expect(
        request.url.path,
        '/gateway/api/v1/learners/learner-1/preparation-sessions/session-1/current-question',
      );
      return http.Response(
        jsonEncode({
          'session_id': 'session-1',
          'question_number': 1,
          'question_count': 1,
          'question_id': 'q-1',
          'stem': 'Choose an option',
          'options': [{'key': 'A', 'text': 'First'}],
          'selected_option_key': 'A',
          'review_marked': false,
          'remaining_seconds': 60,
        }),
        200,
      );
    });
    addTearDown(mock.close);
    final api = AiCompApiClient(
      baseUrl: 'https://api.example.test/gateway/',
      learnerId: 'learner-1',
      accessToken: 'token',
      httpClient: mock,
    );

    final question = await api.getCurrentQuestion('session-1');

    expect(question.selectedOptionKey, 'A');
    expect(question.remainingSeconds, 60);
  });
}
