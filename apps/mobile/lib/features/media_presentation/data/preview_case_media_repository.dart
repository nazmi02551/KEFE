import '../domain/case_media_models.dart';
import 'case_media_repository.dart';

class PreviewCaseMediaRepository implements CaseMediaRepository {
  const PreviewCaseMediaRepository();

  static const _assets = <String, _PreviewMediaSpec>{
    '22222222-2222-4222-8222-222222222222': _PreviewMediaSpec(
      key: 'RESOURCE_PRIORITY',
      hash: '118bd82cf9763acd990df701a8d2374a202d63be8eaf99cae7c3da8d1459043c',
      alt:
          'İki farklı ihtiyacı temsil eden karşılıklı iki figür ve aralarında KEFE terazisi.',
    ),
    '22222222-2222-4222-8222-222222222223': _PreviewMediaSpec(
      key: 'DATA_NETWORK',
      hash: 'db9749500b0f9b370c05509abb5aa877c71387e457bc8c1b31b7e3458da2a463',
      alt:
          'Bir veri ağı, bağlantı düğümleri ve koruma kalkanını temsil eden soyut KEFE illüstrasyonu.',
    ),
    '22222222-2222-4222-8222-222222222224': _PreviewMediaSpec(
      key: 'SPORTS_DECISION',
      hash: 'f33ef847f50971e031e7a92b63eae0d9dc0be5226faa8169dfeede094c09f6c1',
      alt:
          'Futbol sahası, top ve karar anını temsil eden soyut KEFE illüstrasyonu.',
    ),
    '22222222-2222-4222-8222-222222222225': _PreviewMediaSpec(
      key: 'CIVIC_TRANSPARENCY',
      hash: '11fd4b5261d5163238c8ba814504104f8f8e0ad8a218333a6c721f57c4871d71',
      alt:
          'Kamu belgesi, bina ve görünürlük fikrini temsil eden soyut KEFE illüstrasyonu.',
    ),
    '22222222-2222-4222-8222-222222222226': _PreviewMediaSpec(
      key: 'REMOTE_WORK',
      hash: 'f3d7b3760ab1fa8118270898f406b0895b628bac9689b2af9a86b824e4a66cfb',
      alt:
          'Ev ve iş alanlarını bağlayan çalışma düzenini temsil eden soyut KEFE illüstrasyonu.',
    ),
    '22222222-2222-4222-8222-222222222227': _PreviewMediaSpec(
      key: 'AIR_TRAVEL',
      hash: 'c284e1fde999efa6ec885224bd4d50cb46f280b6edea8e3166152b48115ae2a9',
      alt:
          'Uçak kabini, yan yana koltuklar ve aile bütünlüğünü temsil eden soyut KEFE illüstrasyonu.',
    ),
    '22222222-2222-4222-8222-222222222228': _PreviewMediaSpec(
      key: 'WORK_TRANSITION',
      hash: 'b07099e4b960404abd9145b65561c73639d8d61a375abe3dd2f88018f41dec2b',
      alt:
          'İnsan, yapay zekâ ve yeniden öğrenme geçişini temsil eden soyut KEFE illüstrasyonu.',
    ),
    '22222222-2222-4222-8222-222222222229': _PreviewMediaSpec(
      key: 'EDUCATION_AI',
      hash: 'bed6b5fd52537aeddda92b7747ea42af334194dc6931488c577eddf0cf12d678',
      alt:
          'Kitap, mezuniyet başlığı ve yapay zekâ sembollerini temsil eden soyut KEFE illüstrasyonu.',
    ),
  };

  @override
  Future<List<CaseMediaPresentation>> fetchForCaseVersion(
    String caseVersionId, {
    required CaseMediaSlot slot,
    required bool postCommitAvailable,
  }) async {
    final spec = _assets[caseVersionId];
    if (spec == null || slot == CaseMediaSlot.contextSupporting) {
      return const [];
    }

    return [
      CaseMediaPresentation(
        id: 'preview-media-$caseVersionId-${slot.code}',
        caseVersionId: caseVersionId,
        slot: slot,
        kind: CaseMediaKind.illustration,
        assetIdentity: 'preview-abstract:${spec.key}',
        assetContentHash: spec.hash,
        altText: spec.alt,
        exposurePhase: MediaExposurePhase.preCommitSafe,
        rendition: CaseMediaRendition(
          rendererCode: 'KEFE_ABSTRACT_V1',
          locator: spec.key,
          aspectRatio: slot == CaseMediaSlot.caseHero ? 1.85 : 1.55,
        ),
        attribution: 'KEFE Product Preview · temsili illüstrasyon',
      ),
    ];
  }
}

class _PreviewMediaSpec {
  const _PreviewMediaSpec({
    required this.key,
    required this.hash,
    required this.alt,
  });

  final String key;
  final String hash;
  final String alt;
}
