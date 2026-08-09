import 'kefe_locale_catalog.dart';

abstract final class ResultMethodologyStringCatalog {
  static const KefeLocaleResources resources = {
    'en': {
      'result.raw_methodology':
          'Observed committed participation · n={sampleSize} · {confidence}. No representativeness claim.',
      'result.generic_methodology':
          'Result layer {layer} · n={sampleSize} · {confidence}.',
      'confidence.insufficient': 'Confidence not assessed',
    },
    'tr': {
      'result.raw_methodology':
          'Gözlenen kaydedilmiş katılım · n={sampleSize} · {confidence}. Temsiliyet iddiası yok.',
      'result.generic_methodology':
          'Sonuç katmanı {layer} · n={sampleSize} · {confidence}.',
      'confidence.insufficient': 'Güven düzeyi hesaplanmadı',
    },
  };
}
