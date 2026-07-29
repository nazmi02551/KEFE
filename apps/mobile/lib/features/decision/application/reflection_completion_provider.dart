import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/reflection_completion_store.dart';

final reflectionCompletionStoreProvider = Provider<ReflectionCompletionStore>(
  (ref) => SharedPreferencesReflectionCompletionStore(),
);
