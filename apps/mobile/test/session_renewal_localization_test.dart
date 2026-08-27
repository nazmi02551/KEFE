import 'package:flutter/widgets.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';

void main() {
  test('session continuity failures have explicit Turkish and English copy', () {
    final tr = KefeStrings(const Locale('tr', 'TR'));
    final en = KefeStrings(const Locale('en', 'US'));

    expect(
      tr.messageForCode('AUTH_GUEST_CONTINUITY_REQUIRED'),
      contains('sessizce'),
    );
    expect(
      en.messageForCode('AUTH_ACCOUNT_REAUTHENTICATION_REQUIRED'),
      contains('Verify your account again'),
    );
    expect(
      tr.messageForCode('AUTH_LEGACY_CONTINUITY_REQUIRED'),
      contains('eski oturum'),
    );
    expect(
      en.accountFailure('AUTH_ACCOUNT_REAUTHENTICATION_REQUIRED'),
      en.messageForCode('AUTH_ACCOUNT_REAUTHENTICATION_REQUIRED'),
    );
  });
}
