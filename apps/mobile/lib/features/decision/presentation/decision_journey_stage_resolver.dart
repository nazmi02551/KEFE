import '../domain/decision_models.dart';

abstract final class DecisionJourneyStageResolver {
  static FlowRuntimeStep? primary(FlowRuntimeSnapshot runtime) {
    for (final step in runtime.steps.reversed) {
      if (step.state == FlowStepRuntimeState.ready) return step;
    }
    for (final step in runtime.steps.reversed) {
      if (step.state == FlowStepRuntimeState.unsupported) return step;
    }
    for (final step in runtime.steps.reversed) {
      if (step.state == FlowStepRuntimeState.completed) return step;
    }
    return null;
  }

  static int ordinal(FlowRuntimeSnapshot runtime, FlowRuntimeStep active) {
    final index = runtime.steps.indexWhere((step) => step.code == active.code);
    return index < 0 ? 1 : index + 1;
  }

  static bool isRepeatedDecision(
    FlowRuntimeSnapshot runtime,
    FlowRuntimeStep active,
  ) {
    if (active.primitiveCode != 'DECISION') return false;
    final activeIndex = runtime.steps.indexWhere(
      (step) => step.code == active.code,
    );
    if (activeIndex <= 0) return false;
    return runtime.steps
        .take(activeIndex)
        .any((step) => step.primitiveCode == 'DECISION');
  }
}
