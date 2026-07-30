import 'package:flutter/widgets.dart';

typedef KefeLocaleResources = Map<String, Map<String, String>>;

abstract final class KefeLocaleCatalog {
  static const fallbackLanguageCode = 'en';

  static String resolve({
    required Locale locale,
    required KefeLocaleResources resources,
    required String key,
    Map<String, Object?> placeholders = const {},
  }) {
    final fallback =
        resources[fallbackLanguageCode] ?? const <String, String>{};
    final localized = resources[locale.languageCode] ?? fallback;
    final template = localized[key] ?? fallback[key] ?? key;
    return interpolate(template, placeholders);
  }

  static String interpolate(
    String template,
    Map<String, Object?> placeholders,
  ) {
    var result = template;
    for (final entry in placeholders.entries) {
      result = result.replaceAll('{${entry.key}}', '${entry.value ?? ''}');
    }
    return result;
  }

  static Set<String> canonicalKeys(KefeLocaleResources resources) =>
      (resources[fallbackLanguageCode] ?? const <String, String>{}).keys
          .toSet();

  static Set<String> missingKeys(
    KefeLocaleResources resources,
    String languageCode,
  ) {
    final localized = resources[languageCode] ?? const <String, String>{};
    return canonicalKeys(resources).difference(localized.keys.toSet());
  }

  static Set<String> extraKeys(
    KefeLocaleResources resources,
    String languageCode,
  ) {
    final localized = resources[languageCode] ?? const <String, String>{};
    return localized.keys.toSet().difference(canonicalKeys(resources));
  }
}
