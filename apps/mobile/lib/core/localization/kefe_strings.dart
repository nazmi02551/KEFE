import 'package:flutter/widgets.dart';

import '../../features/decision/domain/decision_models.dart';
import 'core_string_catalog.dart';
import 'kefe_locale_catalog.dart';

class KefeStrings {
  const KefeStrings(this.locale);

  final Locale locale;

  static const supportedLocales = [Locale('tr', 'TR'), Locale('en', 'US')];

  static KefeStrings of(BuildContext context) {
    return Localizations.of<KefeStrings>(context, KefeStrings)!;
  }

  String _text(String key, {Map<String, Object?> placeholders = const {}}) =>
      KefeLocaleCatalog.resolve(
        locale: locale,
        resources: CoreStringCatalog.resources,
        key: key,
        placeholders: placeholders,
      );

  String get appName => 'KEFE';
  String get promise => _text('promise');
  String get onboardingTitleOne => _text('onboarding.title_one');
  String get onboardingBodyOne => _text('onboarding.body_one');
  String get onboardingStepTwoEyebrow => _text('onboarding.step_two_eyebrow');
  String get onboardingTitleTwo => _text('onboarding.title_two');
  String get onboardingBodyTwo => _text('onboarding.body_two');
  String get onboardingNext => _text('onboarding.next');
  String get onboardingTryCase => _text('onboarding.try_case');
  String get continueAsGuest => _text('onboarding.continue_as_guest');
  String get firstRevealHelper => _text('onboarding.first_reveal_helper');
  String get exploreTitle => _text('explore.title');
  String get exploreIntro => _text('explore.intro');
  String get exploreEmpty => _text('explore.empty');
  String get openCase => _text('explore.open_case');

  String get contextTitle => _text('context.title');
  String get contextHelper => _text('context.helper');
  String get contextDetails => _text('context.details');
  String get contextSources => _text('context.sources');
  String get contextLoading => _text('context.loading');
  String get contextUnavailable => _text('context.unavailable');
  String get contextRetry => _text('context.retry');

  String contextClaimStatus(String status) => switch (status) {
    'VERIFIED' => _text('context.claim.verified'),
    'CLAIMED' => _text('context.claim.claimed'),
    'DISPUTED' => _text('context.claim.disputed'),
    'UNKNOWN' => _text('context.claim.unknown'),
    _ => status,
  };

  String contextSourceKind(String sourceKind) => switch (sourceKind) {
    'OFFICIAL' => _text('context.source.official'),
    'NEWS' => _text('context.source.news'),
    'RESEARCH' => _text('context.source.research'),
    'EDITORIAL' => _text('context.source.editorial'),
    _ => _text('context.source.other'),
  };

  String get loading => _text('common.loading');
  String get retry => _text('common.retry');
  String get start => _text('common.start');
  String get commit => _text('decision.commit');
  String get retrySync => _text('decision.retry_sync');
  String get commitHelper => _text('decision.commit_helper');
  String get completeRequired => _text('decision.complete_required');
  String get requiredQuestion => _text('decision.required_question');
  String get optionalQuestion => _text('decision.optional_question');
  String get unsupportedQuestionType =>
      _text('decision.unsupported_question_type');
  String get reasonTitle => _text('reason.title');
  String get reasonHelper => _text('reason.helper');
  String reasonSelectionLimit(int maxTags) =>
      _text('reason.selection_limit', placeholders: {'maxTags': maxTags});
  String get reasonTextLabel => _text('reason.text_label');
  String get reasonTextHint => _text('reason.text_hint');

  String reasonTagLabel(String code) => switch (code) {
    'FAIRNESS' => _text('reason.tag.fairness'),
    'NEED' => _text('reason.tag.need'),
    'RESPONSIBILITY' => _text('reason.tag.responsibility'),
    'EMPATHY' => _text('reason.tag.empathy'),
    'RULES' => _text('reason.tag.rules'),
    'CONSEQUENCE' => _text('reason.tag.consequence'),
    'PROPORTIONALITY' => _text('reason.tag.proportionality'),
    'PRACTICAL_IMPACT' => _text('reason.tag.practical_impact'),
    _ => code.replaceAll('_', ' '),
  };

  String get pendingHelper => _text('sync.pending_helper');
  String get offlineDraft => _text('sync.offline_draft');
  String get decisionSyncPending => _text('sync.decision_pending');
  String get revealPending => _text('sync.reveal_pending');
  String get uncertainCommit => _text('sync.uncertain_commit');
  String get revealTitle => _text('reveal.title');
  String get trustedSample => _text('reveal.trusted_sample');
  String get selectAnswer => _text('reveal.select_answer');

  String get reflectionTitle => _text('reflection.title');
  String reflectionDecisionSummary(bool changed, int count) => changed
      ? _text('reflection.decision_changed', placeholders: {'count': count})
      : _text('reflection.decision_unchanged');

  String reflectionInterventionSummary(int count) =>
      _text('reflection.intervention_summary', placeholders: {'count': count});
  String get reflectionNonCausalNote => _text('reflection.non_causal_note');
  String get reflectionComplete => _text('reflection.complete');
  String get reflectionCompleted => _text('reflection.completed');
  String get reflectionLoading => _text('reflection.loading');
  String get reflectionRetry => _text('reflection.retry');

  String get flowCapabilityPendingTitle =>
      _text('flow.capability_pending.title');
  String flowCapabilityPendingBody(String? reasonCode) => switch (reasonCode) {
    'FLOW_DECISION_REVISION_REQUIRED' => _text(
      'flow.capability_pending.decision_revision',
    ),
    'FLOW_REFLECTION_RUNTIME_PENDING' => _text(
      'flow.capability_pending.reflection_runtime',
    ),
    _ => _text('flow.capability_pending.default'),
  };

  String get flowOfflineUnavailable => _text('flow.offline_unavailable');
  String get flowRuntimeUnavailable => _text('flow.runtime_unavailable');
  String get flowRuntimeMismatch => _text('flow.runtime_mismatch');

  String get perspectiveTitle => _text('perspective.title');
  String get perspectiveLoading => _text('perspective.loading');
  String get perspectiveRetry => _text('perspective.retry');
  String get perspectiveUnavailable => _text('perspective.unavailable');
  String get perspectiveCuratedNote => _text('perspective.curated_note');
  String get perspectiveClusterPending => _text('perspective.cluster_pending');
  String get perspectiveEmpty => _text('perspective.empty');
  String get reasonPendingModeration =>
      _text('perspective.reason_pending_moderation');
  String get perspectiveMethodology => _text('perspective.methodology');

  String perspectiveSlotLabel(PerspectiveSlot slot) => switch (slot) {
    PerspectiveSlot.near => _text('perspective.slot.near'),
    PerspectiveSlot.opposing => _text('perspective.slot.opposing'),
    PerspectiveSlot.bridge => _text('perspective.slot.bridge'),
    PerspectiveSlot.alternativeContext => _text(
      'perspective.slot.alternative_context',
    ),
  };

  String perspectiveSourceLabel(String sourceKind) => switch (sourceKind) {
    'CURATED' => _text('perspective.source.curated'),
    'HUMAN_REASON' => _text('perspective.source.human_reason'),
    _ => _text('perspective.source.default'),
  };

  String get genericError => _text('error.generic');

  String messageForCode(String? code) => switch (code) {
    'OFFLINE_DRAFT_RESTORED' => offlineDraft,
    'DECISION_SYNC_PENDING' => decisionSyncPending,
    'WEIGH_COMMIT_UNCERTAIN' => uncertainCommit,
    'RESULT_SYNC_PENDING' => revealPending,
    'FLOW_RUNTIME_OFFLINE_UNAVAILABLE' => flowOfflineUnavailable,
    'FLOW_RUNTIME_UNAVAILABLE' ||
    'FLOW_RUNTIME_NOT_CONFIGURED' => flowRuntimeUnavailable,
    'FLOW_RUNTIME_VERSION_MISMATCH' => flowRuntimeMismatch,
    'NETWORK_UNAVAILABLE' ||
    'NETWORK_TIMEOUT' => _text('error.network_unavailable'),
    'AUTH_GUEST_CONTINUITY_REQUIRED' => _text(
      'error.guest_continuity_required',
    ),
    'AUTH_ACCOUNT_REAUTHENTICATION_REQUIRED' => _text(
      'error.account_reauthentication_required',
    ),
    'AUTH_LEGACY_CONTINUITY_REQUIRED' => _text(
      'error.legacy_continuity_required',
    ),
    _ => genericError,
  };
}

class KefeStringsDelegate extends LocalizationsDelegate<KefeStrings> {
  const KefeStringsDelegate();

  @override
  bool isSupported(Locale locale) =>
      const {'tr', 'en'}.contains(locale.languageCode);

  @override
  Future<KefeStrings> load(Locale locale) async => KefeStrings(locale);

  @override
  bool shouldReload(KefeStringsDelegate old) => false;
}
