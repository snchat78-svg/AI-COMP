import 'dart:convert';

import 'package:ai_comp_mobile/api/ai_comp_api_client.dart';
import 'package:ai_comp_mobile/models/preparation_models.dart';
import 'package:ai_comp_mobile/screens/question_bank_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  http.Response jsonResponse(Map<String, dynamic> body, [int status = 200]) {
    return http.Response(
      jsonEncode(body),
      status,
      headers: {'content-type': 'application/json'},
    );
  }

  Map<String, dynamic> topicRow(String id, String label) => {
        'concept_id': id,
        'label': label,
        'subject': 'Rajasthan Geography',
        'topic': 'Rivers and Drainage',
        'subtopic': label,
        'verified_one_liner_count': 0,
      };

  AiCompApiClient apiFor(MockClient client) => AiCompApiClient(
        baseUrl: 'https://api.example.test',
        learnerId: 'learner-1',
        accessToken: 'test-token',
        httpClient: client,
      );

  testWidgets('loads bounded topic pages and filters by topic/subtopic', (tester) async {
    final topicOffsets = <int>[];
    final mock = MockClient((request) async {
      if (request.url.path.endsWith('/question-bank/topics')) {
        final offset = int.parse(request.url.queryParameters['offset']!);
        topicOffsets.add(offset);
        if (offset == 0) {
          return jsonResponse({
            'items': List.generate(
              100,
              (index) => topicRow('topic-$index', 'Topic $index'),
            ),
            'pagination': {
              'limit': 100,
              'offset': 0,
              'returned': 100,
              'has_more': true,
            },
          });
        }
        if (offset == 100) {
          return jsonResponse({
            'items': [topicRow('topic-thar', 'Thar Desert')],
            'pagination': {
              'limit': 100,
              'offset': 100,
              'returned': 1,
              'has_more': false,
            },
          });
        }
      }
      return jsonResponse({'error': {'code': 'UNEXPECTED', 'message': 'Unexpected request.'}}, 500);
    });
    addTearDown(mock.close);
    final api = apiFor(mock);
    addTearDown(api.close);

    await tester.pumpWidget(MaterialApp(
      home: QuestionBankScreen(api: api, subjectId: 'Rajasthan Geography'),
    ));
    await tester.pumpAndSettle();

    expect(topicOffsets, [0, 100]);

    await tester.enterText(find.byType(TextField), 'Thar');
    await tester.pumpAndSettle();

    expect(find.text('Thar Desert'), findsOneWidget);
    expect(find.text('Topic 0'), findsNothing);
    expect(find.textContaining('1 of 101 topics'), findsOneWidget);
  });

  testWidgets('keeps one-liner and previous-paper empty states independent', (tester) async {
    final requests = <String>[];
    final mock = MockClient((request) async {
      requests.add(request.url.path);
      if (request.url.path.endsWith('/question-bank/topics')) {
        return jsonResponse({
          'items': [topicRow('topic-luni', 'Luni River')],
          'pagination': {
            'limit': 100,
            'offset': 0,
            'returned': 1,
            'has_more': false,
          },
        });
      }
      if (request.url.path.endsWith('/question-bank/one-liners')) {
        return jsonResponse({
          'error': {'code': 'CONTENT_UNAVAILABLE', 'message': 'No content.'},
        }, 503);
      }
      if (request.url.path.endsWith('/question-bank/previous-papers')) {
        return jsonResponse({
          'items': [],
          'pagination': {
            'limit': 100,
            'offset': 0,
            'returned': 0,
            'total_count': 0,
            'has_more': false,
          },
        });
      }
      return jsonResponse({'error': {'code': 'UNEXPECTED', 'message': 'Unexpected request.'}}, 500);
    });
    addTearDown(mock.close);
    final api = apiFor(mock);
    addTearDown(api.close);

    await tester.pumpWidget(MaterialApp(
      home: QuestionBankScreen(api: api, subjectId: 'Rajasthan Geography'),
    ));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Luni River'));
    await tester.pumpAndSettle();

    expect(find.text('One-liners unavailable'), findsOneWidget);
    expect(requests.any((path) => path.endsWith('/question-bank/one-liners')), isTrue);
    expect(requests.any((path) => path.endsWith('/question-bank/previous-papers')), isTrue);

    await tester.tap(find.text('Previous Year'));
    await tester.pumpAndSettle();

    expect(find.text('No verified previous-paper questions yet'), findsOneWidget);
    expect(find.text('One-liners unavailable'), findsNothing);
  });

  testWidgets('displays separate verified one-liner and historical lists', (tester) async {
    final mock = MockClient((request) async {
      if (request.url.path.endsWith('/question-bank/topics')) {
        return jsonResponse({
          'items': [topicRow('topic-luni', 'Luni River')],
          'pagination': {
            'limit': 100,
            'offset': 0,
            'returned': 1,
            'has_more': false,
          },
        });
      }
      if (request.url.path.endsWith('/question-bank/one-liners')) {
        return jsonResponse({
          'items': [
            {
              'one_liner_id': 'one-liner-1',
              'concept_id': 'topic-luni',
              'question_text': 'लूणी नदी किस दिशा में बहती है?',
              'answer_text': 'दक्षिण-पश्चिम दिशा में।',
              'language_code': 'hi',
              'source_url': 'https://official.example/source',
              'source_evidence': 'Official source, river section.',
              'verification_status': 'VERIFIED',
              'importance_score': 0.9,
            }
          ],
          'pagination': {'limit': 100, 'offset': 0, 'returned': 1, 'has_more': false},
        });
      }
      if (request.url.path.endsWith('/question-bank/previous-papers')) {
        return jsonResponse({
          'items': [],
          'pagination': {
            'limit': 100,
            'offset': 0,
            'returned': 0,
            'total_count': 0,
            'has_more': false,
          },
        });
      }
      return jsonResponse({'error': {'code': 'UNEXPECTED', 'message': 'Unexpected request.'}}, 500);
    });
    addTearDown(mock.close);
    final api = apiFor(mock);
    addTearDown(api.close);

    await tester.pumpWidget(MaterialApp(
      home: TopicQuestionBankDetailScreen(
        api: api,
        topic: QuestionBankTopic(
          conceptId: 'topic-luni',
          label: 'Luni River',
          subject: 'Rajasthan Geography',
          topic: 'Rivers and Drainage',
          subtopic: 'Luni River',
          verifiedOneLinerCount: 1,
        ),
      ),
    ));
    await tester.pumpAndSettle();

    expect(find.textContaining('लूणी नदी किस दिशा में बहती है?'), findsOneWidget);
    expect(find.text('Answer: दक्षिण-पश्चिम दिशा में।'), findsOneWidget);
    expect(find.textContaining('Verified source evidence'), findsOneWidget);

    await tester.tap(find.text('Previous Year'));
    await tester.pumpAndSettle();
    expect(find.text('No verified previous-paper questions yet'), findsOneWidget);
    expect(find.textContaining('लूणी नदी किस दिशा में बहती है?'), findsNothing);
  });
  testWidgets('exam-scoped topic browsing does not drop the selected exam ID', (tester) async {
    late http.Request received;
    final mock = MockClient((request) async {
      received = request;
      return jsonResponse({
        'items': [],
        'pagination': {
          'limit': 100,
          'offset': 0,
          'returned': 0,
          'has_more': false,
        },
      });
    });
    addTearDown(mock.close);
    final api = apiFor(mock);
    addTearDown(api.close);

    await tester.pumpWidget(MaterialApp(
      home: QuestionBankScreen(
        api: api,
        subjectId: 'Rajasthan Geography',
        examId: 'RSSB_CET_GRADUATION_2026',
      ),
    ));
    await tester.pumpAndSettle();

    expect(
      received.url.queryParameters['exam_id'],
      'RSSB_CET_GRADUATION_2026',
    );
    expect(received.url.queryParameters['subject'], 'Rajasthan Geography');
    expect(find.textContaining('RSSB_CET_GRADUATION_2026'), findsOneWidget);
    expect(find.text('No topics are mapped yet'), findsOneWidget);
  });


}
