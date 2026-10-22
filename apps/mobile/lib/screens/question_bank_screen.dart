import 'package:flutter/material.dart';

import '../api/ai_comp_api_client.dart';
import '../models/preparation_models.dart';

class QuestionBankScreen extends StatelessWidget {
  const QuestionBankScreen({
    super.key,
    required this.api,
    required this.subjectId,
  });

  final AiCompApiClient api;
  final String subjectId;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('$subjectId — Topics')),
      body: FutureBuilder<List<QuestionBankTopic>>(
        future: api.getQuestionBankTopics(subjectId, limit: 100),
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return const _QuestionBankMessage(
              icon: Icons.cloud_off_outlined,
              title: 'Topics could not be loaded',
              message: 'Refresh later or check whether the server has the topic catalogue and migration installed.',
            );
          }
          final topics = snapshot.data ?? const <QuestionBankTopic>[];
          if (topics.isEmpty) {
            return const _QuestionBankMessage(
              icon: Icons.menu_book_outlined,
              title: 'No topics are mapped yet',
              message: 'This subject exists in the catalogue, but its topic mapping has not been populated yet.',
            );
          }
          return ListView.separated(
            padding: const EdgeInsets.all(16),
            itemCount: topics.length,
            separatorBuilder: (_, __) => const SizedBox(height: 8),
            itemBuilder: (context, index) {
              final topic = topics[index];
              final path = <String>[
                if (topic.topic != null && topic.topic!.isNotEmpty) topic.topic!,
                if (topic.subtopic != null && topic.subtopic!.isNotEmpty) topic.subtopic!,
              ].join(' • ');
              return Card(
                child: ListTile(
                  leading: const CircleAvatar(child: Icon(Icons.topic_outlined)),
                  title: Text(topic.label),
                  subtitle: Text(
                    '${path.isEmpty ? topic.subject : path}\n'
                    '${topic.verifiedOneLinerCount} verified one-liner Q&A',
                  ),
                  isThreeLine: true,
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () {
                    Navigator.of(context).push<void>(
                      MaterialPageRoute(
                        builder: (_) => TopicQuestionBankDetailScreen(
                          api: api,
                          topic: topic,
                        ),
                      ),
                    );
                  },
                ),
              );
            },
          );
        },
      ),
    );
  }
}

class TopicQuestionBankDetailScreen extends StatefulWidget {
  const TopicQuestionBankDetailScreen({
    super.key,
    required this.api,
    required this.topic,
  });

  final AiCompApiClient api;
  final QuestionBankTopic topic;

  @override
  State<TopicQuestionBankDetailScreen> createState() =>
      _TopicQuestionBankDetailScreenState();
}

class _TopicQuestionBankDetailScreenState
    extends State<TopicQuestionBankDetailScreen> {
  late Future<List<TopicOneLinerItem>> _oneLiners;
  late Future<List<PreviousYearQuestion>> _previousQuestions;

  @override
  void initState() {
    super.initState();
    _reload();
  }

  void _reload() {
    _oneLiners = widget.api.getTopicOneLiners(widget.topic.conceptId, limit: 100);
    _previousQuestions = widget.api.getPreviousYearQuestions(
      widget.topic.conceptId,
      subjectId: widget.topic.subject,
      limit: 100,
    );
  }

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 2,
      child: Scaffold(
        appBar: AppBar(
          title: Text(widget.topic.label),
          bottom: const TabBar(
            tabs: [
              Tab(icon: Icon(Icons.short_text), text: 'One-Liner Q&A'),
              Tab(icon: Icon(Icons.history_edu), text: 'Previous Year'),
            ],
          ),
        ),
        body: TabBarView(
          children: [
            _buildOneLiners(),
            _buildPreviousQuestions(),
          ],
        ),
      ),
    );
  }

  Widget _buildOneLiners() {
    return FutureBuilder<List<TopicOneLinerItem>>(
      future: _oneLiners,
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Center(child: CircularProgressIndicator());
        }
        if (snapshot.hasError) {
          return const _QuestionBankMessage(
            icon: Icons.cloud_off_outlined,
            title: 'One-liners unavailable',
            message: 'Verified one-liner Q&A could not be loaded. Try refreshing later.',
          );
        }
        final items = snapshot.data ?? const <TopicOneLinerItem>[];
        if (items.isEmpty) {
          return const _QuestionBankMessage(
            icon: Icons.sticky_note_2_outlined,
            title: 'One-liners are not populated yet',
            message: 'No verified direct question-and-answer items have been added for this topic. This does not mean the topic is fully covered.',
          );
        }
        return ListView.separated(
          padding: const EdgeInsets.all(16),
          itemCount: items.length,
          separatorBuilder: (_, __) => const SizedBox(height: 10),
          itemBuilder: (context, index) {
            final item = items[index];
            return Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Q${index + 1}. ${item.questionText}',
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                    const SizedBox(height: 8),
                    Text('Answer: ${item.answerText}'),
                    const SizedBox(height: 8),
                    Text(
                      'Verified source evidence: ${item.sourceEvidence}',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                    if (item.sourceUrl != null) ...[
                      const SizedBox(height: 4),
                      SelectableText(
                        'Source: ${item.sourceUrl}',
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                    ],
                  ],
                ),
              ),
            );
          },
        );
      },
    );
  }

  Widget _buildPreviousQuestions() {
    return FutureBuilder<List<PreviousYearQuestion>>(
      future: _previousQuestions,
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Center(child: CircularProgressIndicator());
        }
        if (snapshot.hasError) {
          return const _QuestionBankMessage(
            icon: Icons.cloud_off_outlined,
            title: 'Previous-year questions unavailable',
            message: 'Verified historical questions could not be loaded. Try refreshing later.',
          );
        }
        final items = snapshot.data ?? const <PreviousYearQuestion>[];
        if (items.isEmpty) {
          return const _QuestionBankMessage(
            icon: Icons.history_edu,
            title: 'No verified previous-paper questions yet',
            message: 'Only questions backed by a verified official paper and its matched official answer key appear here. Unverified answers are not guessed.',
          );
        }
        return ListView.separated(
          padding: const EdgeInsets.all(16),
          itemCount: items.length,
          separatorBuilder: (_, __) => const SizedBox(height: 10),
          itemBuilder: (context, index) {
            final item = items[index];
            final shiftText = item.examShift == null || item.examShift!.isEmpty
                ? ''
                : ' • Shift ${item.examShift}';
            return Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '${item.examName} • ${item.examYear}$shiftText • Q${item.examQuestionNumber}',
                      style: Theme.of(context).textTheme.labelLarge,
                    ),
                    const SizedBox(height: 12),
                    Text(item.stem, style: Theme.of(context).textTheme.titleMedium),
                    const SizedBox(height: 8),
                    for (final option in item.options)
                      Padding(
                        padding: const EdgeInsets.symmetric(vertical: 3),
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            SizedBox(
                              width: 28,
                              child: Text(
                                '${option.key}.',
                                style: TextStyle(
                                  fontWeight: option.key.toUpperCase() ==
                                          item.correctOptionKey.toUpperCase()
                                      ? FontWeight.bold
                                      : FontWeight.normal,
                                ),
                              ),
                            ),
                            Expanded(child: Text(option.text)),
                          ],
                        ),
                      ),
                    const Divider(height: 24),
                    Text(
                      'Verified answer: ${item.correctOptionKey}. ${item.correctOptionText}',
                      style: TextStyle(
                        color: Theme.of(context).colorScheme.primary,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 6),
                    Text(item.explanation, style: Theme.of(context).textTheme.bodySmall),
                    const SizedBox(height: 8),
                    Text(
                      'Verified appearances: ${item.verifiedAppearanceCount}',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                    SelectableText(
                      'Official paper: ${item.sourceUrl}\n'
                      'Official answer key: ${item.answerKeySourceUrl}',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  ],
                ),
              ),
            );
          },
        );
      },
    );
  }
}

class _QuestionBankMessage extends StatelessWidget {
  const _QuestionBankMessage({
    required this.icon,
    required this.title,
    required this.message,
  });

  final IconData icon;
  final String title;
  final String message;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Center(
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(28),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 40, color: theme.colorScheme.onSurfaceVariant),
            const SizedBox(height: 12),
            Text(title, style: theme.textTheme.titleMedium, textAlign: TextAlign.center),
            const SizedBox(height: 8),
            Text(message, textAlign: TextAlign.center),
          ],
        ),
      ),
    );
  }
}
