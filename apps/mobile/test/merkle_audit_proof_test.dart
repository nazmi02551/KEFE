import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/merkle_audit_proof_models.dart';

void main() {
  group('Merkle Tree Audit Proof & Independent Verifier (CAP-089)', () {
    test('ADR-0219 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0219-merkle-audit-proof.md');
      final contract = File('../../docs/contracts/merkle-audit-proof.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-MERKLE-AUDIT-001'));
      expect(contract.readAsStringSync(), contains('INCLUSION_VERIFIED'));
    });

    test('MerkleAuditProofModel instantiates properly', () {
      const model = MerkleAuditProofModel(
        leafId: 'leaf_1',
        rootEpochId: 'epoch_1',
        merkleRootHash: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
        proofDepth: 8,
        status: MerkleProofStatusModel.inclusionVerified,
        verifiedTimestamp: '2026-09-01T12:00:00Z',
      );

      expect(model.proofDepth, 8);
      expect(model.status, MerkleProofStatusModel.inclusionVerified);
    });

    test('InternalAlphaStrings contains Merkle Proof localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.merklePrfEyebrow, contains('MERKLE AĞACI'));
      expect(tr.merklePrfStInclusion, contains('Kriptografik Ağaç'));

      const en = KefeStrings(Locale('en'));
      expect(en.merklePrfEyebrow, contains('MERKLE TREE'));
      expect(en.merklePrfStInclusion, contains('Inclusion Proof'));
    });
  });
}
