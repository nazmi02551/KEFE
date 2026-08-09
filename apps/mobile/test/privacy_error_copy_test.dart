import 'package:flutter/widgets.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';

void main() {
  test('Turkish invalid deletion receipt copy hides internal error code', () {
    final strings = KefeStrings(const Locale('tr', 'TR'));

    final value = strings.privacyFailure('PRIVACY_DELETE_RECEIPT_INVALID');

    expect(value, contains('güvenli silme onayı'));
    expect(value, contains('silindiği varsayılmadı'));
    expect(value, isNot(contains('PRIVACY_DELETE_RECEIPT_INVALID')));
  });

  test('English invalid deletion receipt copy hides internal error code', () {
    final strings = KefeStrings(const Locale('en', 'US'));

    final value = strings.privacyFailure('PRIVACY_DELETE_RECEIPT_INVALID');

    expect(value, contains('secure-deletion receipt'));
    expect(value, contains('not treated as deleted'));
    expect(value, isNot(contains('PRIVACY_DELETE_RECEIPT_INVALID')));
  });

  test('identity migration error is explicit without leaking code', () {
    final strings = KefeStrings(const Locale('tr', 'TR'));

    final value = strings.privacyFailure('PRIVACY_ACTOR_ID_UNAVAILABLE');

    expect(value, contains('kimlik bilgisi doğrulanamadı'));
    expect(value, isNot(contains('PRIVACY_ACTOR_ID_UNAVAILABLE')));
  });
}
