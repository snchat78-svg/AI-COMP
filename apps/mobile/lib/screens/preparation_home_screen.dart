import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';

import '../api/ai_comp_api_client.dart';
import '../localization/question_bank_labels.dart';
import '../models/preparation_models.dart';
import 'test_session_screen.dart';
import 'question_bank_screen.dart';
import 'offline_study_library_screen.dart';

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
  List<QuestionBankExamProfile> _examProfiles = const [];
  String? _selectedExamId;
  List<QuestionBankSubject> _examSubjects = const [];
  String? _selectedExamSubjectId;
  String? _examProfileError;
  String? _examSubjectError;
  bool _loadingExamSubjects = false;
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
      List<QuestionBankExamProfile> examProfiles = const [];
      String? examProfileError;
      try {
        examProfiles = await candidate.getQuestionBankExamProfiles();
      } on ApiException {
        examProfileError = 'Official exam profiles are not available on this API version yet.';
      }
      final selectedExamId = examProfiles.any((item) => item.examId == _selectedExamId)
          ? _selectedExamId
          : (examProfiles.isEmpty ? null : examProfiles.first.examId);
      List<QuestionBankSubject> examSubjects = const [];
      String? examSubjectError;
      if (selectedExamId != null) {
        try {
          examSubjects = await candidate.getQuestionBankSubjects(examId: selectedExamId);
        } on ApiException {
          examSubjectError = 'Syllabus-mapped subjects could not be loaded. Refresh after the server update.';
        }
      }
      final selectedExamSubjectId = examSubjects.any((item) => item.subjectId == _selectedExamSubjectId)
          ? _selectedExamSubjectId
          : (examSubjects.isEmpty ? null : examSubjects.first.subjectId);
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
        _examProfiles = examProfiles;
        _selectedExamId = selectedExamId;
        _examSubjects = examSubjects;
        _selectedExamSubjectId = selectedExamSubjectId;
        _examProfileError = examProfileError;
        _examSubjectError = examSubjectError;
        _loadingExamSubjects = false;
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
      List<QuestionBankExamProfile> examProfiles = const [];
      String? examProfileError;
      try {
        examProfiles = await api.getQuestionBankExamProfiles();
      } on ApiException {
        examProfileError = 'Official exam profiles are not available on this API version yet.';
      }
      final selectedExamId = examProfiles.any((item) => item.examId == _selectedExamId)
          ? _selectedExamId
          : (examProfiles.isEmpty ? null : examProfiles.first.examId);
      List<QuestionBankSubject> examSubjects = const [];
      String? examSubjectError;
      if (selectedExamId != null) {
        try {
          examSubjects = await api.getQuestionBankSubjects(examId: selectedExamId);
        } on ApiException {
          examSubjectError = 'Syllabus-mapped subjects could not be loaded. Refresh after the server update.';
        }
      }
      final selectedExamSubjectId = examSubjects.any((item) => item.subjectId == _selectedExamSubjectId)
          ? _selectedExamSubjectId
          : (examSubjects.isEmpty ? null : examSubjects.first.subjectId);
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
        _examProfiles = examProfiles;
        _selectedExamId = selectedExamId;
        _examSubjects = examSubjects;
        _selectedExamSubjectId = selectedExamSubjectId;
        _examProfileError = examProfileError;
        _examSubjectError = examSubjectError;
        _loadingExamSubjects = false;
        _questionBankReadiness = readiness;
        _questionBankReadinessError = readinessError;
      });
    } on ApiException catch (error) {
      _setError(_friendlyError(error));
    } catch (_) {
      _setError('Could not load the latest progress. Refresh and try again.');
    }
  }

  QuestionBankExamProfile? get _selectedExamProfile {
    for (final profile in _examProfiles) {
      if (profile.examId == _selectedExamId) return profile;
    }
    return null;
  }

  Future<void> _selectExamProfile(String? examId) async {
    if (examId == null || examId.trim().isEmpty) return;
    final api = _api;
    setState(() {
      _selectedExamId = examId;
      _examSubjects = const [];
      _selectedExamSubjectId = null;
      _examSubjectError = null;
      _loadingExamSubjects = true;
    });
    if (api == null) {
      setState(() => _loadingExamSubjects = false);
      return;
    }
    try {
      final subjects = await api.getQuestionBankSubjects(examId: examId);
      if (!mounted || _selectedExamId != examId) return;
      setState(() {
        _examSubjects = subjects;
        _selectedExamSubjectId = subjects.isEmpty ? null : subjects.first.subjectId;
        _examSubjectError = null;
        _loadingExamSubjects = false;
      });
    } on ApiException {
      if (!mounted || _selectedExamId != examId) return;
      setState(() {
        _examSubjects = const [];
        _selectedExamSubjectId = null;
        _examSubjectError = 'Syllabus-mapped subjects could not be loaded. Refresh and try again.';
        _loadingExamSubjects = false;
      });
    }
  }

  Future<void> _browseExamQuestionBank() async {
    final api = _api;
    final profile = _selectedExamProfile;
    final subjectId = _selectedExamSubjectId;
    if (api == null || profile == null || !profile.selectionReady ||
        subjectId == null || subjectId.isEmpty) {
      _setError('The selected exam syllabus is not completely reviewed yet. Generic topics are not a substitute for exam-specific coverage.');
      return;
    }
    await Navigator.of(context).push<void>(
      MaterialPageRoute(
        builder: (_) => QuestionBankScreen(
          api: api,
          subjectId: subjectId,
          examId: profile.examId,
        ),
      ),
    );
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
            '${session.questionCount} प्रश्नों की ${questionBankHindiLabel(subjectId)} अभ्यास परीक्षा शुरू हो रही है।',
          ),
        ),
      );
      await Navigator.of(context).push<void>(
        MaterialPageRoute(
          builder: (_) => TestSessionScreen(
            api: api,
            initialSession: session,
            title: '${questionBankHindiLabel(subjectId)} अभ्यास परीक्षा',
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
      backgroundColor: const Color(0xFFF5F7FC),
      appBar: AppBar(
        backgroundColor: const Color(0xFFF5F7FC),
        surfaceTintColor: Colors.transparent,
        title: const Text(
          'AI-COMP Preparation',
          style: TextStyle(fontWeight: FontWeight.w800, letterSpacing: -0.3),
        ),
        actions: [
          IconButton(
            tooltip: 'Refresh progress',
            onPressed: _loading || !_connected ? null : _refreshDashboard,
            icon: const Icon(Icons.refresh_rounded),
          ),
          if (widget.firebaseUser != null)
            IconButton(
              tooltip: 'Sign out',
              onPressed: _loading ? null : _signOut,
              icon: const Icon(Icons.logout_rounded),
            ),
          const SizedBox(width: 4),
        ],
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 28),
          children: [
            _buildDashboardHero(theme),
            const SizedBox(height: 16),
            _buildStudyLibraryCard(theme),
            const SizedBox(height: 16),
            _buildConnectionCard(theme),
            if (_error != null) ...[
              const SizedBox(height: 12),
              _ErrorPanel(message: _error!),
            ],
            if (_connected && _examProfiles.isNotEmpty) ...[
              const SizedBox(height: 16),
              _buildExamSyllabusCard(theme),
            ],
            if (_connected &&
                (_questionBankReadiness != null || _questionBankReadinessError != null)) ...[
              const SizedBox(height: 16),
              _buildQuestionBankReadinessCard(theme),
            ],
            const SizedBox(height: 16),
            _buildProgressCard(theme),
            const SizedBox(height: 16),
            _buildAdaptiveTestCard(theme),
            const SizedBox(height: 16),
            _buildWeakTopics(theme),
            const SizedBox(height: 16),
            _buildRecentSessions(theme),
            const SizedBox(height: 20),
            Text(
              'Security: your access token stays in memory on this screen and is never saved to disk.',
              textAlign: TextAlign.center,
              style: theme.textTheme.bodySmall?.copyWith(
                color: theme.colorScheme.onSurfaceVariant,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildDashboardHero(ThemeData theme) {
    final canBrowse = _connected && _selectedSubjectId != null && !_loading;
    return Container(
      padding: const EdgeInsets.all(22),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(28),
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            Color(0xFF172554),
            Color(0xFF3730A3),
            Color(0xFF6D28D9),
          ],
        ),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF4338CA).withValues(alpha: 0.20),
            blurRadius: 24,
            offset: const Offset(0, 12),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 42,
                height: 42,
                decoration: BoxDecoration(
                  color: Colors.white.withValues(alpha: 0.14),
                  borderRadius: BorderRadius.circular(14),
                ),
                child: const Icon(
                  Icons.auto_awesome_rounded,
                  color: Colors.white,
                  size: 23,
                ),
              ),
              const SizedBox(width: 11),
              const Expanded(
                child: Text(
                  'YOUR SMART STUDY SPACE',
                  style: TextStyle(
                    color: Color(0xFFE0E7FF),
                    fontSize: 11,
                    fontWeight: FontWeight.w800,
                    letterSpacing: 1.2,
                  ),
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 7),
                decoration: BoxDecoration(
                  color: Colors.white.withValues(alpha: 0.13),
                  borderRadius: BorderRadius.circular(30),
                  border: Border.all(color: Colors.white.withValues(alpha: 0.16)),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      _connected ? Icons.check_circle : Icons.circle_outlined,
                      size: 13,
                      color: _connected
                          ? const Color(0xFF86EFAC)
                          : const Color(0xFFFDE68A),
                    ),
                    const SizedBox(width: 5),
                    Text(
                      _connected ? 'Connected' : 'Not connected',
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 11,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 22),
          const Text(
            'Prepare smarter.\nLearn with clarity.',
            style: TextStyle(
              color: Colors.white,
              fontSize: 27,
              height: 1.12,
              fontWeight: FontWeight.w800,
              letterSpacing: -0.8,
            ),
          ),
          const SizedBox(height: 10),
          Text(
            'Open your subjects, follow each chapter and reach every One-Liner Q&A with fewer steps.',
            style: TextStyle(
              color: Colors.white.withValues(alpha: 0.82),
              fontSize: 13,
              height: 1.45,
            ),
          ),
          const SizedBox(height: 18),
          Row(
            children: [
              const Icon(
                Icons.account_tree_rounded,
                color: Color(0xFFC4B5FD),
                size: 18,
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  'Subject  →  Chapter  →  Subtopic  →  Q&A',
                  style: TextStyle(
                    color: Colors.white.withValues(alpha: 0.94),
                    fontSize: 12,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 20),
          SizedBox(
            width: double.infinity,
            child: FilledButton.icon(
              onPressed: canBrowse ? _browseQuestionBank : null,
              style: FilledButton.styleFrom(
                backgroundColor: Colors.white,
                foregroundColor: const Color(0xFF312E81),
                disabledBackgroundColor: Colors.white.withValues(alpha: 0.55),
                disabledForegroundColor: const Color(0xFF312E81).withValues(alpha: 0.55),
                minimumSize: const Size.fromHeight(50),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(16),
                ),
              ),
              icon: const Icon(Icons.menu_book_rounded),
              label: const Text(
                'Explore study library',
                style: TextStyle(fontWeight: FontWeight.w800),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStudyLibraryCard(ThemeData theme) {
    final selectedSubject = _subjects.where(
      (item) => item.subjectId == _selectedSubjectId,
    );
    final currentSubject = selectedSubject.isEmpty ? null : selectedSubject.first;
    return Card(
      elevation: 0,
      color: Colors.white,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(24),
        side: const BorderSide(color: Color(0xFFE2E8F0)),
      ),
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  width: 46,
                  height: 46,
                  decoration: BoxDecoration(
                    color: const Color(0xFFEEF2FF),
                    borderRadius: BorderRadius.circular(15),
                  ),
                  child: const Icon(
                    Icons.menu_book_rounded,
                    color: Color(0xFF4338CA),
                    size: 24,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Study library',
                        style: theme.textTheme.titleLarge?.copyWith(
                          fontWeight: FontWeight.w800,
                          letterSpacing: -0.3,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        'Browse every subject in order',
                        style: theme.textTheme.bodySmall?.copyWith(
                          color: theme.colorScheme.onSurfaceVariant,
                        ),
                      ),
                    ],
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 6),
                  decoration: BoxDecoration(
                    color: const Color(0xFFECFDF5),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: const Text(
                    'LEARN',
                    style: TextStyle(
                      color: Color(0xFF047857),
                      fontSize: 10,
                      fontWeight: FontWeight.w800,
                      letterSpacing: 0.8,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 14),
            const Text(
              'Subject  →  Main chapter  →  Subtopic  →  Hindi One-Liner Q&A',
              style: TextStyle(
                color: Color(0xFF475569),
                fontSize: 12,
                height: 1.4,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 14),
            SizedBox(
              width: double.infinity,
              child: FilledButton.icon(
                key: const ValueKey('open-offline-rajasthan-library'),
                onPressed: _loading
                    ? null
                    : () => Navigator.of(context).push<void>(
                          MaterialPageRoute<void>(
                            builder: (_) => const OfflineStudyLibraryScreen(),
                          ),
                        ),
                icon: const Icon(Icons.offline_pin_rounded),
                label: const Text('Open Rajasthan Offline Study Library · 486 Q&A'),
                style: FilledButton.styleFrom(
                  backgroundColor: const Color(0xFF312E81),
                  foregroundColor: Colors.white,
                  minimumSize: const Size.fromHeight(48),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(15),
                  ),
                ),
              ),
            ),
            const SizedBox(height: 14),
            DropdownButtonFormField<String>(
              key: const ValueKey('study-library-subject-selector'),
              initialValue: _subjects.any((item) => item.subjectId == _selectedSubjectId)
                  ? _selectedSubjectId
                  : null,
              decoration: const InputDecoration(
                labelText: 'Choose subject',
                prefixIcon: Icon(Icons.school_outlined),
                border: OutlineInputBorder(),
                contentPadding: EdgeInsets.symmetric(horizontal: 14, vertical: 15),
              ),
              items: _subjects.map((subject) {
                return DropdownMenuItem<String>(
                  value: subject.subjectId,
                  child: Text(
                    '${questionBankHindiLabel(subject.subjectLabel)} · ${subject.conceptCount} विषय',
                    overflow: TextOverflow.ellipsis,
                  ),
                );
              }).toList(growable: false),
              onChanged: _loading || _subjects.isEmpty
                  ? null
                  : _selectQuestionBankSubject,
            ),
            if (_subjectError != null) ...[
              const SizedBox(height: 7),
              Text(
                _subjectError!,
                style: theme.textTheme.bodySmall?.copyWith(
                  color: theme.colorScheme.error,
                ),
              ),
            ],
            if (!_connected) ...[
              const SizedBox(height: 8),
              Text(
                'Offline Rajasthan study material is available above. Connect below to sync server-based exam data and progress.',
                style: theme.textTheme.bodySmall?.copyWith(
                  color: theme.colorScheme.onSurfaceVariant,
                ),
              ),
            ],
            const SizedBox(height: 14),
            SizedBox(
              width: double.infinity,
              child: FilledButton.icon(
                onPressed: _loading || !_connected || _selectedSubjectId == null
                    ? null
                    : _browseQuestionBank,
                icon: const Icon(Icons.arrow_forward_rounded),
                label: Text(
                  currentSubject == null
                      ? 'Choose a subject to continue'
                      : '${questionBankHindiLabel(currentSubject.subjectLabel)} खोलें',
                  overflow: TextOverflow.ellipsis,
                ),
                style: FilledButton.styleFrom(
                  minimumSize: const Size.fromHeight(50),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(15),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildExamSyllabusCard(ThemeData theme) {
    final profile = _selectedExamProfile;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Official exam syllabus', style: theme.textTheme.titleMedium),
            const SizedBox(height: 6),
            const Text(
              'Exam-specific topics are shown only after the official syllabus and every concept mapping have been independently reviewed.',
            ),
            const SizedBox(height: 12),
            if (_examProfiles.isNotEmpty)
              DropdownButtonFormField<String>(
                key: const ValueKey('exam-profile-selector'),
                initialValue: _examProfiles.any((item) => item.examId == _selectedExamId)
                    ? _selectedExamId
                    : null,
                decoration: const InputDecoration(
                  labelText: 'Exam profile',
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.fact_check_outlined),
                ),
                items: _examProfiles.map((item) => DropdownMenuItem<String>(
                  value: item.examId,
                  child: Text(
                    item.selectionReady
                        ? item.examName
                        : '${item.examName} · ${item.unmappedConceptCount} unmapped',
                    overflow: TextOverflow.ellipsis,
                  ),
                )).toList(growable: false),
                onChanged: _loading || _loadingExamSubjects ? null : _selectExamProfile,
              ),
            if (_examProfileError != null) ...[
              const SizedBox(height: 8),
              Text(_examProfileError!, style: theme.textTheme.bodySmall),
            ],
            if (_examProfiles.isEmpty && _examProfileError == null)
              const Text('No official exam profile has been registered yet.'),
            if (profile != null) ...[
              const SizedBox(height: 8),
              Text(
                'Syllabus source: ${profile.sourceStatus} · ${profile.notificationNumber}',
                style: theme.textTheme.bodySmall,
              ),
              Text(
                'Full syllabus inventory: ${profile.syllabusInventoryComplete ? 'reviewed' : 'not yet reviewed'}',
                style: theme.textTheme.bodySmall,
              ),
              Text(
                'Mapped concepts: ${profile.mappedConceptCount} of ${profile.conceptCount}; '
                '${profile.excludedConceptCount} documented out of scope; '
                '${profile.unmappedConceptCount} still unmapped.',
                style: theme.textTheme.bodySmall,
              ),
              if (!profile.selectionReady) ...[
                const SizedBox(height: 8),
                const Text(
                  'This exam cannot be used for syllabus-filtered study yet. The official document or concept mapping still needs review. The app will not silently use the generic topic list for this exam.',
                ),
              ],
            ],
            if (profile != null && profile.selectionReady) ...[
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                key: ValueKey('exam-subject-selector-${profile.examId}'),
                initialValue: _examSubjects.any((item) => item.subjectId == _selectedExamSubjectId)
                    ? _selectedExamSubjectId
                    : null,
                decoration: const InputDecoration(
                  labelText: 'Syllabus-mapped subject',
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.menu_book_outlined),
                ),
                items: _examSubjects.map((item) => DropdownMenuItem<String>(
                  value: item.subjectId,
                  child: Text(
                    '${questionBankHindiLabel(item.subjectLabel)} (${item.conceptCount} विषय)',
                    overflow: TextOverflow.ellipsis,
                  ),
                )).toList(growable: false),
                onChanged: _loading || _loadingExamSubjects || _examSubjects.isEmpty
                    ? null
                    : (value) => setState(() => _selectedExamSubjectId = value),
              ),
              if (_examSubjects.isEmpty && !_loadingExamSubjects)
                const Padding(
                  padding: EdgeInsets.only(top: 8),
                  child: Text('No in-scope subjects have been mapped to this syllabus yet.'),
                ),
              const SizedBox(height: 8),
              SizedBox(
                width: double.infinity,
                child: OutlinedButton.icon(
                  onPressed: _loading || _loadingExamSubjects ||
                          _selectedExamSubjectId == null
                      ? null
                      : _browseExamQuestionBank,
                  icon: const Icon(Icons.menu_book_outlined),
                  label: const Text('Browse this exam syllabus'),
                ),
              ),
            ],
            if (_examSubjectError != null) ...[
              const SizedBox(height: 8),
              Text(_examSubjectError!, style: theme.textTheme.bodySmall),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildConnectionCard(ThemeData theme) {
    return Card(
      elevation: 0,
      color: Colors.white,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(20),
        side: const BorderSide(color: Color(0xFFE2E8F0)),
      ),
      child: ExpansionTile(
        key: ValueKey<bool>(_connected),
        initiallyExpanded: !_connected,
        tilePadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 5),
        childrenPadding: const EdgeInsets.fromLTRB(16, 0, 16, 18),
        leading: Container(
          width: 42,
          height: 42,
          decoration: BoxDecoration(
            color: _connected
                ? const Color(0xFFECFDF5)
                : const Color(0xFFFFF7ED),
            borderRadius: BorderRadius.circular(13),
          ),
          child: Icon(
            _connected ? Icons.cloud_done_rounded : Icons.cloud_off_rounded,
            color: _connected
                ? const Color(0xFF047857)
                : const Color(0xFFB45309),
          ),
        ),
        title: Text(
          _connected ? 'Study service connected' : 'Connect study service',
          style: theme.textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.w800,
          ),
        ),
        subtitle: Text(
          _connected
              ? 'Connection settings · tap to manage'
              : 'Required to load subjects, questions and progress',
          style: theme.textTheme.bodySmall,
        ),
        children: [
          TextField(
            controller: _baseUrlController,
            keyboardType: TextInputType.url,
            autocorrect: false,
            decoration: const InputDecoration(
              labelText: 'API base URL',
              hintText: 'https://your-api.example.com',
              prefixIcon: Icon(Icons.link_rounded),
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
          const SizedBox(height: 14),
          SizedBox(
            width: double.infinity,
            child: FilledButton.icon(
              onPressed: _loading ? null : _connectAndRefresh,
              icon: const Icon(Icons.cloud_sync_rounded),
              label: Text(_connected ? 'Reconnect and refresh' : 'Connect & load progress'),
              style: FilledButton.styleFrom(
                minimumSize: const Size.fromHeight(48),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(14),
                ),
              ),
            ),
          ),
        ],
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
        : ' — ${questionBankHindiLabel(readiness.subjectId ?? '')} के लिए';
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
    final selectedSubject = _subjects.where(
      (item) => item.subjectId == _selectedSubjectId,
    );
    final currentSubject = selectedSubject.isEmpty ? null : selectedSubject.first;
    return Card(
      elevation: 0,
      color: Colors.white,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(24),
        side: const BorderSide(color: Color(0xFFE2E8F0)),
      ),
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  width: 44,
                  height: 44,
                  decoration: BoxDecoration(
                    color: const Color(0xFFFFF7ED),
                    borderRadius: BorderRadius.circular(14),
                  ),
                  child: const Icon(
                    Icons.edit_note_rounded,
                    color: Color(0xFFB45309),
                  ),
                ),
                const SizedBox(width: 11),
                Expanded(
                  child: Text(
                    'Practice test',
                    style: theme.textTheme.titleLarge?.copyWith(
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            const Text(
              'Create a timed test from the selected subject and its eligible verified MCQ pool.',
            ),
            const SizedBox(height: 14),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(13),
              decoration: BoxDecoration(
                color: const Color(0xFFF8FAFC),
                borderRadius: BorderRadius.circular(15),
                border: Border.all(color: const Color(0xFFE2E8F0)),
              ),
              child: Row(
                children: [
                  const Icon(Icons.school_outlined, color: Color(0xFF475569)),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'Selected subject',
                          style: TextStyle(
                            color: Color(0xFF64748B),
                            fontSize: 11,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          currentSubject == null ? 'अध्ययन लाइब्रेरी में विषय चुनें' : questionBankHindiLabel(currentSubject.subjectLabel),
                          style: const TextStyle(
                            color: Color(0xFF0F172A),
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                      ],
                    ),
                  ),

                ],
              ),
            ),
            const SizedBox(height: 14),
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _questionCountController,
                    keyboardType: TextInputType.number,
                    decoration: const InputDecoration(
                      labelText: 'Questions',
                      prefixIcon: Icon(Icons.numbers_rounded),
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
                      prefixIcon: Icon(Icons.timer_outlined),
                      border: OutlineInputBorder(),
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 14),
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
                icon: const Icon(Icons.play_arrow_rounded),
                label: Text(
                  !_connected
                      ? 'Connect to create test'
                      : _subjects.isEmpty
                          ? 'No subjects available'
                          : _selectedSubjectId == null
                              ? 'Select a subject'
                              : 'Generate MCQs and start test',
                ),
                style: FilledButton.styleFrom(
                  minimumSize: const Size.fromHeight(50),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(15),
                  ),
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
  Widget build(BuildContext context) => Container(
        width: double.infinity,
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 14),
        decoration: BoxDecoration(
          color: const Color(0xFFF1F5F9),
          borderRadius: BorderRadius.circular(16),
        ),
        child: Column(
          children: [
            Text(
              value,
              style: Theme.of(context).textTheme.titleLarge?.copyWith(
                    fontWeight: FontWeight.w800,
                    color: const Color(0xFF312E81),
                  ),
            ),
            const SizedBox(height: 4),
            Text(
              label,
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: const Color(0xFF475569),
                    fontWeight: FontWeight.w600,
                  ),
            ),
          ],
        ),
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
