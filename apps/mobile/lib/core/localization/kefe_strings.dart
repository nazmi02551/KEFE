import 'package:flutter/widgets.dart';

class KefeStrings {
  const KefeStrings(this.locale);

  final Locale locale;

  static const supportedLocales = [Locale('tr', 'TR'), Locale('en', 'US')];

  static KefeStrings of(BuildContext context) {
    return Localizations.of<KefeStrings>(context, KefeStrings)!;
  }

  bool get _tr => locale.languageCode == 'tr';

  String get appName => 'KEFE';
  String get promise => _tr
      ? 'Kararını tart. Farklı düşünmenin nedenlerini gör.'
      : 'Weigh your decision. See why people differ.';
  String get loading => _tr ? 'Hazırlanıyor…' : 'Preparing…';
  String get retry => _tr ? 'Tekrar dene' : 'Try again';
  String get start => _tr ? 'Başla' : 'Start';
  String get commit => _tr ? 'Kararımı Ver' : 'Commit My Decision';
  String get commitHelper => _tr
      ? 'Kararını kilitle ve sonucu gör.'
      : 'Lock your decision and reveal the result.';
  String get revealTitle => _tr ? 'Topluluk nasıl tarttı?' : 'How did the community weigh it?';
  String get trustedSample => _tr ? 'Güvenilir örneklem' : 'Trusted sample';
  String get selectAnswer => _tr ? 'Bir seçenek seç' : 'Choose an option';
  String get genericError => _tr
      ? 'Bir sorun oluştu. Kararın kaybolmadı; tekrar deneyebilirsin.'
      : 'Something went wrong. Your decision was not lost; you can retry.';
}

class KefeStringsDelegate extends LocalizationsDelegate<KefeStrings> {
  const KefeStringsDelegate();

  @override
  bool isSupported(Locale locale) => const {'tr', 'en'}.contains(locale.languageCode);

  @override
  Future<KefeStrings> load(Locale locale) async => KefeStrings(locale);

  @override
  bool shouldReload(KefeStringsDelegate old) => false;
}
