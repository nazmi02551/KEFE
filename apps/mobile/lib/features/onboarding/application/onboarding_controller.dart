import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/onboarding_store.dart';

final onboardingStoreProvider = Provider<OnboardingStore>(
  (ref) => SharedPreferencesOnboardingStore(),
);

class OnboardingController {
  OnboardingController(this._store);

  final OnboardingStore _store;

  Future<bool> isCompleted() => _store.isCompleted();

  Future<void> complete() => _store.markCompleted();
}

final onboardingControllerProvider = Provider<OnboardingController>(
  (ref) => OnboardingController(ref.watch(onboardingStoreProvider)),
);
