import '../domain/action_follow_through_models.dart';
import 'action_follow_through_repository.dart';

class PreviewActionFollowThroughRepository
    implements ActionFollowThroughRepository {
  final List<ActionFollowThroughItem> _actions = [
    ActionFollowThroughItem(
      id: '99999999-9999-4999-8999-999999999901',
      caseVersionId: '22222222-2222-4222-8222-222222222222',
      title: 'Toplu Taşıma Gece Seferleri ve Öncelikli Koltuk Yönetmeliği',
      description:
          'Belediye meclisine resmi dilekçe verilmesi ve tarife komisyonu toplantısının izlenmesi.',
      status: ActionFollowThroughStatus.inProgress,
      progressPercentage: 65,
      createdAt: DateTime.utc(2026, 8, 29, 10, 0),
      targetCompletionDate: DateTime.utc(2026, 10, 15),
      evidenceSummary:
          'Dilekçe kabul edildi, belediye meclisi gündemine alındı.',
      evidenceUrl: 'https://belediye.gov.tr/kararlar/2026-44',
    ),
    ActionFollowThroughItem(
      id: '99999999-9999-4999-8999-999999999902',
      caseVersionId: '22222222-2222-4222-8222-222222222223',
      title: 'Yapay Zekâ Veri Toplama Şeffaflık Standartları İnisiyatifi',
      description:
          'Sektörel STK’lar ile ortak çalışma grubu oluşturulması ve tavsiye raporunun yayımlanması.',
      status: ActionFollowThroughStatus.proposed,
      progressPercentage: 20,
      createdAt: DateTime.utc(2026, 8, 31, 14, 0),
      targetCompletionDate: DateTime.utc(2026, 11, 30),
      evidenceSummary: 'Çalışma grubu ilk taslak metnini tamamladı.',
    ),
  ];

  @override
  Future<List<ActionFollowThroughItem>> fetchActions({
    String? caseVersionId,
  }) async {
    if (caseVersionId != null) {
      return _actions
          .where((a) => a.caseVersionId == caseVersionId)
          .toList(growable: false);
    }
    return List.unmodifiable(_actions);
  }

  @override
  Future<ActionFollowThroughItem> proposeAction({
    required String caseVersionId,
    required String title,
    required String description,
    DateTime? targetCompletionDate,
  }) async {
    final newItem = ActionFollowThroughItem(
      id: 'action-preview-${DateTime.now().millisecondsSinceEpoch}',
      caseVersionId: caseVersionId,
      title: title,
      description: description,
      status: ActionFollowThroughStatus.proposed,
      progressPercentage: 0,
      createdAt: DateTime.now().toUtc(),
      targetCompletionDate: targetCompletionDate,
    );
    _actions.add(newItem);
    return newItem;
  }
}
