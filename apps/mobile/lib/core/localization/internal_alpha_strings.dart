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
  String get accountRestartChallenge => _iaText('account.restart_challenge');
  String accountFailure(String code) => switch (code) {
    'AUTH_OTP_INVALID' => _iaText('account.error_otp_invalid'),
    'AUTH_OTP_EXPIRED' => _iaText('account.error_otp_expired'),
    'AUTH_OTP_LOCKED' || 'AUTH_RATE_LIMITED' => _iaText('account.error_otp_locked'),
    'AUTH_CHALLENGE_EXPIRED' ||
    'AUTH_CHALLENGE_NOT_FOUND' => _iaText('account.error_challenge_expired'),
    'AUTH_VERIFICATION_TOKEN_EXPIRED' ||
    'AUTH_VERIFICATION_TOKEN_INVALID' ||
    'AUTH_ACCOUNT_MERGE_FAILED' => _iaText('account.error_merge_failed'),
    'AUTH_OTP_DELIVERY_UNAVAILABLE' ||
    'AUTH_OTP_DELIVERY_REJECTED' => _iaText('account.error_delivery_unavailable'),
    'AUTH_GUEST_CONTINUITY_REQUIRED' ||
    'AUTH_ACCOUNT_REAUTHENTICATION_REQUIRED' ||
    'AUTH_LEGACY_CONTINUITY_REQUIRED' => messageForCode(code),
    _ => _iaText('account.error_generic'),
  };

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
  String get privacyExportSummaryTitle =>
      _iaText('privacy.export_summary_title');
  String privacyExportRecordCount(int count) => _iaText(
    count == 1
        ? 'privacy.export_record_count.one'
        : 'privacy.export_record_count.many',
    placeholders: {'count': count},
  );
  String privacyExportGroupCount(int count) => _iaText(
    count == 1
        ? 'privacy.export_group_count.one'
        : 'privacy.export_group_count.many',
    placeholders: {'count': count},
  );
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
  String get privacyDeleteCompleteTitle =>
      _iaText('privacy.delete_complete_title');
  String get privacyDeleteCompleteBody =>
      _iaText('privacy.delete_complete_body');
  String get privacyDeletePreviewCompleteTitle =>
      _iaText('privacy.delete_preview_complete_title');
  String get privacyDeletePreviewCompleteBody =>
      _iaText('privacy.delete_preview_complete_body');
  String get privacyDeleteContinue => _iaText('privacy.delete_continue');

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
  String get communityPatternsEyebrow => _iaText('community.patterns_eyebrow');
  String get communityPatternsTitle => _iaText('community.patterns_title');
  String communityPatternsSample(int count) =>
      _iaText('community.patterns_sample', placeholders: {'count': count});
  String communityPatternsValue(int count, int sample) => _iaText(
    'community.patterns_value',
    placeholders: {'count': count, 'sample': sample},
  );
  String communityPatternsSemantics(String label, int count, int sample) =>
      _iaText(
        'community.patterns_semantics',
        placeholders: {'label': label, 'count': count, 'sample': sample},
      );
  String get communityPatternsNote => _iaText('community.patterns_note');
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
  String get decisionOptOutInsufficientInfo =>
      _iaText('decision.opt_out_insufficient_info');
  String get decisionOptOutMissingOptions =>
      _iaText('decision.opt_out_missing_options');
  String get decisionOptOutTitle => _iaText('decision.opt_out_title');
  String get reasonsEyebrow => _iaText('reasons.eyebrow');

  String get acadPortCorpGraph => _iaText('alpha.acadPortCorpGraph');
  String get acadPortEyebrow => _iaText('alpha.acadPortEyebrow');
  String get accVoiceEyebrow => _iaText('alpha.accVoiceEyebrow');
  String get accVoiceModeDictation => _iaText('alpha.accVoiceModeDictation');
  String get actionEvidenceButton => _iaText('alpha.actionEvidenceButton');
  String get actionEyebrow => _iaText('alpha.actionEyebrow');
  String get actionStatusInProgress => _iaText('alpha.actionStatusInProgress');
  String get actionStatusProposed => _iaText('alpha.actionStatusProposed');
  String get actionStatusStalled => _iaText('alpha.actionStatusStalled');
  String get actionStatusVerifiedComplete => _iaText('alpha.actionStatusVerifiedComplete');
  String get actionTrackEyebrow => _iaText('alpha.actionTrackEyebrow');
  String get actionTrackStatusProgress => _iaText('alpha.actionTrackStatusProgress');
  String get agendaThrEyebrow => _iaText('alpha.agendaThrEyebrow');
  String get agendaThrTierNational => _iaText('alpha.agendaThrTierNational');
  String get aiAuditEyebrow => _iaText('alpha.aiAuditEyebrow');
  String get aiAuditStGrounded => _iaText('alpha.aiAuditStGrounded');
  String get aiFacEyebrow => _iaText('alpha.aiFacEyebrow');
  String get aiFacModeSocratic => _iaText('alpha.aiFacModeSocratic');
  String get anatomyDriverNormative => _iaText('alpha.anatomyDriverNormative');
  String get anatomyEyebrow => _iaText('alpha.anatomyEyebrow');
  String get appealPanelEyebrow => _iaText('alpha.appealPanelEyebrow');
  String get appealPanelVerdictOverturned => _iaText('alpha.appealPanelVerdictOverturned');
  String get argClusteringArchetypeAlternative => _iaText('alpha.argClusteringArchetypeAlternative');
  String get argClusteringArchetypeBridge => _iaText('alpha.argClusteringArchetypeBridge');
  String get argClusteringArchetypeNearConsensus => _iaText('alpha.argClusteringArchetypeNearConsensus');
  String get argClusteringArchetypeOpposing => _iaText('alpha.argClusteringArchetypeOpposing');
  String get argClusteringEyebrow => _iaText('alpha.argClusteringEyebrow');
  String get argStrengthEyebrow => _iaText('alpha.argStrengthEyebrow');
  String get argStrengthTierRobust => _iaText('alpha.argStrengthTierRobust');
  String get blindEyebrow => _iaText('alpha.blindEyebrow');
  String get blindModeActor => _iaText('alpha.blindModeActor');
  String get botShieldEyebrow => _iaText('alpha.botShieldEyebrow');
  String get botShieldStQuarantine => _iaText('alpha.botShieldStQuarantine');
  String get bridgeEyebrow => _iaText('alpha.bridgeEyebrow');
  String get budgetSimEyebrow => _iaText('alpha.budgetSimEyebrow');
  String get budgetSimProfileBalanced => _iaText('alpha.budgetSimProfileBalanced');
  String get budgetSimProfileEco => _iaText('alpha.budgetSimProfileEco');
  String get budgetSimProfileHuman => _iaText('alpha.budgetSimProfileHuman');
  String get budgetSimProfileInfra => _iaText('alpha.budgetSimProfileInfra');
  String get changeMindClassOpen => _iaText('alpha.changeMindClassOpen');
  String get changeMindEyebrow => _iaText('alpha.changeMindEyebrow');
  String get checklistClose => _iaText('alpha.checklistClose');
  String get checklistFullyAudited => _iaText('alpha.checklistFullyAudited');
  String get checklistMagicScoreRejected => _iaText('alpha.checklistMagicScoreRejected');
  String get checklistMethodologyVerified => _iaText('alpha.checklistMethodologyVerified');
  String get checklistRevisionNeeded => _iaText('alpha.checklistRevisionNeeded');
  String get checklistSheetTitle => _iaText('alpha.checklistSheetTitle');
  String get checklistStatusFlagged => _iaText('alpha.checklistStatusFlagged');
  String get checklistStatusPending => _iaText('alpha.checklistStatusPending');
  String get checklistStatusVerified => _iaText('alpha.checklistStatusVerified');
  String get citJuryEyebrow => _iaText('alpha.citJuryEyebrow');
  String get citJuryStAssembly => _iaText('alpha.citJuryStAssembly');
  String get civPetEyebrow => _iaText('alpha.civPetEyebrow');
  String get civPetStSubmitted => _iaText('alpha.civPetStSubmitted');
  String get civicRepoEyebrow => _iaText('alpha.civicRepoEyebrow');
  String get civicRepoStAttested => _iaText('alpha.civicRepoStAttested');
  String get civicWorkEyebrow => _iaText('alpha.civicWorkEyebrow');
  String get civicWorkModFallacy => _iaText('alpha.civicWorkModFallacy');
  String get cogLoadEyebrow => _iaText('alpha.cogLoadEyebrow');
  String get cogLoadModeStreamlined => _iaText('alpha.cogLoadModeStreamlined');
  String get consCrcEyebrow => _iaText('alpha.consCrcEyebrow');
  String get consCrcStRatified => _iaText('alpha.consCrcStRatified');
  String get contribClassesEligibleBadge => _iaText('alpha.contribClassesEligibleBadge');
  String get contribClassesEyebrow => _iaText('alpha.contribClassesEyebrow');
  String get contribClassesIsolatedBadge => _iaText('alpha.contribClassesIsolatedBadge');
  String get contribClassesIsolationBreached => _iaText('alpha.contribClassesIsolationBreached');
  String get contribClassesIsolationEnforced => _iaText('alpha.contribClassesIsolationEnforced');
  String get contribClassesTitle => _iaText('alpha.contribClassesTitle');
  String get correctionNoCorrections => _iaText('alpha.correctionNoCorrections');
  String get correctionRationaleLabel => _iaText('alpha.correctionRationaleLabel');
  String get correctionSheetTitle => _iaText('alpha.correctionSheetTitle');
  String get correctionTypeClarification => _iaText('alpha.correctionTypeClarification');
  String get correctionTypeFactual => _iaText('alpha.correctionTypeFactual');
  String get correctionTypeLegal => _iaText('alpha.correctionTypeLegal');
  String get correctionTypeSource => _iaText('alpha.correctionTypeSource');
  String get correctionTypeTypo => _iaText('alpha.correctionTypeTypo');
  String get crossSimEyebrow => _iaText('alpha.crossSimEyebrow');
  String get crossSimTierHigh => _iaText('alpha.crossSimTierHigh');
  String get cultNormDimSolidarity => _iaText('alpha.cultNormDimSolidarity');
  String get cultNormEyebrow => _iaText('alpha.cultNormEyebrow');
  String get delibDepthEyebrow => _iaText('alpha.delibDepthEyebrow');
  String get delibDepthLevelProfound => _iaText('alpha.delibDepthLevelProfound');
  String get depolarEyebrow => _iaText('alpha.depolarEyebrow');
  String get depolarStateHigh => _iaText('alpha.depolarStateHigh');
  String get discProfileAntiAlgorithmNotice => _iaText('alpha.discProfileAntiAlgorithmNotice');
  String get discProfileComplexityTitle => _iaText('alpha.discProfileComplexityTitle');
  String get discProfileDiversityBoostDesc => _iaText('alpha.discProfileDiversityBoostDesc');
  String get discProfileDiversityBoostTitle => _iaText('alpha.discProfileDiversityBoostTitle');
  String get discProfileDomainsTitle => _iaText('alpha.discProfileDomainsTitle');
  String get discProfileSaveButton => _iaText('alpha.discProfileSaveButton');
  String get discProfileSheetTitle => _iaText('alpha.discProfileSheetTitle');
  String get diversityCatAcademic => _iaText('alpha.diversityCatAcademic');
  String get diversityCatCivic => _iaText('alpha.diversityCatCivic');
  String get diversityCatGov => _iaText('alpha.diversityCatGov');
  String get diversityCatIndustry => _iaText('alpha.diversityCatIndustry');
  String get diversityCatJournalism => _iaText('alpha.diversityCatJournalism');
  String get diversityEyebrow => _iaText('alpha.diversityEyebrow');
  String get diversityLevelBalanced => _iaText('alpha.diversityLevelBalanced');
  String get diversityLevelHigh => _iaText('alpha.diversityLevelHigh');
  String get diversityLevelLimited => _iaText('alpha.diversityLevelLimited');
  String get driftEyebrow => _iaText('alpha.driftEyebrow');
  String get driftNatureMatured => _iaText('alpha.driftNatureMatured');
  String get emergencyEyebrow => _iaText('alpha.emergencyEyebrow');
  String get emergencyStProportionate => _iaText('alpha.emergencyStProportionate');
  String get encBkpEyebrow => _iaText('alpha.encBkpEyebrow');
  String get encBkpStSynced => _iaText('alpha.encBkpStSynced');
  String get entBoardEyebrow => _iaText('alpha.entBoardEyebrow');
  String get entBoardScopeEsg => _iaText('alpha.entBoardScopeEsg');
  String get ethVecDomDeontological => _iaText('alpha.ethVecDomDeontological');
  String get ethVecEyebrow => _iaText('alpha.ethVecEyebrow');
  String get evidenceCategoryAcademic => _iaText('alpha.evidenceCategoryAcademic');
  String get evidenceStatusExpert => _iaText('alpha.evidenceStatusExpert');
  String get expertEyebrow => _iaText('alpha.expertEyebrow');
  String get expertGapBridgesTitle => _iaText('alpha.expertGapBridgesTitle');
  String get expertGapClassConvergent => _iaText('alpha.expertGapClassConvergent');
  String get expertGapClassNormative => _iaText('alpha.expertGapClassNormative');
  String get expertGapClassTechnical => _iaText('alpha.expertGapClassTechnical');
  String get expertGapClassTrust => _iaText('alpha.expertGapClassTrust');
  String get expertGapDriversTitle => _iaText('alpha.expertGapDriversTitle');
  String get expertGapEyebrow => _iaText('alpha.expertGapEyebrow');
  String get expertGapTitle => _iaText('alpha.expertGapTitle');
  String get expertTierAcademic => _iaText('alpha.expertTierAcademic');
  String get fallacyEyebrow => _iaText('alpha.fallacyEyebrow');
  String get fallacyTypeStrawMan => _iaText('alpha.fallacyTypeStrawMan');
  String get fatigueEyebrow => _iaText('alpha.fatigueEyebrow');
  String get fatigueStatusOptimal => _iaText('alpha.fatigueStatusOptimal');
  String get futureGenEyebrow => _iaText('alpha.futureGenEyebrow');
  String get futureGenH100Yr => _iaText('alpha.futureGenH100Yr');
  String get futureProxyEyebrow => _iaText('alpha.futureProxyEyebrow');
  String get futureProxyStRegenerative => _iaText('alpha.futureProxyStRegenerative');
  String get halflifeEyebrow => _iaText('alpha.halflifeEyebrow');
  String get halflifeStateFresh => _iaText('alpha.halflifeStateFresh');
  String get impactEviEyebrow => _iaText('alpha.impactEviEyebrow');
  String get impactEviStatusVerified => _iaText('alpha.impactEviStatusVerified');
  String get impactVerEyebrow => _iaText('alpha.impactVerEyebrow');
  String get impactVerVerdictFull => _iaText('alpha.impactVerVerdictFull');
  String get incentiveMapEyebrow => _iaText('alpha.incentiveMapEyebrow');
  String get incentiveMapStatusAligned => _iaText('alpha.incentiveMapStatusAligned');
  String get incentiveMapStatusMisaligned => _iaText('alpha.incentiveMapStatusMisaligned');
  String get incentiveMapStatusPerverse => _iaText('alpha.incentiveMapStatusPerverse');
  String get incentiveMapTypeBureaucratic => _iaText('alpha.incentiveMapTypeBureaucratic');
  String get incentiveMapTypeCivic => _iaText('alpha.incentiveMapTypeCivic');
  String get incentiveMapTypeElectoral => _iaText('alpha.incentiveMapTypeElectoral');
  String get incentiveMapTypeProfit => _iaText('alpha.incentiveMapTypeProfit');
  String get instRespEyebrow => _iaText('alpha.instRespEyebrow');
  String get instRespVerifiedBadge => _iaText('alpha.instRespVerifiedBadge');
  String get irreversibleClassPerm => _iaText('alpha.irreversibleClassPerm');
  String get irreversibleEyebrow => _iaText('alpha.irreversibleEyebrow');
  String get judicialEyebrow => _iaText('alpha.judicialEyebrow');
  String get judicialStAligned => _iaText('alpha.judicialStAligned');
  String get lensPillarLegal => _iaText('alpha.lensPillarLegal');
  String get lensSheetTitle => _iaText('alpha.lensSheetTitle');
  String get lobbyRdrEyebrow => _iaText('alpha.lobbyRdrEyebrow');
  String get lobbyRdrLvlClean => _iaText('alpha.lobbyRdrLvlClean');
  String get mediaScanEyebrow => _iaText('alpha.mediaScanEyebrow');
  String get mediaScanLvlPluralistic => _iaText('alpha.mediaScanLvlPluralistic');
  String get merklePrfEyebrow => _iaText('alpha.merklePrfEyebrow');
  String get merklePrfStInclusion => _iaText('alpha.merklePrfStInclusion');
  String get meshSyncChanBundle => _iaText('alpha.meshSyncChanBundle');
  String get meshSyncEyebrow => _iaText('alpha.meshSyncEyebrow');
  String get methodologyClose => _iaText('alpha.methodologyClose');
  String get methodologySafeguardCommitFirst => _iaText('alpha.methodologySafeguardCommitFirst');
  String get methodologySafeguardNoProfiling => _iaText('alpha.methodologySafeguardNoProfiling');
  String get methodologySheetTitle => _iaText('alpha.methodologySheetTitle');
  String get modAuditActionRemove => _iaText('alpha.modAuditActionRemove');
  String get modAuditEyebrow => _iaText('alpha.modAuditEyebrow');
  String get multiLlmEyebrow => _iaText('alpha.multiLlmEyebrow');
  String get multiLlmLvlUnanimous => _iaText('alpha.multiLlmLvlUnanimous');
  String get multiLocEyebrow => _iaText('alpha.multiLocEyebrow');
  String get multiLocTierCertified => _iaText('alpha.multiLocTierCertified');
  String get munBudDomParks => _iaText('alpha.munBudDomParks');
  String get munBudEyebrow => _iaText('alpha.munBudEyebrow');
  String get ngoDeskDomClimate => _iaText('alpha.ngoDeskDomClimate');
  String get ngoDeskEyebrow => _iaText('alpha.ngoDeskEyebrow');
  String get objectionCategoryAmbiguous => _iaText('alpha.objectionCategoryAmbiguous');
  String get objectionCategoryBias => _iaText('alpha.objectionCategoryBias');
  String get objectionCategoryDrift => _iaText('alpha.objectionCategoryDrift');
  String get objectionCategoryFactual => _iaText('alpha.objectionCategoryFactual');
  String get objectionCategoryStakeholder => _iaText('alpha.objectionCategoryStakeholder');
  String get objectionDialogTitle => _iaText('alpha.objectionDialogTitle');
  String get objectionEvidenceUrlHint => _iaText('alpha.objectionEvidenceUrlHint');
  String get objectionStatementHint => _iaText('alpha.objectionStatementHint');
  String get objectionSubmitButton => _iaText('alpha.objectionSubmitButton');
  String get observeModeEyebrow => _iaText('alpha.observeModeEyebrow');
  String get observeModeModeObserve => _iaText('alpha.observeModeModeObserve');
  String get observeModeModeStudy => _iaText('alpha.observeModeModeStudy');
  String get observeModeModeTransition => _iaText('alpha.observeModeModeTransition');
  String get observeModeNonBindingBadge => _iaText('alpha.observeModeNonBindingBadge');
  String get perspSpecEyebrow => _iaText('alpha.perspSpecEyebrow');
  String get perspSpecValEquality => _iaText('alpha.perspSpecValEquality');
  String get policySimEyebrow => _iaText('alpha.policySimEyebrow');
  String get policySimStateDeficit => _iaText('alpha.policySimStateDeficit');
  String get policySimStateEnv => _iaText('alpha.policySimStateEnv');
  String get policySimStateOptimal => _iaText('alpha.policySimStateOptimal');
  String get policySimStateSocial => _iaText('alpha.policySimStateSocial');
  String get principleEyebrow => _iaText('alpha.principleEyebrow');
  String get principleTypeLiberty => _iaText('alpha.principleTypeLiberty');
  String get privBudEyebrow => _iaText('alpha.privBudEyebrow');
  String get privBudStHealthy => _iaText('alpha.privBudStHealthy');
  String get processAnalysisCompleted => _iaText('alpha.processAnalysisCompleted');
  String get processAnalysisEyebrow => _iaText('alpha.processAnalysisEyebrow');
  String get procureEyebrow => _iaText('alpha.procureEyebrow');
  String get procureLvlOpen => _iaText('alpha.procureLvlOpen');
  String get promMtxEyebrow => _iaText('alpha.promMtxEyebrow');
  String get promMtxStDelivered => _iaText('alpha.promMtxStDelivered');
  String get proportionalEyebrow => _iaText('alpha.proportionalEyebrow');
  String get proportionalOutcomeValid => _iaText('alpha.proportionalOutcomeValid');
  String get rebuttalEyebrow => _iaText('alpha.rebuttalEyebrow');
  String get rebuttalTypeEmpirical => _iaText('alpha.rebuttalTypeEmpirical');
  String get receiptEyebrow => _iaText('alpha.receiptEyebrow');
  String get receiptVerifiedBadge => _iaText('alpha.receiptVerifiedBadge');
  String get respAnalysisDutyEthical => _iaText('alpha.respAnalysisDutyEthical');
  String get respAnalysisDutyExecution => _iaText('alpha.respAnalysisDutyExecution');
  String get respAnalysisDutyLegal => _iaText('alpha.respAnalysisDutyLegal');
  String get respAnalysisDutyOversight => _iaText('alpha.respAnalysisDutyOversight');
  String get respAnalysisEyebrow => _iaText('alpha.respAnalysisEyebrow');
  String get respAnalysisGapWarning => _iaText('alpha.respAnalysisGapWarning');
  String get retroSimEraCentury20 => _iaText('alpha.retroSimEraCentury20');
  String get retroSimEyebrow => _iaText('alpha.retroSimEyebrow');
  String get revolveEyebrow => _iaText('alpha.revolveEyebrow');
  String get revolveStCompliant => _iaText('alpha.revolveStCompliant');
  String get rightsEyebrow => _iaText('alpha.rightsEyebrow');
  String get rightsSevPermissible => _iaText('alpha.rightsSevPermissible');
  String get roleFlipEyebrow => _iaText('alpha.roleFlipEyebrow');
  String get roleFlipInitialLabel => _iaText('alpha.roleFlipInitialLabel');
  String get segmentDistEyebrow => _iaText('alpha.segmentDistEyebrow');
  String get segmentDistTitle => _iaText('alpha.segmentDistTitle');
  String get segmentDistTypeAge => _iaText('alpha.segmentDistTypeAge');
  String get segmentDistTypeExperience => _iaText('alpha.segmentDistTypeExperience');
  String get segmentDistTypeRegional => _iaText('alpha.segmentDistTypeRegional');
  String get segmentDistTypeStakeholder => _iaText('alpha.segmentDistTypeStakeholder');
  String get segmentDistTypeUrbanRural => _iaText('alpha.segmentDistTypeUrbanRural');
  String get sessDevEyebrow => _iaText('alpha.sessDevEyebrow');
  String get sessDevTierHardware => _iaText('alpha.sessDevTierHardware');
  String get sigHealthClose => _iaText('alpha.sigHealthClose');
  String get sigHealthEyebrow => _iaText('alpha.sigHealthEyebrow');
  String get sigHealthFlagged => _iaText('alpha.sigHealthFlagged');
  String get sigHealthNotice => _iaText('alpha.sigHealthNotice');
  String get sigHealthPassed => _iaText('alpha.sigHealthPassed');
  String get sigHealthStNoise => _iaText('alpha.sigHealthStNoise');
  String get sigHealthStProvisional => _iaText('alpha.sigHealthStProvisional');
  String get sigHealthStQualified => _iaText('alpha.sigHealthStQualified');
  String get sigScopeDimensionInvalid => _iaText('alpha.sigScopeDimensionInvalid');
  String get sigScopeDimensionValid => _iaText('alpha.sigScopeDimensionValid');
  String get sigScopeEyebrow => _iaText('alpha.sigScopeEyebrow');
  String get sigScopeNotice => _iaText('alpha.sigScopeNotice');
  String get sigScopeStAligned => _iaText('alpha.sigScopeStAligned');
  String get sigScopeStDisqualified => _iaText('alpha.sigScopeStDisqualified');
  String get sigScopeStOverbroad => _iaText('alpha.sigScopeStOverbroad');
  String get sigScopeTitle => _iaText('alpha.sigScopeTitle');
  String get sigTargetEyebrow => _iaText('alpha.sigTargetEyebrow');
  String get sigTargetNotice => _iaText('alpha.sigTargetNotice');
  String get sigTargetPrimaryBadge => _iaText('alpha.sigTargetPrimaryBadge');
  String get sigTargetSecondaryBadge => _iaText('alpha.sigTargetSecondaryBadge');
  String get sigTargetStAcknowledged => _iaText('alpha.sigTargetStAcknowledged');
  String get sigTargetStDeclined => _iaText('alpha.sigTargetStDeclined');
  String get sigTargetStDispatched => _iaText('alpha.sigTargetStDispatched');
  String get sigTargetStPledged => _iaText('alpha.sigTargetStPledged');
  String get sigTargetStProposed => _iaText('alpha.sigTargetStProposed');
  String get sigTargetStVerified => _iaText('alpha.sigTargetStVerified');
  String get sigTargetTitle => _iaText('alpha.sigTargetTitle');
  String get sigVersChainInvalid => _iaText('alpha.sigVersChainInvalid');
  String get sigVersChainVerified => _iaText('alpha.sigVersChainVerified');
  String get sigVersDeltaTitle => _iaText('alpha.sigVersDeltaTitle');
  String get sigVersEyebrow => _iaText('alpha.sigVersEyebrow');
  String get sigVersGenesis => _iaText('alpha.sigVersGenesis');
  String get sigVersNotice => _iaText('alpha.sigVersNotice');
  String get sigVersTitle => _iaText('alpha.sigVersTitle');
  String get signalQualChannelsTitle => _iaText('alpha.signalQualChannelsTitle');
  String get signalQualEyebrow => _iaText('alpha.signalQualEyebrow');
  String get signalQualStatusDisqualified => _iaText('alpha.signalQualStatusDisqualified');
  String get signalQualStatusProvisional => _iaText('alpha.signalQualStatusProvisional');
  String get signalQualStatusQualified => _iaText('alpha.signalQualStatusQualified');
  String get signalQualTierBronze => _iaText('alpha.signalQualTierBronze');
  String get signalQualTierGold => _iaText('alpha.signalQualTierGold');
  String get signalQualTierSilver => _iaText('alpha.signalQualTierSilver');
  String get signalQualTierUnqualified => _iaText('alpha.signalQualTierUnqualified');
  String get signalQualTitle => _iaText('alpha.signalQualTitle');
  String get sovereigntyEyebrow => _iaText('alpha.sovereigntyEyebrow');
  String get sovereigntyStEnforced => _iaText('alpha.sovereigntyStEnforced');
  String get stakeholderDistEyebrow => _iaText('alpha.stakeholderDistEyebrow');
  String get stakeholderDistRoleCivic => _iaText('alpha.stakeholderDistRoleCivic');
  String get stakeholderDistRoleCommercial => _iaText('alpha.stakeholderDistRoleCommercial');
  String get stakeholderDistRoleDirectlyImpacted => _iaText('alpha.stakeholderDistRoleDirectlyImpacted');
  String get stakeholderDistRoleFrontline => _iaText('alpha.stakeholderDistRoleFrontline');
  String get stakeholderDistRoleRegulatory => _iaText('alpha.stakeholderDistRoleRegulatory');
  String get stakeholderDistTitle => _iaText('alpha.stakeholderDistTitle');
  String get stakeholderEyebrow => _iaText('alpha.stakeholderEyebrow');
  String get stakeholderMatrixEyebrow => _iaText('alpha.stakeholderMatrixEyebrow');
  String get stakeholderTitle => _iaText('alpha.stakeholderTitle');
  String get sysHealthEyebrow => _iaText('alpha.sysHealthEyebrow');
  String get sysHealthStOptimal => _iaText('alpha.sysHealthStOptimal');
  String get tempFlowEpochInitial => _iaText('alpha.tempFlowEpochInitial');
  String get tempFlowEyebrow => _iaText('alpha.tempFlowEyebrow');
  String get thresholdEyebrow => _iaText('alpha.thresholdEyebrow');
  String get treeBranchEyebrow => _iaText('alpha.treeBranchEyebrow');
  String get treeBranchNodeFork => _iaText('alpha.treeBranchNodeFork');
  String get triangleArchetypeRights => _iaText('alpha.triangleArchetypeRights');
  String get triangleEyebrow => _iaText('alpha.triangleEyebrow');
  String get trustStandEyebrow => _iaText('alpha.trustStandEyebrow');
  String get trustStandTierExemplary => _iaText('alpha.trustStandTierExemplary');
  String get ugcPropEyebrow => _iaText('alpha.ugcPropEyebrow');
  String get ugcPropStateApproved => _iaText('alpha.ugcPropStateApproved');
  String get ugcPropStateDraft => _iaText('alpha.ugcPropStateDraft');
  String get ugcPropStateRejected => _iaText('alpha.ugcPropStateRejected');
  String get ugcPropStateReview => _iaText('alpha.ugcPropStateReview');
  String get unintendedEyebrow => _iaText('alpha.unintendedEyebrow');
  String get unintendedTypePerverse => _iaText('alpha.unintendedTypePerverse');
  String get vulnerableCohortDisability => _iaText('alpha.vulnerableCohortDisability');
  String get vulnerableEyebrow => _iaText('alpha.vulnerableEyebrow');
  String get xaiProvEyebrow => _iaText('alpha.xaiProvEyebrow');
  String get xaiProvTierAxiomatic => _iaText('alpha.xaiProvTierAxiomatic');
  String get youthSpaceEyebrow => _iaText('alpha.youthSpaceEyebrow');
  String get youthSpaceFocusCampus => _iaText('alpha.youthSpaceFocusCampus');

  String actionProgressLabel(int pct) => _iaText('alpha.actionProgressLabel', placeholders: {'pct': pct});
  String actionTargetDate(String date) => _iaText('alpha.actionTargetDate', placeholders: {'date': date});
  String argClusteringTotalArgs(int total) => _iaText('alpha.argClusteringTotalArgs', placeholders: {'total': total});
  String bridgeCrossSupport(int pct, int count) => _iaText('alpha.bridgeCrossSupport', placeholders: {'pct': pct, 'count': count});
  String budgetSimBreakdownLabel(int h, int e, int i, int g) => _iaText('alpha.budgetSimBreakdownLabel', placeholders: {'h': h, 'e': e, 'i': i, 'g': g});
  String budgetSimUnallocatedLabel(int pct) => _iaText('alpha.budgetSimUnallocatedLabel', placeholders: {'pct': pct});
  String contribClassesProofLabel(String proof) => _iaText('alpha.contribClassesProofLabel', placeholders: {'proof': proof});
  String contribClassesTotalLabel(int total) => _iaText('alpha.contribClassesTotalLabel', placeholders: {'total': total});
  String expertGapExpertsSample(int sample) => _iaText('alpha.expertGapExpertsSample', placeholders: {'sample': sample});
  String expertGapMagnitude(int points) => _iaText('alpha.expertGapMagnitude', placeholders: {'points': points});
  String expertGapPublicSample(int sample) => _iaText('alpha.expertGapPublicSample', placeholders: {'sample': sample});
  String incentiveMapAlignmentLabel(int pct) => _iaText('alpha.incentiveMapAlignmentLabel', placeholders: {'pct': pct});
  String incentiveMapDriverLabel(String driver) => _iaText('alpha.incentiveMapDriverLabel', placeholders: {'driver': driver});
  String incentiveMapMitigationLabel(String mech) => _iaText('alpha.incentiveMapMitigationLabel', placeholders: {'mech': mech});
  String incentiveMapRiskLabel(String risk) => _iaText('alpha.incentiveMapRiskLabel', placeholders: {'risk': risk});
  String methodologyEngine(String v) => _iaText('alpha.methodologyEngine', placeholders: {'v': v});
  String observeModeStatsLabel(int args, int ev) => _iaText('alpha.observeModeStatsLabel', placeholders: {'args': args, 'ev': ev});
  String policySimKnobLabel(String knob, int val) => _iaText('alpha.policySimKnobLabel', placeholders: {'knob': knob, 'val': val});
  String policySimScoresLabel(int f, int s, int e) => _iaText('alpha.policySimScoresLabel', placeholders: {'f': f, 's': s, 'e': e});
  String processAnalysisCurrentStage(String stage) => _iaText('alpha.processAnalysisCurrentStage', placeholders: {'stage': stage});
  String processAnalysisDays(int days) => _iaText('alpha.processAnalysisDays', placeholders: {'days': days});
  String processAnalysisIntegrityLabel(int pct) => _iaText('alpha.processAnalysisIntegrityLabel', placeholders: {'pct': pct});
  String processAnalysisOversightLabel(String body) => _iaText('alpha.processAnalysisOversightLabel', placeholders: {'body': body});
  String respAnalysisClarityLabel(int pct) => _iaText('alpha.respAnalysisClarityLabel', placeholders: {'pct': pct});
  String respAnalysisRedressLabel(String ch) => _iaText('alpha.respAnalysisRedressLabel', placeholders: {'ch': ch});
  String segmentDistEntropyLabel(String entropy) => _iaText('alpha.segmentDistEntropyLabel', placeholders: {'entropy': entropy});
  String segmentDistOverallSample(int sample) => _iaText('alpha.segmentDistOverallSample', placeholders: {'sample': sample});
  String segmentDistPrimaryPref(String choice) => _iaText('alpha.segmentDistPrimaryPref', placeholders: {'choice': choice});
  String segmentDistPrivacyBadge(int k) => _iaText('alpha.segmentDistPrivacyBadge', placeholders: {'k': k});
  String segmentDistSuppressedNotice(int threshold) => _iaText('alpha.segmentDistSuppressedNotice', placeholders: {'threshold': threshold});
  String selectLocale(String tr, String en) => isTr ? tr : en;
  String sigHealthMethodologyVerified(String h) => _iaText('alpha.sigHealthMethodologyVerified', placeholders: {'h': h});
  String sigHealthSampleLabel(int sample) => _iaText('alpha.sigHealthSampleLabel', placeholders: {'sample': sample});
  String sigHealthScoreLabel(num score) => _iaText('alpha.sigHealthScoreLabel', placeholders: {'score': score is double && score <= 1.0 ? (score * 100).round() : score.round()});
  String sigScopeGeoLabel(String geo) => _iaText('alpha.sigScopeGeoLabel', placeholders: {'geo': geo});
  String sigScopeJurisdictionLabel(String jur) => _iaText('alpha.sigScopeJurisdictionLabel', placeholders: {'jur': jur});
  String sigScopePopulationLabel(String pop) => _iaText('alpha.sigScopePopulationLabel', placeholders: {'pop': pop});
  String sigScopeScoreLabel(int score) => _iaText('alpha.sigScopeScoreLabel', placeholders: {'score': score});
  String sigScopeSealVerified(String seal) => _iaText('alpha.sigScopeSealVerified', placeholders: {'seal': seal});
  String sigScopeValidityLabel(int days) => _iaText('alpha.sigScopeValidityLabel', placeholders: {'days': days});
  String sigTargetChannelLabel(String ch) => _iaText('alpha.sigTargetChannelLabel', placeholders: {'ch': ch});
  String sigTargetProofVerified(String proof) => _iaText('alpha.sigTargetProofVerified', placeholders: {'proof': proof});
  String sigTargetResponseDue(int days) => _iaText('alpha.sigTargetResponseDue', placeholders: {'days': days});
  String sigVersCurrentVersionLabel(String v) => _iaText('alpha.sigVersCurrentVersionLabel', placeholders: {'v': v});
  String sigVersDeltaConfidenceLabel(int conf) => _iaText('alpha.sigVersDeltaConfidenceLabel', placeholders: {'conf': conf});
  String sigVersDeltaShiftLabel(int shift) => _iaText('alpha.sigVersDeltaShiftLabel', placeholders: {'shift': shift});
  String sigVersParentHash(String hash) => _iaText('alpha.sigVersParentHash', placeholders: {'hash': hash});
  String sigVersSnapshotSample(int s, int c) => _iaText('alpha.sigVersSnapshotSample', placeholders: {'s': s, 'c': c});
  String signalQualAuditHashLabel(String hash) => _iaText('alpha.signalQualAuditHashLabel', placeholders: {'hash': hash});
  String signalQualSampleLabel(int sample) => _iaText('alpha.signalQualSampleLabel', placeholders: {'sample': sample});
  String signalQualScoreLabel(int score) => _iaText('alpha.signalQualScoreLabel', placeholders: {'score': score});
  String stakeholderDistCohesionLabel(String c) => _iaText('alpha.stakeholderDistCohesionLabel', placeholders: {'c': c});
  String stakeholderDistDivergenceNegative(int pts) => _iaText('alpha.stakeholderDistDivergenceNegative', placeholders: {'pts': pts});
  String stakeholderDistDivergencePositive(int pts) => _iaText('alpha.stakeholderDistDivergencePositive', placeholders: {'pts': pts});
  String stakeholderDistPluralismScore(String score) => _iaText('alpha.stakeholderDistPluralismScore', placeholders: {'score': score});
  String stakeholderDistTotalRepresented(int count) => _iaText('alpha.stakeholderDistTotalRepresented', placeholders: {'count': count});
  String stakeholderMatrixNetScore(int score) => _iaText('alpha.stakeholderMatrixNetScore', placeholders: {'score': score});
  String stakeholderSampleInfo(int sample) => _iaText('alpha.stakeholderSampleInfo', placeholders: {'sample': sample});
  String thresholdTippingPoint(String val, String unit) => _iaText('alpha.thresholdTippingPoint', placeholders: {'val': val, 'unit': unit});
  String ugcPropNeutralityLabel(int score) => _iaText('alpha.ugcPropNeutralityLabel', placeholders: {'score': score});
  String ugcPropSupportersLabel(int count) => _iaText('alpha.ugcPropSupportersLabel', placeholders: {'count': count});
}
