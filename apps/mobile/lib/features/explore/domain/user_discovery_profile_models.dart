import 'package:flutter/foundation.dart';

enum DomainPreferenceModel {
  civic,
  technology,
  bioethics,
  environment,
  justice,
  economic;

  static DomainPreferenceModel fromString(String val) =>
      switch (val.toUpperCase()) {
        'TECHNOLOGY' => technology,
        'BIOETHICS' => bioethics,
        'ENVIRONMENT' => environment,
        'JUSTICE' => justice,
        'ECONOMIC' => economic,
        _ => civic,
      };

  String get serializedName => switch (this) {
    civic => 'CIVIC',
    technology => 'TECHNOLOGY',
    bioethics => 'BIOETHICS',
    environment => 'ENVIRONMENT',
    justice => 'JUSTICE',
    economic => 'ECONOMIC',
  };
}

enum ComplexityLevelModel {
  introductory,
  balanced,
  deepDeliberation;

  static ComplexityLevelModel fromString(String val) =>
      switch (val.toUpperCase()) {
        'INTRODUCTORY' => introductory,
        'DEEP_DELIBERATION' => deepDeliberation,
        _ => balanced,
      };

  String get serializedName => switch (this) {
    introductory => 'INTRODUCTORY',
    balanced => 'BALANCED',
    deepDeliberation => 'DEEP_DELIBERATION',
  };
}

enum FreshnessPreferenceModel {
  currentEvents,
  balanced,
  timelessFoundations;

  static FreshnessPreferenceModel fromString(String val) =>
      switch (val.toUpperCase()) {
        'CURRENT_EVENTS' => currentEvents,
        'TIMELESS_FOUNDATIONS' => timelessFoundations,
        _ => balanced,
      };

  String get serializedName => switch (this) {
    currentEvents => 'CURRENT_EVENTS',
    balanced => 'BALANCED',
    timelessFoundations => 'TIMELESS_FOUNDATIONS',
  };
}

enum RealEventPreferenceModel {
  realEventsFirst,
  balanced,
  hypotheticalsFirst;

  static RealEventPreferenceModel fromString(String val) =>
      switch (val.toUpperCase()) {
        'REAL_EVENTS_FIRST' => realEventsFirst,
        'HYPOTHETICALS_FIRST' => hypotheticalsFirst,
        _ => balanced,
      };

  String get serializedName => switch (this) {
    realEventsFirst => 'REAL_EVENTS_FIRST',
    balanced => 'BALANCED',
    hypotheticalsFirst => 'HYPOTHETICALS_FIRST',
  };
}

@immutable
class UserDiscoveryProfileModel {
  const UserDiscoveryProfileModel({
    required this.userId,
    required this.preferredDomains,
    required this.complexityLevel,
    required this.freshnessPreference,
    required this.realEventPreference,
    required this.diversificationBoost,
    required this.updatedAt,
  });

  final String userId;
  final List<DomainPreferenceModel> preferredDomains;
  final ComplexityLevelModel complexityLevel;
  final FreshnessPreferenceModel freshnessPreference;
  final RealEventPreferenceModel realEventPreference;
  final double diversificationBoost;
  final DateTime updatedAt;

  UserDiscoveryProfileModel copyWith({
    String? userId,
    List<DomainPreferenceModel>? preferredDomains,
    ComplexityLevelModel? complexityLevel,
    FreshnessPreferenceModel? freshnessPreference,
    RealEventPreferenceModel? realEventPreference,
    double? diversificationBoost,
    DateTime? updatedAt,
  }) {
    return UserDiscoveryProfileModel(
      userId: userId ?? this.userId,
      preferredDomains: preferredDomains ?? this.preferredDomains,
      complexityLevel: complexityLevel ?? this.complexityLevel,
      freshnessPreference: freshnessPreference ?? this.freshnessPreference,
      realEventPreference: realEventPreference ?? this.realEventPreference,
      diversificationBoost: diversificationBoost ?? this.diversificationBoost,
      updatedAt: updatedAt ?? this.updatedAt,
    );
  }

  factory UserDiscoveryProfileModel.fromJson(Map<String, dynamic> json) =>
      UserDiscoveryProfileModel(
        userId: json['user_id'] as String? ?? 'guest-actor',
        preferredDomains: (json['preferred_domains'] as List<dynamic>? ?? const [])
            .map((e) => DomainPreferenceModel.fromString(e as String))
            .toList(),
        complexityLevel: ComplexityLevelModel.fromString(
          json['complexity_level'] as String? ?? '',
        ),
        freshnessPreference: FreshnessPreferenceModel.fromString(
          json['freshness_preference'] as String? ?? '',
        ),
        realEventPreference: RealEventPreferenceModel.fromString(
          json['real_event_preference'] as String? ?? '',
        ),
        diversificationBoost:
            (json['diversification_boost'] as num?)?.toDouble() ?? 0.5,
        updatedAt:
            DateTime.tryParse(json['updated_at'] as String? ?? '')?.toUtc() ??
            DateTime.now().toUtc(),
      );

  Map<String, dynamic> toJson() => {
    'user_id': userId,
    'preferred_domains': preferredDomains.map((d) => d.serializedName).toList(),
    'complexity_level': complexityLevel.serializedName,
    'freshness_preference': freshnessPreference.serializedName,
    'real_event_preference': realEventPreference.serializedName,
    'diversification_boost': diversificationBoost,
    'updated_at': updatedAt.toIso8601String(),
  };
}
