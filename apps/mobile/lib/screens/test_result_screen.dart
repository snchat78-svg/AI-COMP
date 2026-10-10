import 'package:flutter/material.dart';

import '../api/ai_comp_api_client.dart';
import '../models/preparation_models.dart';

class TestResultScreen extends StatefulWidget {
  const TestResultScreen({
    required this.api,
    required this.submitted,
    required this.title,
    super.key,
  });

  final AiCompApiClient api;
  final SubmittedTest submitted;
  final String title;

  @override
  State<TestResultScreen> createState() => _TestResultScreenState();
}

class _TestResultScreenState extends State<TestResultScreen> {
  AnswerReview? _review;
  String? _reviewError;
  bool _loadingReview = true;

  @override
  void initState() {
    super.initState();
    unawaited(_loadReview());
  }

  Future<void> _loadReview() async {
    try {
      final review = await widget.api.getAnswerReview(widget.submitted.result.sessionId);
      if (!mounted) return;
      setState(() {
        _review = review;
        _loadingReview = false;
        _reviewError = null;
      });
    } on ApiException catch (error) {
      if (!mounted) return;
      setState(() {
        _loadingReview = false;
        _reviewError = error.message;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _loadingReview = false;
        _reviewError = 'Answer review abhi load nahi hua.';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final result = widget.submitted.result;
    final theme = Theme.of(context);
    final percent = result.percentage.clamp(0.0, 100.0);
    return Scaffold(
      appBar: AppBar(title: const Text('Test result')),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Card(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  children: [
                    Text(widget.title, style: theme.textTheme.titleLarge, textAlign: TextAlign.center),
                    const SizedBox(height: 20),
                    SizedBox(
                      width: 140,
                      height: 140,
                      child: Stack(
                        fit: StackFit.expand,
                        children: [
                          CircularProgressIndicator(
                            value: percent / 100,
                            strokeWidth: 10,
                            backgroundColor: theme.colorScheme.surfaceContainerHighest,
                          ),
                          Center(
                            child: Text(
                              '${percent.toStringAsFixed(1)}%',
                              style: theme.textTheme.headlineSmall,
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 20),
                    Row(
                      children: [
                        Expanded(child: _ScoreMetric(label: 'Correct', value: result.correctAnswers.toString())),
                        Expanded(child: _ScoreMetric(label: 'Incorrect', value: result.incorrectAnswers.toString())),
                        Expanded(child: _ScoreMetric(label: 'Skipped', value: result.unattemptedQuestions.toString())),
                      ],
                    ),
                    const SizedBox(height: 12),
                    Text(
                      'Score: ${result.rawScore.toStringAsFixed(2)} / ${result.maxScore.toStringAsFixed(2)}',
                      style: theme.textTheme.titleMedium,
                    ),
                    Text('Status: ${result.status}'),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
            Text('Answer review', style: theme.textTheme.titleLarge),
            const SizedBox(height: 8),
            if (_loadingReview)
              const Center(child: CircularProgressIndicator())
            else if (_reviewError != null)
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(_reviewError!, style: TextStyle(color: theme.colorScheme.error)),
                  TextButton.icon(
                    onPressed: _loadReview,
                    icon: const Icon(Icons.refresh),
                    label: const Text('Retry review'),
                  ),
                ],
              )
            else if (_review?.questions.isEmpty ?? true)
              const Text('Is test ke liye answer review items nahi mile.')
            else
              for (final question in _review!.questions)
                _ReviewCard(question: question),
            const SizedBox(height: 24),
            FilledButton.icon(
              onPressed: () => Navigator.of(context).pop(),
              icon: const Icon(Icons.dashboard_outlined),
              label: const Text('Back to dashboard'),
            ),
          ],
        ),
      ),
    );
  }
}

class _ScoreMetric extends StatelessWidget {
  const _ScoreMetric({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) => Column(
        children: [
          Text(value, style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 4),
          Text(label, style: Theme.of(context).textTheme.bodySmall),
        ],
      );
}

class _ReviewCard extends StatelessWidget {
  const _ReviewCard({required this.question});

  final ReviewQuestion question;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final color = switch (question.outcome) {
      'CORRECT' => theme.colorScheme.primary,
      'INCORRECT' => theme.colorScheme.error,
      _ => theme.colorScheme.onSurfaceVariant,
    };
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    'Question ${question.number}',
                    style: theme.textTheme.titleMedium,
                  ),
                ),
                Text(
                  question.outcome,
                  style: TextStyle(color: color, fontWeight: FontWeight.w600),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(question.stem),
            const SizedBox(height: 12),
            Text('Your answer: ${question.selectedOptionText ?? 'Not attempted'}'),
            Text('Correct answer: ${question.correctOptionText ?? 'Not available'}'),
            if (question.explanation.isNotEmpty) ...[
              const SizedBox(height: 8),
              Text('Explanation', style: theme.textTheme.labelLarge),
              Text(question.explanation),
            ],
          ],
        ),
      ),
    );
  }
}
