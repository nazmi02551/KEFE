import 'package:flutter/foundation.dart';

enum SystemHealthStatusModel {
  operationalOptimal,
  degradedPerformance,
  incidentActive,
}

@immutable
class SystemHealthModel {
  const SystemHealthModel({
    required this.subsystemId,
    required this.subsystemName,
    required this.status,
    required this.p99LatencyMs,
    required this.uptimePercentage30d,
    this.activeIncidentSummary = '',
  });

  final String subsystemId;
  final String subsystemName;
  final SystemHealthStatusModel status;
  final int p99LatencyMs;
  final double uptimePercentage30d;
  final String activeIncidentSummary;
}
