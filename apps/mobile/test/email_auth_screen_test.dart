import 'package:ai_comp_mobile/screens/email_auth_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('login screen uses English labels and offers password reset', (tester) async {
    await tester.pumpWidget(const MaterialApp(home: EmailAuthScreen()));

    expect(find.text('Sign in to AI-COMP'), findsOneWidget);
    expect(find.text('Email address'), findsOneWidget);
    expect(find.text('Password'), findsOneWidget);
    expect(find.text('Forgot password?'), findsOneWidget);
    expect(find.text('New to AI-COMP? Create an account'), findsOneWidget);
    expect(find.text('Confirm password'), findsNothing);
  });

  testWidgets('registration asks to confirm password and rejects mismatches', (tester) async {
    await tester.pumpWidget(const MaterialApp(home: EmailAuthScreen()));

    await tester.tap(find.text('New to AI-COMP? Create an account'));
    await tester.pumpAndSettle();

    expect(find.text('Create your account'), findsOneWidget);
    expect(find.text('Confirm password'), findsOneWidget);
    expect(find.text('Forgot password?'), findsNothing);

    await tester.enterText(find.byType(TextFormField).at(0), 'learner@example.com');
    await tester.enterText(find.byType(TextFormField).at(1), 'password123');
    await tester.enterText(find.byType(TextFormField).at(2), 'password456');
    await tester.tap(find.text('Create account'));
    await tester.pumpAndSettle();

    expect(find.text('Passwords do not match.'), findsOneWidget);
  });
}
