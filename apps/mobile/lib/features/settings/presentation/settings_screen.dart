import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/localization/kefe_strings.dart';
import '../../../core/localization/settings_strings.dart';
import '../../../core/preferences/app_preferences.dart';

class SettingsScreen extends ConsumerWidget {
  const SettingsScreen({this.showPrivacyControls = true, super.key});

  final bool showPrivacyControls;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final strings = KefeStrings.of(context);
    final preferences = ref.watch(appPreferencesControllerProvider);
    final controller = ref.read(appPreferencesControllerProvider.notifier);

    return Scaffold(
      appBar: AppBar(title: Text(strings.settingsTitle)),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(20, 12, 20, 32),
        children: [
          Text(strings.languageTitle, style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 8),
          _ChoiceTile<AppLocalePreference>(
            value: AppLocalePreference.system,
            groupValue: preferences.locale,
            title: strings.languageSystem,
            onChanged: controller.setLocale,
          ),
          _ChoiceTile<AppLocalePreference>(
            value: AppLocalePreference.tr,
            groupValue: preferences.locale,
            title: strings.languageTurkish,
            onChanged: controller.setLocale,
          ),
          _ChoiceTile<AppLocalePreference>(
            value: AppLocalePreference.en,
            groupValue: preferences.locale,
            title: strings.languageEnglish,
            onChanged: controller.setLocale,
          ),
          const SizedBox(height: 24),
          Text(strings.appearanceTitle, style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 8),
          _ChoiceTile<AppThemePreference>(
            value: AppThemePreference.system,
            groupValue: preferences.theme,
            title: strings.themeSystem,
            onChanged: controller.setTheme,
          ),
          _ChoiceTile<AppThemePreference>(
            value: AppThemePreference.light,
            groupValue: preferences.theme,
            title: strings.themeLight,
            onChanged: controller.setTheme,
          ),
          _ChoiceTile<AppThemePreference>(
            value: AppThemePreference.dark,
            groupValue: preferences.theme,
            title: strings.themeDark,
            onChanged: controller.setTheme,
          ),
          if (showPrivacyControls) ...[
            const SizedBox(height: 24),
            ListTile(
              contentPadding: EdgeInsets.zero,
              leading: const Icon(Icons.privacy_tip_outlined),
              title: Text(strings.privacyAndData),
              subtitle: Text(strings.privacyAndDataHelper),
              trailing: const Icon(Icons.chevron_right_rounded),
              onTap: () => context.push('/privacy'),
            ),
          ],
        ],
      ),
    );
  }
}

class _ChoiceTile<T> extends StatelessWidget {
  const _ChoiceTile({
    required this.value,
    required this.groupValue,
    required this.title,
    required this.onChanged,
  });

  final T value;
  final T groupValue;
  final String title;
  final Future<void> Function(T value) onChanged;

  @override
  Widget build(BuildContext context) {
    return RadioListTile<T>(
      contentPadding: EdgeInsets.zero,
      value: value,
      groupValue: groupValue,
      title: Text(title),
      onChanged: (selected) {
        if (selected != null) {
          onChanged(selected);
        }
      },
    );
  }
}
