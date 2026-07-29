enum CaseMediaSlot {
  exploreCard('EXPLORE_CARD'),
  caseHero('CASE_HERO'),
  contextSupporting('CONTEXT_SUPPORTING');

  const CaseMediaSlot(this.code);
  final String code;
}

enum CaseMediaKind {
  image('IMAGE'),
  illustration('ILLUSTRATION'),
  videoPoster('VIDEO_POSTER');

  const CaseMediaKind(this.code);
  final String code;
}

enum MediaExposurePhase {
  preCommitSafe('PRE_COMMIT_SAFE'),
  postCommitOnly('POST_COMMIT_ONLY');

  const MediaExposurePhase(this.code);
  final String code;
}

class CaseMediaPresentation {
  const CaseMediaPresentation({
    required this.id,
    required this.caseVersionId,
    required this.slot,
    required this.kind,
    required this.assetIdentity,
    required this.assetContentHash,
    required this.exposurePhase,
    required this.rendition,
    this.altText,
    this.decorative = false,
    this.caption,
    this.attribution,
  }) : assert(decorative || (altText != null && altText != ''));

  final String id;
  final String caseVersionId;
  final CaseMediaSlot slot;
  final CaseMediaKind kind;
  final String assetIdentity;
  final String assetContentHash;
  final String? altText;
  final bool decorative;
  final String? caption;
  final String? attribution;
  final MediaExposurePhase exposurePhase;
  final CaseMediaRendition rendition;
}

class CaseMediaRendition {
  const CaseMediaRendition({
    required this.rendererCode,
    required this.locator,
    required this.aspectRatio,
  });

  /// Provider-neutral renderer family. The first preview slice only supports
  /// KEFE_ABSTRACT_V1. Remote image/CDN renderers are deliberately deferred.
  final String rendererCode;
  final String locator;
  final double aspectRatio;
}
