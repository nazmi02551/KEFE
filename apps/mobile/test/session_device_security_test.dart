import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/session_device_security_models.dart';

void main() {
  group('Session & Active Device Security Hub (CAP-087)', () {
    test('ADR-0217 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0217-session-device-security.md');
      final contract = File('../../docs/contracts/session-device-security.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-SESS-SEC-001'));
      expect(contract.readAsStringSync(), contains('HARDWARE_ATTESTED_SECURE'));
    });

    test('SessionDeviceModel instantiates properly', () {
      const model = SessionDeviceModel(
        sessionId: 'sess_1',
        deviceName: 'Xiaomi Redmi Note 13 Pro 5G',
        clientPlatform: ClientPlatformModel.android,
        trustTier: DeviceTrustTierModel.hardwareAttestedSecure,
        ipCountryCode: 'TR',
        isCurrentDevice: true,
      );

      expect(model.isCurrentDevice, isTrue);
      expect(model.trustTier, DeviceTrustTierModel.hardwareAttestedSecure);
    });

    test('InternalAlphaStrings contains Session Device localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.sessDevEyebrow, contains('OTURUM VE AKTİF'));
      expect(tr.sessDevTierHardware, contains('Donanım Anahtar'));

      const en = KefeStrings(Locale('en'));
      expect(en.sessDevEyebrow, contains('SESSION & ACTIVE'));
      expect(en.sessDevTierHardware, contains('Hardware Keystore'));
    });
  });
}
