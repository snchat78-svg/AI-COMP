import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';

import '../api/ai_comp_api_client.dart';
import '../models/preparation_models.dart';
import 'test_session_screen.dart';
import 'question_bank_screen.dart';

class PreparationHomeScreen extends StatefulWidget {
  const PreparationHomeScreen({super.key, this.firebaseUser});

  final User? firebaseUser;

  @override
  State<PreparationHomeScreen> createState() => _PreparationHomeScreenState();
}

class _PreparationHomeScreenState extends State<PreparationHomeScreen> {
  final _baseUrlController = TextEditingController(
    text: const String.fromEnvironment(
      'AI_COMP_API_BASE_URL',
      defaultValue: 'https://ai-comp-api.onrender.com',
    ),
  );
  final _learnerIdController = TextEditingController(
    text: const String.fromEnvironment('AI_COMP_LEARNER_ID'),
  );
  final _tokenController = TextEditingController();
  final _questionCountController = TextEditingController(text: '20');
  final _durationMinutesController = TextEditingController(text: '30');

  AiCompApiClient? _api;
  LearnerAnalytics? _analytics;
  ResultsSummary? _summary;
  QuestionBankReadiness? _questionBankReadiness;
  String? _questionBankReadinessError;
  List<QuestionBankSubject> _subjects = const [];
  String? _selectedSubjectId;
  String? _subjectError;
  List<TestHistoryItem> _recentSessions = const [];
  bool _loading = false;
  String? _error;
  bool _hideToken = true;

  bool get _connected => _api != null;

  @override
  void initState() {
    super.initState();
    final user = widget.firebaseUser;
    if (user != null) _learnerIdController.text = user.uid;
  }

  @override
  void dispose() {
    _api?.close();
    _baseUrlController.dispose();
    _learnerIdController.dispose();
    _tokenController.dispose();
    _questionCountController.dispose();
    _durationMinutesController.dispose();
    super.dispose();
  }

  Future<void> _connectAndRefresh() async {
    final baseUrl = _baseUrlController.text.trim();
    final user = widget.firebaseUser;
    final learnerId = user?.uid ?? _learnerIdController.text.trim();
    final token = _tokenController.text.trim();
    if (baseUrl.isEmpty || learnerId.isEmpty || (user == null && token.isEmpty)) {
      setState(() {
        _error = user == null
            ? 'API URL, learner ID, and access token are required.'
            : 'The API base URL is required.';
      });
      return;
    }

    setState(() {
      _loading = true;
      _error = null;
    });
    AiCompApiClient? candidate;
    try {
      candidate = AiCompApiClient(
        baseUrl: baseUrl,
        learnerId: learnerId,
        accessToken: token,
        accessTokenProvider: user == null ? null : () => user.getIdToken(),
      );
      final analytics = await candidate.getAnalytics();
      final summary = await candidate.getResultsSummary();
      final sessions = await candidate.getSessions(limit: 8);
      List<QuestionBankSubject> subjects = const [];
      String? subjectError;
      try {
        subjects = await candidate.getQuestionBankSubjects();
      } on ApiException {
        subjectError = 'Subject catalogue is not available on this API version yet.';
      }
      final selectedSubjectId = subjects.any((item) => item.subjectId == _selectedSubjectId)
          ? _selectedSubjectId
          : (subjects.isEmpty ? null : subjects.first.subjectId);
      QuestionBankReadiness? readiness;
      String? readinessError;
      try {
        readiness = selectedSubjectId == null
            ? await candidate.getQuestionBankReadiness()
            : await candidate.getQuestionBankReadiness(subjectId: selectedSubjectId);
      } on ApiException {
        readinessError = 'Question-bank status could not be checked. Refresh after the server update completes.';
      }
      final previous = _api;
      _api = candidate;
      candidate = null;
      previous?.close();
      if (!mounted) return;
      setState(() {
        _analytics = analytics;
        _summary = summary;
        _recentSessions = sessions;
        _subjects = subjects;
        _selectedSubjectId = selectedSubjectId;
        _subjectError = subjectError;
        _questionBankReadiness = readiness;
        _questionBankReadinessError = readinessError;
        _loading = false;
        _error = null;
      });
    } on ApiException catch (error) {
      candidate?.close();
      _setError(_friendlyError(error));
    } on ArgumentError catch (error) {
      candidate?.close();
      _setError(error.message?.toString() ?? 'API configuration is invalid.');
    } catch (_) {
      candidate?.close();
      _setError('Could not connect. Check the API URL, access token, and network connection.');
    }
  }

  Future<void> _signOut() async {
    await FirebaseAuth.instance.signOut();
  }

  Future<void> _refreshDashboard() async {
    final api = _api;
    if (api == null) return;
    try {
      final analytics = await api.getAnalytics();
      final summary = await api.getResultsSummary();
      final sessions = await api.getSessions(limit: 8);
      List<QuestionBankSubject> subjects = const [];
      String? subjectError;
      try {
        subjects = await api.getQuestionBankSubjects();
      } on ApiException {
        subjectError = 'Subject catalogue is not available on this API version yet.';
      }
      final selectedSubjectId = subjects.any((item) => item.subjectId == _selectedSubjectId)
          ? _selectedSubjectId
          : (subjects.isEmpty ? null : subjects.first.subjectId);
      QuestionBankReadiness? readiness;
      String? readinessError;
      try {
        readiness = selectedSubjectId == null
            ? await api.getQuestionBankReadiness()
            : await api.getQuestionBankReadiness(subjectId: selectedSubjectId);
      } on ApiException {
        readinessError = 'Question-bank status could not be checked. Refresh after the server update completes.';
      }
      if (!mounted) return;
      setState(() {
        _analytics = analytics;
        _summary = summary;
        _recentSessions = sessions;
        _subjects = subjects;
        _selectedSubjectId = selectedSubjectId;
        _subjectError = subjectError;
        _questionBankReadiness = readiness;
        _questionBankReadinessError = readinessError;
      });
    } on ApiException catch (error) {
      _setError(_friendlyError(error));
    } catch (_) {
      _setError('Could not load the latest progress. Refresh and try again.');
    }
  }

  Future<void> _browseQuestionBank() async {
    final api = _api;
    final subjectId = _selectedSubjectId;
    if (api == null || subjectId == null || subjectId.isEmpty) {
      _setError('Connect to the API and select a subject before browsing topics.');
      return;
    }
    await Navigator.of(context).push<void>(
      MaterialPageRoute(
        builder: (_) => QuestionBankScreen(api: api, subjectId: subjectId),
      ),
    );
  }

  Future<void> _selectQuestionBankSubject(String? subjectId) async {
    if (subjectId == null || subjectId.trim().isEmpty) return;
    final api = _api;
    setState(() {
      _selectedSubjectId = subjectId;
      _questionBankReadiness = null;
      _questionBankReadinessError = null;
    });
    if (api == null) return;
    try {
      final readiness = await api.getQuestionBankReadiness(subjectId: subjectId);
      if (!mounted) return;
      setState(() {
        _questionBankReadiness = readiness;
        _questionBankReadinessError = null;
      });
    } on ApiException {
      if (!mounted) return;
      setState(() {
        _questionBankReadiness = null;
        _questionBankReadinessError = 'Question-bank status for this subject could not be checked.';
      });
    }
  }

  Future<void> _startAdaptivePractice() async {
    final api = _api;
    if (api == null) {
      _setError('Connect to the API first.');
      return;
    }
    final subjectId = _selectedSubjectId;
    if (subjectId == null || subjectId.isEmpty) {
      _setError('Select a subject before creating a test.');
      return;
    }
    // An empty existing MCQ pool does not block a new generation attempt:
    // the server can derive alternatives from verified one-liners/history.
    final questionCount = int.tryParse(_questionCountController.text.trim());
    final durationMinutes = int.tryParse(_durationMinutesController.text.trim());
    if (questionCount == null || questionCount < 1 || questionCount > 500) {
      _setError('Enter between 1 and 500 questions.');
      return;
    }
    if (durationMinutes == null ||
        durationMinutes < 1 ||
        durationMinutes > 1440) {
      _setError('Enter a duration between 1 and 1,440 minutes.');
      return;
    }

    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      // Generate source-grounded alternatives first; the API persists the
      // selected subject/count/time and the existing test engine then builds the session.
      final generation = await api.generateSubjectPractice(
        subjectId: subjectId,
        questionCount: questionCount,
        durationSeconds: durationMinutes * 60,
      );
      final session = await api.createSession();
      if (!mounted) return;
      setState(() => _loading = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            'Generated ${generation.generatedAlternativeCount} verified alternative MCQs. '
            'Starting a ${session.questionCount}-question test for $subjectId.',
          ),
        ),
      );
      await Navigator.of(context).push<void>(
        MaterialPageRoute(
          builder: (_) => TestSessionScreen(
            api: api,
            initialSession: session,
            title: '$subjectId practice test',
            focusConceptIds: const <String>[],
          ),
        ),
      );
      if (mounted) {
        await _refreshDashboard();
      }
    } on ApiException catch (error) {
      _setError(_friendlyError(error));
    } catch (_) {
      _setError('Could not create a practice test. Refresh the dashboard to check whether your progress was saved.');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _resumeSession(TestHistoryItem item) async {
    final api = _api;
    if (api == null || _loading) return;
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final session = await api.getSession(item.sessionId);
      if (!mounted) return;
      setState(() => _loading = false);
      await Navigator.of(context).push<void>(
        MaterialPageRoute<void>(
          builder: (_) => TestSessionScreen(
            api: api,
            initialSession: session,
            title: item.title,
            focusConceptIds: session.focusConceptIds,
          ),
        ),
      );
      if (mounted) await _refreshDashboard();
    } on ApiException catch (error) {
      _setError(_friendlyError(error));
    } catch (_) {
      _setError('Could not resume the saved test session. Please try again.');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  String _friendlyError(ApiException error) {
    switch (error.code) {
      case 'AUTHENTICATION_REQUIRED':
        return 'Authentication is required. Provide a valid access token for this server.';
      case 'LEARNER_SCOPE_MISMATCH':
        return 'This learner ID is not authorized for the current token.';
      case 'NO_ADAPTIVE_PRACTICE_SIGNAL':
        return 'Complete a test first to enable adaptive recommendations.';
      case 'NO_ELIGIBLE_ADAPTIVE_QUESTIONS':
        return 'There are no eligible verified questions for the recommended topics yet.';
      case 'NO_ELIGIBLE_PREPARATION_QUESTIONS':
        return 'No eligible verified questions are available yet. Check this subject\'s reviewed one-liners and official answer-key history.';
      case 'QUESTION_GENERATION_NOT_CONFIGURED':
        return 'AI question generation is not configured on the server. The server owner must add the model API key as a secret; never put it in the app.';
      case 'QUESTION_BANK_SOURCE_UNAVAILABLE':
        return 'Verified one-liners or previous-paper answers could not be loaded for this subject. Refresh and try again later.';
      case 'QUESTION_GENERATION_FAILED':
        return 'New MCQs could not pass generation and answer verification. No test was started; try again after the server issue is resolved.';
      case 'NO_VERIFIED_ALTERNATIVE_MCQS':
        return 'No new four-option MCQs passed answer verification. The app will not create a test from unverified questions.';
      case 'NO_ELIGIBLE_SUBJECT_QUESTIONS':
        return 'The selected subject has no eligible four-option MCQs yet. Check topic mapping and source verification.';
      case 'NETWORK_UNAVAILABLE':
        return 'Could not reach the API. Check the base URL and network connection.';
      default:
        return error.message;
    }
  }

  void _setError(String message) {
    if (!mounted) return;
    setState(() {
      _loading = false;
      _error = message;
    });
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(
        title: const Text('AI-COMP Preparation'),
        actions: [
          IconButton(
            tooltip: 'Refresh progress',
            onPressed: _loading || !_connected ? null : _refreshDashboard,
            icon: const Icon(Icons.refresh),
          ),
          if (widget.firebaseUser != null)
            IconButton(
              tooltip: 'Sign out',
              onPressed: _loading ? null : _signOut,
              icon: const Icon(Icons.logout),
            ),
        ],
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Text(
              'Your preparation, guided by your progress',
              style: theme.textTheme.headlineSmall,
            ),
            const SizedBox(height: 6),
            Text(
              'Build your next practice test around weak topics and previous mistakes.',
              style: theme.textTheme.bodyMedium,
            ),
            const SizedBox(height: 20),
            _buildConnectionCard(theme),
            if (_error != null) ...[
              const SizedBox(height: 12),
              _ErrorPanel(message: _error!),
            ],
            if (_connected &&
                (_questionBankReadiness != null || _questionBankReadinessError != null)) ...[
              const SizedBox(height: 16),
              _buildQuestionBankReadinessCard(theme),
            ],
            const SizedBox(height: 16),
            _buildAdaptiveTestCard(theme),
            const SizedBox(height: 16),
            _buildProgressCard(theme),
            const SizedBox(height: 16),
            _buildWeakTopics(theme),
            const SizedBox(height: 16),
            _buildRecentSessions(theme),
            const SizedBox(height: 24),
            Text(
              'Security: the access token is kept only in memory on this screen and is not saved to disk.',
              style: theme.textTheme.bodySmall,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildConnectionCard(ThemeData theme) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('API connection', style: theme.textTheme.titleMedium),
            const SizedBox(height: 12),
            TextField(
              controller: _baseUrlController,
              keyboardType: TextInputType.url,
              autocorrect: false,
              decoration: const InputDecoration(
                labelText: 'API base URL',
                hintText: 'https://your-api.example.com',
                prefixIcon: Icon(Icons.link),
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 12),
            if (widget.firebaseUser != null)
              ListTile(
                contentPadding: EdgeInsets.zero,
                leading: const Icon(Icons.verified_user_outlined),
                title: const Text('Firebase account'),
                subtitle: Text(widget.firebaseUser!.email ?? widget.firebaseUser!.uid),
              ),
            if (widget.firebaseUser == null) ...[
              TextField(
                controller: _learnerIdController,
                autocorrect: false,
                decoration: const InputDecoration(
                  labelText: 'Learner ID',
                  prefixIcon: Icon(Icons.person_outline),
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: _tokenController,
                obscureText: _hideToken,
                autocorrect: false,
                enableSuggestions: false,
                decoration: InputDecoration(
                  labelText: 'Access token',
                  helperText: 'Enter a token accepted by this API server.',
                  prefixIcon: const Icon(Icons.key_outlined),
                  suffixIcon: IconButton(
                    tooltip: _hideToken ? 'Show token' : 'Hide token',
                    onPressed: () => setState(() => _hideToken = !_hideToken),
                    icon: Icon(_hideToken ? Icons.visibility : Icons.visibility_off),
                  ),
                  border: const OutlineInputBorder(),
                ),
              ),
            ],
            const SizedBox(height: 12),
            SizedBox(
              width: double.infinity,
              child: OutlinedButton.icon(
                onPressed: _loading ? null : _connectAndRefresh,
                icon: const Icon(Icons.cloud_done_outlined),
                label: Text(_connected ? 'Reconnect and refresh' : 'Connect & load progress'),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildQuestionBankReadinessCard(ThemeData theme) {
    final readiness = _questionBankReadiness;
    if (readiness == null) {
      return Card(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              const Icon(Icons.info_outline),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  _questionBankReadinessError ??
                      'Question-bank status has not been checked yet.',
                ),
              ),
            ],
          ),
        ),
      );
    }
    final available = readiness.eligibleQuestionCount;
    final empty = available == 0;
    final scopeLabel = readiness.subjectId == null
        ? ''
        : ' for ${readiness.subjectId}';
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  empty ? Icons.info_outline : Icons.verified_outlined,
                  color: empty
                      ? theme.colorScheme.onSurfaceVariant
                      : theme.colorScheme.primary,
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    empty ? 'Question bank status' : 'Verified question bank ready',
                    style: theme.textTheme.titleMedium,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              '$available eligible questions available$scopeLabel '
              '(${readiness.verifiedHistoryQuestionCount} from verified exam history, '
              '${readiness.acceptedGeneratedQuestionCount} accepted generated questions).',
            ),
            if (empty) ...[
              const SizedBox(height: 8),
              const Text(
                'Past-paper questions enter the verified pool only after an official paper '
                'is paired with its verified official answer key. The subject-test flow can '
                'try to generate new alternatives from reviewed one-liners and verified past-paper '
                'answers; it still stops when source evidence or answer verification is insufficient.',
              ),
            ],
            const SizedBox(height: 8),
            Text(
              'Counts are bounded by the configured pool limit of ${readiness.questionPoolLimit}.',
              style: theme.textTheme.bodySmall,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildAdaptiveTestCard(ThemeData theme) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Practice test', style: theme.textTheme.titleMedium),
            const SizedBox(height: 8),
            const Text('Choose a subject first, set the question count and time, then start a test. Questions are taken only from the selected subject and the existing verified/accepted four-option MCQ pool.'),
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(
              value: _subjects.any((item) => item.subjectId == _selectedSubjectId)
                  ? _selectedSubjectId
                  : null,
              decoration: const InputDecoration(
                labelText: 'Subject',
                border: OutlineInputBorder(),
                prefixIcon: Icon(Icons.menu_book_outlined),
              ),
              items: _subjects
                  .map(
                    (subject) => DropdownMenuItem<String>(
                      value: subject.subjectId,
                      child: Text(
                        '${subject.subjectLabel} (${subject.conceptCount} topics)',
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                  )
                  .toList(growable: false),
              onChanged: _loading || _subjects.isEmpty
                  ? null
                  : _selectQuestionBankSubject,
            ),
            if (_subjectError != null) ...[
              const SizedBox(height: 6),
              Text(_subjectError!, style: theme.textTheme.bodySmall),
            ],
            const SizedBox(height: 8),
            SizedBox(
              width: double.infinity,
              child: OutlinedButton.icon(
                onPressed: _loading || !_connected || _selectedSubjectId == null
                    ? null
                    : _browseQuestionBank,
                icon: const Icon(Icons.menu_book_outlined),
                label: const Text('Browse topics, One-Liners & Previous Papers'),
              ),
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _questionCountController,
                    keyboardType: TextInputType.number,
                    decoration: const InputDecoration(
                      labelText: 'Questions',
                      border: OutlineInputBorder(),
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: TextField(
                    controller: _durationMinutesController,
                    keyboardType: TextInputType.number,
                    decoration: const InputDecoration(
                      labelText: 'Minutes',
                      border: OutlineInputBorder(),
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            if (_loading) const LinearProgressIndicator(),
            const SizedBox(height: 8),
            SizedBox(
              width: double.infinity,
              child: FilledButton.icon(
                onPressed: _loading ||
                        !_connected ||
                        _selectedSubjectId == null ||
                        _subjects.isEmpty
                    ? null
                    : _startAdaptivePractice,
                icon: const Icon(Icons.play_arrow),
                label: Text(
                  !_connected
                      ? 'Connect to create test'
                      : _subjects.isEmpty
                          ? 'No subjects available'
                          : _selectedSubjectId == null
                              ? 'Select a subject'
                              : 'Generate MCQs and start test',
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildProgressCard(ThemeData theme) {
    final summary = _summary;
    final analytics = _analytics;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Learning progress', style: theme.textTheme.titleMedium),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: _Metric(
                    label: 'Completed tests',
                    value: '${summary?.completedTestCount ?? analytics?.completedTestCount ?? 0}',
                  ),
                ),
                Expanded(
                  child: _Metric(
                    label: 'Average score',
                    value: '${(summary?.averagePercentage ?? analytics?.averagePercentage ?? 0).toStringAsFixed(1)}%',
                  ),
                ),
                Expanded(
                  child: _Metric(
                    label: 'Best score',
                    value: '${(summary?.bestPercentage ?? 0).toStringAsFixed(1)}%',
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildWeakTopics(ThemeData theme) {
    final topics = _analytics?.weakTopics ?? const <WeakTopicSummary>[];
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Focus topics', style: theme.textTheme.titleMedium),
            const SizedBox(height: 8),
            if (!_connected)
              const Text('Connect to the API to view your progress.')
            else if (topics.isEmpty)
              const Text('No weak topics have been reported in your saved history.')
            else
              for (final topic in topics.take(5))
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  leading: const CircleAvatar(child: Icon(Icons.menu_book_outlined)),
                  title: Text(topic.conceptId),
                  subtitle: Text('${topic.trend} · ${topic.performance}'),
                  trailing: Text('${topic.accuracyPercentage.toStringAsFixed(0)}%'),
                ),
          ],
        ),
      ),
    );
  }

  Widget _buildRecentSessions(ThemeData theme) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Recent tests', style: theme.textTheme.titleMedium),
            const SizedBox(height: 8),
            if (!_connected)
              const Text('Recent results will appear here.')
            else if (_recentSessions.isEmpty)
              const Text('You do not have any test sessions yet.')
            else
              for (final item in _recentSessions)
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  leading: const Icon(Icons.assignment_turned_in_outlined),
                  title: Text(item.title),
                  subtitle: Text(item.status),
                  trailing: item.status == 'IN_PROGRESS' || item.status == 'CREATED'
                      ? TextButton(
                          onPressed: _loading ? null : () => _resumeSession(item),
                          child: const Text('Continue'),
                        )
                      : Text(
                          item.percentage == null
                              ? '—'
                              : '${item.percentage!.toStringAsFixed(1)}%',
                          style: theme.textTheme.titleSmall,
                        ),
                ),
          ],
        ),
      ),
    );
  }
}

class _Metric extends StatelessWidget {
  const _Metric({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) => Column(
        children: [
          Text(value, style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 4),
          Text(label, textAlign: TextAlign.center, style: Theme.of(context).textTheme.bodySmall),
        ],
      );
}

class _ErrorPanel extends StatelessWidget {
  const _ErrorPanel({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: Theme.of(context).colorScheme.errorContainer,
          borderRadius: BorderRadius.circular(12),
        ),
        child: Text(
          message,
          style: TextStyle(color: Theme.of(context).colorScheme.onErrorContainer),
        ),
      );
}
