import 'package:shared_preferences/shared_preferences.dart';

abstract interface class OnboardingStore {
  Future<bool> isCompleted();
  Future<void> markCompleted();
}

class SharedPreferencesOnboardingStore implements OnboardingStore {
  SharedPreferencesOnboardingStore({SharedPreferences? preferences})
    : _preferences = preferences;

  static const _completedKey = 'kefe.onboarding.completed.v1';

  SharedPreferences? _preferences;

  Future<SharedPreferences> _prefs() async {
    return _preferences ??= await SharedPreferences.getInstance();
  }

  @override
  Future<bool> isCompleted() async {
    final preferences = await _prefs();
    return preferences.getBool(_completedKey) ?? false;
  }

  @override
  Future<void> markCompleted() async {
    final preferences = await _prefs();
    await preferences.setBool(_completedKey, true);
  }
}

class MemoryOnboardingStore implements OnboardingStore {
  bool completed = false;

  @override
  Future<bool> isCompleted() async => completed;

  @override
  Future<void> markCompleted() async => completed = true;
}
