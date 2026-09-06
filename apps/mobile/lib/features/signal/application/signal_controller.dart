import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/signal_repository.dart';
import '../domain/signal_consensus_card_models.dart';

class SignalState {
  const SignalState({
    this.loading = false,
    this.cards = const [],
    this.errorCode,
  });

  final bool loading;
  final List<SignalConsensusCardModel> cards;
  final String? errorCode;
}

final signalControllerProvider =
    NotifierProvider<SignalController, SignalState>(SignalController.new);

class SignalController extends Notifier<SignalState> {
  SignalRepository get _repository => ref.read(signalRepositoryProvider);

  @override
  SignalState build() {
    Future.microtask(load);
    return const SignalState(loading: true);
  }

  Future<void> load() async {
    state = const SignalState(loading: true);
    try {
      final cards = await _repository.fetchSignalConsensusCards();
      state = SignalState(cards: cards);
    } catch (_) {
      state = const SignalState(errorCode: 'FAILED_TO_LOAD_SIGNALS');
    }
  }
}
