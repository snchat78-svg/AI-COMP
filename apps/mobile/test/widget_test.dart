import 'package:ai_comp_mobile/main.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('dashboard starts with connection setup and disabled test action', (tester) async {
    await tester.pumpWidget(const AiCompMobileApp(firebaseEnabled: false));

    expect(find.text('AI-COMP Preparation'), findsOneWidget);
    expect(find.text('Prepare smarter.\nLearn with clarity.'), findsOneWidget);
    expect(find.text('Study library'), findsOneWidget);
    expect(find.textContaining('Main chapter'), findsOneWidget);
    expect(find.text('Explore study library'), findsOneWidget);
    expect(find.text('Choose a subject to continue'), findsOneWidget);
    expect(find.text('API base URL'), findsOneWidget);
    expect(find.text('Learner ID'), findsOneWidget);
    expect(find.text('Access token'), findsOneWidget);
    expect(find.text('Connect & load progress'), findsOneWidget);
    expect(find.text('Connect to create test'), findsOneWidget);

    final testButton = tester.widget<FilledButton>(
      find.widgetWithText(FilledButton, 'Connect to create test'),
    );
    expect(testButton.onPressed, isNull);

    final libraryButton = tester.widget<FilledButton>(
      find.widgetWithText(FilledButton, 'Explore study library'),
    );
    expect(libraryButton.onPressed, isNull);
  });
}
