import 'internal_alpha_strings.dart';
import 'kefe_locale_catalog.dart';
import 'kefe_strings.dart';
import 'result_methodology_string_catalog.dart';

extension ResultMethodologyStrings on KefeStrings {
  String _resultText(
    String key, {
    Map<String, Object?> placeholders = const {},
  }) => KefeLocaleCatalog.resolve(
    locale: locale,
    resources: ResultMethodologyStringCatalog.resources,
    key: key,
    placeholders: placeholders,
  );

  String resultMethodologyForLayer({
    required String layer,
    required int sampleSize,
    required String confidence,
  }) {
    if (layer == 'TRUSTED') {
      return InternalAlphaStrings(this).resultMethodology(
        sampleSize: sampleSize,
        confidence: confidence,
      );
    }

    final confidenceText = confidence == 'INSUFFICIENT'
        ? _resultText('confidence.insufficient')
        : InternalAlphaStrings(this).confidenceLabel(confidence);

    if (layer == 'RAW') {
      return _resultText(
        'result.raw_methodology',
        placeholders: {
          'sampleSize': sampleSize,
          'confidence': confidenceText,
        },
      );
    }

    return _resultText(
      'result.generic_methodology',
      placeholders: {
        'layer': layer,
        'sampleSize': sampleSize,
        'confidence': confidenceText,
      },
    );
  }
}
