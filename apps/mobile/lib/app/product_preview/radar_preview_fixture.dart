class RadarPreviewItem {
  const RadarPreviewItem({
    required this.rank,
    required this.caseId,
    required this.domainCode,
    required this.signalCode,
    required this.fallbackTitle,
  });

  final int rank;
  final String caseId;
  final String domainCode;
  final String signalCode;
  final String fallbackTitle;
}

abstract final class RadarPreviewFixture {
  static const items = <RadarPreviewItem>[
    RadarPreviewItem(
      rank: 1,
      caseId: '11111111-1111-4111-8111-111111111112',
      domainCode: 'TECH_GLOBAL',
      signalCode: 'RISING_DISCUSSION',
      fallbackTitle:
          'Yapay zekâ şirketlerinin veri toplaması sınırlandırılmalı mı?',
    ),
    RadarPreviewItem(
      rank: 2,
      caseId: '11111111-1111-4111-8111-111111111113',
      domainCode: 'SPORTS',
      signalCode: 'SPORTS_CALL',
      fallbackTitle: 'Tartışmalı penaltı kararı doğru muydu?',
    ),
    RadarPreviewItem(
      rank: 3,
      caseId: '11111111-1111-4111-8111-111111111117',
      domainCode: 'WORK',
      signalCode: 'WORK_ECONOMY',
      fallbackTitle:
          'YZ nedeniyle işten çıkarma öncesi yeniden eğitim zorunlu olmalı mı?',
    ),
    RadarPreviewItem(
      rank: 4,
      caseId: '11111111-1111-4111-8111-111111111116',
      domainCode: 'DAILY_LIFE',
      signalCode: 'DAILY_DILEMMA',
      fallbackTitle:
          'Çocuklar uçakta ebeveynleriyle ücretsiz yan yana oturmalı mı?',
    ),
    RadarPreviewItem(
      rank: 5,
      caseId: '11111111-1111-4111-8111-111111111118',
      domainCode: 'EDUCATION',
      signalCode: 'EDUCATION',
      fallbackTitle:
          'Üniversitelerde üretken YZ kullanımı sınırlandırılmalı mı?',
    ),
  ];
}
