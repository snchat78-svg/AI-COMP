import 'package:ai_comp_mobile/main.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('dashboard starts with connection setup and disabled test action', (tester) async {
    await tester.pumpWidget(const AiCompMobileApp());

    expect(find.text('AI-COMP तैयारी'), findsOneWidget);
    expect(find.text('API base URL'), findsOneWidget);
    expect(find.text('Learner ID'), findsOneWidget);
    expect(find.text('Access token'), findsOneWidget);
    expect(find.text('Connect & load progress'), findsOneWidget);
    expect(find.text('Create and start test'), findsOneWidget);

    final testButton = tester.widget<FilledButton>(
      find.widgetWithText(FilledButton, 'Create and start test'),
    );
    expect(testButton.onPressed, isNull);
  });
}
