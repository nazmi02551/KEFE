import '../domain/progress_models.dart';

abstract interface class ProgressRepository {
  Future<ProgressEnvelope> fetchProgress();
}
