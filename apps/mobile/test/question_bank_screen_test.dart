import 'dart:convert';

import 'package:ai_comp_mobile/api/ai_comp_api_client.dart';
import 'package:ai_comp_mobile/models/preparation_models.dart';
import 'package:ai_comp_mobile/screens/question_bank_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:ai_comp_mobile/localization/question_bank_labels.dart';
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
        'subject': 'राजस्थान भूगोल',
        'topic': 'नदियाँ एवं अपवाह तंत्र',
        'subtopic': label,
        'verified_one_liner_count': 0,
        'pending_one_liner_count': 0,
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
              (index) => topicRow('topic-$index', 'विषय $index'),
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
            'items': [topicRow('topic-thar', 'थार मरुस्थल')],
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
      home: QuestionBankScreen(api: api, subjectId: 'राजस्थान भूगोल'),
    ));
    await tester.pumpAndSettle();

    expect(topicOffsets, [0, 100]);

    await tester.enterText(find.byType(TextField), 'थार');
    await tester.pumpAndSettle();

    expect(find.text('थार मरुस्थल'), findsOneWidget);
    expect(find.text('विषय 0'), findsNothing);
    expect(find.textContaining('1 / 101 उप-विषय'), findsOneWidget);
    expect(find.text('नदियाँ एवं अपवाह तंत्र'), findsOneWidget);
  });

  testWidgets('keeps one-liner and previous-paper empty states independent', (tester) async {
    final requests = <String>[];
    final mock = MockClient((request) async {
      requests.add(request.url.path);
      if (request.url.path.endsWith('/question-bank/topics')) {
        return jsonResponse({
          'items': [topicRow('topic-luni', 'लूणी नदी')],
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
      if (request.url.path.endsWith('/question-bank/pending-one-liners')) {
        return jsonResponse({
          'items': [],
          'pagination': {
            'limit': 100,
            'offset': 0,
            'returned': 0,
            'has_more': false,
          },
        });
      }
      if (request.url.path.endsWith('/question-bank/pending-one-liners')) {
        return jsonResponse({
          'items': [],
          'pagination': {
            'limit': 100, 'offset': 0, 'returned': 0, 'has_more': false,
          },
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
      home: QuestionBankScreen(api: api, subjectId: 'राजस्थान भूगोल'),
    ));
    await tester.pumpAndSettle();
    await tester.tap(find.text('लूणी नदी'));
    await tester.pumpAndSettle();

    expect(find.textContaining('सत्यापित प्रश्न लोड नहीं हो सके'), findsOneWidget);
    expect(requests.any((path) => path.endsWith('/question-bank/one-liners')), isTrue);
    expect(requests.any((path) => path.endsWith('/question-bank/previous-papers')), isTrue);

    await tester.tap(find.text('पिछले वर्षों के प्रश्न'));
    await tester.pumpAndSettle();

    expect(find.text('अभी कोई सत्यापित पुराने प्रश्न उपलब्ध नहीं हैं'), findsOneWidget);
    expect(find.textContaining('सत्यापित प्रश्न लोड नहीं हो सके'), findsNothing);
  });

  testWidgets('displays separate verified one-liner and historical lists', (tester) async {
    final mock = MockClient((request) async {
      if (request.url.path.endsWith('/question-bank/topics')) {
        return jsonResponse({
          'items': [topicRow('topic-luni', 'लूणी नदी')],
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
          label: 'लूणी नदी',
          subject: 'राजस्थान भूगोल',
          topic: 'नदियाँ एवं अपवाह तंत्र',
          subtopic: 'लूणी नदी',
          verifiedOneLinerCount: 1,
        ),
      ),
    ));
    await tester.pumpAndSettle();

    expect(find.textContaining('लूणी नदी किस दिशा में बहती है?'), findsOneWidget);
    expect(find.text('उत्तर: दक्षिण-पश्चिम दिशा में।'), findsOneWidget);
    expect(find.textContaining('सत्यापित स्रोत-साक्ष्य'), findsOneWidget);

    await tester.tap(find.text('पिछले वर्षों के प्रश्न'));
    await tester.pumpAndSettle();
    expect(find.text('अभी कोई सत्यापित पुराने प्रश्न उपलब्ध नहीं हैं'), findsOneWidget);
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
        subjectId: 'राजस्थान भूगोल',
        examId: 'RSSB_CET_GRADUATION_2026',
      ),
    ));
    await tester.pumpAndSettle();

    expect(
      received.url.queryParameters['exam_id'],
      'RSSB_CET_GRADUATION_2026',
    );
    expect(received.url.queryParameters['subject'], 'राजस्थान भूगोल');
    expect(find.textContaining('RSSB_CET_GRADUATION_2026'), findsOneWidget);
    expect(find.text('अभी कोई विषय सूचीबद्ध नहीं है'), findsOneWidget);
  });


  testWidgets('groups child sites under one book chapter without changing concept IDs',
      (tester) async {
    final mock = MockClient((request) async {
      if (request.url.path.endsWith('/question-bank/topics')) {
        return jsonResponse({
          'items': [
            {
              'concept_id': 'catalog.rajasthan_history_ancient_history_kalibangan',
              'label': 'कालीबंगा',
              'subject': 'राजस्थान इतिहास',
              'topic': 'राजस्थान के प्राचीन सभ्यता स्थल',
              'subtopic': 'कालीबंगा',
              'verified_one_liner_count': 0,
              'pending_one_liner_count': 0,
            },
            {
              'concept_id': 'catalog.rajasthan_history_ancient_history_ahar_banas_culture',
              'label': 'आहड़-बनास संस्कृति',
              'subject': 'राजस्थान इतिहास',
              'topic': 'राजस्थान के प्राचीन सभ्यता स्थल',
              'subtopic': 'आहड़-बनास संस्कृति',
              'verified_one_liner_count': 0,
              'pending_one_liner_count': 0,
            },
            {
              'concept_id': 'catalog.rajasthan_history_ancient_history_ganeshwar_jodhpura_culture',
              'label': 'गणेश्वर-जोधपुरा संस्कृति',
              'subject': 'राजस्थान इतिहास',
              'topic': 'राजस्थान के प्राचीन सभ्यता स्थल',
              'subtopic': 'गणेश्वर-जोधपुरा संस्कृति',
              'verified_one_liner_count': 0,
              'pending_one_liner_count': 0,
            },
            {
              'concept_id': 'catalog.rajasthan_history_ancient_history_bairat',
              'label': 'बैराठ / विराटनगर',
              'subject': 'राजस्थान इतिहास',
              'topic': 'राजस्थान के प्राचीन सभ्यता स्थल',
              'subtopic': 'बैराठ / विराटनगर',
              'verified_one_liner_count': 0,
              'pending_one_liner_count': 0,
            },
            {
              'concept_id': 'catalog.rajasthan_history_ancient_history_matsya_janapada',
              'label': 'मत्स्य जनपद',
              'subject': 'राजस्थान इतिहास',
              'topic': 'राजस्थान के प्राचीन सभ्यता स्थल',
              'subtopic': 'मत्स्य जनपद',
              'verified_one_liner_count': 0,
              'pending_one_liner_count': 0,
            },
          ],
          'pagination': {
            'limit': 100,
            'offset': 0,
            'returned': 5,
            'has_more': false,
          },
        });
      }
      return jsonResponse({'items': [], 'pagination': {
        'limit': 100,
        'offset': 0,
        'returned': 0,
        'total_count': 0,
        'has_more': false,
      }});
    });
    addTearDown(mock.close);
    final api = apiFor(mock);
    addTearDown(api.close);

    await tester.pumpWidget(MaterialApp(
      home: QuestionBankScreen(api: api, subjectId: 'राजस्थान इतिहास'),
    ));
    await tester.pumpAndSettle();

    expect(find.text('राजस्थान के प्राचीन सभ्यता स्थल'), findsOneWidget);
    expect(find.text('5 उप-विषय • 0 सत्यापित • 368 समीक्षा बाकी'), findsOneWidget);
    expect(find.text('कालीबंगा'), findsOneWidget);
    expect(find.text('आहड़-बनास संस्कृति'), findsOneWidget);
    expect(find.text('गणेश्वर-जोधपुरा संस्कृति'), findsOneWidget);
    expect(find.text('बैराठ / विराटनगर'), findsOneWidget);
    expect(find.text('मत्स्य जनपद'), findsOneWidget);
  });

  testWidgets('question bank navigation uses Hindi labels', (tester) async {
    final mock = MockClient((request) async => jsonResponse({
      'items': [topicRow('topic-hindi', 'लूणी नदी')],
      'pagination': {
        'limit': 100, 'offset': 0, 'returned': 1, 'has_more': false,
      },
    }));
    addTearDown(mock.close);
    final api = apiFor(mock);
    addTearDown(api.close);
  
    await tester.pumpWidget(MaterialApp(
      home: QuestionBankScreen(api: api, subjectId: 'राजस्थान भूगोल'),
    ));
    await tester.pumpAndSettle();
  
    expect(find.text('राजस्थान भूगोल — विषय'), findsOneWidget);
    expect(find.text('विषय और उप-विषय खोजें'), findsOneWidget);
    expect(find.text('लूणी नदी'), findsOneWidget);
  });

  test('translates legacy English catalogue values for display', () {
    expect(questionBankHindiLabel('Rajasthan History'), 'राजस्थान इतिहास');
    expect(questionBankHindiLabel('Rivers and Drainage'), 'नदियाँ एवं अपवाह तंत्र');
    expect(questionBankHindiLabel('Luni River'), 'लूणी नदी');
    expect(questionBankHindiLabel('मत्स्य जनपद'), 'मत्स्य जनपद');
  });

  testWidgets('search finds a Hindi alias from an English API catalogue', (tester) async {
    String? requestedSubject;
    final mock = MockClient((request) async {
      requestedSubject = request.url.queryParameters['subject'];
      return jsonResponse({
        'items': [
          {
            'concept_id': 'catalog.rajasthan_geography_luni_river',
            'label': 'Luni River',
            'subject': 'Rajasthan Geography',
            'topic': 'Rivers and Drainage',
            'subtopic': 'Luni River',
            'verified_one_liner_count': 0,
          },
        ],
        'pagination': {
          'limit': 100, 'offset': 0, 'returned': 1, 'has_more': false,
        },
      });
    });
    addTearDown(mock.close);
    final api = apiFor(mock);
    addTearDown(api.close);

    await tester.pumpWidget(MaterialApp(
      home: QuestionBankScreen(api: api, subjectId: 'Rajasthan Geography'),
    ));
    await tester.pumpAndSettle();

    expect(find.text('राजस्थान भूगोल — विषय'), findsOneWidget);
    expect(find.text('नदियाँ एवं अपवाह तंत्र'), findsOneWidget);
    await tester.enterText(find.byType(TextField), 'लूणी नदी');
    await tester.pumpAndSettle();
    expect(find.text('लूणी नदी'), findsNWidgets(2));
    expect(requestedSubject, 'Rajasthan Geography');
  });


  testWidgets('shows Chapter 2 AI drafts in a clearly labelled pending lane', (tester) async {
    final requests = <String>[];
    final mock = MockClient((request) async {
      requests.add(request.url.path);
      if (request.url.path.endsWith('/question-bank/one-liners')) {
        return jsonResponse({
          'items': [],
          'pagination': {
            'limit': 100, 'offset': 0, 'returned': 0, 'has_more': false,
          },
        });
      }
      if (request.url.path.endsWith('/question-bank/pending-one-liners')) {
        expect(request.url.queryParameters['concept_id'], 'catalog.rajasthan_history_ancient_history_kalibangan');
        expect(request.url.queryParameters['language_code'], 'hi');
        return jsonResponse({
          'items': [
            {
              'one_liner_id': 'ch2_KAL-001',
              'concept_id': 'catalog.rajasthan_history_ancient_history_kalibangan',
              'question_text': 'कालीबंगा राजस्थान के किस जिले में स्थित है?',
              'answer_text': 'हनुमानगढ़ जिले में।',
              'language_code': 'hi',
              'source_url': 'https://example.gov.in/kalibanga.pdf',
              'source_evidence': 'KAL-001 — S4, मुद्रित पृष्ठ 34 — स्वतंत्र स्रोत-समीक्षा लंबित।',
              'verification_status': 'NEEDS_REVIEW',
              'importance_score': 0.8,
            },
          ],
          'pagination': {
            'limit': 100, 'offset': 0, 'returned': 1, 'has_more': false,
          },
        });
      }
      if (request.url.path.endsWith('/question-bank/previous-papers')) {
        return jsonResponse({
          'items': [],
          'pagination': {
            'limit': 100, 'offset': 0, 'returned': 0,
            'total_count': 0, 'has_more': false,
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
        topic: const QuestionBankTopic(
          conceptId: 'catalog.rajasthan_history_ancient_history_kalibangan',
          label: 'कालीबंगा',
          subject: 'राजस्थान इतिहास',
          topic: 'राजस्थान के प्राचीन सभ्यता स्थल',
          subtopic: 'कालीबंगा',
          verifiedOneLinerCount: 0,
          pendingOneLinerCount: 311,
        ),
      ),
    ));
    await tester.pumpAndSettle();

    expect(find.text('AI मसौदा — समीक्षा बाकी'), findsOneWidget);
    expect(find.textContaining('कालीबंगा राजस्थान के किस जिले में स्थित है?'), findsOneWidget);
    expect(find.text('उत्तर: हनुमानगढ़ जिले में।'), findsOneWidget);
    expect(find.textContaining('स्रोत-सूचक (जाँच बाकी)'), findsOneWidget);
    expect(find.text('सत्यापित प्रश्न'), findsNothing);
    expect(requests, contains('/api/v1/learners/learner-1/question-bank/pending-one-liners'));
  });

  testWidgets('shows bundled Chapter 2 questions when the server draft API is unavailable', (tester) async {
    final requests = <String>[];
    final mock = MockClient((request) async {
      requests.add(request.url.path);
      if (request.url.path.endsWith('/question-bank/one-liners')) {
        return jsonResponse({
          'items': [],
          'pagination': {
            'limit': 100, 'offset': 0, 'returned': 0, 'has_more': false,
          },
        });
      }
      if (request.url.path.endsWith('/question-bank/pending-one-liners')) {
        return jsonResponse({
          'error': {'code': 'QUESTION_BANK_PENDING_ONE_LINERS_UNAVAILABLE', 'message': 'Database import pending.'},
        }, 503);
      }
      if (request.url.path.endsWith('/question-bank/previous-papers')) {
        return jsonResponse({
          'items': [],
          'pagination': {
            'limit': 100, 'offset': 0, 'returned': 0,
            'total_count': 0, 'has_more': false,
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
        topic: const QuestionBankTopic(
          conceptId: 'catalog.rajasthan_history_ancient_history_kalibangan',
          label: 'कालीबंगा',
          subject: 'राजस्थान इतिहास',
          topic: 'राजस्थान के प्राचीन सभ्यता स्थल',
          subtopic: 'कालीबंगा',
          verifiedOneLinerCount: 0,
          pendingOneLinerCount: 0,
        ),
      ),
    ));
    await tester.pumpAndSettle();

    expect(find.text('AI मसौदा — समीक्षा बाकी'), findsWidgets);
    expect(find.textContaining('कालीबंगा राजस्थान के किस जिले में स्थित है?'), findsOneWidget);
    expect(find.text('उत्तर: हनुमानगढ़ जिले में।'), findsOneWidget);
    expect(find.textContaining('KAL-001'), findsOneWidget);
    expect(find.textContaining('APK में सुरक्षित स्थानीय प्रति'), findsOneWidget);
    expect(find.text('सत्यापित प्रश्न'), findsNothing);
    expect(requests, contains('/api/v1/learners/learner-1/question-bank/pending-one-liners'));
  });


}
