import 'internal_alpha_string_catalog.dart';
import 'kefe_locale_catalog.dart';
import 'kefe_strings.dart';
import 'privacy_error_string_catalog.dart';

extension InternalAlphaStrings on KefeStrings {
  String _iaText(String key, {Map<String, Object?> placeholders = const {}}) =>
      KefeLocaleCatalog.resolve(
        locale: locale,
        resources: InternalAlphaStringCatalog.resources,
        key: key,
        placeholders: placeholders,
      );

  String _privacyErrorText(String key) => KefeLocaleCatalog.resolve(
    locale: locale,
    resources: PrivacyErrorStringCatalog.resources,
    key: key,
  );

  String get primaryNavExplore => _iaText('primary_nav.explore');
  String get primaryNavWeigh => _iaText('primary_nav.weigh');
  String get primaryNavActivity => _iaText('primary_nav.activity');
  String get primaryNavMyKefe => _iaText('primary_nav.my_kefe');

  String get accountTitle => _iaText('account.title');
  String get accountHeading => _iaText('account.heading');
  String get accountBody => _iaText('account.body');
  String get accountEmail => _iaText('account.email');
  String get accountPhone => _iaText('account.phone');
  String get accountEmailAddress => _iaText('account.email_address');
  String get accountPhoneNumber => _iaText('account.phone_number');
  String get accountSendCode => _iaText('account.send_code');
  String accountCodeInstruction(String destination) => _iaText(
    'account.code_instruction',
    placeholders: {'destination': destination},
  );
  String get accountVerificationCode => _iaText('account.verification_code');
  String get accountConvert => _iaText('account.convert');
  String get accountMerged => _iaText('account.merged');
  String get accountPreserved => _iaText('account.preserved');
  String get accountReturnMyKefe => _iaText('account.return_my_kefe');
  String get accountProtectAction => _iaText('account.protect_action');
  String accountFailure(String code) =>
      _iaText('account.failure', placeholders: {'code': code});

  String get activityEyebrow => _iaText('activity.eyebrow');
  String get activityTitle => _iaText('activity.title');
  String get activitySubtitle => _iaText('activity.subtitle');
  String get activityLoading => _iaText('activity.loading');
  String get activityUnavailable => _iaText('activity.unavailable');
  String get activityRetry => _iaText('activity.retry');
  String get activityEmpty => _iaText('activity.empty');
  String get activityHistoryTitle => _iaText('activity.history_title');
  String get activityCommitted => _iaText('activity.committed');
  String get activityReflected => _iaText('activity.reflected');
  String activityUpdateCount(int count) => _iaText(
    count == 1 ? 'activity.update_count.one' : 'activity.update_count.many',
    placeholders: {'count': count},
  );
  String get activityPreviewNotice => _iaText('activity.preview_notice');

  String get weighHubEyebrow => _iaText('weigh_hub.eyebrow');
  String get weighHubTitle => _iaText('weigh_hub.title');
  String get weighHubSubtitle => _iaText('weigh_hub.subtitle');
  String get weighHubRecommended => _iaText('weigh_hub.recommended');
  String get weighHubStart => _iaText('weigh_hub.start');
  String get weighHubMore => _iaText('weigh_hub.more');
  String get weighHubEmpty => _iaText('weigh_hub.empty');

  String get privacyTitle => _iaText('privacy.title');
  String get privacyHeading => _iaText('privacy.heading');
  String get privacyBody => _iaText('privacy.body');
  String get privacyExportReady => _iaText('privacy.export_ready');
  String get privacyExportCopied => _iaText('privacy.export_copied');
  String get privacyDone => _iaText('privacy.done');
  String get privacyExport => _iaText('privacy.export');
  String get privacyDelete => _iaText('privacy.delete');
  String privacyFailure(String code) => switch (code) {
    'AUTH_REQUIRED' => _privacyErrorText('auth_required'),
    'PRIVACY_ACTOR_ID_UNAVAILABLE' => _privacyErrorText('identity_unavailable'),
    'PRIVACY_DELETE_RECEIPT_INVALID' => _privacyErrorText('receipt_invalid'),
    _ => _iaText('privacy.failure', placeholders: {'code': code}),
  };
  String get privacyDeleteTitle => _iaText('privacy.delete_title');
  String get privacyDeleteBody => _iaText('privacy.delete_body');
  String get privacyCancel => _iaText('privacy.cancel');
  String get privacyDeletePermanently => _iaText('privacy.delete_permanently');

  String get shareTitle => _iaText('share.title');
  String get shareCaseOnlyNote => _iaText('share.case_only_note');
  String get sharePreparing => _iaText('share.preparing');
  String get shareCreate => _iaText('share.create');
  String get shareCopied => _iaText('share.copied');
  String get shareCopy => _iaText('share.copy');
  String get shareRevoke => _iaText('share.revoke');
  String shareFailure(String code) =>
      _iaText('share.failure', placeholders: {'code': code});
  String get publicShareUnavailable => _iaText('public_share.unavailable');
  String get publicShareRetry => _iaText('public_share.retry');
  String get publicShareEyebrow => _iaText('public_share.eyebrow');
  String get publicShareBlindFirst => _iaText('public_share.blind_first');
  String get publicShareWeigh => _iaText('public_share.weigh');

  String get communityTitle => _iaText('community.title');
  String get communityPrivateNote => _iaText('community.private_note');
  String get communityPublishHeading => _iaText('community.publish_heading');
  String get communityOptionalText => _iaText('community.optional_text');
  String get communityModerationNote => _iaText('community.moderation_note');
  String get communitySubmitting => _iaText('community.submitting');
  String get communityPublish => _iaText('community.publish');
  String get communityReceiptPending => _iaText('community.receipt_pending');
  String get communityReceiptAllowed => _iaText('community.receipt_allowed');
  String communityUnavailable(String code) =>
      _iaText('community.unavailable', placeholders: {'code': code});
  String get communityPublished => _iaText('community.published');
  String get communityResonates => _iaText('community.resonates');
  String get communityUseful => _iaText('community.useful');
  String get communityReport => _iaText('community.report');

  String get consensusLoading => _iaText('consensus.loading');
  String get consensusCommitFirst => _iaText('consensus.commit_first');
  String get consensusCommitFirstBody => _iaText('consensus.commit_first_body');
  String get consensusRetry => _iaText('consensus.retry');
  String get consensusExposed => _iaText('consensus.exposed');
  String get consensusPrompt => _iaText('consensus.prompt');
  String consensusReasonLimit(int max) =>
      _iaText('consensus.reason_limit', placeholders: {'max': max});
  String get consensusSubmitting => _iaText('consensus.submitting');
  String get consensusJoin => _iaText('consensus.join');
  String get consensusExposedMethodology =>
      _iaText('consensus.exposed_methodology');
  String get consensusDistribution => _iaText('consensus.distribution');
  String get consensusReasonPatterns => _iaText('consensus.reason_patterns');
  String get consensusEyebrow => _iaText('consensus.eyebrow');
  String get consensusCardTitle => _iaText('consensus.card_title');
  String consensusUnavailable(String? code) => code == null
      ? _iaText('consensus.unavailable')
      : _iaText(
          'consensus.unavailable_with_code',
          placeholders: {'code': code},
        );

  String consensusStanceLabel(String code) => switch (code) {
    'AGREE' => _iaText('consensus.stance.agree'),
    'MIXED' => _iaText('consensus.stance.mixed'),
    'DISAGREE' => _iaText('consensus.stance.disagree'),
    _ => code.replaceAll('_', ' '),
  };

  String consensusReasonLabel(String code) => switch (code) {
    'FAIRNESS' => _iaText('consensus.reason.fairness'),
    'NEED' => _iaText('consensus.reason.need'),
    'RULES' => _iaText('consensus.reason.rules'),
    'PRACTICAL_IMPACT' => _iaText('consensus.reason.practical_impact'),
    'RESPONSIBILITY' => _iaText('consensus.reason.responsibility'),
    _ => code.replaceAll('_', ' '),
  };

  String domainName(String code) => switch (code) {
    'DAILY_LIFE' => _iaText('domain.daily_life'),
    'TECHNOLOGY' || 'TECHNOLOGY_AI' => _iaText('domain.technology'),
    'SPORTS' => _iaText('domain.sports'),
    'CIVIC' || 'CITY_PUBLIC_LIFE' => _iaText('domain.civic'),
    'WORK_ECONOMY' || 'WORK_BUSINESS' => _iaText('domain.work_economy'),
    'EDUCATION' => _iaText('domain.education'),
    'FAMILY_PARENTING' => _iaText('domain.family_parenting'),
    'CULTURE_MEDIA' => _iaText('domain.culture_media'),
    _ => code.replaceAll('_', ' '),
  };

  String get contextEventSummary => _iaText('context.event_summary');
  String get contextInformationStatus => _iaText('context.information_status');
  String get journeyLabel => _iaText('journey.label');
  String get stepCase => _iaText('step.case');
  String get stepWeigh => _iaText('step.weigh');
  String get stepResult => _iaText('step.result');
  String get stepReflection => _iaText('step.reflection');
  String get stepCompleted => _iaText('step.completed');
  String get resultEyebrow => _iaText('result.eyebrow');
  String get yourDecision => _iaText('result.your_decision');
  String get communityDistribution => _iaText('result.community_distribution');
  String get kefeGap => _iaText('result.kefe_gap');

  String gapInsight({required bool selectedIsTop, required int percent}) =>
      _iaText(
        selectedIsTop ? 'result.gap.top' : 'result.gap.not_top',
        placeholders: {'percent': percent},
      );

  String gapDifferenceInsight({
    required int selectedPercent,
    required int gapPoints,
  }) => _iaText(
    'result.gap.difference',
    placeholders: {'selectedPercent': selectedPercent, 'gapPoints': gapPoints},
  );

  String get decisionYou => _iaText('result.decision_you');
  String get balanceNoSelection => _iaText('result.balance_no_selection');
  String balanceSemantics(String selectedLabel) => _iaText(
    'result.balance_semantics',
    placeholders: {'selectedLabel': selectedLabel},
  );

  String resultMethodology({
    required int sampleSize,
    required String confidence,
  }) => _iaText(
    'result.methodology',
    placeholders: {
      'trustedSample': trustedSample,
      'sampleSize': sampleSize,
      'confidence': confidenceLabel(confidence),
    },
  );

  String confidenceLabel(String code) => switch (code) {
    'HIGH' => _iaText('confidence.high'),
    'MEDIUM' => _iaText('confidence.medium'),
    'LOW' => _iaText('confidence.low'),
    _ => code.replaceAll('_', ' '),
  };

  String get perspectiveEyebrow => _iaText('perspective.eyebrow');
  String get questionConfidence => _iaText('question.confidence');
  String get questionDecision => _iaText('question.decision');
  String get reasonsEyebrow => _iaText('reasons.eyebrow');
}
