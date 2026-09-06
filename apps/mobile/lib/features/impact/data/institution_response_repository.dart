import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../domain/institution_response_models.dart';
import 'preview_institution_response_repository.dart';

abstract class InstitutionResponseRepository {
  Future<List<InstitutionResponseItem>> fetchInstitutionResponses({
    String? caseVersionId,
  });
}

final institutionResponseRepositoryProvider =
    Provider<InstitutionResponseRepository>((ref) {
      return PreviewInstitutionResponseRepository();
    });
