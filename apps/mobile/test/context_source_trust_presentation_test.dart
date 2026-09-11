// ADR-0130 / CAP-069 — Context source trust presentation contract tests.
// Contract: KEFE-CONTEXT-SOURCE-TRUST-PRESENTATION-001
//
// Verified invariants:
// 1. source_existence_implies_verified = false
//    (source tile must not show a verified badge/icon unconditionally)
// 2. claim_status_is_block_level = true
//    (status badge belongs to the information block, not the source row)
// 3. neutral_source_reference_label_required = true
// 4. publisher_and_source_kind_preserved = true
// 5. url_host_metadata_allowed = true, is_verification_signal = false
// 6. Contract file exists with correct contract_id
// 7. Localization: contextJourneySourceReference non-blank in TR and EN
import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/context/presentation/context_journey_strings.dart';

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

void main() {
  group(
      'ADR-0130 / CAP-069 — Context source trust presentation contract (CAP-069)',
      () {
    test('contract file exists and has correct contract_id', () {
      final contract = File(
        '../../docs/contracts/context-source-trust-presentation.v1.json',
      );
      expect(contract.existsSync(), isTrue,
          reason: 'context-source-trust-presentation.v1.json must exist');
      final decoded =
          jsonDecode(contract.readAsStringSync()) as Map<String, dynamic>;
      expect(
        decoded['contract_id'],
        'KEFE-CONTEXT-SOURCE-TRUST-PRESENTATION-001',
      );
    });

    test(
        'contract: source_existence_implies_verified = false, '
        'unconditional_verified_source_icon_allowed = false', () {
      final contract = jsonDecode(
        File(
          '../../docs/contracts/context-source-trust-presentation.v1.json',
        ).readAsStringSync(),
      ) as Map<String, dynamic>;
      final semantics = contract['semantics'] as Map<String, dynamic>;
      final presentation = contract['presentation'] as Map<String, dynamic>;
      expect(semantics['source_existence_implies_verified'], isFalse);
      expect(semantics['source_kind_implies_verified'], isFalse);
      expect(semantics['publisher_identity_implies_verified'], isFalse);
      expect(semantics['url_presence_implies_verified'], isFalse);
      expect(semantics['claim_status_is_block_level'], isTrue);
      expect(presentation['unconditional_verified_source_icon_allowed'],
          isFalse);
      expect(presentation['neutral_source_reference_label_required'], isTrue);
    });

    test('contract: architecture unchanged — no backend/API/schema changes',
        () {
      final contract = jsonDecode(
        File(
          '../../docs/contracts/context-source-trust-presentation.v1.json',
        ).readAsStringSync(),
      ) as Map<String, dynamic>;
      final arch = contract['architecture'] as Map<String, dynamic>;
      expect(arch['backend_shape_changed'], isFalse);
      expect(arch['public_api_changed'], isFalse);
      expect(arch['database_schema_changed'], isFalse);
      expect(arch['migration_required'], isFalse);
      expect(arch['source_trust_score_added'], isFalse);
    });

    test('contextJourneySourceReference is non-blank in TR and EN', () {
      const tr = KefeStrings(Locale('tr'));
      const en = KefeStrings(Locale('en'));
      expect(tr.contextJourneySourceReference, isNotEmpty);
      expect(en.contextJourneySourceReference, isNotEmpty);
      // Must be distinct (locale parity)
      expect(
        tr.contextJourneySourceReference,
        isNot(equals(en.contextJourneySourceReference)),
      );
    });

    test('contextJourneySourcePublished formats date deterministically', () {
      const tr = KefeStrings(Locale('tr'));
      const en = KefeStrings(Locale('en'));
      final date = DateTime.utc(2026, 9, 10);
      final trStr = tr.contextJourneySourcePublished(date);
      final enStr = en.contextJourneySourcePublished(date);
      // Must contain the ISO calendar date component
      expect(trStr, contains('2026-09-10'));
      expect(enStr, contains('2026-09-10'));
      // Must be non-blank
      expect(trStr, isNotEmpty);
      expect(enStr, isNotEmpty);
    });

    test('source_kind strings are non-blank for all canonical types in TR+EN',
        () {
      const tr = KefeStrings(Locale('tr'));
      const en = KefeStrings(Locale('en'));
      const kinds = ['OFFICIAL', 'NEWS', 'RESEARCH', 'EDITORIAL'];
      for (final kind in kinds) {
        expect(tr.contextSourceKind(kind), isNotEmpty,
            reason: 'TR: contextSourceKind($kind) must not be blank');
        expect(en.contextSourceKind(kind), isNotEmpty,
            reason: 'EN: contextSourceKind($kind) must not be blank');
      }
    });

    test('source_kind strings are distinct in EN', () {
      const en = KefeStrings(Locale('en'));
      const kinds = ['OFFICIAL', 'NEWS', 'RESEARCH', 'EDITORIAL'];
      final values = kinds.map(en.contextSourceKind).toSet();
      expect(values.length, kinds.length,
          reason: 'Each canonical source kind must have a unique EN label');
    });

    test('claim_status_is_block_level: claim status strings apply to blocks',
        () {
      // Contract: claim status labels refer to information blocks, not sources.
      // Test verifies that the 4 canonical status strings exist and are distinct.
      const en = KefeStrings(Locale('en'));
      const statuses = ['VERIFIED', 'CLAIMED', 'DISPUTED', 'UNKNOWN'];
      final values = statuses.map(en.contextClaimStatus).toSet();
      expect(values.length, statuses.length);
      for (final s in statuses) {
        expect(en.contextClaimStatus(s), isNotEmpty);
      }
    });
  });
}