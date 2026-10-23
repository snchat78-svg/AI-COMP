import 'package:flutter/material.dart';

import '../api/ai_comp_api_client.dart';
import '../models/preparation_models.dart';

class QuestionBankScreen extends StatefulWidget {
  const QuestionBankScreen({
    super.key,
    required this.api,
    required this.subjectId,
    this.examId,
  });

  final AiCompApiClient api;
  final String subjectId;
  final String? examId;

  @override
  State<QuestionBankScreen> createState() => _QuestionBankScreenState();
}

class _QuestionBankScreenState extends State<QuestionBankScreen> {
  final TextEditingController _searchController = TextEditingController();
  late Future<List<QuestionBankTopic>> _topicsFuture;
  String _searchQuery = '';

  @override
  void initState() {
    super.initState();
    _topicsFuture = _loadAllTopics();
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  Future<List<QuestionBankTopic>> _loadAllTopics() async {
    const pageSize = 100;
    const maximumTopics = 10000;
    final topics = <QuestionBankTopic>[];
    var offset = 0;
    while (offset <= 100000 && topics.length < maximumTopics) {
      final page = await widget.api.getQuestionBankTopics(
        widget.subjectId,
        examId: widget.examId,
        limit: pageSize,
        offset: offset,
      );
      if (page.isEmpty) break;
      topics.addAll(page);
      offset += page.length;
      if (page.length < pageSize) break;
    }
    return topics;
  }

  void _refreshTopics() {
    setState(() {
      _topicsFuture = _loadAllTopics();
    });
  }

  bool _matchesSearch(QuestionBankTopic topic) {
    if (_searchQuery.isEmpty) return true;
    final searchable = <String>[
      topic.label,
      topic.subject,
      if (topic.topic != null) topic.topic!,
      if (topic.subtopic != null) topic.subtopic!,
      topic.conceptId,
    ].join(' ').toLowerCase();
    return searchable.contains(_searchQuery);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.examId == null
            ? '${widget.subjectId} — Topics'
            : '${widget.subjectId} — Topics · ${widget.examId}'),
        actions: [
          IconButton(
            tooltip: 'Refresh topics',
            onPressed: _refreshTopics,
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
            child: TextField(
              controller: _searchController,
              onChanged: (value) => setState(() => _searchQuery = value.trim().toLowerCase()),
              textInputAction: TextInputAction.search,
              decoration: InputDecoration(
                labelText: 'Search topics and subtopics',
                hintText: 'For example, Luni River or Sandhi',
                prefixIcon: const Icon(Icons.search),
                suffixIcon: _searchQuery.isEmpty
                    ? null
                    : IconButton(
                        tooltip: 'Clear search',
                        onPressed: () {
                          _searchController.clear();
                          setState(() => _searchQuery = '');
                        },
                        icon: const Icon(Icons.clear),
                      ),
              ),
            ),
          ),
          Expanded(
            child: FutureBuilder<List<QuestionBankTopic>>(
              future: _topicsFuture,
              builder: (context, snapshot) {
                if (snapshot.connectionState == ConnectionState.waiting) {
                  return const Center(child: CircularProgressIndicator());
                }
                if (snapshot.hasError) {
                  return _QuestionBankMessage(
                    icon: Icons.cloud_off_outlined,
                    title: 'Topics could not be loaded',
                    message: 'Refresh later or check whether the server has the topic catalogue and migration installed.',
                    actionLabel: 'Retry',
                    onAction: _refreshTopics,
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
                final filtered = topics.where(_matchesSearch).toList(growable: false);
                final visibleVerifiedCount = filtered.fold<int>(
                  0,
                  (sum, topic) => sum + topic.verifiedOneLinerCount,
                );
                return Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Padding(
                      padding: const EdgeInsets.fromLTRB(16, 4, 16, 8),
                      child: Text(
                        '${filtered.length} of ${topics.length} topics • '
                        '$visibleVerifiedCount verified one-liner Q&A available',
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                    ),
                    const Padding(
                      padding: EdgeInsets.fromLTRB(16, 0, 16, 12),
                      child: Text(
                        'Topic-list presence is not proof of full syllabus or question coverage. Only source-reviewed Q&A count as verified.',
                      ),
                    ),
                    if (filtered.isEmpty)
                      const Expanded(
                        child: _QuestionBankMessage(
                          icon: Icons.search_off,
                          title: 'No matching topics',
                          message: 'Try another topic, subtopic or keyword.',
                        ),
                      )
                    else
                      Expanded(
                        child: ListView.separated(
                          padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
                          itemCount: filtered.length,
                          separatorBuilder: (_, __) => const SizedBox(height: 8),
                          itemBuilder: (context, index) {
                            final topic = filtered[index];
                            final path = <String>[
                              if (topic.topic != null && topic.topic!.isNotEmpty) topic.topic!,
                              if (topic.subtopic != null && topic.subtopic!.isNotEmpty)
                                topic.subtopic!,
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
                                        api: widget.api,
                                        topic: topic,
                                      ),
                                    ),
                                  );
                                },
                              ),
                            );
                          },
                        ),
                      ),
                  ],
                );
              },
            ),
          ),
        ],
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
  static const int _pageSize = 100;

  List<TopicOneLinerItem> _oneLiners = const [];
  List<PreviousYearQuestion> _previousQuestions = const [];
  int _oneLinerOffset = 0;
  int _previousOffset = 0;
  bool _oneLinersLoading = false;
  bool _previousLoading = false;
  bool _oneLinersLoaded = false;
  bool _previousLoaded = false;
  bool _oneLinersHasMore = false;
  bool _previousHasMore = false;
  String? _oneLinersError;
  String? _previousError;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _loadOneLiners(reset: true);
      _loadPreviousQuestions(reset: true);
    });
  }

  Future<void> _reload() async {
    await Future.wait([
      _loadOneLiners(reset: true),
      _loadPreviousQuestions(reset: true),
    ]);
  }

  Future<void> _loadOneLiners({bool reset = false}) async {
    if (_oneLinersLoading) return;
    final offset = reset ? 0 : _oneLinerOffset;
    setState(() {
      _oneLinersLoading = true;
      if (reset) {
        _oneLiners = const [];
        _oneLinerOffset = 0;
        _oneLinersLoaded = false;
        _oneLinersHasMore = false;
        _oneLinersError = null;
      }
    });
    try {
      final page = await widget.api.getTopicOneLiners(
        widget.topic.conceptId,
        limit: _pageSize,
        offset: offset,
      );
      if (!mounted) return;
      setState(() {
        _oneLiners = reset ? page : [..._oneLiners, ...page];
        _oneLinerOffset = offset + page.length;
        _oneLinersHasMore = page.length == _pageSize;
        _oneLinersLoading = false;
        _oneLinersLoaded = true;
        _oneLinersError = null;
      });
    } on ApiException {
      if (!mounted) return;
      setState(() {
        _oneLinersLoading = false;
        _oneLinersLoaded = _oneLiners.isNotEmpty;
        _oneLinersError = 'Verified one-liners could not be loaded. Try again.';
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _oneLinersLoading = false;
        _oneLinersLoaded = _oneLiners.isNotEmpty;
        _oneLinersError = 'Verified one-liners could not be loaded. Check the connection and retry.';
      });
    }
  }

  Future<void> _loadPreviousQuestions({bool reset = false}) async {
    if (_previousLoading) return;
    final offset = reset ? 0 : _previousOffset;
    setState(() {
      _previousLoading = true;
      if (reset) {
        _previousQuestions = const [];
        _previousOffset = 0;
        _previousLoaded = false;
        _previousHasMore = false;
        _previousError = null;
      }
    });
    try {
      final page = await widget.api.getPreviousYearQuestionPage(
        widget.topic.conceptId,
        subjectId: widget.topic.subject,
        limit: _pageSize,
        offset: offset,
      );
      if (!mounted) return;
      setState(() {
        _previousQuestions =
            reset ? page.items : [..._previousQuestions, ...page.items];
        _previousOffset = offset + page.items.length;
        _previousHasMore = page.pagination.hasMore;
        _previousLoading = false;
        _previousLoaded = true;
        _previousError = null;
      });
    } on ApiException {
      if (!mounted) return;
      setState(() {
        _previousLoading = false;
        _previousLoaded = _previousQuestions.isNotEmpty;
        _previousError = 'Verified historical questions could not be loaded. Try again.';
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _previousLoading = false;
        _previousLoaded = _previousQuestions.isNotEmpty;
        _previousError = 'Verified historical questions could not be loaded. Check the connection and retry.';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 2,
      child: Scaffold(
        appBar: AppBar(
          title: Text(widget.topic.label),
          actions: [
            IconButton(
              tooltip: 'Refresh topic content',
              onPressed: _reload,
              icon: const Icon(Icons.refresh),
            ),
          ],
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
    if (!_oneLinersLoaded && _oneLinersLoading) {
      return const Center(child: CircularProgressIndicator());
    }
    if (_oneLinersError != null && _oneLiners.isEmpty) {
      return _QuestionBankMessage(
        icon: Icons.cloud_off_outlined,
        title: 'One-liners unavailable',
        message: _oneLinersError!,
        actionLabel: 'Retry',
        onAction: () => _loadOneLiners(reset: true),
      );
    }
    if (_oneLinersLoaded && _oneLiners.isEmpty) {
      return const _QuestionBankMessage(
        icon: Icons.sticky_note_2_outlined,
        title: 'One-liners are not populated yet',
        message: 'No verified direct question-and-answer items have been added for this topic. This does not mean the topic is fully covered.',
      );
    }
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 10, 16, 6),
          child: Align(
            alignment: Alignment.centerLeft,
            child: Text(
              '${_oneLiners.length} verified one-liner Q&A loaded',
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ),
        ),
        if (_oneLinersError != null)
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Text(_oneLinersError!),
          ),
        Expanded(
          child: ListView.separated(
            padding: const EdgeInsets.all(16),
            itemCount: _oneLiners.length,
            separatorBuilder: (_, __) => const SizedBox(height: 10),
            itemBuilder: (context, index) {
              final item = _oneLiners[index];
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
          ),
        ),
        if (_oneLinersHasMore || _oneLinersLoading)
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
            child: _oneLinersLoading
                ? const CircularProgressIndicator()
                : OutlinedButton.icon(
                    onPressed: () => _loadOneLiners(),
                    icon: const Icon(Icons.expand_more),
                    label: const Text('Load more one-liners'),
                  ),
          ),
      ],
    );
  }

  Widget _buildPreviousQuestions() {
    if (!_previousLoaded && _previousLoading) {
      return const Center(child: CircularProgressIndicator());
    }
    if (_previousError != null && _previousQuestions.isEmpty) {
      return _QuestionBankMessage(
        icon: Icons.cloud_off_outlined,
        title: 'Previous-year questions unavailable',
        message: _previousError!,
        actionLabel: 'Retry',
        onAction: () => _loadPreviousQuestions(reset: true),
      );
    }
    if (_previousLoaded && _previousQuestions.isEmpty) {
      return const _QuestionBankMessage(
        icon: Icons.history_edu,
        title: 'No verified previous-paper questions yet',
        message: 'Only questions backed by a verified official paper and its matched official answer key appear here. Unverified answers are not guessed.',
      );
    }
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 10, 16, 6),
          child: Align(
            alignment: Alignment.centerLeft,
            child: Text(
              '${_previousQuestions.length} verified previous-paper questions loaded',
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ),
        ),
        if (_previousError != null)
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Text(_previousError!),
          ),
        Expanded(
          child: ListView.separated(
            padding: const EdgeInsets.all(16),
            itemCount: _previousQuestions.length,
            separatorBuilder: (_, __) => const SizedBox(height: 10),
            itemBuilder: (context, index) {
              final item = _previousQuestions[index];
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
          ),
        ),
        if (_previousHasMore || _previousLoading)
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
            child: _previousLoading
                ? const CircularProgressIndicator()
                : OutlinedButton.icon(
                    onPressed: () => _loadPreviousQuestions(),
                    icon: const Icon(Icons.expand_more),
                    label: const Text('Load more previous-year questions'),
                  ),
          ),
      ],
    );
  }
}

class _QuestionBankMessage extends StatelessWidget {
  const _QuestionBankMessage({
    required this.icon,
    required this.title,
    required this.message,
    this.actionLabel,
    this.onAction,
  });

  final IconData icon;
  final String title;
  final String message;
  final String? actionLabel;
  final VoidCallback? onAction;

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
            if (actionLabel != null && onAction != null) ...[
              const SizedBox(height: 16),
              FilledButton.tonal(
                onPressed: onAction,
                child: Text(actionLabel!),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
