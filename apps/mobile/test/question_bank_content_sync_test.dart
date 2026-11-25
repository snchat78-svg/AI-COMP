import 'dart:convert';
import 'dart:io';

import 'package:ai_comp_mobile/api/ai_comp_api_client.dart';
import 'package:ai_comp_mobile/data/question_bank_content_sync.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

void main() {
  Map<String, dynamic> manifest(String revision, {String catalogue = 'catalog-a'}) => {
        'schema_version': 1,
        'revision': revision,
        'catalogue_revision': catalogue,
        'published_questions_revision': 'published-$revision',
        'topic_count': 10,
        'verified_one_liner_count': 1,
        'review_pending_one_liner_count': 376,
      };

  Map<String, dynamic> item(
    String id, {
    String status = 'VERIFIED',
    String concept = 'topic-river',
  }) =>
      {
        'one_liner_id': id,
        'concept_id': concept,
        'question_text': 'नदी किस दिशा में बहती है?',
        'answer_text': 'दक्षिण-पश्चिम दिशा में।',
        'language_code': 'hi',
        'source_url': 'https://example.gov.in/river',
        'source_evidence': 'नदी अनुभाग, अनुच्छेद 2',
        'verification_status': status,
        'importance_score': 0.9,
        'updated_at': '2026-11-23T10:00:00+00:00',
      };

  Map<String, dynamic> delta(
    List<Map<String, dynamic>> items, {
    bool hasMore = false,
    String? cursor = 'cursor-tail',
  }) =>
      {
        'schema_version': 1,
        'items': items,
        'pagination': {
          'limit': 100,
          'returned': items.length,
          'has_more': hasMore,
          'next_cursor': cursor,
        },
      };

  Future<Directory> temporaryDirectory() => Directory.systemTemp.createTemp(
        'ai_comp_content_sync_test_',
      );

  test('cache stores only verified rows and round-trips the sync cursor', () async {
    final directory = await temporaryDirectory();
    addTearDown(() => directory.delete(recursive: true));
    final cache = QuestionBankContentCache(
      directoryProvider: () async => directory,
    );
    final verified = TopicOneLinerItem.fromJson(item('verified-1'));
    final pending = TopicOneLinerItem.fromJson(
      item('pending-1', status: 'NEEDS_REVIEW'),
    );

    await expectLater(
      cache.write(QuestionBankContentSnapshot(
        revision: 'revision-1',
        catalogueRevision: 'catalog-a',
        cursor: 'cursor-1',
        items: [verified, pending],
      )),
      throwsArgumentError,
    );

    await cache.write(QuestionBankContentSnapshot(
      revision: 'revision-1',
      catalogueRevision: 'catalog-a',
      cursor: 'cursor-1',
      items: [verified],
    ));
    final restored = await cache.read();

    expect(restored, isNotNull);
    expect(restored!.revision, 'revision-1');
    expect(restored.cursor, 'cursor-1');
    expect(restored.items.map((value) => value.oneLinerId), ['verified-1']);
  });

  test('first sync downloads verified rows and excludes review-pending drafts', () async {
    final directory = await temporaryDirectory();
    addTearDown(() => directory.delete(recursive: true));
    final cache = QuestionBankContentCache(
      directoryProvider: () async => directory,
    );
    final requests = <http.Request>[];
    final mock = MockClient((request) async {
      requests.add(request);
      if (request.url.path.endsWith('/content-manifest')) {
        return http.Response(
          jsonEncode(manifest('revision-1')),
          200,
          headers: {'content-type': 'application/json'},
        );
      }
      if (request.url.path.endsWith('/content-delta')) {
        return http.Response(
          jsonEncode(delta([
            item('verified-1'),
            item('pending-1', status: 'NEEDS_REVIEW'),
          ])),
          200,
          headers: {'content-type': 'application/json'},
        );
      }
      return http.Response('{}', 404);
    });
    addTearDown(mock.close);
    final api = AiCompApiClient(
      baseUrl: 'https://api.example.test',
      learnerId: 'learner-1',
      accessToken: 'firebase-token',
      httpClient: mock,
    );
    addTearDown(api.close);

    final snapshot = await QuestionBankContentSyncService(
      api: api,
      cache: cache,
    ).sync();

    expect(snapshot.revision, 'revision-1');
    expect(snapshot.items.map((value) => value.oneLinerId), ['verified-1']);
    expect(requests, hasLength(3));
    expect(requests.first.headers['authorization'], 'Bearer firebase-token');
    expect(requests[1].url.path, endsWith('/question-bank/content-delta'));
    expect((await cache.read())!.items.single.verificationStatus, 'VERIFIED');
  });

  test('unchanged manifest avoids another delta download', () async {
    final directory = await temporaryDirectory();
    addTearDown(() => directory.delete(recursive: true));
    final cache = QuestionBankContentCache(
      directoryProvider: () async => directory,
    );
    await cache.write(QuestionBankContentSnapshot(
      revision: 'revision-same',
      catalogueRevision: 'catalog-a',
      cursor: 'cursor-saved',
      items: [TopicOneLinerItem.fromJson(item('existing-1'))],
    ));
    var deltaCalls = 0;
    final mock = MockClient((request) async {
      if (request.url.path.endsWith('/content-manifest')) {
        return http.Response(
          jsonEncode(manifest('revision-same')),
          200,
        );
      }
      if (request.url.path.endsWith('/content-delta')) {
        deltaCalls++;
        return http.Response(jsonEncode(delta([])), 200);
      }
      return http.Response('{}', 404);
    });
    addTearDown(mock.close);
    final api = AiCompApiClient(
      baseUrl: 'https://api.example.test',
      learnerId: 'learner-1',
      accessToken: 'token',
      httpClient: mock,
    );
    addTearDown(api.close);

    final snapshot = await QuestionBankContentSyncService(
      api: api,
      cache: cache,
    ).sync();

    expect(snapshot.items.single.oneLinerId, 'existing-1');
    expect(deltaCalls, 0);
  });

  test('incremental sync upserts new verified rows and removes review regressions', () async {
    final directory = await temporaryDirectory();
    addTearDown(() => directory.delete(recursive: true));
    final cache = QuestionBankContentCache(
      directoryProvider: () async => directory,
    );
    await cache.write(QuestionBankContentSnapshot(
      revision: 'revision-1',
      catalogueRevision: 'catalog-a',
      cursor: 'saved-cursor',
      items: [TopicOneLinerItem.fromJson(item('old-verified'))],
    ));
    final requestedCursors = <String?>[];
    var manifestCalls = 0;
    final mock = MockClient((request) async {
      if (request.url.path.endsWith('/content-manifest')) {
        manifestCalls++;
        return http.Response(
          jsonEncode(manifest('revision-2')),
          200,
        );
      }
      if (request.url.path.endsWith('/content-delta')) {
        requestedCursors.add(request.url.queryParameters['cursor']);
        return http.Response(
          jsonEncode(delta([
            item('new-verified'),
            item('old-verified', status: 'NEEDS_REVIEW'),
          ], cursor: 'next-cursor')),
          200,
        );
      }
      return http.Response('{}', 404);
    });
    addTearDown(mock.close);
    final api = AiCompApiClient(
      baseUrl: 'https://api.example.test',
      learnerId: 'learner-1',
      accessToken: 'token',
      httpClient: mock,
    );
    addTearDown(api.close);

    final snapshot = await QuestionBankContentSyncService(
      api: api,
      cache: cache,
    ).sync();

    expect(manifestCalls, 2);
    expect(requestedCursors, ['saved-cursor']);
    expect(snapshot.items.map((value) => value.oneLinerId), ['new-verified']);
  });

  test('catalogue revision change triggers a full content snapshot', () async {
    final directory = await temporaryDirectory();
    addTearDown(() => directory.delete(recursive: true));
    final cache = QuestionBankContentCache(
      directoryProvider: () async => directory,
    );
    await cache.write(QuestionBankContentSnapshot(
      revision: 'revision-1',
      catalogueRevision: 'old-catalogue',
      cursor: 'old-cursor',
      items: [TopicOneLinerItem.fromJson(item('stale-topic'))],
    ));
    String? suppliedCursor = 'not-requested';
    final mock = MockClient((request) async {
      if (request.url.path.endsWith('/content-manifest')) {
        return http.Response(
          jsonEncode(manifest('revision-2', catalogue: 'new-catalogue')),
          200,
        );
      }
      if (request.url.path.endsWith('/content-delta')) {
        suppliedCursor = request.url.queryParameters['cursor'];
        return http.Response(jsonEncode(delta([item('fresh-topic')])), 200);
      }
      return http.Response('{}', 404);
    });
    addTearDown(mock.close);
    final api = AiCompApiClient(
      baseUrl: 'https://api.example.test',
      learnerId: 'learner-1',
      accessToken: 'token',
      httpClient: mock,
    );
    addTearDown(api.close);

    final snapshot = await QuestionBankContentSyncService(
      api: api,
      cache: cache,
    ).sync();

    expect(suppliedCursor, isNull);
    expect(snapshot.catalogueRevision, 'new-catalogue');
    expect(snapshot.items.map((value) => value.oneLinerId), ['fresh-topic']);
  });

  test('manifest change during pagination preserves the previous cache', () async {
    final directory = await temporaryDirectory();
    addTearDown(() => directory.delete(recursive: true));
    final cache = QuestionBankContentCache(
      directoryProvider: () async => directory,
    );
    await cache.write(QuestionBankContentSnapshot(
      revision: 'revision-old',
      catalogueRevision: 'catalog-a',
      cursor: 'saved-cursor',
      items: [TopicOneLinerItem.fromJson(item('known-good'))],
    ));
    var manifestCalls = 0;
    final mock = MockClient((request) async {
      if (request.url.path.endsWith('/content-manifest')) {
        manifestCalls++;
        final revision = manifestCalls == 1 ? 'revision-start' : 'revision-end';
        return http.Response(jsonEncode(manifest(revision)), 200);
      }
      if (request.url.path.endsWith('/content-delta')) {
        return http.Response(
          jsonEncode(delta([item('candidate-new')], cursor: 'next-cursor')),
          200,
        );
      }
      return http.Response('{}', 404);
    });
    addTearDown(mock.close);
    final api = AiCompApiClient(
      baseUrl: 'https://api.example.test',
      learnerId: 'learner-1',
      accessToken: 'token',
      httpClient: mock,
    );
    addTearDown(api.close);

    await expectLater(
      QuestionBankContentSyncService(api: api, cache: cache).sync(),
      throwsStateError,
    );
    final unchanged = await cache.read();
    expect(unchanged!.revision, 'revision-old');
    expect(unchanged.items.single.oneLinerId, 'known-good');
  });

  test('corrupt cache is ignored instead of exposing partial records', () async {
    final directory = await temporaryDirectory();
    addTearDown(() => directory.delete(recursive: true));
    final file = File(
      '${directory.path}${Platform.pathSeparator}question_bank_verified_content_v1.json',
    );
    await file.writeAsString('{"schema_version": 1, "items": [');
    final snapshot = await QuestionBankContentCache(
      directoryProvider: () async => directory,
    ).read();
    expect(snapshot, isNull);
  });
}
