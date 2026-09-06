import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/institution_response_repository.dart';
import '../domain/institution_response_models.dart';

class InstitutionResponseState {
  const InstitutionResponseState({
    this.loading = false,
    this.items = const [],
    this.errorCode,
  });

  final bool loading;
  final List<InstitutionResponseItem> items;
  final String? errorCode;
}

final institutionResponseControllerProvider =
    NotifierProvider<InstitutionResponseController, InstitutionResponseState>(
      InstitutionResponseController.new,
    );

class InstitutionResponseController
    extends Notifier<InstitutionResponseState> {
  InstitutionResponseRepository get _repository =>
      ref.read(institutionResponseRepositoryProvider);

  @override
  InstitutionResponseState build() {
    Future.microtask(load);
    return const InstitutionResponseState(loading: true);
  }

  Future<void> load({String? caseVersionId}) async {
    state = const InstitutionResponseState(loading: true);
    try {
      final items = await _repository.fetchInstitutionResponses(
        caseVersionId: caseVersionId,
      );
      state = InstitutionResponseState(items: items);
    } catch (_) {
      state = const InstitutionResponseState(
        errorCode: 'FAILED_TO_LOAD_INSTITUTION_RESPONSES',
      );
    }
  }
}
