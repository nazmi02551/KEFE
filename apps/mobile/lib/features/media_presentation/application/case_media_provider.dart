import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/case_media_repository.dart';

final caseMediaRepositoryProvider = Provider<CaseMediaRepository>(
  (ref) => const EmptyCaseMediaRepository(),
);
