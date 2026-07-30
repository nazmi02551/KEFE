import 'package:flutter/widgets.dart';

import '../../core/localization/kefe_content_localizer.dart';

class PreviewContentLocalizer implements KefeContentLocalizer {
  const PreviewContentLocalizer();

  static const _en = <String, String>{
    'case.title:11111111-1111-4111-8111-111111111111':
        'Who should get the last seat?',
    'case.summary:11111111-1111-4111-8111-111111111111':
        'How would you allocate a limited resource between two reasonable needs?',
    'case.title:11111111-1111-4111-8111-111111111112':
        "Should AI companies' personal data collection be limited?",
    'case.summary:11111111-1111-4111-8111-111111111112':
        'Weigh personalization and innovation against privacy.',
    'case.title:11111111-1111-4111-8111-111111111113':
        'Was the penalty decision correct?',
    'case.summary:11111111-1111-4111-8111-111111111113':
        'Make a Sports CALL by weighing contact, advantage and VAR intervention.',
    'case.title:11111111-1111-4111-8111-111111111114':
        'Should public contracts be open by default?',
    'case.summary:11111111-1111-4111-8111-111111111114':
        'Weigh transparency, commercial confidentiality and the public interest.',
    'case.title:11111111-1111-4111-8111-111111111115':
        'Should remote workers receive the same benefits?',
    'case.summary:11111111-1111-4111-8111-111111111115':
        'Weigh equality and cost responsibility as the way of working changes.',
    'case.title:11111111-1111-4111-8111-111111111116':
        'Should children sit next to their parents on flights at no extra charge?',
    'case.summary:11111111-1111-4111-8111-111111111116':
        'Weigh family cohesion, pricing and operational flexibility.',
    'case.title:11111111-1111-4111-8111-111111111117':
        'Should retraining be required before AI-related layoffs?',
    'case.summary:11111111-1111-4111-8111-111111111117':
        'Weigh efficiency, employer responsibility and workers’ right to adapt.',
    'case.title:11111111-1111-4111-8111-111111111118':
        'Should generative AI use be limited at universities?',
    'case.summary:11111111-1111-4111-8111-111111111118':
        'Weigh learning, academic integrity and adapting to new tools.',

    'question.prompt:33333333-3333-4333-8333-333333333333':
        'Who would you give the last seat to?',
    'question.prompt:33333333-3333-4333-8333-333333333334':
        'Do you support stricter limits on data collection?',
    'question.prompt:33333333-3333-4333-8333-333333333335':
        "How do you assess the referee's penalty decision?",
    'question.prompt:33333333-3333-4333-8333-333333333336':
        'Do you support openness by default?',
    'question.prompt:33333333-3333-4333-8333-333333333337':
        'Should benefits stay the same regardless of work location?',
    'question.prompt:33333333-3333-4333-8333-333333333338':
        'Should airlines guarantee this without an extra fee?',
    'question.prompt:33333333-3333-4333-8333-333333333339':
        'Do you support requiring a retraining offer first?',
    'question.prompt:33333333-3333-4333-8333-333333333340':
        'Do you support stricter AI limits in courses and assignments?',
    'question.prompt:77777777-7777-4777-8777-777777777777':
        'How confident are you in this decision?',
    'question.prompt:77777777-7777-4777-8777-777777777778':
        'How confident are you in this decision?',
    'question.prompt:77777777-7777-4777-8777-777777777779':
        'How confident are you in your decision?',
    'question.prompt:77777777-7777-4777-8777-777777777780':
        'How confident are you in this decision?',
    'question.prompt:77777777-7777-4777-8777-777777777781':
        'How confident are you in this decision?',
    'question.prompt:77777777-7777-4777-8777-777777777782':
        'How confident are you in this decision?',
    'question.prompt:77777777-7777-4777-8777-777777777783':
        'How confident are you in this decision?',
    'question.prompt:77777777-7777-4777-8777-777777777784':
        'How confident are you in this decision?',

    'question.option:Evet': 'Yes',
    'question.option:Hayır': 'No',
    'question.option:Doğru': 'Correct',
    'question.option:Yanlış': 'Incorrect',
    'question.option:Öncelikli ihtiyacı olana': 'The person with priority need',
    'question.option:Sırada önce olana': 'The person first in line',

    'context.source.title:preview-journey-counterview-source':
        'KEFE Product Preview · counter-view scenario',
    'context.source.publisher:KEFE Editoryal': 'KEFE Editorial',
    'context.block.title:preview-journey-counterview': 'Counter-view',
    'context.block.body:preview-journey-counterview':
        'The counter-view argues that a free adjacent-seat guarantee can be difficult because seat inventory may change late, several fare classes are managed on the same flight, and a strict guarantee can affect other passengers’ seat choices.',
    'context.block.title:preview-journey-retest-note': 'Weigh it again now',
    'context.block.body:preview-journey-retest-note':
        'Seeing this counter-view does not automatically make your first decision right or wrong. Weigh the same question again; KEFE records only the observed difference between the two decisions.',
    'context.block.title:preview-journey-disclosure': 'Preview note',
    'context.block.body:preview-journey-disclosure':
        'This counter-view and journey are representative Product Preview data, not live user or research results.',
  };

  @override
  String text({
    required String namespace,
    required String id,
    required Locale locale,
    required String fallback,
  }) {
    if (locale.languageCode != 'en') return fallback;

    final direct = _en['$namespace:$id'];
    if (direct != null) return direct;

    if (namespace == KefeContentNamespace.contextSourceTitle &&
        id.startsWith('preview-source-')) {
      return 'KEFE Product Preview scenario';
    }
    if (namespace == KefeContentNamespace.contextBlockTitle) {
      if (id.startsWith('preview-context-a-')) return 'What are we weighing?';
      if (id.startsWith('preview-context-b-')) return 'Decision tension';
      if (id.startsWith('preview-context-c-')) return 'Preview note';
    }
    if (namespace == KefeContentNamespace.contextBlockBody) {
      if (id.startsWith('preview-context-a-')) {
        final caseId = id.substring('preview-context-a-'.length);
        return _en['${KefeContentNamespace.caseSummary}:$caseId'] ?? fallback;
      }
      if (id.startsWith('preview-context-c-')) {
        return 'This is not live news. It is a representative scenario prepared to test KEFE’s product flow, source separation and pre-Commit decision experience.';
      }
      if (id.startsWith('preview-context-b-')) {
        return _englishTensionForCaseId(
          id.substring('preview-context-b-'.length),
        );
      }
    }
    if (namespace == KefeContentNamespace.perspectiveBody) {
      if (id.startsWith('preview-near-')) {
        return 'This perspective prioritizes the practical effect the decision may have on the people directly affected.';
      }
      if (id.startsWith('preview-opposing-')) {
        return 'The opposing view argues that even a well-intentioned exception can weaken a general rule, and that predictability can also be part of fairness.';
      }
      if (id.startsWith('preview-bridge-')) {
        return 'The bridge perspective suggests combining a clear baseline rule with narrow, reviewable exceptions.';
      }
      if (id.startsWith('preview-alternative-')) {
        return 'This perspective asks how the decision might change when the surrounding context or constraints change.';
      }
    }
    if (namespace == KefeContentNamespace.perspectiveProvenance &&
        id.startsWith('preview-')) {
      return 'KEFE Preview · Editorial example';
    }
    if (namespace == KefeContentNamespace.perspectiveMethodologyProvenance) {
      return 'Fixed editorial demo perspectives for Product Preview.';
    }
    if (namespace == KefeContentNamespace.perspectiveSampleKind) {
      return switch (fallback) {
        'CURATED_FALLBACK' => 'Curated fallback',
        'CURATED' => 'Curated sample',
        'CLUSTERED' => 'Clustered sample',
        _ => fallback.replaceAll('_', ' ').toLowerCase(),
      };
    }

    return fallback;
  }

  String _englishTensionForCaseId(String caseId) => switch (caseId) {
    '11111111-1111-4111-8111-111111111112' =>
      'Privacy and user control are weighed alongside personalization, innovation and service quality.',
    '11111111-1111-4111-8111-111111111113' =>
      'Technical rule application is weighed alongside game flow, the effect of contact and the referee’s room for judgment.',
    '11111111-1111-4111-8111-111111111114' =>
      'Public transparency and accountability are balanced against legal limits, confidentiality and practical implementation.',
    '11111111-1111-4111-8111-111111111115' ||
    '11111111-1111-4111-8111-111111111117' =>
      'Worker rights and equal opportunity are weighed against cost, efficiency and the employer’s operational responsibility.',
    '11111111-1111-4111-8111-111111111118' =>
      'Learning and academic integrity are weighed alongside adapting to new tools, equal access and reliable assessment.',
    _ =>
      'A genuine trade-off emerges between applying the same rule and accounting for individual need, context and proportionality.',
  };
}
