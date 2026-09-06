import '../domain/signal_consensus_card_models.dart';
import 'signal_repository.dart';

class PreviewSignalRepository implements SignalRepository {
  static final List<SignalConsensusCardModel> _previewCards = [
    SignalConsensusCardModel(
      signalId: '77777777-7777-4777-8777-777777777701',
      caseVersionId: '22222222-2222-4222-8222-222222222222',
      caseTitle: 'Son koltuk kime verilmeli?',
      consensusStatement:
          'Öncelikli ihtiyacı olan yurttaşlara pozitif ayrımcılık kamu vicdanında yüksek uzlaşı taşımaktadır.',
      agreementPercentage: 82.4,
      sampleSize: 1420,
      confidenceTier: SignalConfidenceTierModel.gold,
      certifiedAt: DateTime.utc(2026, 8, 15, 12, 0),
    ),
    SignalConsensusCardModel(
      signalId: '77777777-7777-4777-8777-777777777702',
      caseVersionId: '22222222-2222-4222-8222-222222222223',
      caseTitle: 'Yapay zekâ şirketlerinin veri toplaması sınırlandırılmalı mı?',
      consensusStatement:
          'Kişisel mahremiyet ve açık rıza olmaksızın model eğitimi sınırlandırılmalıdır.',
      agreementPercentage: 76.8,
      sampleSize: 1150,
      confidenceTier: SignalConfidenceTierModel.gold,
      certifiedAt: DateTime.utc(2026, 8, 20, 14, 30),
    ),
    SignalConsensusCardModel(
      signalId: '77777777-7777-4777-8777-777777777703',
      caseVersionId: '22222222-2222-4222-8222-222222222225',
      caseTitle: 'Kamu sözleşmeleri varsayılan olarak herkese açık olmalı mı?',
      consensusStatement:
          'Ticari sır kısıtlaması daraltılarak kamu ihalelerinde tam şeffaflık sağlanmalıdır.',
      agreementPercentage: 69.2,
      sampleSize: 780,
      confidenceTier: SignalConfidenceTierModel.silver,
      certifiedAt: DateTime.utc(2026, 8, 25, 9, 15),
    ),
  ];

  @override
  Future<List<SignalConsensusCardModel>> fetchSignalConsensusCards() async {
    return List.unmodifiable(_previewCards);
  }
}
