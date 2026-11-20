import 'package:flutter/material.dart';

import '../api/ai_comp_api_client.dart';
import '../data/local_question_bank_drafts.dart';
import '../localization/question_bank_labels.dart';
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

  int _pendingCount(QuestionBankTopic topic) {
    final localCount = LocalQuestionBankDrafts.countForConcept(topic.conceptId);
    return topic.pendingOneLinerCount > localCount
        ? topic.pendingOneLinerCount
        : localCount;
  }

  bool _matchesSearch(QuestionBankTopic topic) {
    if (_searchQuery.isEmpty) return true;
    final searchable = <String>[
      topic.label,
      topic.subject,
      if (topic.topic != null) topic.topic!,
      if (topic.subtopic != null) topic.subtopic!,
      questionBankHindiLabel(topic.label),
      questionBankHindiLabel(topic.subject),
      if (topic.topic != null) questionBankHindiLabel(topic.topic!),
      if (topic.subtopic != null) questionBankHindiLabel(topic.subtopic!),
      topic.conceptId,
    ].join(' ').toLowerCase();
    return searchable.contains(_searchQuery);
  }

  Map<String, List<QuestionBankTopic>> _groupTopicsByMainTopic(
    List<QuestionBankTopic> topics,
  ) {
    final groups = <String, List<QuestionBankTopic>>{};
    for (final topic in topics) {
      final mainTopic = topic.topic?.trim().isNotEmpty == true
          ? topic.topic!.trim()
          : topic.subject;
      groups.putIfAbsent(mainTopic, () => <QuestionBankTopic>[]).add(topic);
    }
    return groups;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.examId == null
            ? '${questionBankHindiLabel(widget.subjectId)} — विषय'
            : '${questionBankHindiLabel(widget.subjectId)} — विषय · ${widget.examId}'),
        actions: [
          IconButton(
            tooltip: 'विषय ताज़ा करें',
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
                labelText: 'विषय और उप-विषय खोजें',
                hintText: 'जैसे लूणी नदी या संधि',
                prefixIcon: const Icon(Icons.search),
                suffixIcon: _searchQuery.isEmpty
                    ? null
                    : IconButton(
                        tooltip: 'खोज हटाएँ',
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
                    title: 'विषय लोड नहीं हो सके',
                    message: 'बाद में पुनः प्रयास करें। सर्वर पर विषय-सूची और आवश्यक डेटाबेस परिवर्तन लागू होने चाहिए।',
                    actionLabel: 'पुनः प्रयास करें',
                    onAction: _refreshTopics,
                  );
                }
                final topics = snapshot.data ?? const <QuestionBankTopic>[];
                if (topics.isEmpty) {
                  return const _QuestionBankMessage(
                    icon: Icons.menu_book_outlined,
                    title: 'अभी कोई विषय सूचीबद्ध नहीं है',
                    message: 'यह विषय सूची में है, लेकिन इसके अध्याय और उप-विषय अभी उपलब्ध नहीं कराए गए हैं।',
                  );
                }
                final filtered = topics.where(_matchesSearch).toList(growable: false);
                final groups = _groupTopicsByMainTopic(filtered);
                final visibleVerifiedCount = filtered.fold<int>(
                  0,
                  (sum, topic) => sum + topic.verifiedOneLinerCount,
                );
                final visiblePendingCount = filtered.fold<int>(
                  0,
                  (sum, topic) => sum + _pendingCount(topic),
                );
                return Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Padding(
                      padding: const EdgeInsets.fromLTRB(16, 4, 16, 8),
                      child: Text(
                        '${filtered.length} / ${topics.length} उप-विषय • '
                        '${groups.length} मुख्य अध्याय • '
                        '$visibleVerifiedCount सत्यापित • $visiblePendingCount समीक्षा बाकी',
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                    ),
                    const Padding(
                      padding: EdgeInsets.fromLTRB(16, 0, 16, 12),
                      child: Text(
                        'मुख्य अध्याय खोलकर उसके सभी उप-विषय देखें। केवल स्वतंत्र स्रोत-समीक्षा से स्वीकृत प्रश्न ही सत्यापित माने जाते हैं; विषय-सूची में नाम होना पूर्ण कवरेज का प्रमाण नहीं है।',
                      ),
                    ),
                    if (filtered.isEmpty)
                      const Expanded(
                        child: _QuestionBankMessage(
                          icon: Icons.search_off,
                          title: 'कोई मिलता-जुलता विषय नहीं मिला',
                          message: 'दूसरा अध्याय, स्थल, उप-विषय या शब्द खोजें।',
                        ),
                      )
                    else
                      Expanded(
                        child: ListView.separated(
                          padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
                          itemCount: groups.length,
                          separatorBuilder: (_, __) => const SizedBox(height: 8),
                          itemBuilder: (context, index) {
                            final group = groups.entries.elementAt(index);
                            final childTopics = group.value;
                            final groupVerifiedCount = childTopics.fold<int>(
                              0,
                              (sum, topic) => sum + topic.verifiedOneLinerCount,
                            );
                            final groupPendingCount = childTopics.fold<int>(
                              0,
                              (sum, topic) => sum + _pendingCount(topic),
                            );
                            return Card(
                              child: ExpansionTile(
                                key: PageStorageKey<String>(
                                  'question-bank-main-topic-${group.key}',
                                ),
                                initiallyExpanded:
                                    _searchQuery.isNotEmpty || groups.length == 1,
                                leading: const CircleAvatar(
                                  child: Icon(Icons.menu_book_outlined),
                                ),
                                title: Text(questionBankHindiLabel(group.key)),
                                subtitle: Text(
                                  '${childTopics.length} उप-विषय • '
                                  '$groupVerifiedCount सत्यापित • $groupPendingCount समीक्षा बाकी',
                                ),
                                children: [
                                  for (final topic in childTopics)
                                    ListTile(
                                      contentPadding: const EdgeInsets.only(
                                        left: 24,
                                        right: 16,
                                      ),
                                      leading: const Icon(Icons.account_tree_outlined),
                                      title: Text(questionBankHindiLabel(topic.subtopic ?? topic.label)),
                                      subtitle: Text(
                                        '${questionBankHindiLabel(topic.label)} • '
                                        '${topic.verifiedOneLinerCount} सत्यापित • ${_pendingCount(topic)} समीक्षा बाकी',
                                      ),
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
                                ],
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
  List<TopicOneLinerItem> _pendingOneLiners = const [];
  List<TopicOneLinerItem> _allPendingOneLiners = const [];
  List<PreviousYearQuestion> _previousQuestions = const [];
  int _oneLinerOffset = 0;
  int _pendingOneLinerOffset = 0;
  int _previousOffset = 0;
  bool _oneLinersLoading = false;
  bool _pendingOneLinersLoading = false;
  bool _previousLoading = false;
  bool _oneLinersLoaded = false;
  bool _pendingOneLinersLoaded = false;
  bool _previousLoaded = false;
  bool _oneLinersHasMore = false;
  bool _pendingOneLinersHasMore = false;
  bool _pendingUsingLocalFallback = false;
  bool _previousHasMore = false;
  String? _oneLinersError;
  String? _pendingOneLinersError;
  String? _previousError;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _loadOneLiners(reset: true);
      _loadPendingOneLiners(reset: true);
      _loadPreviousQuestions(reset: true);
    });
  }

  Future<void> _reload() async {
    await Future.wait([
      _loadOneLiners(reset: true),
      _loadPendingOneLiners(reset: true),
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
        _oneLinersLoaded = true;
        _oneLinersError = 'सत्यापित प्रश्न लोड नहीं हो सके। पुनः प्रयास करें।';
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _oneLinersLoading = false;
        _oneLinersLoaded = _oneLiners.isNotEmpty;
        _oneLinersError = 'सत्यापित प्रश्न लोड नहीं हो सके। इंटरनेट कनेक्शन जाँचकर पुनः प्रयास करें।';
      });
    }
  }

  Future<void> _loadPendingOneLiners({bool reset = false}) async {
    if (_pendingOneLinersLoading) return;

    if (!reset) {
      final page = _allPendingOneLiners
          .skip(_pendingOneLinerOffset)
          .take(_pageSize)
          .toList(growable: false);
      if (!mounted) return;
      setState(() {
        _pendingOneLiners = [..._pendingOneLiners, ...page];
        _pendingOneLinerOffset += page.length;
        _pendingOneLinersHasMore =
            _pendingOneLinerOffset < _allPendingOneLiners.length;
      });
      return;
    }

    setState(() {
      _pendingOneLinersLoading = true;
      _pendingOneLiners = const [];
      _allPendingOneLiners = const [];
      _pendingOneLinerOffset = 0;
      _pendingOneLinersLoaded = false;
      _pendingOneLinersHasMore = false;
      _pendingUsingLocalFallback = false;
      _pendingOneLinersError = null;
    });

    List<TopicOneLinerItem> localItems = const [];
    try {
      localItems = await LocalQuestionBankDrafts.loadForConcept(
        widget.topic.conceptId,
      );
    } catch (_) {
      // The server can still provide the review-pending records.
    }
    localItems = localItems.toList()
      ..sort((a, b) => a.oneLinerId.compareTo(b.oneLinerId));

    // Make the APK-bundled copy visible before waiting on any network request.
    // This keeps the screen usable when migration 0030 is not live yet.
    if (!mounted) return;
    setState(() {
      _allPendingOneLiners = localItems;
      _pendingOneLiners = localItems.take(_pageSize).toList(growable: false);
      _pendingOneLinerOffset = _pendingOneLiners.length;
      _pendingOneLinersHasMore =
          _pendingOneLinerOffset < _allPendingOneLiners.length;
      _pendingUsingLocalFallback = localItems.isNotEmpty;
      _pendingOneLinersLoading = false;
      _pendingOneLinersLoaded = true;
      _pendingOneLinersError = null;
    });

    // Fetch all server pages after the local copy is already readable.
    // The server copy wins for duplicate IDs; the asset fills any DB gaps.
    final remoteItems = <TopicOneLinerItem>[];
    var remoteFailed = false;
    var remoteOffset = 0;
    try {
      while (remoteOffset <= 10000) {
        final page = await widget.api.getPendingTopicOneLiners(
          widget.topic.conceptId,
          limit: _pageSize,
          offset: remoteOffset,
          languageCode: 'hi',
        );
        remoteItems.addAll(page);
        remoteOffset += page.length;
        if (page.length < _pageSize) break;
      }
    } catch (_) {
      remoteFailed = true;
    }

    final mergedById = <String, TopicOneLinerItem>{};
    for (final item in localItems) {
      mergedById[item.oneLinerId] = item;
    }
    for (final item in remoteItems) {
      mergedById[item.oneLinerId] = item;
    }
    final mergedItems = mergedById.values.toList()
      ..sort((a, b) => a.oneLinerId.compareTo(b.oneLinerId));
    final remoteIds = remoteItems.map((item) => item.oneLinerId).toSet();
    final usedLocalFallback =
        localItems.any((item) => !remoteIds.contains(item.oneLinerId));

    if (!mounted) return;
    setState(() {
      // Keep already visible rows if the user paged while the server request
      // was running; stable IDs keep page boundaries deterministic.
      final visibleCount = _pendingOneLinerOffset;
      _allPendingOneLiners = mergedItems;
      _pendingOneLiners = mergedItems
          .take(visibleCount)
          .toList(growable: false);
      _pendingOneLinerOffset = _pendingOneLiners.length;
      _pendingOneLinersHasMore =
          _pendingOneLinerOffset < _allPendingOneLiners.length;
      _pendingUsingLocalFallback = usedLocalFallback;
      _pendingOneLinersLoaded = true;
      _pendingOneLinersError =
          mergedItems.isEmpty && remoteFailed && localItems.isEmpty
              ? 'सर्वर और स्थानीय प्रश्न-सूची दोनों लोड नहीं हो सके। पुनः प्रयास करें।'
              : null;
    });
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
        _previousError = 'पिछले वर्षों के सत्यापित प्रश्न लोड नहीं हो सके। पुनः प्रयास करें।';
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _previousLoading = false;
        _previousLoaded = _previousQuestions.isNotEmpty;
        _previousError = 'पिछले वर्षों के सत्यापित प्रश्न लोड नहीं हो सके। कनेक्शन जाँचकर पुनः प्रयास करें।';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 2,
      child: Scaffold(
        appBar: AppBar(
          title: Text(questionBankHindiLabel(widget.topic.subtopic ?? widget.topic.label)),
          actions: [
            IconButton(
              tooltip: 'प्रश्न ताज़ा करें',
              onPressed: _reload,
              icon: const Icon(Icons.refresh),
            ),
          ],
          bottom: const TabBar(
            tabs: [
              Tab(icon: Icon(Icons.short_text), text: 'एक-पंक्ति प्रश्नोत्तर'),
              Tab(icon: Icon(Icons.history_edu), text: 'पिछले वर्षों के प्रश्न'),
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
    final hasAnyLoaded = _oneLinersLoaded || _pendingOneLinersLoaded;
    final hasAnyItems = _oneLiners.isNotEmpty || _pendingOneLiners.isNotEmpty;
    if (!hasAnyLoaded && (_oneLinersLoading || _pendingOneLinersLoading)) {
      return const Center(child: CircularProgressIndicator());
    }
    if (!hasAnyItems && _oneLinersError != null) {
      return _QuestionBankMessage(
        icon: Icons.cloud_off_outlined,
        title: 'सत्यापित प्रश्न लोड नहीं हो सके',
        message: _pendingOneLinersError ??
            'सत्यापित प्रश्न उपलब्ध नहीं हैं। इंटरनेट कनेक्शन जाँचकर पुनः प्रयास करें।',
        actionLabel: 'पुनः प्रयास करें',
        onAction: _reload,
      );
    }
    if (!hasAnyItems && _pendingOneLinersError != null) {
      return _QuestionBankMessage(
        icon: Icons.cloud_off_outlined,
        title: 'AI मसौदे लोड नहीं हो सके',
        message: _pendingOneLinersError!,
        actionLabel: 'पुनः प्रयास करें',
        onAction: _reload,
      );
    }
    if (hasAnyLoaded && !hasAnyItems &&
        _oneLinersLoaded && _pendingOneLinersLoaded &&
        _oneLinersError == null && _pendingOneLinersError == null) {
      return const _QuestionBankMessage(
        icon: Icons.sticky_note_2_outlined,
        title: 'अभी कोई एक-पंक्ति प्रश्न उपलब्ध नहीं है',
        message: 'इस उप-विषय में न सत्यापित प्रश्न हैं, न समीक्षा के लिए AI मसौदे।',
      );
    }
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 10, 16, 6),
          child: Align(
            alignment: Alignment.centerLeft,
            child: Text(
              '${_oneLiners.length} सत्यापित प्रश्न • '
              '${_allPendingOneLiners.length} AI मसौदे (समीक्षा बाकी)',
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ),
        ),
        if (_pendingOneLiners.isNotEmpty)
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 2, 16, 8),
            child: Align(
              alignment: Alignment.centerLeft,
              child: Text(
                'AI मसौदा — समीक्षा बाकी',
                style: Theme.of(context).textTheme.titleSmall?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
              ),
            ),
          ),
        if (_pendingUsingLocalFallback)
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 0, 16, 10),
            child: Container(
              width: double.infinity,
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.secondaryContainer,
                borderRadius: BorderRadius.circular(12),
              ),
              child: const Text(
                'ये प्रश्न APK में सुरक्षित स्थानीय प्रति से दिखाए जा रहे हैं। सर्वर डेटाबेस में आयात होने तक भी आप इन्हें पढ़ सकते हैं; स्वतंत्र समीक्षा अभी बाकी है।',
              ),
            ),
          ),
        if (_pendingOneLiners.isNotEmpty)
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 0, 16, 10),
            child: Container(
              width: double.infinity,
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.secondaryContainer,
                borderRadius: BorderRadius.circular(12),
              ),
              child: const Text(
                'नीचे दिए गए AI मसौदे पढ़ने के लिए उपलब्ध हैं। इनकी स्वतंत्र स्रोत-जाँच बाकी है; इन्हें सत्यापित प्रश्न या पुराने वर्षों के प्रश्न न समझें।',
              ),
            ),
          ),
        if (_oneLinersError != null)
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
            child: Text(_oneLinersError!),
          ),
        if (_pendingOneLinersError != null)
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
            child: Text(_pendingOneLinersError!),
          ),
        Expanded(
          child: ListView.separated(
            padding: const EdgeInsets.all(16),
            itemCount: _oneLiners.length + _pendingOneLiners.length,
            separatorBuilder: (_, __) => const SizedBox(height: 10),
            itemBuilder: (context, index) {
              final item = index < _oneLiners.length
                  ? _oneLiners[index]
                  : _pendingOneLiners[index - _oneLiners.length];
              final isPending = item.verificationStatus != 'VERIFIED';
              return Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        isPending
                            ? 'AI मसौदा — समीक्षा बाकी'
                            : 'सत्यापित प्रश्न',
                        style: Theme.of(context).textTheme.labelLarge?.copyWith(
                              fontWeight: FontWeight.bold,
                              color: isPending
                                  ? Theme.of(context).colorScheme.secondary
                                  : Theme.of(context).colorScheme.primary,
                            ),
                      ),
                      const SizedBox(height: 6),
                      Text(
                        'प्रश्न ${index + 1}. ${item.questionText}',
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      const SizedBox(height: 8),
                      Text('उत्तर: ${item.answerText}'),
                      const SizedBox(height: 8),
                      Text(
                        isPending
                            ? 'स्रोत-सूचक (जाँच बाकी): ${item.sourceEvidence}'
                            : 'सत्यापित स्रोत-साक्ष्य: ${item.sourceEvidence}',
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                      if (item.sourceUrl != null) ...[
                        const SizedBox(height: 4),
                        SelectableText(
                          'स्रोत: ${item.sourceUrl}',
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
            padding: const EdgeInsets.fromLTRB(16, 0, 16, 8),
            child: _oneLinersLoading
                ? const CircularProgressIndicator()
                : OutlinedButton.icon(
                    onPressed: () => _loadOneLiners(),
                    icon: const Icon(Icons.expand_more),
                    label: const Text('और सत्यापित प्रश्न देखें'),
                  ),
          ),
        if (_pendingOneLinersHasMore || _pendingOneLinersLoading)
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
            child: _pendingOneLinersLoading
                ? const CircularProgressIndicator()
                : OutlinedButton.icon(
                    onPressed: () => _loadPendingOneLiners(),
                    icon: const Icon(Icons.expand_more),
                    label: const Text('और AI मसौदे देखें'),
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
        title: 'पिछले वर्षों के प्रश्न उपलब्ध नहीं हैं',
        message: _previousError!,
        actionLabel: 'पुनः प्रयास करें',
        onAction: () => _loadPreviousQuestions(reset: true),
      );
    }
    if (_previousLoaded && _previousQuestions.isEmpty) {
      return const _QuestionBankMessage(
        icon: Icons.history_edu,
        title: 'अभी कोई सत्यापित पुराने प्रश्न उपलब्ध नहीं हैं',
        message: 'यहाँ केवल आधिकारिक प्रश्नपत्र और उससे मेल खाती सत्यापित उत्तर-कुंजी वाले प्रश्न दिखते हैं। अपुष्ट उत्तर अनुमान से नहीं जोड़े जाते।',
      );
    }
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 10, 16, 6),
          child: Align(
            alignment: Alignment.centerLeft,
            child: Text(
              '${_previousQuestions.length} सत्यापित पुराने प्रश्न लोड हुए',
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
                  : ' • पारी ${item.examShift}';
              return Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '${item.examName} • ${item.examYear}$shiftText • प्रश्न ${item.examQuestionNumber}',
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
                        'सत्यापित उत्तर: ${item.correctOptionKey}. ${item.correctOptionText}',
                        style: TextStyle(
                          color: Theme.of(context).colorScheme.primary,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 6),
                      Text(item.explanation, style: Theme.of(context).textTheme.bodySmall),
                      const SizedBox(height: 8),
                      Text(
                        'सत्यापित बार पूछे जाने की संख्या: ${item.verifiedAppearanceCount}',
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                      SelectableText(
                        'आधिकारिक प्रश्नपत्र: ${item.sourceUrl}\n'
                        'आधिकारिक उत्तर-कुंजी: ${item.answerKeySourceUrl}',
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
                    label: const Text('और पुराने प्रश्न देखें'),
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
