import 'package:flutter/foundation.dart';

enum InstitutionTypeModel {
  officialGovernment,
  municipalLocal,
  corporateEnterprise,
  civilSociety,
}

@immutable
class VerifiedInstitutionResponseModel {
  const VerifiedInstitutionResponseModel({
    required this.responseId,
    required this.signalId,
    required this.institutionName,
    required this.institutionType,
    required this.responseBody,
    required this.verificationFingerprint,
    required this.respondedAtUtc,
  });

  final String responseId;
  final String signalId;
  final String institutionName;
  final InstitutionTypeModel institutionType;
  final String responseBody;
  final String verificationFingerprint;
  final String respondedAtUtc;
}
