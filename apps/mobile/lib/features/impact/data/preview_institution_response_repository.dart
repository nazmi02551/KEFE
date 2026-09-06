import '../domain/institution_response_models.dart';
import 'institution_response_repository.dart';

class PreviewInstitutionResponseRepository
    implements InstitutionResponseRepository {
  static final List<InstitutionResponseItem> _previewResponses = [
    InstitutionResponseItem(
      id: '88888888-8888-4888-8888-888888888801',
      caseVersionId: '22222222-2222-4222-8222-222222222222',
      institutionName: 'Ulaştırma ve Altyapı Denetleme Kurulu',
      authorityRole: 'Halkla İlişkiler ve Yolcu Hakları Dairesi',
      verificationStatus: AuthorityVerificationStatus.verified,
      responseType: InstitutionResponseType.policyChange,
      statement:
          'Topluluk müzakereleri ve yüksek uzlaşı verileri dikkate alınarak öncelikli yolcu kontenjanı genelgeye eklenmiştir.',
      publishedAt: DateTime.utc(2026, 8, 28, 11, 0),
      milestoneDate: DateTime.utc(2026, 10, 1),
    ),
    InstitutionResponseItem(
      id: '88888888-8888-4888-8888-888888888802',
      caseVersionId: '22222222-2222-4222-8222-222222222223',
      institutionName: 'Kişisel Verileri Koruma Kurumu (KVKK)',
      authorityRole: 'Veri Güvenliği ve Yapay Zekâ İzleme Masası',
      verificationStatus: AuthorityVerificationStatus.verified,
      responseType: InstitutionResponseType.commitment,
      statement:
          'Model eğitimi amaçlı veri toplama süreçlerine ilişkin şeffaflık kılavuzu taslağı kamuoyu görüşüne açılmıştır.',
      publishedAt: DateTime.utc(2026, 8, 30, 15, 30),
      milestoneDate: DateTime.utc(2026, 11, 15),
    ),
  ];

  @override
  Future<List<InstitutionResponseItem>> fetchInstitutionResponses({
    String? caseVersionId,
  }) async {
    if (caseVersionId != null) {
      return _previewResponses
          .where((r) => r.caseVersionId == caseVersionId)
          .toList(growable: false);
    }
    return List.unmodifiable(_previewResponses);
  }
}
