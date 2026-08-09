import 'package:flutter/widgets.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/result_methodology_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';

void main() {
  test('Turkish RAW methodology is explicit and non-representative', () {
    final strings = KefeStrings(const Locale('tr', 'TR'));

    final value = strings.resultMethodologyForLayer(
      layer: 'RAW',
      sampleSize: 2,
      confidence: 'INSUFFICIENT',
    );

    expect(value, contains('Gözlenen kaydedilmiş katılım'));
    expect(value, contains('n=2'));
    expect(value, contains('Güven düzeyi hesaplanmadı'));
    expect(value, contains('Temsiliyet iddiası yok'));
    expect(value, isNot(contains('Güvenilir örneklem')));
    expect(value, isNot(contains('INSUFFICIENT')));
  });

  test('English RAW methodology is explicit and non-representative', () {
    final strings = KefeStrings(const Locale('en', 'US'));

    final value = strings.resultMethodologyForLayer(
      layer: 'RAW',
      sampleSize: 3,
      confidence: 'INSUFFICIENT',
    );

    expect(value, contains('Observed committed participation'));
    expect(value, contains('n=3'));
    expect(value, contains('Confidence not assessed'));
    expect(value, contains('No representativeness claim'));
    expect(value, isNot(contains('Trusted sample')));
    expect(value, isNot(contains('INSUFFICIENT')));
  });

  test('TRUSTED methodology remains backward compatible', () {
    final tr = KefeStrings(const Locale('tr', 'TR'));
    final en = KefeStrings(const Locale('en', 'US'));

    expect(
      tr.resultMethodologyForLayer(
        layer: 'TRUSTED',
        sampleSize: 1284,
        confidence: 'MEDIUM',
      ),
      contains('Güvenilir örneklem · n=1284 · Orta güven'),
    );
    expect(
      en.resultMethodologyForLayer(
        layer: 'TRUSTED',
        sampleSize: 1284,
        confidence: 'MEDIUM',
      ),
      contains('Trusted sample · n=1284 · Medium confidence'),
    );
  });

  test('unknown future layers are never silently labeled TRUSTED', () {
    final tr = KefeStrings(const Locale('tr', 'TR'));
    final en = KefeStrings(const Locale('en', 'US'));

    final trValue = tr.resultMethodologyForLayer(
      layer: 'EXPERIMENTAL',
      sampleSize: 4,
      confidence: 'INSUFFICIENT',
    );
    final enValue = en.resultMethodologyForLayer(
      layer: 'EXPERIMENTAL',
      sampleSize: 4,
      confidence: 'INSUFFICIENT',
    );

    expect(trValue, contains('Sonuç katmanı EXPERIMENTAL'));
    expect(trValue, isNot(contains('Güvenilir örneklem')));
    expect(enValue, contains('Result layer EXPERIMENTAL'));
    expect(enValue, isNot(contains('Trusted sample')));
  });
}
