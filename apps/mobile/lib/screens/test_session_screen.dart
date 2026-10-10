import 'dart:async';

import 'package:flutter/material.dart';

import '../api/ai_comp_api_client.dart';
import '../models/preparation_models.dart';
import 'test_result_screen.dart';

class TestSessionScreen extends StatefulWidget {
  const TestSessionScreen({
    required this.api,
    required this.initialSession,
    required this.title,
    required this.focusConceptIds,
    super.key,
  });

  final AiCompApiClient api;
  final TestSessionSnapshot initialSession;
  final String title;
  final List<String> focusConceptIds;

  @override
  State<TestSessionScreen> createState() => _TestSessionScreenState();
}

class _TestSessionScreenState extends State<TestSessionScreen> {
  TestSessionSnapshot? _session;
  CurrentQuestion? _question;
  String? _selectedOptionKey;
  String? _error;
  double _remainingSeconds = 0;
  bool _loading = true;
  bool _savingAnswer = false;
  bool _submitting = false;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _session = widget.initialSession;
    _startAndLoad();
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  Future<void> _startAndLoad() async {
    try {
      final session = widget.initialSession.status == 'IN_PROGRESS'
          ? await widget.api.getSession(widget.initialSession.sessionId)
          : await widget.api.startSession(widget.initialSession.sessionId);
      if (!mounted) return;
      setState(() {
        _session = session;
        _loading = false;
        _error = null;
      });
      _setTimer(session.remainingSeconds ?? 0);
      await _loadQuestion();
    } on ApiException catch (error) {
      _showError(error.message);
    } catch (_) {
      _showError('Test start nahi hua. Connection check karke wapas try karein.');
    }
  }

  void _setTimer(double seconds) {
    _timer?.cancel();
    _remainingSeconds = seconds < 0 ? 0 : seconds;
    if (mounted) setState(() {});
    _timer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (!mounted) {
        timer.cancel();
        return;
      }
      if (_remainingSeconds <= 1) {
        timer.cancel();
        setState(() => _remainingSeconds = 0);
        _submit(expired: true);
      } else {
        setState(() => _remainingSeconds -= 1);
      }
    });
  }

  Future<void> _loadQuestion() async {
    final session = _session;
    if (session == null) return;
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final question = await widget.api.getCurrentQuestion(session.sessionId);
      if (!mounted) return;
      setState(() {
        _question = question;
        _selectedOptionKey = question.selectedOptionKey;
        _loading = false;
      });
      _setTimer(question.remainingSeconds);
    } on ApiException catch (error) {
      _showError(error.message);
    } catch (_) {
      _showError('Question load nahi hua. Dobara try karein.');
    }
  }

  Future<void> _saveAnswer() async {
    final session = _session;
    final question = _question;
    final selected = _selectedOptionKey;
    if (session == null || question == null || selected == null || _savingAnswer) {
      return;
    }
    setState(() {
      _savingAnswer = true;
      _error = null;
    });
    try {
      final updated = await widget.api.submitAnswer(session.sessionId, selected);
      if (!mounted) return;
      setState(() {
        _session = updated;
        _savingAnswer = false;
      });
      await _loadQuestion();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Answer server par save ho gaya.')),
        );
      }
    } on ApiException catch (error) {
      _showError(error.message, answerError: true);
    } catch (_) {
      _showError('Answer save nahi hua. Dobara try karein.', answerError: true);
    }
  }

  Future<void> _navigate(String direction) async {
    final session = _session;
    if (session == null || _loading || _savingAnswer || _submitting) return;
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final updated = await widget.api.navigateQuestion(
        session.sessionId,
        direction: direction,
      );
      if (!mounted) return;
      setState(() => _session = updated);
      await _loadQuestion();
    } on ApiException catch (error) {
      _showError(error.message);
    } catch (_) {
      _showError('Question navigation nahi ho saki.');
    }
  }

  Future<void> _submit({bool expired = false}) async {
    final session = _session;
    if (session == null || _submitting || _savingAnswer || (!expired && _loading)) return;
    if (!expired) {
      final confirmed = await showDialog<bool>(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text('Submit test?'),
          content: const Text(
            'Submit karne ke baad answer review aur result khul jayega.',
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(false),
              child: const Text('Continue test'),
            ),
            FilledButton(
              onPressed: () => Navigator.of(context).pop(true),
              child: const Text('Submit'),
            ),
          ],
        ),
      );
      if (confirmed != true || !mounted) return;
    }
    setState(() {
      _submitting = true;
      _loading = true;
      _error = null;
    });
    _timer?.cancel();
    try {
      final submitted = await widget.api.submitSession(session.sessionId);
      if (!mounted) return;
      await Navigator.of(context).pushReplacement<void, void>(
        MaterialPageRoute<void>(
          builder: (_) => TestResultScreen(
            api: widget.api,
            submitted: submitted,
            title: widget.title,
          ),
        ),
      );
    } on ApiException catch (error) {
      _showError(error.message);
    } catch (_) {
      _showError('Result save ya load nahi hua. Submit dobara try karein.');
    } finally {
      if (mounted) {
        setState(() {
          _submitting = false;
          _loading = false;
        });
      }
    }
  }

  void _showError(String message, {bool answerError = false}) {
    if (!mounted) return;
    setState(() {
      _loading = false;
      _savingAnswer = false;
      _submitting = false;
      _error = message;
    });
    if (answerError) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(message)),
      );
    }
  }

  String _formatTime(double seconds) {
    final total = seconds.ceil().clamp(0, 86400);
    final minutes = total ~/ 60;
    final remaining = total % 60;
    return '${minutes.toString().padLeft(2, '0')}:${remaining.toString().padLeft(2, '0')}';
  }

  @override
  Widget build(BuildContext context) {
    final session = _session;
    final question = _question;
    final answeredCount = session?.answeredQuestionCount ?? 0;
    final total = session?.questionCount ?? widget.initialSession.questionCount;
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.title, maxLines: 1, overflow: TextOverflow.ellipsis),
        actions: [
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 12),
            child: Center(
              child: Chip(
                avatar: const Icon(Icons.timer_outlined, size: 18),
                label: Text(_formatTime(_remainingSeconds)),
              ),
            ),
          ),
        ],
      ),
      body: SafeArea(
        child: _loading && question == null
            ? const Center(child: CircularProgressIndicator())
            : ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  if (widget.focusConceptIds.isNotEmpty) ...[
                    Text('Focus: ${widget.focusConceptIds.join(', ')}'),
                    const SizedBox(height: 8),
                  ],
                  LinearProgressIndicator(
                    value: total > 0 ? (answeredCount / total).clamp(0.0, 1.0) : 0,
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Question ${question?.questionNumber ?? session?.currentQuestionNumber ?? 1} of $total · Answered $answeredCount',
                    style: Theme.of(context).textTheme.titleSmall,
                  ),
                  const SizedBox(height: 16),
                  if (_error != null) _InlineError(message: _error!),
                  if (question != null) ...[
                    Card(
                      child: Padding(
                        padding: const EdgeInsets.all(18),
                        child: Text(
                          question.stem,
                          style: Theme.of(context).textTheme.titleLarge,
                        ),
                      ),
                    ),
                    const SizedBox(height: 12),
                    for (final option in question.options)
                      Card(
                        child: RadioListTile<String>(
                          value: option.key,
                          groupValue: _selectedOptionKey,
                          onChanged: _remainingSeconds <= 0 || _savingAnswer
                              ? null
                              : (value) {
                                  if (value == null) return;
                                  setState(() => _selectedOptionKey = value);
                                  _saveAnswer();
                                },
                          title: Text(option.text),
                          subtitle: Text('Option ${option.key}'),
                        ),
                      ),
                    const SizedBox(height: 8),
                    if (_savingAnswer) ...[
                      const LinearProgressIndicator(),
                      const SizedBox(height: 8),
                      const Text('Answer save ho raha hai...'),
                    ],
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        Expanded(
                          child: OutlinedButton(
                            onPressed: _loading || question.questionNumber <= 1
                                ? null
                                : () => _navigate('previous'),
                            child: const Text('Previous'),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: OutlinedButton.icon(
                            onPressed: _loading ? null : () => _navigate('review'),
                            icon: Icon(
                              question.reviewMarked ? Icons.bookmark : Icons.bookmark_border,
                            ),
                            label: Text(question.reviewMarked ? 'Unmark review' : 'Review later'),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: FilledButton(
                            onPressed: _loading ||
                                    question.questionNumber >= question.questionCount
                                ? null
                                : () => _navigate('next'),
                            child: const Text('Next'),
                          ),
                        ),
                      ],
                    ),
                  ],
                  const SizedBox(height: 20),
                  FilledButton.icon(
                    onPressed: _submitting || _savingAnswer || _loading
                        ? null
                        : () => _submit(),
                    icon: const Icon(Icons.check_circle_outline),
                    label: Text(_submitting ? 'Submitting...' : 'Submit test'),
                  ),
                  if (_remainingSeconds <= 0) ...[
                    const SizedBox(height: 8),
                    const Text('Time complete. Test result submit ho raha hai.'),
                  ],
                  if (_loading) const LinearProgressIndicator(),
                ],
              ),
      ),
    );
  }
}

class _InlineError extends StatelessWidget {
  const _InlineError({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.only(bottom: 12),
        child: Text(
          message,
          style: TextStyle(color: Theme.of(context).colorScheme.error),
        ),
      );
}
