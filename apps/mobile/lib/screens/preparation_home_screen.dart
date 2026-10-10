import 'package:flutter/material.dart';

import '../api/ai_comp_api_client.dart';
import '../models/preparation_models.dart';
import 'test_session_screen.dart';

class PreparationHomeScreen extends StatefulWidget {
  const PreparationHomeScreen({super.key});

  @override
  State<PreparationHomeScreen> createState() => _PreparationHomeScreenState();
}

class _PreparationHomeScreenState extends State<PreparationHomeScreen> {
  final _baseUrlController = TextEditingController(
    text: const String.fromEnvironment('AI_COMP_API_BASE_URL'),
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
  List<TestHistoryItem> _recentResults = const [];
  bool _loading = false;
  String? _error;
  bool _hideToken = true;

  bool get _connected => _api != null;

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
    final learnerId = _learnerIdController.text.trim();
    final token = _tokenController.text.trim();
    if (baseUrl.isEmpty || learnerId.isEmpty || token.isEmpty) {
      setState(() {
        _error = 'API URL, learner ID aur access token teeno bharna zaroori hai.';
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
      );
      final analytics = await candidate.getAnalytics();
      final summary = await candidate.getResultsSummary();
      final results = await candidate.getResults(limit: 5);
      final previous = _api;
      _api = candidate;
      candidate = null;
      previous?.close();
      if (!mounted) return;
      setState(() {
        _analytics = analytics;
        _summary = summary;
        _recentResults = results;
        _loading = false;
        _error = null;
      });
    } on ApiException catch (error) {
      candidate?.close();
      _setError(_friendlyError(error));
    } on ArgumentError catch (error) {
      candidate?.close();
      _setError(error.message?.toString() ?? 'API configuration sahi nahi hai.');
    } catch (_) {
      candidate?.close();
      _setError('Connect nahi ho saka. API URL, token aur network check karein.');
    }
  }

  Future<void> _refreshDashboard() async {
    final api = _api;
    if (api == null) return;
    try {
      final analytics = await api.getAnalytics();
      final summary = await api.getResultsSummary();
      final results = await api.getResults(limit: 5);
      if (!mounted) return;
      setState(() {
        _analytics = analytics;
        _summary = summary;
        _recentResults = results;
      });
    } on ApiException catch (error) {
      _setError(_friendlyError(error));
    } catch (_) {
      _setError('Latest progress load nahi hua. Refresh karke dobara try karein.');
    }
  }

  Future<void> _startAdaptivePractice() async {
    final api = _api;
    if (api == null) {
      _setError('Pehle API se connect karein.');
      return;
    }
    final questionCount = int.tryParse(_questionCountController.text.trim());
    final durationMinutes = int.tryParse(_durationMinutesController.text.trim());
    if (questionCount == null || questionCount < 1 || questionCount > 500) {
      _setError('Questions ki sankhya 1 se 500 ke beech honi chahiye.');
      return;
    }
    if (durationMinutes == null ||
        durationMinutes < 1 ||
        durationMinutes > 1440) {
      _setError('Duration 1 se 1440 minutes ke beech honi chahiye.');
      return;
    }

    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final recommendation = await api.recommendAdaptivePractice(
        questionCount: questionCount,
        durationSeconds: durationMinutes * 60,
      );
      final session = await api.createSession();
      if (!mounted) return;
      setState(() => _loading = false);
      if (recommendation.questionCountAdjusted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              'Question pool ke hisaab se ${recommendation.questionCount} questions ka test banega.',
            ),
          ),
        );
      }
      await Navigator.of(context).push<void>(
        MaterialPageRoute(
          builder: (_) => TestSessionScreen(
            api: api,
            initialSession: session,
            title: recommendation.title,
            focusConceptIds: recommendation.focusConceptIds,
          ),
        ),
      );
      if (mounted) {
        await _refreshDashboard();
      }
    } on ApiException catch (error) {
      _setError(_friendlyError(error));
    } catch (_) {
      _setError('Adaptive test create nahi ho saka. Progress save hui hai ya nahi, dashboard refresh karke check karein.');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  String _friendlyError(ApiException error) {
    switch (error.code) {
      case 'AUTHENTICATION_REQUIRED':
        return 'Authentication required: server ke liye sahi access token dein.';
      case 'LEARNER_SCOPE_MISMATCH':
        return 'Yeh learner ID current token se authorized nahi hai.';
      case 'NO_ADAPTIVE_PRACTICE_SIGNAL':
        return 'Adaptive recommendation ke liye pehle ek test complete karein.';
      case 'NO_ELIGIBLE_ADAPTIVE_QUESTIONS':
        return 'Recommended topics ke liye abhi eligible verified questions nahi hain.';
      case 'NETWORK_UNAVAILABLE':
        return 'API tak pahunch nahi hui. Base URL aur network check karein.';
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
        title: const Text('AI-COMP तैयारी'),
        actions: [
          IconButton(
            tooltip: 'Refresh progress',
            onPressed: _loading || !_connected ? null : _refreshDashboard,
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Text(
              'आपकी तैयारी, आपकी प्रगति के अनुसार',
              style: theme.textTheme.headlineSmall,
            ),
            const SizedBox(height: 6),
            Text(
              'Weak topics aur pichhli galtiyon se agla practice test banayein.',
              style: theme.textTheme.bodyMedium,
            ),
            const SizedBox(height: 20),
            _buildConnectionCard(theme),
            if (_error != null) ...[
              const SizedBox(height: 12),
              _ErrorPanel(message: _error!),
            ],
            const SizedBox(height: 16),
            _buildAdaptiveTestCard(theme),
            const SizedBox(height: 16),
            _buildProgressCard(theme),
            const SizedBox(height: 16),
            _buildWeakTopics(theme),
            const SizedBox(height: 16),
            _buildRecentResults(theme),
            const SizedBox(height: 24),
            Text(
              'Security: access token sirf is screen ke memory mein rakha gaya hai; disk par save nahi hota.',
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
                helperText: 'Server ke configured authentication ke mutabik token dein.',
                prefixIcon: const Icon(Icons.key_outlined),
                suffixIcon: IconButton(
                  tooltip: _hideToken ? 'Show token' : 'Hide token',
                  onPressed: () => setState(() => _hideToken = !_hideToken),
                  icon: Icon(_hideToken ? Icons.visibility : Icons.visibility_off),
                ),
                border: const OutlineInputBorder(),
              ),
            ),
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

  Widget _buildAdaptiveTestCard(ThemeData theme) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Adaptive practice test', style: theme.textTheme.titleMedium),
            const SizedBox(height: 8),
            const Text('Server saved test history se focus topics choose karega.'),
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
                onPressed: _loading || !_connected ? null : _startAdaptivePractice,
                icon: const Icon(Icons.play_arrow),
                label: const Text('Create and start test'),
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
              const Text('Progress dekhne ke liye API connect karein.')
            else if (topics.isEmpty)
              const Text('Saved history mein koi weak topic report nahi hua.')
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

  Widget _buildRecentResults(ThemeData theme) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Recent tests', style: theme.textTheme.titleMedium),
            const SizedBox(height: 8),
            if (!_connected)
              const Text('Recent results yahan dikhai denge.')
            else if (_recentResults.isEmpty)
              const Text('Abhi koi completed test nahi hai.')
            else
              for (final item in _recentResults)
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  leading: const Icon(Icons.assignment_turned_in_outlined),
                  title: Text(item.title),
                  subtitle: Text(item.status),
                  trailing: Text(
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
