import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../domain/signal_consensus_card_models.dart';
import 'preview_signal_repository.dart';

abstract class SignalRepository {
  Future<List<SignalConsensusCardModel>> fetchSignalConsensusCards();
}

final signalRepositoryProvider = Provider<SignalRepository>((ref) {
  return PreviewSignalRepository();
});
