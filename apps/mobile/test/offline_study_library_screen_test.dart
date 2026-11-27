import 'package:ai_comp_mobile/screens/offline_study_library_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

const _subjectDefinitions = <Map<String, dynamic>>[
  {
    'subject_label': 'राजस्थान इतिहास',
    'topic_name': 'राजस्थान के प्राचीन सभ्यता स्थल',
    'count': 34,
    'first_label': 'कालीबंगा',
    'first_id': 'history.kalibanga',
  },
  {
    'subject_label': 'राजस्थान भूगोल',
    'topic_name': 'नदियाँ एवं अपवाह तंत्र',
    'count': 32,
    'first_label': 'लूणी नदी',
    'first_id': 'geography.luni',
  },
  {
    'subject_label': 'राजस्थान राजव्यवस्था एवं प्रशासन',
    'topic_name': 'प्रशासनिक व्यवस्था',
    'count': 21,
    'first_label': 'राज्य प्रशासन',
    'first_id': 'polity.administration',
  },
  {
    'subject_label': 'राजस्थान कला एवं संस्कृति',
    'topic_name': 'लोक कला और नृत्य',
    'count': 29,
    'first_label': 'कालबेलिया',
    'first_id': 'art.kalbelia',
  },
  {
    'subject_label': 'राजस्थान अर्थव्यवस्था',
    'topic_name': 'खनिज एवं उद्योग',
    'count': 21,
    'first_label': 'खनन अर्थव्यवस्था',
    'first_id': 'economy.mining',
  },
];

OfflineStudyLibraryData _fixture() {
  final subjects = _subjectDefinitions.map((definition) {
    final count = definition['count'] as int;
    final firstId = definition['first_id'] as String;
    final firstLabel = definition['first_label'] as String;
    final subtopics = List<Map<String, dynamic>>.generate(count, (index) => {
          'concept_id': index == 0 ? firstId : '$firstId.$index',
          'label': index == 0 ? firstLabel : 'उप-विषय ${index + 1}',
        });
    return <String, dynamic>{
      'subject_label': definition['subject_label'],
      'topic_groups': [
        {
          'topic_name': definition['topic_name'],
          'subtopics': subtopics.take(1).toList(growable: false),
        },
        {
          'topic_name': 'अन्य उप-विषय',
          'subtopics': subtopics.skip(1).toList(growable: false),
        },
      ],
    };
  }).toList(growable: false);

  final items = <Map<String, dynamic>>[
    {
      'one_liner_id': 'luni-1',
      'concept_id': 'geography.luni',
      'question_text': 'राजस्थान के मरुस्थलीय क्षेत्र की प्रमुख नदी प्रणाली कौन-सी है?',
      'answer_text': 'लूणी नदी और उसकी सहायक नदियाँ।',
      'source_evidence': 'राजस्थान का भौगोलिक परिचय, नदी प्रणाली अनुभाग।',
      'source_url': 'https://environment.rajasthan.gov.in/example',
      'verification_status': 'NEEDS_REVIEW',
      'language_code': 'hi',
    },
  ];
  for (var i = 1; i < 486; i++) {
    items.add({
      'one_liner_id': 'fixture-$i',
      'concept_id': 'history.kalibanga',
      'question_text': 'परीक्षण प्रश्न संख्या $i क्या है?',
      'answer_text': 'परीक्षण उत्तर संख्या $i।',
      'source_evidence': 'परीक्षण स्रोत, अनुभाग $i।',
      'source_url': 'https://example.gov.in/source/$i',
      'verification_status': 'NEEDS_REVIEW',
      'language_code': 'hi',
    });
  }
  return OfflineStudyLibraryData(subjects: subjects, questions: items);
}

Future<void> _pumpLibrary(WidgetTester tester) async {
  await tester.pump();
  await tester.pump(const Duration(milliseconds: 1));
  await tester.pumpAndSettle();
  expect(find.text('486'), findsOneWidget);
}

Future<void> _scrollToText(WidgetTester tester, String value) async {
  final finder = find.text(value);
  for (var attempt = 0; attempt < 12 && finder.evaluate().isEmpty; attempt++) {
    await tester.drag(find.byType(ListView).first, const Offset(0, -420));
    await tester.pumpAndSettle();
  }
  expect(finder, findsWidgets, reason: 'Could not scroll to "$value".');
  await tester.ensureVisible(finder.first);
  await tester.pumpAndSettle();
}

Widget _testApp() => MaterialApp(
      home: OfflineStudyLibraryScreen(dataLoader: () async => _fixture()),
    );

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('offline Rajasthan library exposes all five subjects and 137 concepts',
      (tester) async {
    await tester.pumpWidget(_testApp());
    await _pumpLibrary(tester);

    expect(find.text('राजस्थान अध्ययन लाइब्रेरी'), findsOneWidget);
    expect(find.text('137'), findsOneWidget);
    for (final subject in _subjectDefinitions) {
      await _scrollToText(tester, subject['subject_label'] as String);
    }
  });

  testWidgets('offline browsing opens Geography topic and Hindi one-liner answers',
      (tester) async {
    await tester.pumpWidget(_testApp());
    await _pumpLibrary(tester);

    await _scrollToText(tester, 'राजस्थान भूगोल');
    await tester.tap(find.text('राजस्थान भूगोल'));
    await tester.pumpAndSettle();

    await _scrollToText(tester, 'नदियाँ एवं अपवाह तंत्र');
    await tester.tap(find.text('नदियाँ एवं अपवाह तंत्र'));
    await tester.pumpAndSettle();

    await _scrollToText(tester, 'लूणी नदी');
    await tester.tap(find.text('लूणी नदी').last);
    await tester.pumpAndSettle();

    expect(
      find.textContaining('राजस्थान के मरुस्थलीय क्षेत्र की प्रमुख नदी प्रणाली कौन-सी है?'),
      findsOneWidget,
    );
    expect(find.textContaining('लूणी नदी और उसकी सहायक नदियाँ।'), findsOneWidget);
    expect(find.textContaining('स्रोत-साक्ष्य:'), findsWidgets);
  });

  testWidgets('empty planned subtopic is clearly marked rather than inventing questions',
      (tester) async {
    await tester.pumpWidget(_testApp());
    await _pumpLibrary(tester);

    await _scrollToText(tester, 'राजस्थान अर्थव्यवस्था');
    await tester.tap(find.text('राजस्थान अर्थव्यवस्था'));
    await tester.pumpAndSettle();

    await _scrollToText(tester, 'खनिज एवं उद्योग');
    await tester.tap(find.text('खनिज एवं उद्योग'));
    await tester.pumpAndSettle();

    await _scrollToText(tester, 'खनन अर्थव्यवस्था');
    await tester.tap(find.text('खनन अर्थव्यवस्था'));
    await tester.pumpAndSettle();

    expect(find.text('इस उप-विषय के प्रश्न तैयारी में हैं'), findsOneWidget);
  });
}
