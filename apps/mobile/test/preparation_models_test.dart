import 'dart:convert';

import 'package:ai_comp_mobile/models/preparation_models.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('API response models', () {
    test('recommendation reads focus and question count adjustment', () {
      final parsed = AdaptiveRecommendation.fromJson({
        'request_id': 'request-1',
        'status': 'ACTIVE',
        'title': 'Adaptive practice',
        'mode': 'ADAPTIVE',
        'question_count': 5,
        'duration_seconds': 900,
        'recommendation': {
          'focus_concept_ids': ['geography', 'history'],
          'revision_question_ids': ['question-previous-mistake'],
          'requested_question_count': 10,
          'eligible_question_count_in_configured_pool': 5,
          'effective_question_count': 5,
          'question_count_adjusted': true,
        },
      });

      expect(parsed.requestId, 'request-1');
      expect(parsed.focusConceptIds, ['geography', 'history']);
      expect(parsed.revisionQuestionIds, ['question-previous-mistake']);
      expect(parsed.questionCount, 5);
      expect(parsed.requestedQuestionCount, 10);
      expect(parsed.questionCountAdjusted, isTrue);
    });

    test('current question restores learner selection but has no answer key', () {
      final parsed = CurrentQuestion.fromJson({
        'session_id': 'session-1',
        'question_number': 2,
        'question_count': 4,
        'question_id': 'question-2',
        'stem': 'Choose one',
        'options': [
          {'key': 'A', 'text': 'First'},
          {'key': 'B', 'text': 'Second'},
        ],
        'selected_option_key': 'B',
        'review_marked': true,
        'remaining_seconds': 215.5,
      });

      expect(parsed.selectedOptionKey, 'B');
      expect(parsed.options.map((item) => item.key), ['A', 'B']);
      expect(parsed.reviewMarked, isTrue);
      expect(parsed.remainingSeconds, 215.5);
    });


    test('previous-paper page parses exact filtered counts and original sources', () {
      final page = PreviousYearQuestionPage.fromJson({
        'items': [
          {
            'question_id': 'history-1',
            'stem': 'Which river flows west?',
            'options': [
              {'key': 'A', 'text': 'Luni'},
              {'key': 'B', 'text': 'Banas'},
              {'key': 'C', 'text': 'Chambal'},
              {'key': 'D', 'text': 'Mahi'},
            ],
            'correct_option_key': 'A',
            'explanation': 'Matched official answer key.',
            'exam_name': 'State recruitment exam',
            'exam_id': 'STATE_EXAM',
            'exam_year': 2024,
            'exam_shift': 'MORNING',
            'exam_question_number': 12,
            'source_url': 'https://official.example/paper.pdf',
            'answer_key_source_url': 'https://official.example/key.pdf',
            'verified_appearance_count': 2,
            'concept_ids': ['topic-rivers'],
          },
        ],
        'pagination': {
          'limit': 20,
          'offset': 0,
          'returned': 1,
          'total_count': 8,
          'has_more': true,
        },
      });

      expect(page.items, hasLength(1));
      expect(page.items.single.examYear, 2024);
      expect(page.items.single.sourceUrl, 'https://official.example/paper.pdf');
      expect(page.items.single.answerKeySourceUrl, 'https://official.example/key.pdf');
      expect(page.items.single.verifiedAppearanceCount, 2);
      expect(page.pagination.totalCount, 8);
      expect(page.pagination.hasMore, isTrue);
    });

    test('common API errors retain stable code and safe message', () {
      final error = ApiException.fromResponse(
        409,
        jsonEncode({
          'error': {
            'code': 'NO_ADAPTIVE_PRACTICE_SIGNAL',
            'message': 'Complete a test first.',
          },
        }),
      );

      expect(error.statusCode, 409);
      expect(error.code, 'NO_ADAPTIVE_PRACTICE_SIGNAL');
      expect(error.message, 'Complete a test first.');
    });
  });
}
