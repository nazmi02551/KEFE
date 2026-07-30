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
          Text(
            strings.languageTitle,
            style: Theme.of(context).textTheme.titleLarge,
          ),
          const SizedBox(height: 8),
          RadioGroup<AppLocalePreference>(
            groupValue: preferences.locale,
            onChanged: (value) {
              if (value != null) {
                controller.setLocale(value);
              }
            },
            child: Column(
              children: [
                _ChoiceTile<AppLocalePreference>(
                  value: AppLocalePreference.system,
                  title: strings.languageSystem,
                ),
                _ChoiceTile<AppLocalePreference>(
                  value: AppLocalePreference.tr,
                  title: strings.languageTurkish,
                ),
                _ChoiceTile<AppLocalePreference>(
                  value: AppLocalePreference.en,
                  title: strings.languageEnglish,
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),
          Text(
            strings.appearanceTitle,
            style: Theme.of(context).textTheme.titleLarge,
          ),
          const SizedBox(height: 8),
          RadioGroup<AppThemePreference>(
            groupValue: preferences.theme,
            onChanged: (value) {
              if (value != null) {
                controller.setTheme(value);
              }
            },
            child: Column(
              children: [
                _ChoiceTile<AppThemePreference>(
                  value: AppThemePreference.system,
                  title: strings.themeSystem,
                ),
                _ChoiceTile<AppThemePreference>(
                  value: AppThemePreference.light,
                  title: strings.themeLight,
                ),
                _ChoiceTile<AppThemePreference>(
                  value: AppThemePreference.dark,
                  title: strings.themeDark,
                ),
              ],
            ),
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
  const _ChoiceTile({required this.value, required this.title});

  final T value;
  final String title;

  @override
  Widget build(BuildContext context) {
    return RadioListTile<T>(
      contentPadding: EdgeInsets.zero,
      value: value,
      title: Text(title),
    );
  }
}
