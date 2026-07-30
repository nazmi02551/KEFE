import 'privacy_repository.dart';

class PreviewPrivacyRepository implements PrivacyRepository {
  bool _deleted = false;

  @override
  Future<Map<String, Object?>> export() async {
    return {
      'preview': true,
      'deleted': _deleted,
      'retention': {'mode': 'PRODUCT_PREVIEW_SAMPLE_ONLY'},
      'product_data': {
        'note':
            'No production credentials or another actor data are present in Product Preview.',
      },
    };
  }

  @override
  Future<PrivacyDeletionReceipt> delete() async {
    _deleted = true;
    return PrivacyDeletionReceipt(
      receiptId: 'preview-deletion-receipt',
      deletedAt: DateTime.now().toUtc(),
      policyVersion: 'PRODUCT_PREVIEW_ONLY',
    );
  }
}
