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
            'availability_scope': 'configured_eligible_pool',
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

  test('mixed practice request provides a non-adaptive first-test path', () async {
    late http.Request received;
    final mock = MockClient((request) async {
      received = request;
      return http.Response(
        jsonEncode({
          'request_id': 'request-mixed-1',
          'learner_id': 'learner-1',
          'status': 'ACTIVE',
          'test_id': 'prep-request-mixed-1',
          'title': 'Mixed practice test',
          'question_count': 20,
          'duration_seconds': 1800,
          'scoring': {
            'correct_marks': 1.0,
            'incorrect_marks': -0.25,
            'unattempted_marks': 0.0,
          },
          'mode': 'MIXED',
          'concept_ids': [],
          'exclude_question_ids': [],
          'shuffle_questions': false,
          'shuffle_seed': null,
          'exam_id': null,
          'subject_id': null,
          'created_at': '2026-10-16T00:00:00Z',
          'updated_at': '2026-10-16T00:00:00Z',
        }),
        201,
        headers: {'content-type': 'application/json'},
      );
    });
    addTearDown(mock.close);
    final api = AiCompApiClient(
      baseUrl: 'https://api.example.test/',
      learnerId: 'learner-1',
      accessToken: 'test-token',
      httpClient: mock,
    );

    await api.createMixedPracticeRequest(
      questionCount: 20,
      durationSeconds: 1800,
    );

    expect(received.method, 'POST');
    expect(
      received.url.path,
      '/api/v1/learners/learner-1/preparation-requests',
    );
    expect(received.headers['authorization'], 'Bearer test-token');
    final posted = jsonDecode(received.body) as Map<String, dynamic>;
    expect(posted['title'], 'Mixed practice test');
    expect(posted['question_count'], 20);
    expect(posted['duration_seconds'], 1800);
    expect(posted['mode'], 'MIXED');
    expect(posted['concept_ids'], isEmpty);
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
          'source_kind': 'VERIFIED_EXAM_HISTORY',
          'source_url': 'https://official.example/paper.pdf',
          'answer_key_source_url': 'https://official.example/key.pdf',
          'exam_name': 'Test recruitment exam',
          'exam_id': 'TEST_EXAM',
          'exam_year': 2024,
          'exam_shift': 'MORNING',
          'exam_question_number': 7,
          'verified_appearance_count': 2,
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
    expect(question.sourceKind, 'VERIFIED_EXAM_HISTORY');
    expect(question.examName, 'Test recruitment exam');
    expect(question.examYear, 2024);
    expect(question.verifiedAppearanceCount, 2);
  });

  test('question-bank readiness returns generated/history counts with bearer authentication', () async {
    late http.Request received;
    final mock = MockClient((request) async {
      received = request;
      return http.Response(
        jsonEncode({
          'learner_id': 'learner-1',
          'question_pool_limit': 5000,
          'eligible_question_count': 7,
          'verified_history_question_count': 5,
          'accepted_generated_question_count': 2,
          'practice_test_available': true,
          'source_counts_scope': 'configured_eligible_pool',
        }),
        200,
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

    final readiness = await api.getQuestionBankReadiness();

    expect(received.method, 'GET');
    expect(
      received.url.path,
      '/api/v1/learners/learner-1/question-bank/readiness',
    );
    expect(received.headers['authorization'], 'Bearer test-token');
    expect(readiness.eligibleQuestionCount, 7);
    expect(readiness.verifiedHistoryQuestionCount, 5);
    expect(readiness.acceptedGeneratedQuestionCount, 2);
    expect(readiness.practiceTestAvailable, isTrue);
  });

  test('previous-paper client sends exam year shift and source filters', () async {
    late http.Request received;
    final mock = MockClient((request) async {
      received = request;
      return http.Response(
        jsonEncode({
          'items': [
            {
              'question_id': 'history-1',
              'stem': 'Which river flows west?',
              'options': [
                {'key': 'A', 'text': 'Luni'},
                {'key': 'B', 'text': 'Banas'},
                {'key': 'C', 'text': 'Chambal'},
                {'key': 'D', 'text': 'Mahi'},
              ],
              'correct_option_key': 'A',
              'explanation': 'Matched official answer key.',
              'exam_name': 'State recruitment exam',
              'exam_id': 'STATE_EXAM',
              'exam_year': 2024,
              'exam_shift': 'MORNING',
              'exam_question_number': 12,
              'source_url': 'https://official.example/paper.pdf',
              'answer_key_source_url': 'https://official.example/key.pdf',
              'verified_appearance_count': 2,
              'concept_ids': ['topic-rivers'],
            },
          ],
          'pagination': {
            'limit': 20,
            'offset': 0,
            'returned': 1,
            'total_count': 8,
            'has_more': true,
          },
        }),
        200,
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

    final page = await api.getPreviousYearQuestionPage(
      'topic-rivers',
      subjectId: 'Rajasthan Geography',
      examId: 'STATE_EXAM',
      examYear: 2024,
      examShift: 'MORNING',
      sourceDomain: 'official.example',
      limit: 20,
      offset: 0,
    );

    expect(received.method, 'GET');
    expect(
      received.url.path,
      '/api/v1/learners/learner-1/question-bank/previous-papers',
    );
    expect(received.url.queryParameters['concept_id'], 'topic-rivers');
    expect(received.url.queryParameters['subject_id'], 'Rajasthan Geography');
    expect(received.url.queryParameters['exam_id'], 'STATE_EXAM');
    expect(received.url.queryParameters['exam_year'], '2024');
    expect(received.url.queryParameters['exam_shift'], 'MORNING');
    expect(received.url.queryParameters['source_domain'], 'official.example');
    expect(received.headers['authorization'], 'Bearer test-token');
    expect(page.items.single.correctOptionText, 'Luni');
    expect(page.pagination.totalCount, 8);
  });

  test('exam profile parser preserves pending syllabus and unmapped counts', () async {
    late http.Request received;
    final mock = MockClient((request) async {
      received = request;
      return http.Response(
        jsonEncode({
          'items': [
            {
              'exam_id': 'RSSB_CET_GRADUATION_2026',
              'exam_name': 'Rajasthan CET Graduation Level 2026',
              'syllabus_id': 'syllabus-2026',
              'syllabus_title': 'Advertisement 09/2026 — review pending',
              'source_url': 'https://rssb.rajasthan.gov.in/notice.pdf',
              'notification_number': '09/2026',
              'source_status': 'REVIEW_PENDING',
              'syllabus_inventory_complete': false,
              'concept_count': 340,
              'mapped_concept_count': 0,
              'excluded_concept_count': 0,
              'unmapped_concept_count': 340,
              'selection_ready': false,
            },
          ],
        }),
        200,
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

    final profiles = await api.getQuestionBankExamProfiles();

    expect(received.method, 'GET');
    expect(received.url.path, '/api/v1/learners/learner-1/question-bank/exam-profiles');
    expect(received.url.queryParameters['limit'], '100');
    expect(received.headers['authorization'], 'Bearer test-token');
    expect(profiles.single.sourceStatus, 'REVIEW_PENDING');
    expect(profiles.single.unmappedConceptCount, 340);
    expect(profiles.single.syllabusInventoryComplete, isFalse);
    expect(profiles.single.selectionReady, isFalse);
  });

  test('exam-scoped subject and topic requests send the selected profile ID', () async {
    final received = <http.Request>[];
    final mock = MockClient((request) async {
      received.add(request);
      if (request.url.path.endsWith('/question-bank/subjects')) {
        return http.Response(jsonEncode({'items': []}), 200);
      }
      if (request.url.path.endsWith('/question-bank/topics')) {
        return http.Response(
          jsonEncode({
            'items': [],
            'pagination': {
              'limit': 20,
              'offset': 0,
              'returned': 0,
              'has_more': false,
            },
          }),
          200,
        );
      }
      return http.Response('not found', 404);
    });
    addTearDown(mock.close);
    final api = AiCompApiClient(
      baseUrl: 'https://api.example.test',
      learnerId: 'learner-1',
      accessToken: 'test-token',
      httpClient: mock,
    );

    final subjects = await api.getQuestionBankSubjects(examId: 'RSSB_CET_GRADUATION_2026');
    final topics = await api.getQuestionBankTopics(
      'Rajasthan Geography',
      examId: 'RSSB_CET_GRADUATION_2026',
      limit: 20,
      offset: 0,
    );

    expect(subjects, isEmpty);
    expect(topics, isEmpty);
    expect(received, hasLength(2));
    expect(received[0].url.queryParameters['exam_id'], 'RSSB_CET_GRADUATION_2026');
    expect(received[1].url.queryParameters['exam_id'], 'RSSB_CET_GRADUATION_2026');
    expect(received[1].url.queryParameters['subject'], 'Rajasthan Geography');
  });


}
