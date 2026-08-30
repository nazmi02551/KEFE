class PrivacyExportSummary {
  const PrivacyExportSummary({
    required this.totalRecords,
    required this.nonEmptyDatasetCount,
  });

  final int totalRecords;
  final int nonEmptyDatasetCount;

  static PrivacyExportSummary? tryParse(Map<String, Object?> export) {
    if (export['schema_version'] != 'privacy-export.v2') return null;

    final manifest = export['manifest'];
    if (manifest is! Map) return null;
    final rawCounts = manifest['dataset_counts'];
    final rawTotal = manifest['total_records'];
    final rawEmpty = manifest['empty_datasets'];
    if (rawCounts is! Map ||
        rawTotal is! int ||
        rawTotal < 0 ||
        rawEmpty is! List) {
      return null;
    }

    final counts = <String, int>{};
    var calculatedTotal = 0;
    for (final entry in rawCounts.entries) {
      final key = entry.key;
      final count = entry.value;
      if (key is! String || key.trim().isEmpty || count is! int || count < 0) {
        return null;
      }
      counts[key] = count;
      calculatedTotal += count;
    }
    if (calculatedTotal != rawTotal) return null;

    final emptyDatasets = <String>{};
    for (final value in rawEmpty) {
      if (value is! String ||
          value.trim().isEmpty ||
          !emptyDatasets.add(value)) {
        return null;
      }
    }
    final expectedEmpty = counts.entries
        .where((entry) => entry.value == 0)
        .map((entry) => entry.key)
        .toSet();
    if (emptyDatasets.length != expectedEmpty.length ||
        !emptyDatasets.containsAll(expectedEmpty)) {
      return null;
    }

    return PrivacyExportSummary(
      totalRecords: rawTotal,
      nonEmptyDatasetCount: counts.length - emptyDatasets.length,
    );
  }
}
