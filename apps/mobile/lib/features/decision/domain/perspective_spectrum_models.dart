import 'package:flutter/foundation.dart';

enum PrimaryValueHueModel {
  securityAndOrder,
  autonomyAndLiberty,
  equalityAndCare,
  innovationAndProgress,
  traditionAndHeritage,
}

@immutable
class PerspectiveSpectrumModel {
  const PerspectiveSpectrumModel({
    required this.spectrumId,
    required this.caseVersionId,
    required this.primaryValueHue,
    required this.argumentResonanceCount,
    required this.crossValueBridgeRatio,
    required this.coreMoralIntuition,
  });

  final String spectrumId;
  final String caseVersionId;
  final PrimaryValueHueModel primaryValueHue;
  final int argumentResonanceCount;
  final double crossValueBridgeRatio;
  final String coreMoralIntuition;
}
