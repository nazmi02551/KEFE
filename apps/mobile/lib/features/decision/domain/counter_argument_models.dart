import 'package:flutter/foundation.dart';

enum RefutationTypeModel {
  directEmpiricalRebuttal,
  logicalInvalidation,
  valueHierarchyChallenge,
  boundaryQualification,
}

@immutable
class ArgumentRefutationLinkModel {
  const ArgumentRefutationLinkModel({
    required this.refutationId,
    required this.sourceArgumentId,
    required this.targetArgumentId,
    required this.refutationType,
    required this.refutationStrength,
    required this.rebuttalThesis,
  });

  final String refutationId;
  final String sourceArgumentId;
  final String targetArgumentId;
  final RefutationTypeModel refutationType;
  final double refutationStrength;
  final String rebuttalThesis;
}
