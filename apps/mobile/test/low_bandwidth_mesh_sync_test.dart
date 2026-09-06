import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/low_bandwidth_mesh_sync_models.dart';

void main() {
  group('Low-Bandwidth Offline Mesh & Delay-Tolerant Sync (CAP-084)', () {
    test('ADR-0230 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0230-low-bandwidth-mesh-sync.md');
      final contract = File('../../docs/contracts/low-bandwidth-mesh-sync.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-MESH-SYNC-001'));
      expect(contract.readAsStringSync(), contains('COMPRESSED_DELAY_TOLERANT_BUNDLE'));
    });

    test('MeshSyncModel instantiates properly', () {
      const model = MeshSyncModel(
        bundleId: 'msh_1',
        networkChannel: MeshSyncChannelModel.compressedDelayTolerantBundle,
        queuedReceiptsCount: 45,
        compressedPayloadBytes: 2252,
        syncCompressionRatio: 0.22,
        isReplayGuarded: true,
      );

      expect(model.queuedReceiptsCount, 45);
      expect(model.compressedPayloadBytes, 2252);
      expect(model.isReplayGuarded, isTrue);
    });

    test('InternalAlphaStrings contains Mesh Sync localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.meshSyncEyebrow, contains('DÜŞÜK BANT'));
      expect(tr.meshSyncChanBundle, contains('Gecikmeye Dayanıklı'));

      const en = KefeStrings(Locale('en'));
      expect(en.meshSyncEyebrow, contains('LOW-BANDWIDTH'));
      expect(en.meshSyncChanBundle, contains('Delay-Tolerant'));
    });
  });
}
