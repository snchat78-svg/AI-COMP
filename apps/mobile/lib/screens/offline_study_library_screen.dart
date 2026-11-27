import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

class OfflineStudyLibraryScreen extends StatefulWidget {
  const OfflineStudyLibraryScreen({super.key});

  @override
  State<OfflineStudyLibraryScreen> createState() =>
      _OfflineStudyLibraryScreenState();
}

class _OfflineStudyLibraryScreenState extends State<OfflineStudyLibraryScreen> {
  late final Future<_OfflineLibraryData> _libraryFuture = _loadLibrary();

  Future<_OfflineLibraryData> _loadLibrary() async {
    final catalogueSource = await rootBundle.loadString(
      'assets/question_bank/rajasthan_offline_catalogue.json',
    );
    final parallelDraftSource = await rootBundle.loadString(
      'assets/question_bank/rajasthan_parallel_subjects_drafts.json',
    );
    final historyDraftSource = await rootBundle.loadString(
      'assets/question_bank/rajasthan_history_chapter_2_drafts.json',
    );

    final catalogueRaw = jsonDecode(catalogueSource);
    final parallelRaw = jsonDecode(parallelDraftSource);
    final historyRaw = jsonDecode(historyDraftSource);
    if (catalogueRaw is! Map || catalogueRaw['subjects'] is! List ||
        parallelRaw is! Map || parallelRaw['items'] is! List ||
        historyRaw is! List) {
      throw const FormatException('राजस्थान offline study data का प्रारूप सही नहीं है।');
    }

    final subjects = (catalogueRaw['subjects'] as List)
        .whereType<Map>()
        .map((row) => Map<String, dynamic>.from(row))
        .toList(growable: false);
    final questions = <Map<String, dynamic>>[
      ...historyRaw
          .whereType<Map>()
          .map((row) => Map<String, dynamic>.from(row)),
      ...(parallelRaw['items'] as List)
          .whereType<Map>()
          .map((row) => Map<String, dynamic>.from(row)),
    ];

    if (subjects.length != 5 || questions.length != 486) {
      throw FormatException(
        'राजस्थान library integrity check failed: '
        '${subjects.length} विषय, ${questions.length} प्रश्न मिले।',
      );
    }
    if (questions.any((item) =>
        item['language_code'] != 'hi' ||
        item['verification_status'] != 'NEEDS_REVIEW' ||
        (item['source_url'] as String? ?? '').isEmpty ||
        (item['source_evidence'] as String? ?? '').isEmpty)) {
      throw const FormatException(
        'Offline library में हिंदी, स्रोत-साक्ष्य या review status की जाँच विफल हुई।',
      );
    }
    return _OfflineLibraryData(subjects: subjects, questions: questions);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF5F7FC),
      appBar: AppBar(
        title: const Text(
          'राजस्थान अध्ययन लाइब्रेरी',
          style: TextStyle(fontWeight: FontWeight.w800),
        ),
        backgroundColor: const Color(0xFFF5F7FC),
        surfaceTintColor: Colors.transparent,
      ),
      body: FutureBuilder<_OfflineLibraryData>(
        future: _libraryFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError || !snapshot.hasData) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(Icons.menu_book_outlined, size: 42),
                    const SizedBox(height: 12),
                    const Text(
                      'अध्ययन सामग्री लोड नहीं हो सकी',
                      style: TextStyle(fontWeight: FontWeight.w800, fontSize: 18),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'Offline content bundle की जाँच आवश्यक है।${snapshot.error ?? ''}',
                      textAlign: TextAlign.center,
                    ),
                  ],
                ),
              ),
            );
          }
          final library = snapshot.data!;
          return ListView(
            padding: const EdgeInsets.fromLTRB(16, 10, 16, 28),
            children: [
              Container(
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(24),
                  gradient: const LinearGradient(
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                    colors: [Color(0xFF172554), Color(0xFF3730A3), Color(0xFF6D28D9)],
                  ),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'RAJASTHAN STUDY SPACE',
                      style: TextStyle(
                        color: Color(0xFFE0E7FF),
                        fontSize: 11,
                        fontWeight: FontWeight.w800,
                        letterSpacing: 1.1,
                      ),
                    ),
                    const SizedBox(height: 10),
                    const Text(
                      'विषय से प्रश्न तक\nबिना इंटरनेट पढ़ाई',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 25,
                        height: 1.15,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                    const SizedBox(height: 14),
                    Row(
                      children: [
                        _LibraryMetric(
                          value: '${library.subjects.length}',
                          label: 'विषय',
                        ),
                        const SizedBox(width: 20),
                        _LibraryMetric(
                          value: '${library.conceptCount}',
                          label: 'उप-विषय',
                        ),
                        const SizedBox(width: 20),
                        _LibraryMetric(
                          value: '${library.questions.length}',
                          label: 'One-Liners',
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    Text(
                      'सभी प्रश्न हिंदी में हैं। समीक्षा बाकी मसौदे, सत्यापित प्रश्न और वास्तविक पुराने प्रश्न अलग रखे गए हैं।',
                      style: TextStyle(
                        color: Colors.white.withValues(alpha: 0.88),
                        fontSize: 12,
                        height: 1.4,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 18),
              Text(
                'राजस्थान के पाँच मुख्य विषय',
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                      fontWeight: FontWeight.w800,
                    ),
              ),
              const SizedBox(height: 10),
              GridView.builder(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                itemCount: library.subjects.length,
                gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: 2,
                  crossAxisSpacing: 10,
                  mainAxisSpacing: 10,
                  childAspectRatio: 1.25,
                ),
                itemBuilder: (context, index) {
                  final subject = library.subjects[index];
                  final concepts = _subtopics(subject);
                  final questionCount = concepts.fold<int>(
                    0,
                    (sum, concept) =>
                        sum + library.itemsForConcept(concept['concept_id'] as String).length,
                  );
                  return Card(
                    elevation: 0,
                    color: Colors.white,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(18),
                      side: const BorderSide(color: Color(0xFFE2E8F0)),
                    ),
                    child: InkWell(
                      borderRadius: BorderRadius.circular(18),
                      onTap: () => Navigator.of(context).push<void>(
                        MaterialPageRoute(
                          builder: (_) => _OfflineSubjectScreen(
                            subject: subject,
                            library: library,
                          ),
                        ),
                      ),
                      child: Padding(
                        padding: const EdgeInsets.all(14),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            const Icon(Icons.menu_book_rounded, color: Color(0xFF4338CA)),
                            Text(
                              subject['subject_label'] as String,
                              maxLines: 2,
                              overflow: TextOverflow.ellipsis,
                              style: const TextStyle(
                                fontWeight: FontWeight.w800,
                                fontSize: 14,
                              ),
                            ),
                            Text(
                              '${concepts.length} उप-विषय • $questionCount प्रश्न',
                              style: const TextStyle(
                                color: Color(0xFF64748B),
                                fontSize: 11,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  );
                },
              ),
              const SizedBox(height: 10),
              const Text(
                'ध्यान दें: ये source-backed AI study drafts हैं। स्वतंत्र समीक्षा के बाद ही इन्हें VERIFIED माना जाएगा; इन्हें PYQ नहीं कहा गया है।',
                style: TextStyle(color: Color(0xFF64748B), fontSize: 12, height: 1.4),
              ),
            ],
          );
        },
      ),
    );
  }

  static List<Map<String, dynamic>> _subtopics(Map<String, dynamic> subject) {
    final result = <Map<String, dynamic>>[];
    final groups = subject['topic_groups'];
    if (groups is! List) return result;
    for (final rawGroup in groups.whereType<Map>()) {
      final subtopics = rawGroup['subtopics'];
      if (subtopics is List) {
        result.addAll(
          subtopics.whereType<Map>().map((row) => Map<String, dynamic>.from(row)),
        );
      }
    }
    return result;
  }
}

class _OfflineLibraryData {
  const _OfflineLibraryData({required this.subjects, required this.questions});

  final List<Map<String, dynamic>> subjects;
  final List<Map<String, dynamic>> questions;

  int get conceptCount => subjects.fold<int>(
        0,
        (sum, subject) {
          final groups = subject['topic_groups'];
          if (groups is! List) return sum;
          return sum + groups.whereType<Map>().fold<int>(
            0,
            (groupSum, group) {
              final subs = group['subtopics'];
              return groupSum + (subs is List ? subs.length : 0);
            },
          );
        },
      );

  List<Map<String, dynamic>> itemsForConcept(String conceptId) {
    return questions.where((item) {
      if (item['concept_id'] == conceptId) return true;
      final related = item['related_concept_ids'];
      return related is List && related.contains(conceptId);
    }).toList(growable: false)
      ..sort((a, b) => (a['one_liner_id'] as String)
          .compareTo(b['one_liner_id'] as String));
  }
}

class _LibraryMetric extends StatelessWidget {
  const _LibraryMetric({required this.value, required this.label});

  final String value;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          value,
          style: const TextStyle(
            color: Colors.white,
            fontSize: 22,
            fontWeight: FontWeight.w800,
          ),
        ),
        Text(
          label,
          style: const TextStyle(color: Color(0xFFDDD6FE), fontSize: 11),
        ),
      ],
    );
  }
}

class _OfflineSubjectScreen extends StatelessWidget {
  const _OfflineSubjectScreen({
    required this.subject,
    required this.library,
  });

  final Map<String, dynamic> subject;
  final _OfflineLibraryData library;

  @override
  Widget build(BuildContext context) {
    final groups = (subject['topic_groups'] as List? ?? const [])
        .whereType<Map>()
        .map((row) => Map<String, dynamic>.from(row))
        .toList(growable: false);
    final conceptTotal = groups.fold<int>(
      0,
      (sum, group) => sum + ((group['subtopics'] as List?)?.length ?? 0),
    );
    return Scaffold(
      backgroundColor: const Color(0xFFF5F7FC),
      appBar: AppBar(
        title: Text(subject['subject_label'] as String),
        backgroundColor: const Color(0xFFF5F7FC),
        surfaceTintColor: Colors.transparent,
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text(
            '$conceptTotal उप-विषय • पूरा मुख्य विषयवार क्रम',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: const Color(0xFF64748B),
                  fontWeight: FontWeight.w600,
                ),
          ),
          const SizedBox(height: 12),
          for (final group in groups)
            Builder(builder: (context) {
              final subtopics = (group['subtopics'] as List? ?? const [])
                  .whereType<Map>()
                  .map((row) => Map<String, dynamic>.from(row))
                  .toList(growable: false);
              final groupQuestions = subtopics.fold<int>(
                0,
                (sum, concept) => sum +
                    library.itemsForConcept(concept['concept_id'] as String).length,
              );
              return Card(
                elevation: 0,
                margin: const EdgeInsets.only(bottom: 10),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(18),
                  side: const BorderSide(color: Color(0xFFE2E8F0)),
                ),
                child: ExpansionTile(
                  initiallyExpanded: groups.length == 1,
                  leading: const CircleAvatar(
                    backgroundColor: Color(0xFFEEF2FF),
                    child: Icon(Icons.account_tree_outlined, color: Color(0xFF4338CA)),
                  ),
                  title: Text(
                    group['topic_name'] as String,
                    style: const TextStyle(fontWeight: FontWeight.w800),
                  ),
                  subtitle: Text('${subtopics.length} उप-विषय • $groupQuestions प्रश्न'),
                  children: [
                    for (final concept in subtopics)
                      Builder(builder: (context) {
                        final conceptId = concept['concept_id'] as String;
                        final count = library.itemsForConcept(conceptId).length;
                        return ListTile(
                          title: Text(concept['label'] as String),
                          subtitle: Text(
                            count == 0
                                ? 'प्रश्न तैयारी में'
                                : '$count One-Liner • समीक्षा बाकी',
                            style: const TextStyle(fontSize: 12),
                          ),
                          trailing: const Icon(Icons.chevron_right),
                          onTap: () => Navigator.of(context).push<void>(
                            MaterialPageRoute(
                              builder: (_) => _OfflineTopicScreen(
                                concept: concept,
                                topicName: group['topic_name'] as String,
                                subjectName: subject['subject_label'] as String,
                                items: library.itemsForConcept(conceptId),
                              ),
                            ),
                          ),
                        );
                      }),
                  ],
                ),
              );
            }),
        ],
      ),
    );
  }
}

class _OfflineTopicScreen extends StatelessWidget {
  const _OfflineTopicScreen({
    required this.concept,
    required this.topicName,
    required this.subjectName,
    required this.items,
  });

  final Map<String, dynamic> concept;
  final String topicName;
  final String subjectName;
  final List<Map<String, dynamic>> items;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF5F7FC),
      appBar: AppBar(
        title: Text(concept['label'] as String),
        backgroundColor: const Color(0xFFF5F7FC),
        surfaceTintColor: Colors.transparent,
      ),
      body: items.isEmpty
          ? Center(
              child: Padding(
                padding: const EdgeInsets.all(28),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(Icons.edit_note_rounded, size: 48, color: Color(0xFF64748B)),
                    const SizedBox(height: 12),
                    const Text(
                      'इस उप-विषय के प्रश्न तैयारी में हैं',
                      textAlign: TextAlign.center,
                      style: TextStyle(fontWeight: FontWeight.w800, fontSize: 17),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      '$subjectName → $topicName → ${concept['label']}\n'
                      'यह उप-विषय master roadmap में मौजूद है। स्रोत-जाँच के बाद प्रश्न जोड़े जाएँगे।',
                      textAlign: TextAlign.center,
                      style: const TextStyle(color: Color(0xFF64748B), height: 1.5),
                    ),
                  ],
                ),
              ),
            )
          : ListView(
              padding: const EdgeInsets.all(16),
              children: [
                Text(
                  '$subjectName → $topicName → ${concept['label']}',
                  style: const TextStyle(
                    color: Color(0xFF64748B),
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  '${items.length} One-Liner प्रश्न • सभी समीक्षा बाकी',
                  style: const TextStyle(fontWeight: FontWeight.w700),
                ),
                const SizedBox(height: 12),
                for (var index = 0; index < items.length; index++)
                  _DraftQuestionCard(index: index + 1, item: items[index]),
              ],
            ),
    );
  }
}

class _DraftQuestionCard extends StatelessWidget {
  const _DraftQuestionCard({required this.index, required this.item});

  final int index;
  final Map<String, dynamic> item;

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 0,
      margin: const EdgeInsets.only(bottom: 12),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(18),
        side: const BorderSide(color: Color(0xFFE2E8F0)),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
              decoration: BoxDecoration(
                color: const Color(0xFFFFF7ED),
                borderRadius: BorderRadius.circular(20),
              ),
              child: const Text(
                'AI मसौदा • समीक्षा बाकी',
                style: TextStyle(
                  color: Color(0xFF9A3412),
                  fontSize: 10,
                  fontWeight: FontWeight.w800,
                ),
              ),
            ),
            const SizedBox(height: 10),
            Text(
              'प्रश्न $index. ${item['question_text']}',
              style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16, height: 1.35),
            ),
            const SizedBox(height: 9),
            Text(
              'उत्तर: ${item['answer_text']}',
              style: const TextStyle(fontSize: 14, height: 1.45),
            ),
            const SizedBox(height: 10),
            Text(
              'स्रोत-साक्ष्य: ${item['source_evidence']}',
              style: const TextStyle(color: Color(0xFF64748B), fontSize: 11, height: 1.4),
            ),
            const SizedBox(height: 5),
            SelectableText(
              'स्रोत: ${item['source_url']}',
              style: const TextStyle(color: Color(0xFF475569), fontSize: 11),
            ),
          ],
        ),
      ),
    );
  }
}
