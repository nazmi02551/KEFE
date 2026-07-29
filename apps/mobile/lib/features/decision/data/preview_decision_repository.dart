import '../../context/data/context_repository.dart';
import '../../context/domain/context_models.dart';
import '../domain/decision_models.dart';
import 'decision_repository.dart';

class PreviewDecisionRepository
    implements
        DecisionRepository,
        FlowRuntimeRepository,
        DecisionLineageRepository,
        PerspectiveRepository,
        ContextRepository {
  static const caseId = '11111111-1111-4111-8111-111111111111';
  static const caseVersionId = '22222222-2222-4222-8222-222222222222';

  static const _reasonSchema = <String, Object?>{
    'tags': [
      'FAIRNESS',
      'NEED',
      'RESPONSIBILITY',
      'EMPATHY',
      'RULES',
      'CONSEQUENCE',
      'PROPORTIONALITY',
      'PRACTICAL_IMPACT',
    ],
    'max_tags': 3,
    'text_enabled': true,
    'text_max_length': 500,
  };

  static const _cases = <DecisionCase>[
    DecisionCase(
      id: caseId,
      versionId: caseVersionId,
      title: 'Son koltuk kime verilmeli?',
      summary: 'İki makul ihtiyaç arasında sınırlı bir kaynağı nasıl paylaştırırsın?',
      format: 'DILEMMA',
      domain: 'DAILY_LIFE',
      risk: 'L0',
      questions: [
        DecisionQuestion(
          id: '33333333-3333-4333-8333-333333333333',
          prompt: 'Son koltuğu kime verirdin?',
          responseType: 'SINGLE_CHOICE',
          options: ['Öncelikli ihtiyacı olana', 'Sırada önce olana'],
          responseSchema: {'reason': _reasonSchema},
        ),
        DecisionQuestion(
          id: '77777777-7777-4777-8777-777777777777',
          prompt: 'Bu kararından ne kadar eminsin?',
          responseType: 'CONFIDENCE',
          required: false,
          responseSchema: {'min': 1, 'max': 10, 'step': 1},
        ),
      ],
    ),
    DecisionCase(
      id: '11111111-1111-4111-8111-111111111112',
      versionId: '22222222-2222-4222-8222-222222222223',
      title: 'Yapay zekâ şirketlerinin veri toplaması sınırlandırılmalı mı?',
      summary: 'Kişiselleştirme ve inovasyon ile mahremiyet arasındaki dengeyi tart.',
      format: 'DILEMMA',
      domain: 'TECHNOLOGY',
      risk: 'L1',
      questions: [
        DecisionQuestion(
          id: '33333333-3333-4333-8333-333333333334',
          prompt: 'Daha sıkı veri toplama sınırlarını destekliyor musun?',
          responseType: 'SINGLE_CHOICE',
          options: ['Evet', 'Hayır'],
          responseSchema: {'reason': _reasonSchema},
        ),
        DecisionQuestion(
          id: '77777777-7777-4777-8777-777777777778',
          prompt: 'Bu kararından ne kadar eminsin?',
          responseType: 'CONFIDENCE',
          required: false,
          responseSchema: {'min': 1, 'max': 10, 'step': 1},
        ),
      ],
    ),
    DecisionCase(
      id: '11111111-1111-4111-8111-111111111113',
      versionId: '22222222-2222-4222-8222-222222222224',
      title: 'Bu pozisyonda penaltı kararı doğru muydu?',
      summary: 'Temas, avantaj ve VAR müdahalesi üzerinden bir Sports CALL yap.',
      format: 'SPORTS_CALL',
      domain: 'SPORTS',
      risk: 'L0',
      questions: [
        DecisionQuestion(
          id: '33333333-3333-4333-8333-333333333335',
          prompt: 'Hakemin penaltı kararını nasıl değerlendiriyorsun?',
          responseType: 'SINGLE_CHOICE',
          options: ['Doğru', 'Yanlış'],
          responseSchema: {'reason': _reasonSchema},
        ),
        DecisionQuestion(
          id: '77777777-7777-4777-8777-777777777779',
          prompt: 'Kararından ne kadar eminsin?',
          responseType: 'CONFIDENCE',
          required: false,
          responseSchema: {'min': 1, 'max': 10, 'step': 1},
        ),
      ],
    ),
    DecisionCase(
      id: '11111111-1111-4111-8111-111111111114',
      versionId: '22222222-2222-4222-8222-222222222225',
      title: 'Kamu sözleşmeleri varsayılan olarak herkese açık olmalı mı?',
      summary: 'Şeffaflık, ticari sır ve kamu yararı arasındaki sınırı belirle.',
      format: 'CIVIC',
      domain: 'CIVIC',
      risk: 'L1',
      questions: [
        DecisionQuestion(
          id: '33333333-3333-4333-8333-333333333336',
          prompt: 'Varsayılan açıklık ilkesini destekliyor musun?',
          responseType: 'SINGLE_CHOICE',
          options: ['Evet', 'Hayır'],
          responseSchema: {'reason': _reasonSchema},
        ),
        DecisionQuestion(
          id: '77777777-7777-4777-8777-777777777780',
          prompt: 'Bu kararından ne kadar eminsin?',
          responseType: 'CONFIDENCE',
          required: false,
          responseSchema: {'min': 1, 'max': 10, 'step': 1},
        ),
      ],
    ),
    DecisionCase(
      id: '11111111-1111-4111-8111-111111111115',
      versionId: '22222222-2222-4222-8222-222222222226',
      title: 'Uzaktan çalışanlar aynı yan haklara sahip olmalı mı?',
      summary: 'Çalışma biçimi değişse de eşitlik ve maliyet sorumluluğunu birlikte tart.',
      format: 'DILEMMA',
      domain: 'WORK_ECONOMY',
      risk: 'L0',
      questions: [
        DecisionQuestion(
          id: '33333333-3333-4333-8333-333333333337',
          prompt: 'Yan hakların çalışma yerine göre değişmemesini destekliyor musun?',
          responseType: 'SINGLE_CHOICE',
          options: ['Evet', 'Hayır'],
          responseSchema: {'reason': _reasonSchema},
        ),
        DecisionQuestion(
          id: '77777777-7777-4777-8777-777777777781',
          prompt: 'Bu kararından ne kadar eminsin?',
          responseType: 'CONFIDENCE',
          required: false,
          responseSchema: {'min': 1, 'max': 10, 'step': 1},
        ),
      ],
    ),
    DecisionCase(
      id: '11111111-1111-4111-8111-111111111116',
      versionId: '22222222-2222-4222-8222-222222222227',
      title: 'Çocuklar uçakta ebeveynleriyle ücretsiz yan yana oturmalı mı?',
      summary: 'Aile bütünlüğü, fiyatlandırma ve operasyonel esneklik arasındaki gerilimi tart.',
      format: 'DILEMMA',
      domain: 'DAILY_LIFE',
      risk: 'L0',
      questions: [
        DecisionQuestion(
          id: '33333333-3333-4333-8333-333333333338',
          prompt: 'Havayolları bunu ek ücret almadan garanti etmeli mi?',
          responseType: 'SINGLE_CHOICE',
          options: ['Evet', 'Hayır'],
          responseSchema: {'reason': _reasonSchema},
        ),
        DecisionQuestion(
          id: '77777777-7777-4777-8777-777777777782',
          prompt: 'Bu kararından ne kadar eminsin?',
          responseType: 'CONFIDENCE',
          required: false,
          responseSchema: {'min': 1, 'max': 10, 'step': 1},
        ),
      ],
    ),
    DecisionCase(
      id: '11111111-1111-4111-8111-111111111117',
      versionId: '22222222-2222-4222-8222-222222222228',
      title: 'YZ nedeniyle işten çıkarma öncesi yeniden eğitim zorunlu olmalı mı?',
      summary: 'Verimlilik, işveren sorumluluğu ve çalışanların uyum hakkını tart.',
      format: 'DILEMMA',
      domain: 'WORK_ECONOMY',
      risk: 'L1',
      questions: [
        DecisionQuestion(
          id: '33333333-3333-4333-8333-333333333339',
          prompt: 'Yeniden eğitim teklifinin zorunlu olmasını destekliyor musun?',
          responseType: 'SINGLE_CHOICE',
          options: ['Evet', 'Hayır'],
          responseSchema: {'reason': _reasonSchema},
        ),
        DecisionQuestion(
          id: '77777777-7777-4777-8777-777777777783',
          prompt: 'Bu kararından ne kadar eminsin?',
          responseType: 'CONFIDENCE',
          required: false,
          responseSchema: {'min': 1, 'max': 10, 'step': 1},
        ),
      ],
    ),
    DecisionCase(
      id: '11111111-1111-4111-8111-111111111118',
      versionId: '22222222-2222-4222-8222-222222222229',
      title: 'Üniversitelerde üretken YZ kullanımı sınırlandırılmalı mı?',
      summary: 'Öğrenme, akademik dürüstlük ve yeni araçlara uyum arasındaki dengeyi tart.',
      format: 'DILEMMA',
      domain: 'EDUCATION',
      risk: 'L0',
      questions: [
        DecisionQuestion(
          id: '33333333-3333-4333-8333-333333333340',
          prompt: 'Ders ve ödevlerde daha sıkı YZ sınırlarını destekliyor musun?',
          responseType: 'SINGLE_CHOICE',
          options: ['Evet', 'Hayır'],
          responseSchema: {'reason': _reasonSchema},
        ),
        DecisionQuestion(
          id: '77777777-7777-4777-8777-777777777784',
          prompt: 'Bu kararından ne kadar eminsin?',
          responseType: 'CONFIDENCE',
          required: false,
          responseSchema: {'min': 1, 'max': 10, 'step': 1},
        ),
      ],
    ),
  ];

  final Set<String> _committedSessions = <String>{};
  final Map<String, DecisionCase> _sessionCases = <String, DecisionCase>{};
  DecisionCase _activeCase = _cases.first;
  int _sessionCounter = 0;

  @override
  Future<GuestCredential> ensureGuestCredential() async => GuestCredential(
        actorId: 'preview-actor',
        accessToken: 'preview-token',
        expiresAt: DateTime.utc(2030),
      );

  @override
  Future<List<DecisionCaseSummary>> fetchExploreCases({int limit = 20}) async =>
      _cases
          .take(limit)
          .map(
            (item) => DecisionCaseSummary(
              id: item.id,
              versionId: item.versionId,
              title: item.title,
              summary: item.summary,
              format: item.format,
              domain: item.domain,
              risk: item.risk,
            ),
          )
          .toList(growable: false);

  @override
  Future<DecisionCase> fetchCase(String requestedCaseId) async {
    final item = _cases.where((candidate) => candidate.id == requestedCaseId).firstOrNull;
    if (item == null) {
      throw StateError('Unknown preview Case: $requestedCaseId');
    }
    _activeCase = item;
    return item;
  }

  @override
  Future<String> startSession(String requestedCaseId) async {
    final item = await fetchCase(requestedCaseId);
    final sessionId = 'preview-${item.id}-${++_sessionCounter}';
    _sessionCases[sessionId] = item;
    _committedSessions.remove(sessionId);
    return sessionId;
  }

  @override
  Future<FlowRuntimeSnapshot> fetchFlowRuntime(String sessionId) async {
    final item = _sessionCases[sessionId] ?? _activeCase;
    _sessionCases[sessionId] = item;
    final committed = _committedSessions.contains(sessionId);
    return FlowRuntimeSnapshot(
      sessionId: sessionId,
      caseVersionId: item.versionId,
      sessionState: committed ? 'COMMITTED' : 'DRAFT',
      templateCode: 'STANDARD_COMMIT_REVEAL',
      templateVersionNo: 1,
      entryStepCode: 'CONTEXT',
      executionSupport: FlowExecutionSupport.full,
      steps: [
        const FlowRuntimeStep(
          code: 'CONTEXT',
          primitiveCode: 'CONTEXT',
          capabilityCodes: ['SOURCE_REVEAL'],
          nextStepCodes: ['DECISION'],
          state: FlowStepRuntimeState.ready,
        ),
        FlowRuntimeStep(
          code: 'DECISION',
          primitiveCode: 'DECISION',
          capabilityCodes: const ['COMMIT_FIRST', 'CONFIDENCE_CAPTURE'],
          nextStepCodes: const ['RESULT'],
          state: committed
              ? FlowStepRuntimeState.completed
              : FlowStepRuntimeState.ready,
        ),
        FlowRuntimeStep(
          code: 'RESULT',
          primitiveCode: 'COLLECTIVE_RESULT',
          capabilityCodes: const [],
          nextStepCodes: const [],
          state: committed
              ? FlowStepRuntimeState.ready
              : FlowStepRuntimeState.blocked,
          reasonCode: committed ? null : 'FLOW_COMMIT_REQUIRED',
        ),
      ],
    );
  }

  @override
  Future<void> recordFlowStepExposure({
    required String sessionId,
    required String stepCode,
    required String idempotencyKey,
  }) async {}

  @override
  Future<void> answerRevision({
    required String sessionId,
    required String stepCode,
    required String questionId,
    required Object value,
  }) async {}

  @override
  Future<void> saveRevisionReason({
    required String sessionId,
    required String stepCode,
    required List<String> tags,
    required String? text,
  }) async {}

  @override
  Future<void> commitRevision({
    required String sessionId,
    required String stepCode,
    required String idempotencyKey,
  }) async {
    _committedSessions.add(sessionId);
  }

  @override
  Future<void> answer({
    required String sessionId,
    required String questionId,
    required Object value,
  }) async {}

  @override
  Future<void> savePrivateReason({
    required String sessionId,
    required List<String> tags,
    required String? text,
  }) async {}

  @override
  Future<void> commit({
    required String sessionId,
    required String idempotencyKey,
  }) async {
    _committedSessions.add(sessionId);
  }

  @override
  Future<RevealResult> reveal(String sessionId) async {
    final item = _sessionCases[sessionId] ?? _activeCase;
    final sports = item.domain == 'SPORTS';
    final seat = item.id == caseId;
    return RevealResult(
      layer: 'TRUSTED',
      sampleSize: sports ? 18472 : seat ? 1284 : 6240,
      confidence: 'HIGH',
      values: sports
          ? const {'Doğru': 0.57, 'Yanlış': 0.43}
          : seat
              ? const {
                  'Öncelikli ihtiyacı olana': 0.61,
                  'Sırada önce olana': 0.39,
                }
              : const {'Evet': 0.64, 'Hayır': 0.36},
    );
  }

  @override
  Future<PerspectiveResult> fetchPerspectives(String sessionId) async {
    final item = _sessionCases[sessionId] ?? _activeCase;
    final topic = item.title;
    return PerspectiveResult(
      sessionId: sessionId,
      caseVersionId: item.versionId,
      cards: [
        PerspectiveCard(
          id: 'preview-near-${item.id}',
          slot: PerspectiveSlot.near,
          body: 'Bu yaklaşım, kararın doğrudan etkilenen kişilere vereceği pratik sonucu öncelemeyi savunuyor.',
          sourceKind: 'CURATED',
          provenanceLabel: 'KEFE Preview · Editoryal örnek',
          moderationState: 'NOT_REQUIRED',
        ),
        PerspectiveCard(
          id: 'preview-opposing-${item.id}',
          slot: PerspectiveSlot.opposing,
          body: 'Karşı görüş, tek bir iyi niyetli istisnanın genel kuralı zayıflatabileceğini ve öngörülebilirliğin de adaletin parçası olduğunu söylüyor.',
          sourceKind: 'CURATED',
          provenanceLabel: 'KEFE Preview · Editoryal örnek',
          moderationState: 'NOT_REQUIRED',
        ),
        PerspectiveCard(
          id: 'preview-bridge-${item.id}',
          slot: PerspectiveSlot.bridge,
          body: 'Köprü yaklaşım, “$topic” tartışmasında hem açık bir temel kural hem de dar, denetlenebilir istisnalar tasarlamayı öneriyor.',
          sourceKind: 'CURATED',
          provenanceLabel: 'KEFE Preview · Editoryal örnek',
          moderationState: 'NOT_REQUIRED',
        ),
      ],
      methodology: PerspectiveMethodology(
        mode: 'DEGRADED_CURATED',
        sampleKind: 'CURATED_FALLBACK',
        sampleSize: 3,
        generatedAt: DateTime.utc(2026, 7, 29),
        provenanceNote: 'Product Preview için sabit, editoryal demo perspektifleri.',
      ),
    );
  }

  @override
  Future<CaseContextSnapshot> fetchContext(String requestedCaseVersionId) async {
    final item = _cases
        .where((candidate) => candidate.versionId == requestedCaseVersionId)
        .firstOrNull;
    if (item == null) {
      return CaseContextSnapshot(
        caseVersionId: requestedCaseVersionId,
        blocks: const [],
        sources: const [],
      );
    }

    final sourceId = 'preview-source-${item.id}';
    return CaseContextSnapshot(
      caseVersionId: item.versionId,
      sources: [
        CaseContextSource(
          id: sourceId,
          title: 'KEFE Product Preview senaryosu',
          publisher: 'KEFE Editoryal',
          sourceKind: 'EDITORIAL',
          url: null,
          publishedAt: DateTime.utc(2026, 7, 29),
        ),
      ],
      blocks: [
        CaseContextBlock(
          id: 'preview-context-a-${item.id}',
          displayOrder: 1,
          disclosureLevel: 'ESSENTIAL',
          title: 'Ne tartıyoruz?',
          body: item.summary,
          claimStatus: 'VERIFIED',
          sourceIds: [sourceId],
        ),
        CaseContextBlock(
          id: 'preview-context-b-${item.id}',
          displayOrder: 2,
          disclosureLevel: 'ESSENTIAL',
          title: 'Karar gerilimi',
          body: _tensionFor(item.domain),
          claimStatus: 'CLAIMED',
          sourceIds: [sourceId],
        ),
        CaseContextBlock(
          id: 'preview-context-c-${item.id}',
          displayOrder: 3,
          disclosureLevel: 'DETAIL',
          title: 'Preview notu',
          body: 'Bu içerik canlı haber değildir. KEFE’nin ürün akışını, kaynak ayrımını ve Commit öncesi karar deneyimini test etmek için hazırlanmış temsili bir senaryodur.',
          claimStatus: 'VERIFIED',
          sourceIds: [sourceId],
        ),
      ],
    );
  }

  String _tensionFor(String domain) => switch (domain) {
        'TECHNOLOGY' =>
          'Mahremiyet ve kullanıcı kontrolü; kişiselleştirme, inovasyon ve hizmet kalitesiyle aynı anda korunmaya çalışılıyor.',
        'SPORTS' =>
          'Kuralın teknik uygulanışı ile oyunun akışı, temasın etkisi ve hakemin yorum alanı birlikte değerlendiriliyor.',
        'CIVIC' =>
          'Kamusal şeffaflık ve hesap verebilirlik; hukuki sınırlar, gizlilik ve uygulanabilirlikle dengeleniyor.',
        'WORK_ECONOMY' =>
          'Çalışan hakkı ve fırsat eşitliği; maliyet, verimlilik ve işverenin operasyonel sorumluluğuyla karşı karşıya geliyor.',
        'EDUCATION' =>
          'Öğrenme ve akademik dürüstlük; yeni araçları öğrenme, erişim eşitliği ve ölçme güvenilirliğiyle birlikte ele alınıyor.',
        _ =>
          'Eşit kural uygulaması ile bireysel ihtiyaç, bağlam ve orantılılık arasında gerçek bir tercih oluşuyor.',
      };
}
