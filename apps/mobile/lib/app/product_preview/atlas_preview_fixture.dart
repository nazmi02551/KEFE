class AtlasCountryAverage {
  const AtlasCountryAverage({required this.countryCode, required this.value});

  final String countryCode;
  final double value;
}

abstract final class AtlasPreviewFixture {
  static const selectedCaseId = '11111111-1111-4111-8111-111111111112';
  static const selectedCaseFallbackTitle =
      'Yapay zekâ şirketlerinin veri toplaması sınırlandırılmalı mı?';

  static const countries = <AtlasCountryAverage>[
    AtlasCountryAverage(countryCode: 'TR', value: 7.1),
    AtlasCountryAverage(countryCode: 'DE', value: 5.4),
    AtlasCountryAverage(countryCode: 'US', value: 6.2),
    AtlasCountryAverage(countryCode: 'JP', value: 4.8),
    AtlasCountryAverage(countryCode: 'BR', value: 6.7),
    AtlasCountryAverage(countryCode: 'ID', value: 7.3),
  ];
}
