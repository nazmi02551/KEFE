import 'package:flutter/widgets.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Presentation-time localization boundary for server/fixture content strings.
///
/// Production content normally arrives already localized/pinned by CaseVersion and
/// therefore uses the pass-through implementation. Product Preview may override
/// this provider with a deterministic catalog without changing raw decision
/// values, ids, or repository semantics.
abstract interface class KefeContentLocalizer {
  const KefeContentLocalizer();

  String text({
    required String namespace,
    required String id,
    required Locale locale,
    required String fallback,
  });
}

class PassthroughKefeContentLocalizer implements KefeContentLocalizer {
  const PassthroughKefeContentLocalizer();

  @override
  String text({
    required String namespace,
    required String id,
    required Locale locale,
    required String fallback,
  }) => fallback;
}

final kefeContentLocalizerProvider = Provider<KefeContentLocalizer>(
  (_) => const PassthroughKefeContentLocalizer(),
);

abstract final class KefeContentNamespace {
  static const caseTitle = 'case.title';
  static const caseSummary = 'case.summary';
  static const questionPrompt = 'question.prompt';
  static const option = 'question.option';
  static const contextSourceTitle = 'context.source.title';
  static const contextPublisher = 'context.source.publisher';
  static const contextBlockTitle = 'context.block.title';
  static const contextBlockBody = 'context.block.body';
  static const perspectiveBody = 'perspective.body';
  static const perspectiveProvenance = 'perspective.provenance';
}
