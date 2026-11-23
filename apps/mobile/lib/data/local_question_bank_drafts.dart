import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';

import '../models/preparation_models.dart';

/// Local copy of the five Chapter 2 child-site Q&A draft sets.
///
/// These records are for reading/study only. They are not VERIFIED and are
/// not previous-year questions. Their source locators are shown as pending
/// review until an independent reviewer approves the database records.
class LocalQuestionBankDrafts {
  LocalQuestionBankDrafts._();

  static const String _assetPath =
      'assets/question_bank/rajasthan_history_chapter_2_drafts.json';

  static const Map<String, int> _countsByConcept = {
    'catalog.rajasthan_history_ancient_history_kalibangan': 311,
    'catalog.rajasthan_history_ancient_history_ahar_banas_culture': 26,
    'catalog.rajasthan_history_ancient_history_ganeshwar_jodhpura_culture': 18,
    'catalog.rajasthan_history_ancient_history_bairat': 11,
    'catalog.rajasthan_history_ancient_history_matsya_janapada': 10,
  };

  static Future<List<TopicOneLinerItem>>? _cachedAll;

  static int countForConcept(String conceptId) =>
      _countsByConcept[conceptId] ?? 0;

  static int get totalCount =>
      _countsByConcept.values.fold<int>(0, (sum, count) => sum + count);

  @visibleForTesting
  static void primeForTests(List<TopicOneLinerItem> items) {
    _cachedAll = Future.value(List.unmodifiable(items));
  }

  @visibleForTesting
  static void resetForTests() {
    _cachedAll = null;
  }

  static Future<List<TopicOneLinerItem>> loadAll() {
    return _cachedAll ??= _readAsset();
  }

  static Future<List<TopicOneLinerItem>> loadForConcept(
    String conceptId,
  ) async {
    final items = await loadAll();
    return items
        .where((item) => item.conceptId == conceptId)
        .toList(growable: false);
  }

  static Future<List<TopicOneLinerItem>> _readAsset() async {
    final source = await rootBundle.loadString(_assetPath);
    final decoded = jsonDecode(source);
    if (decoded is! List) {
      throw const FormatException('Local question-bank asset must be a list.');
    }
    final items = decoded
        .whereType<Map>()
        .map((value) => TopicOneLinerItem.fromJson(
              Map<String, dynamic>.from(value),
            ))
        .toList(growable: false);
    if (items.length != totalCount) {
      throw FormatException(
        'Local question-bank asset expected $totalCount rows but found ${items.length}.',
      );
    }
    if (items.any((item) => item.verificationStatus != 'NEEDS_REVIEW')) {
      throw const FormatException(
        'Local Chapter 2 questions must remain NEEDS_REVIEW.',
      );
    }
    return items;
  }
}
