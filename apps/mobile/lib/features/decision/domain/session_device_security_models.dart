import 'package:flutter/foundation.dart';

enum ClientPlatformModel {
  android,
  ios,
  webBrowser,
  desktopClient,
}

enum DeviceTrustTierModel {
  hardwareAttestedSecure,
  standardAuthenticated,
  unrecognizedStale,
}

@immutable
class SessionDeviceModel {
  const SessionDeviceModel({
    required this.sessionId,
    required this.deviceName,
    required this.clientPlatform,
    required this.trustTier,
    required this.ipCountryCode,
    required this.isCurrentDevice,
  });

  final String sessionId;
  final String deviceName;
  final ClientPlatformModel clientPlatform;
  final DeviceTrustTierModel trustTier;
  final String ipCountryCode;
  final bool isCurrentDevice;
}
