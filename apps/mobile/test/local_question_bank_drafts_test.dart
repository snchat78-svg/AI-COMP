import 'package:flutter_test/flutter_test.dart';



import 'package:ai_comp_mobile/data/local_question_bank_drafts.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('bundled Chapter 2 Hindi drafts include all five child sites', () async {
    final items = await LocalQuestionBankDrafts.loadAll();
    expect(items.length, 368);
    expect(LocalQuestionBankDrafts.totalCount, 368);

    final expected = <String, int>{
      'catalog.rajasthan_history_ancient_history_kalibangan': 311,
      'catalog.rajasthan_history_ancient_history_ahar_banas_culture': 20,
      'catalog.rajasthan_history_ancient_history_ganeshwar_jodhpura_culture': 18,
      'catalog.rajasthan_history_ancient_history_bairat': 9,
      'catalog.rajasthan_history_ancient_history_matsya_janapada': 10,
    };
    for (final entry in expected.entries) {
      final childItems =
          await LocalQuestionBankDrafts.loadForConcept(entry.key);
      expect(childItems.length, entry.value, reason: entry.key);
      expect(childItems.every((item) => item.verificationStatus == 'NEEDS_REVIEW'), isTrue);
      expect(childItems.every((item) => item.languageCode == 'hi'), isTrue);
      expect(childItems.every((item) => item.sourceEvidence.isNotEmpty), isTrue);
    }
  });

  test('local draft IDs are unique and never marked verified', () async {
    final items = await LocalQuestionBankDrafts.loadAll();
    expect(items.map((item) => item.oneLinerId).toSet().length, 368);
    expect(items.any((item) => item.verificationStatus == 'VERIFIED'), isFalse);
    expect(
      items.firstWhere((item) => item.oneLinerId == 'ch2_KAL-001').questionText,
      'कालीबंगा राजस्थान के किस जिले में स्थित है?',
    );
  });
}
