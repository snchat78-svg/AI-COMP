import 'dart:convert';
import 'dart:io';

import 'package:path_provider/path_provider.dart';

import '../api/ai_comp_api_client.dart';
import '../models/preparation_models.dart';

typedef SupportDirectoryProvider = Future<Directory> Function();

class QuestionBankContentSnapshot {
  const QuestionBankContentSnapshot({
    required this.revision,
    required this.catalogueRevision,
    required this.items,
    this.cursor,
  });

  final String revision;
  final String catalogueRevision;
  final String? cursor;
  final List<TopicOneLinerItem> items;
}

/// Disk-backed cache for published content only.
///
/// NEEDS_REVIEW, DRAFT and REJECTED rows are never written to this file.
/// The bundled Chapter 2 review-pending asset is deliberately separate.
class QuestionBankContentCache {
  QuestionBankContentCache({SupportDirectoryProvider? directoryProvider})
      : _directoryProvider =
            directoryProvider ?? getApplicationSupportDirectory;

  static const int _schemaVersion = 1;
  static const int _maximumCacheBytes = 16 * 1024 * 1024;

  final SupportDirectoryProvider _directoryProvider;

  Future<File> _file() async {
    final directory = await _directoryProvider();
    return File(
      '${directory.path}${Platform.pathSeparator}question_bank_verified_content_v1.json',
    );
  }

  Future<QuestionBankContentSnapshot?> read() async {
    try {
      final file = await _file();
      if (!await file.exists()) return null;
      final bytes = await file.readAsBytes();
      if (bytes.isEmpty || bytes.length > _maximumCacheBytes) return null;

      final decoded = jsonDecode(utf8.decode(bytes));
      if (decoded is! Map<String, dynamic> ||
          decoded['schema_version'] != _schemaVersion ||
          decoded['revision'] is! String ||
          decoded['catalogue_revision'] is! String ||
          decoded['items'] is! List) {
        return null;
      }

      final items = <TopicOneLinerItem>[];
      final seenIds = <String>{};
      for (final raw in decoded['items'] as List) {
        if (raw is! Map) return null;
        final item = TopicOneLinerItem.fromJson(
          Map<String, dynamic>.from(raw),
        );
        if (item.oneLinerId.isEmpty || item.conceptId.isEmpty) return null;
        if (item.verificationStatus != 'VERIFIED') return null;
        if (!seenIds.add(item.oneLinerId)) return null;
        items.add(item);
      }

      final cursorValue = decoded['cursor'];
      if (cursorValue != null && cursorValue is! String) return null;

      return QuestionBankContentSnapshot(
        revision: decoded['revision'] as String,
        catalogueRevision: decoded['catalogue_revision'] as String,
        cursor: cursorValue as String?,
        items: List.unmodifiable(items),
      );
    } on FileSystemException {
      return null;
    } on FormatException {
      return null;
    } on TypeError {
      return null;
    } on StateError {
      return null;
    }
  }

  Future<void> write(QuestionBankContentSnapshot snapshot) async {
    if (snapshot.items.any(
      (item) => item.verificationStatus != 'VERIFIED',
    )) {
      throw ArgumentError('Only VERIFIED questions may enter the published cache.');
    }
    final payload = <String, dynamic>{
      'schema_version': _schemaVersion,
      'revision': snapshot.revision,
      'catalogue_revision': snapshot.catalogueRevision,
      'cursor': snapshot.cursor,
      'items': snapshot.items.map((item) => item.toJson()).toList(),
    };
    final encoded = utf8.encode(jsonEncode(payload));
    if (encoded.length > _maximumCacheBytes) {
      throw const FileSystemException('Published question cache exceeds the safe size limit.');
    }

    final target = await _file();
    await target.parent.create(recursive: true);
    final temporary = File('${target.path}.tmp');
    await temporary.writeAsBytes(encoded, flush: true);
    try {
      await temporary.rename(target.path);
    } on FileSystemException {
      // Some file systems do not replace an existing destination on rename.
      if (await target.exists()) await target.delete();
      await temporary.rename(target.path);
    }
  }

  Future<void> clear() async {
    final file = await _file();
    if (await file.exists()) await file.delete();
    final temporary = File('${file.path}.tmp');
    if (await temporary.exists()) await temporary.delete();
  }
}

/// Downloads changed rows using the authenticated manifest/delta API.
///
/// A new snapshot is committed only after a second manifest read proves that
/// the source revision did not change during pagination. On a catalogue
/// change, the one-liner cache is rebuilt from the beginning.
class QuestionBankContentSyncService {
  QuestionBankContentSyncService({
    required this.api,
    required this.cache,
  });

  static const int _pageSize = 100;
  static const int _maximumPagesPerSync = 1000;

  final AiCompApiClient api;
  final QuestionBankContentCache cache;

  Future<QuestionBankContentSnapshot> sync() async {
    final startingManifest = await api.getQuestionBankContentManifest();
    if (startingManifest.schemaVersion != 1 ||
        startingManifest.revision.isEmpty ||
        startingManifest.catalogueRevision.isEmpty) {
      throw const FormatException('Unsupported question-bank manifest.');
    }

    final previous = await cache.read();
    if (previous != null &&
        previous.revision == startingManifest.revision &&
        previous.catalogueRevision == startingManifest.catalogueRevision) {
      return previous;
    }

    final canContinue = previous != null &&
        previous.catalogueRevision == startingManifest.catalogueRevision;
    final merged = <String, TopicOneLinerItem>{
      if (canContinue)
        for (final item in previous!.items) item.oneLinerId: item,
    };
    var cursor = canContinue ? previous!.cursor : null;
    var completed = false;

    for (var pageNumber = 0;
        pageNumber < _maximumPagesPerSync;
        pageNumber++) {
      final page = await api.getQuestionBankContentDelta(
        cursor: cursor,
        limit: _pageSize,
      );
      for (final item in page.items) {
        if (item.oneLinerId.isEmpty || item.conceptId.isEmpty) {
          throw const FormatException('The content delta contains an invalid question identity.');
        }
        if (item.verificationStatus == 'VERIFIED') {
          merged[item.oneLinerId] = item;
        } else {
          // A review/rejection transition removes the old published copy.
          merged.remove(item.oneLinerId);
        }
      }

      if (!page.hasMore) {
        cursor = page.nextCursor ?? cursor;
        completed = true;
        break;
      }
      if (page.nextCursor == null || page.nextCursor == cursor) {
        throw const FormatException('The content delta cursor did not advance.');
      }
      cursor = page.nextCursor;
    }

    if (!completed) {
      throw const FormatException('Question-bank content sync exceeded its page limit.');
    }

    final endingManifest = await api.getQuestionBankContentManifest();
    if (endingManifest.revision != startingManifest.revision ||
        endingManifest.catalogueRevision != startingManifest.catalogueRevision) {
      throw const StateError('Published question-bank content changed during sync.');
    }

    final items = merged.values.toList()
      ..sort((left, right) => left.oneLinerId.compareTo(right.oneLinerId));
    final snapshot = QuestionBankContentSnapshot(
      revision: startingManifest.revision,
      catalogueRevision: startingManifest.catalogueRevision,
      cursor: cursor,
      items: List.unmodifiable(items),
    );
    await cache.write(snapshot);
    return snapshot;
  }
}
