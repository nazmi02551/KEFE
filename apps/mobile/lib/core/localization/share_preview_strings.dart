import 'kefe_locale_catalog.dart';
import 'kefe_strings.dart';
import 'share_preview_string_catalog.dart';

extension SharePreviewStrings on KefeStrings {
  String _sharePreviewText(String key) => KefeLocaleCatalog.resolve(
    locale: locale,
    resources: SharePreviewStringCatalog.resources,
    key: key,
  );

  String get sharePreviewReceiver =>
      _sharePreviewText('share.preview_receiver');
  String get shareExternalEntryBoundary =>
      _sharePreviewText('share.external_entry_boundary');
}
