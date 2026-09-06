import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/enterprise_boardroom_room_models.dart';

void main() {
  group('Enterprise & Boardroom Decision Room (CAP-035)', () {
    test('ADR-0208 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0208-enterprise-boardroom-room.md');
      final contract = File('../../docs/contracts/enterprise-boardroom-room.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-BOARDROOM-ROOM-001'));
      expect(contract.readAsStringSync(), contains('ESG_AND_SUSTAINABILITY'));
    });

    test('EnterpriseBoardroomModel instantiates properly', () {
      const model = EnterpriseBoardroomModel(
        roomId: 'room_1',
        organizationName: 'Global Tech Ventures',
        dilemmaScope: BoardroomDilemmaScopeModel.esgAndSustainability,
        boardMemberCount: 9,
        fiduciaryConsensusRatio: 0.78,
        esgAlignmentScore: 0.92,
      );

      expect(model.boardMemberCount, 9);
      expect(model.fiduciaryConsensusRatio, 0.78);
    });

    test('InternalAlphaStrings contains Enterprise Boardroom localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.entBoardEyebrow, contains('KURUMSAL YÖNETİM KURULU'));
      expect(tr.entBoardScopeEsg, contains('ESG'));

      const en = KefeStrings(Locale('en'));
      expect(en.entBoardEyebrow, contains('ENTERPRISE & BOARDROOM'));
      expect(en.entBoardScopeEsg, contains('ESG'));
    });
  });
}
