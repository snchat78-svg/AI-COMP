import 'package:firebase_auth/firebase_auth.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:flutter/material.dart';

import 'screens/email_auth_screen.dart';
import 'screens/email_verification_screen.dart';
import 'screens/preparation_home_screen.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  try {
    await Firebase.initializeApp();
    runApp(const AiCompMobileApp());
  } catch (_) {
    runApp(const FirebaseInitializationFailureApp());
  }
}

class AiCompMobileApp extends StatelessWidget {
  const AiCompMobileApp({super.key, this.firebaseEnabled = true});

  /// False is used by widget tests that intentionally exercise the API-only
  /// dashboard without requiring the native Firebase platform channel.
  final bool firebaseEnabled;

  @override
  Widget build(BuildContext context) {
    const seed = Color(0xFF3447A5);
    return MaterialApp(
      title: 'AI-COMP',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(seedColor: seed),
        appBarTheme: const AppBarTheme(centerTitle: false),
        inputDecorationTheme: const InputDecorationTheme(
          filled: true,
          border: OutlineInputBorder(),
        ),
        cardTheme: const CardThemeData(
          clipBehavior: Clip.antiAlias,
          margin: EdgeInsets.zero,
        ),
      ),
      home: firebaseEnabled ? const _FirebaseAuthGate() : const PreparationHomeScreen(),
    );
  }
}

class _FirebaseAuthGate extends StatelessWidget {
  const _FirebaseAuthGate();

  @override
  Widget build(BuildContext context) {
    return StreamBuilder<User?>(
      stream: FirebaseAuth.instance.authStateChanges(),
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Scaffold(
            body: Center(child: CircularProgressIndicator()),
          );
        }
        if (snapshot.hasError) {
          return const FirebaseInitializationFailureApp();
        }
        final user = snapshot.data;
        if (user == null) return const EmailAuthScreen();
        if (!user.emailVerified) return EmailVerificationScreen(user: user);
        return PreparationHomeScreen(firebaseUser: user);
      },
    );
  }
}

class FirebaseInitializationFailureApp extends StatelessWidget {
  const FirebaseInitializationFailureApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'AI-COMP setup',
      home: Scaffold(
        appBar: AppBar(title: const Text('AI-COMP setup')),
        body: const Padding(
          padding: EdgeInsets.all(24),
          child: Center(
            child: Text(
              'Firebase could not initialize. Check the '
              'GOOGLE_SERVICES_JSON_BASE64 GitHub Actions secret and confirm that '
              'the Firebase Android app uses package ID com.aicomp.ai_comp_mobile.',
              textAlign: TextAlign.center,
            ),
          ),
        ),
      ),
    );
  }
}
