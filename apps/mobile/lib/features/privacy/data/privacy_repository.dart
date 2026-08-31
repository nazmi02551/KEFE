abstract interface class PrivacyRepository {
  Future<Map<String, Object?>> export();

  Future<PrivacyDeletionReceipt> delete();
}

class PrivacyDeletionReceipt {
  const PrivacyDeletionReceipt({
    required this.receiptId,
    required this.deletedAt,
    required this.policyVersion,
    this.isProductPreview = false,
  });

  final String receiptId;
  final DateTime deletedAt;
  final String policyVersion;
  final bool isProductPreview;
}
