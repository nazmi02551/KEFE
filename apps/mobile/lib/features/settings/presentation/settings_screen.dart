import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/kefe_strings.dart';
import '../../../core/localization/settings_strings.dart';
import '../../../core/preferences/app_preferences.dart';
import 'settings_persistence_state_surface.dart';

class SettingsScreen extends ConsumerStatefulWidget {
  const SettingsScreen({this.showPrivacyControls = true, super.key});

  final bool showPrivacyControls;

  @override
  ConsumerState<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends ConsumerState<SettingsScreen> {
  @override
  void initState() {
    super.initState();
    Future<void>.microtask(
      () => ref.read(appPreferencesControllerProvider.notifier).load(),
    );
  }

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final preferences = ref.watch(appPreferencesControllerProvider);
    final controller = ref.read(appPreferencesControllerProvider.notifier);
    final visual = context.kefeVisual;
    final showLoading =
        preferences.loading || (!preferences.loaded && !preferences.hasError);
    final choicesEnabled =
        preferences.loaded && !preferences.loading && !preferences.saving;
    final showPersistenceState =
        showLoading || preferences.hasError || preferences.saving;

    return Scaffold(
      appBar: AppBar(
        backgroundColor: visual.surfaceRaised,
        foregroundColor: visual.foreground,
        title: Text(strings.settingsTitle),
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(1),
          child: Divider(height: 1, thickness: 1, color: visual.border),
        ),
      ),
      body: SafeArea(
        child: ListView(
          key: const ValueKey('settings-screen'),
          padding: const EdgeInsets.fromLTRB(14, 12, 14, 20),
          children: [
            if (showLoading)
              SettingsPersistenceStateSurface(
                key: const ValueKey('settings-loading'),
                message: strings.settingsLoading,
                icon: Icons.hourglass_empty_rounded,
                isError: false,
              ),
            if (preferences.hasError)
              SettingsPersistenceStateSurface(
                key: const ValueKey('settings-error'),
                message: strings.settingsUnavailable,
                icon: Icons.cloud_off_outlined,
                isError: true,
                retryLabel: strings.settingsRetry,
                retryKey: const ValueKey('settings-retry'),
                onRetry: controller.retry,
              ),
            if (preferences.saving)
              SettingsPersistenceStateSurface(
                key: const ValueKey('settings-saving'),
                message: strings.settingsSaving,
                icon: Icons.save_outlined,
                isError: false,
              ),
            if (showPersistenceState) const SizedBox(height: 10),
            _SettingsChoiceGroup<AppLocalePreference>(
              key: const ValueKey('settings-language-group'),
              icon: Icons.language_rounded,
              title: strings.languageTitle,
              groupValue: preferences.locale,
              enabled: choicesEnabled,
              onChanged: controller.setLocale,
              choices: [
                _SettingsChoice(
                  value: AppLocalePreference.system,
                  title: strings.languageSystem,
                ),
                _SettingsChoice(
                  value: AppLocalePreference.tr,
                  title: strings.languageTurkish,
                ),
                _SettingsChoice(
                  value: AppLocalePreference.en,
                  title: strings.languageEnglish,
                ),
              ],
            ),
            const SizedBox(height: 10),
            _SettingsChoiceGroup<AppThemePreference>(
              key: const ValueKey('settings-appearance-group'),
              icon: Icons.contrast_rounded,
              title: strings.appearanceTitle,
              groupValue: preferences.theme,
              enabled: choicesEnabled,
              onChanged: controller.setTheme,
              choices: [
                _SettingsChoice(
                  value: AppThemePreference.system,
                  title: strings.themeSystem,
                ),
                _SettingsChoice(
                  value: AppThemePreference.light,
                  title: strings.themeLight,
                ),
                _SettingsChoice(
                  value: AppThemePreference.dark,
                  title: strings.themeDark,
                ),
              ],
            ),
            const SizedBox(height: 10),
            KefeSurface(
              key: const ValueKey('settings-account-entry'),
              tone: KefeSurfaceTone.raised,
              padding: EdgeInsets.zero,
              borderRadius: 18,
              child: Semantics(
                button: true,
                label: strings.accountAndContinuity,
                child: InkWell(
                  onTap: () => context.push('/account'),
                  child: Padding(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 14,
                      vertical: 12,
                    ),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.center,
                      children: [
                        _SettingsIcon(
                          icon: Icons.manage_accounts_outlined,
                          color: visual.goldSoft,
                          compact: true,
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                strings.accountAndContinuity,
                                style: Theme.of(context).textTheme.titleSmall
                                    ?.copyWith(fontWeight: FontWeight.w800),
                              ),
                              const SizedBox(height: 2),
                              Text(
                                strings.accountAndContinuityHelper,
                                maxLines: 3,
                                overflow: TextOverflow.ellipsis,
                                style: Theme.of(context).textTheme.bodySmall
                                    ?.copyWith(color: visual.mutedForeground),
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(width: 8),
                        ExcludeSemantics(
                          child: Icon(
                            Icons.chevron_right_rounded,
                            size: 20,
                            color: visual.mutedForeground,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
            if (widget.showPrivacyControls) ...[
              const SizedBox(height: 10),
              KefeSurface(
                key: const ValueKey('settings-privacy-entry'),
                tone: KefeSurfaceTone.raised,
                padding: EdgeInsets.zero,
                borderRadius: 18,
                child: Semantics(
                  button: true,
                  child: InkWell(
                    onTap: () => context.push('/privacy'),
                    child: Padding(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 14,
                        vertical: 12,
                      ),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.center,
                        children: [
                          _SettingsIcon(
                            icon: Icons.privacy_tip_outlined,
                            color: visual.goldSoft,
                            compact: true,
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  strings.privacyAndData,
                                  style: Theme.of(context).textTheme.titleSmall
                                      ?.copyWith(fontWeight: FontWeight.w800),
                                ),
                                const SizedBox(height: 2),
                                Text(
                                  strings.privacyAndDataHelper,
                                  maxLines: 2,
                                  overflow: TextOverflow.ellipsis,
                                  style: Theme.of(context).textTheme.bodySmall
                                      ?.copyWith(color: visual.mutedForeground),
                                ),
                              ],
                            ),
                          ),
                          const SizedBox(width: 8),
                          ExcludeSemantics(
                            child: Icon(
                              Icons.chevron_right_rounded,
                              size: 20,
                              color: visual.mutedForeground,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _SettingsChoice<T> {
  const _SettingsChoice({required this.value, required this.title});

  final T value;
  final String title;
}

class _SettingsChoiceGroup<T> extends StatelessWidget {
  const _SettingsChoiceGroup({
    required this.icon,
    required this.title,
    required this.groupValue,
    required this.enabled,
    required this.onChanged,
    required this.choices,
    super.key,
  });

  final IconData icon;
  final String title;
  final T groupValue;
  final bool enabled;
  final ValueChanged<T> onChanged;
  final List<_SettingsChoice<T>> choices;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;

    return KefeSurface(
      tone: KefeSurfaceTone.raised,
      padding: const EdgeInsets.fromLTRB(14, 12, 14, 8),
      borderRadius: 18,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              _SettingsIcon(icon: icon, color: visual.goldSoft, compact: true),
              const SizedBox(width: 10),
              Expanded(
                child: Semantics(
                  header: true,
                  child: Text(
                    title,
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.w900,
                    ),
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Semantics(
            enabled: enabled,
            child: IgnorePointer(
              ignoring: !enabled,
              child: Opacity(
                opacity: enabled ? 1 : 0.58,
                child: RadioGroup<T>(
                  groupValue: groupValue,
                  onChanged: (value) {
                    if (value != null) onChanged(value);
                  },
                  child: Column(
                    children: [
                      for (var index = 0; index < choices.length; index++) ...[
                        _ChoiceTile<T>(
                          value: choices[index].value,
                          title: choices[index].title,
                          selected: choices[index].value == groupValue,
                        ),
                        if (index != choices.length - 1)
                          Divider(height: 1, color: visual.border),
                      ],
                    ],
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _ChoiceTile<T> extends StatelessWidget {
  const _ChoiceTile({
    required this.value,
    required this.title,
    required this.selected,
  });

  final T value;
  final String title;
  final bool selected;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;

    return RadioListTile<T>(
      contentPadding: EdgeInsets.zero,
      visualDensity: const VisualDensity(horizontal: -1, vertical: -2),
      value: value,
      selected: selected,
      activeColor: visual.gold,
      selectedTileColor: visual.gold.withValues(alpha: 0.08),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      title: Text(
        title,
        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
          fontWeight: selected ? FontWeight.w800 : FontWeight.w600,
        ),
      ),
    );
  }
}

class _SettingsIcon extends StatelessWidget {
  const _SettingsIcon({
    required this.icon,
    required this.color,
    this.compact = false,
  });

  final IconData icon;
  final Color color;
  final bool compact;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    final dimension = compact ? 32.0 : 38.0;
    return ExcludeSemantics(
      child: DecoratedBox(
        decoration: BoxDecoration(
          color: color.withValues(alpha: 0.12),
          borderRadius: BorderRadius.circular(compact ? 10 : 12),
          border: Border.all(color: visual.border),
        ),
        child: SizedBox.square(
          dimension: dimension,
          child: Icon(icon, size: compact ? 18 : 20, color: color),
        ),
      ),
    );
  }
}
