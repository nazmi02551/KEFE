class AtlasCountryAverage {
  const AtlasCountryAverage({
    required this.countryCode,
    required this.value,
    required this.markerX,
    required this.markerY,
  }) : assert(value >= 0 && value <= 10),
       assert(markerX >= 0 && markerX <= 1),
       assert(markerY >= 0 && markerY <= 1);

  final String countryCode;
  final double value;
  final double markerX;
  final double markerY;
}

abstract final class AtlasPreviewFixture {
  static const selectedCaseId = '11111111-1111-4111-8111-111111111112';
  static const selectedCaseFallbackTitle =
      'Yapay zekâ şirketlerinin veri toplaması sınırlandırılmalı mı?';

  static const countries = <AtlasCountryAverage>[
    AtlasCountryAverage(
      countryCode: 'TR',
      value: 7.1,
      markerX: 0.58,
      markerY: 0.38,
    ),
    AtlasCountryAverage(
      countryCode: 'DE',
      value: 5.4,
      markerX: 0.48,
      markerY: 0.30,
    ),
    AtlasCountryAverage(
      countryCode: 'US',
      value: 6.2,
      markerX: 0.22,
      markerY: 0.36,
    ),
    AtlasCountryAverage(
      countryCode: 'JP',
      value: 4.8,
      markerX: 0.79,
      markerY: 0.39,
    ),
    AtlasCountryAverage(
      countryCode: 'BR',
      value: 6.7,
      markerX: 0.34,
      markerY: 0.67,
    ),
    AtlasCountryAverage(
      countryCode: 'ID',
      value: 7.3,
      markerX: 0.70,
      markerY: 0.68,
    ),
  ];
}
