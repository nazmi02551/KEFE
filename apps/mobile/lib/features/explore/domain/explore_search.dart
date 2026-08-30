String normalizeExploreSearchText(String value) {
  final normalized = StringBuffer();
  for (final rune in value.runes) {
    final character = String.fromCharCode(rune);
    normalized.write(switch (character) {
      'I' || 'İ' || 'ı' || 'i' => 'i',
      'Ç' || 'ç' => 'c',
      'Ğ' || 'ğ' => 'g',
      'Ö' || 'ö' => 'o',
      'Ş' || 'ş' => 's',
      'Ü' || 'ü' => 'u',
      '\u0307' => '',
      _ => character.toLowerCase(),
    });
  }
  return normalized.toString().trim().replaceAll(RegExp(r'\s+'), ' ');
}

bool matchesExploreSearchQuery({
  required String query,
  required Iterable<String> fields,
}) {
  final normalizedQuery = normalizeExploreSearchText(query);
  if (normalizedQuery.isEmpty) {
    return true;
  }
  final searchable = fields.map(normalizeExploreSearchText).join(' ');
  return normalizedQuery.split(' ').every(searchable.contains);
}
