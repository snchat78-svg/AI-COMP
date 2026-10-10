import 'package:flutter/material.dart';

import 'screens/preparation_home_screen.dart';

void main() {
  runApp(const AiCompMobileApp());
}

class AiCompMobileApp extends StatelessWidget {
  const AiCompMobileApp({super.key});

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
      home: const PreparationHomeScreen(),
    );
  }
}
