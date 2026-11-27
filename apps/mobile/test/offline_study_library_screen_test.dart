import 'package:ai_comp_mobile/screens/offline_study_library_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

Future<void> pumpLibrary(WidgetTester tester) async {
  await tester.pump();
  final title = find.text('राजस्थान अध्ययन लाइब्रेरी');
  for (var attempt = 0; attempt < 30 && title.evaluate().isEmpty; attempt++) {
    await tester.pump(const Duration(milliseconds: 100));
  }
  await tester.pump();
}

Future<void> scrollToText(WidgetTester tester, String value) async {
  final finder = find.text(value);
  for (var attempt = 0; attempt < 12 && finder.evaluate().isEmpty; attempt++) {
    await tester.drag(find.byType(ListView).first, const Offset(0, -420));
    await tester.pumpAndSettle();
  }
  expect(finder, findsWidgets, reason: 'Could not scroll to "$value".');
  await tester.ensureVisible(finder.first);
  await tester.pumpAndSettle();
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('offline Rajasthan library exposes all five subjects and 137 concepts',
      (tester) async {
    await tester.pumpWidget(
      const MaterialApp(home: OfflineStudyLibraryScreen()),
    );
    await pumpLibrary(tester);

    expect(find.text('राजस्थान अध्ययन लाइब्रेरी'), findsOneWidget);
    for (final subject in [
      'राजस्थान इतिहास',
      'राजस्थान भूगोल',
      'राजस्थान राजव्यवस्था एवं प्रशासन',
      'राजस्थान कला एवं संस्कृति',
      'राजस्थान अर्थव्यवस्था',
    ]) {
      await scrollToText(tester, subject);
    }
    expect(find.text('137'), findsOneWidget);
    expect(find.text('486'), findsOneWidget);
  });

  testWidgets('offline browsing opens Geography topic and Hindi one-liner answers',
      (tester) async {
    await tester.pumpWidget(
      const MaterialApp(home: OfflineStudyLibraryScreen()),
    );
    await pumpLibrary(tester);

    await scrollToText(tester, 'राजस्थान भूगोल');
    await tester.tap(find.text('राजस्थान भूगोल'));
    await tester.pumpAndSettle();
    await scrollToText(tester, 'नदियाँ एवं अपवाह तंत्र');
    await tester.tap(find.text('नदियाँ एवं अपवाह तंत्र'));
    await tester.pumpAndSettle();
    await scrollToText(tester, 'लूणी नदी');
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
    await tester.pumpWidget(
      const MaterialApp(home: OfflineStudyLibraryScreen()),
    );
    await pumpLibrary(tester);

    await scrollToText(tester, 'राजस्थान अर्थव्यवस्था');
    await tester.tap(find.text('राजस्थान अर्थव्यवस्था'));
    await tester.pumpAndSettle();
    await scrollToText(tester, 'खनिज एवं उद्योग');
    await tester.tap(find.text('खनिज एवं उद्योग'));
    await tester.pumpAndSettle();
    await scrollToText(tester, 'खनन अर्थव्यवस्था');
    await tester.tap(find.text('खनन अर्थव्यवस्था'));
    await tester.pumpAndSettle();

    expect(find.text('इस उप-विषय के प्रश्न तैयारी में हैं'), findsOneWidget);
  });
}
