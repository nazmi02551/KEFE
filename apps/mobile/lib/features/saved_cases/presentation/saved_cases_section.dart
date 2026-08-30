import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/kefe_content_localizer.dart';
import '../../../core/localization/kefe_strings.dart';
import '../../decision/domain/decision_models.dart';
import '../../explore/application/explore_controller.dart';
import '../application/saved_cases_controller.dart';
import '../domain/saved_case.dart';
import 'saved_case_strings.dart';
import 'saved_cases_state_surface.dart';

class SavedCasesSection extends ConsumerStatefulWidget {
  const SavedCasesSection({
    this.visible = false,
    this.lifecycleUpdates = false,
    super.key,
  });

  final bool visible;
  final bool lifecycleUpdates;

  @override
  ConsumerState<SavedCasesSection> createState() => _SavedCasesSectionState();
}

class _SavedCasesSectionState extends ConsumerState<SavedCasesSection> {
  @override
  void initState() {
    super.initState();
    if (widget.visible) {
      Future.microtask(_load);
    }
  }

  @override
  void didUpdateWidget(covariant SavedCasesSection oldWidget) {
    super.didUpdateWidget(oldWidget);
    final becameVisible = !oldWidget.visible && widget.visible;
    final enabledUpdates =
        !oldWidget.lifecycleUpdates && widget.lifecycleUpdates && widget.visible;
    if (becameVisible || enabledUpdates) {
      Future.microtask(_load);
    }
  }

  Future<void> _load() async {
    await Future.wait([
      ref.read(savedCasesControllerProvider.notifier).load(),
      if (widget.lifecycleUpdates)
        ref.read(exploreControllerProvider.notifier).load(),
    ]);
  }

  @override
  Widget build(BuildContext context) {
    if (!widget.visible) return const SizedBox.shrink();

    final strings = KefeStrings.of(context);
    final state = ref.watch(savedCasesControllerProvider);
    final catalog = widget.lifecycleUpdates
        ? ref.watch(exploreControllerProvider)
        : const ExploreState();
    final currentByCaseId = catalog.loading || catalog.errorCode != null
        ? const <String, DecisionCaseSummary>{}
        : {for (final item in catalog.items) item.id: item};
    final updateCount = state.items.where((item) {
      final current = currentByCaseId[item.caseId];
      return current != null && current.versionId != item.caseVersionId;
    }).length;
    final visual = context.kefeVisual;
    final isLoading =
        state.uiState == SavedCasesUiState.idle ||
        state.uiState == SavedCasesUiState.loading;
    final isError = state.uiState == SavedCasesUiState.error;

    return KefeSurface(
      key: const ValueKey('saved-cases-section'),
      tone: KefeSurfaceTone.raised,
      accent: visual.gold,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              Container(
                width: 40,
                height: 40,
                decoration: BoxDecoration(
                  color: visual.subtleGoldSurface,
                  borderRadius: BorderRadius.circular(14),
                ),
                child: ExcludeSemantics(
                  child: Icon(
                    Icons.bookmark_added_outlined,
                    color: visual.gold,
                  ),
                ),
              ),
              const SizedBox(width: 11),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      strings.savedCasesTitle,
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                    const SizedBox(height: 3),
                    Text(
                      strings.savedCasesSubtitle,
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: visual.mutedForeground,
                      ),
                    ),
                  ],
                ),
              ),
              if (state.items.isNotEmpty)
                Container(
                  constraints: const BoxConstraints(minWidth: 34),
                  padding: const EdgeInsets.symmetric(
                    horizontal: 9,
                    vertical: 6,
                  ),
                  decoration: BoxDecoration(
                    color: visual.subtleGoldSurface,
                    borderRadius: BorderRadius.circular(999),
                  ),
                  child: Text(
                    '${state.items.length}',
                    textAlign: TextAlign.center,
                    style: Theme.of(context).textTheme.labelLarge?.copyWith(
                      color: visual.gold,
                      fontWeight: FontWeight.w900,
                    ),
                  ),
                ),
            ],
          ),
          if (updateCount > 0) ...[
            const SizedBox(height: 12),
            Semantics(
              liveRegion: true,
              label: strings.savedCasesUpdateCount(updateCount),
              child: Container(
                key: const ValueKey('saved-cases-update-count'),
                padding: const EdgeInsets.symmetric(
                  horizontal: 12,
                  vertical: 9,
                ),
                decoration: BoxDecoration(
                  color: visual.subtleRulesSurface,
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(
                    color: visual.rules.withValues(alpha: 0.34),
                  ),
                ),
                child: Row(
                  children: [
                    Icon(Icons.update_rounded, color: visual.rules, size: 19),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        strings.savedCasesUpdateCount(updateCount),
                        style: Theme.of(context).textTheme.labelLarge?.copyWith(
                          color: visual.rules,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
          const SizedBox(height: 14),
          if (isLoading) ...[
            SavedCasesStateSurface.loading(
              key: const ValueKey('saved-cases-loading'),
              message: strings.savedCasesLoading,
              compact: state.items.isNotEmpty,
            ),
            if (state.items.isNotEmpty) const SizedBox(height: 10),
          ],
          if (isError) ...[
            SavedCasesStateSurface.error(
              key: const ValueKey('saved-cases-error'),
              retryButtonKey: const ValueKey('saved-cases-retry'),
              message: strings.savedCasesUnavailable,
              retryLabel: strings.savedCasesRetry,
              compact: state.items.isNotEmpty,
              onRetry: ref.read(savedCasesControllerProvider.notifier).load,
            ),
            if (state.items.isNotEmpty) const SizedBox(height: 10),
          ],
          if (state.uiState == SavedCasesUiState.ready && state.items.isEmpty)
            Text(
              strings.savedCasesEmpty,
              key: const ValueKey('saved-cases-empty'),
              style: Theme.of(
                context,
              ).textTheme.bodyMedium?.copyWith(color: visual.mutedForeground),
            )
          else if (state.items.isNotEmpty)
            for (var index = 0; index < state.items.length; index++) ...[
              _SavedCaseTile(
                item: state.items[index],
                currentSummary: currentByCaseId[state.items[index].caseId],
              ),
              if (index != state.items.length - 1) const SizedBox(height: 10),
            ],
        ],
      ),
    );
  }
}

class _SavedCaseTile extends ConsumerWidget {
  const _SavedCaseTile({required this.item, this.currentSummary});

  final SavedCase item;
  final DecisionCaseSummary? currentSummary;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final locale = Localizations.localeOf(context);
    final localizer = ref.watch(kefeContentLocalizerProvider);
    final hasUpdate =
        currentSummary != null &&
        currentSummary!.versionId != item.caseVersionId;
    final title = localizer.text(
      namespace: KefeContentNamespace.caseTitle,
      id: item.caseId,
      locale: locale,
      fallback: item.title,
    );
    final summary = localizer.text(
      namespace: KefeContentNamespace.caseSummary,
      id: item.caseId,
      locale: locale,
      fallback: item.summary,
    );

    return Semantics(
      container: true,
      label: hasUpdate ? '$title. ${strings.savedCasesUpdated}' : title,
      child: Container(
        padding: const EdgeInsets.all(13),
        decoration: BoxDecoration(
          color: visual.surfaceSunken,
          borderRadius: BorderRadius.circular(17),
          border: Border.all(color: visual.border),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (hasUpdate) ...[
              Container(
                key: ValueKey('saved-case-update-${item.caseId}'),
                padding: const EdgeInsets.all(11),
                decoration: BoxDecoration(
                  color: visual.subtleRulesSurface,
                  borderRadius: BorderRadius.circular(13),
                  border: Border.all(
                    color: visual.rules.withValues(alpha: 0.34),
                  ),
                ),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Icon(
                      Icons.new_releases_outlined,
                      color: visual.rules,
                      size: 19,
                    ),
                    const SizedBox(width: 9),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            strings.savedCasesUpdated,
                            style: Theme.of(context).textTheme.labelLarge
                                ?.copyWith(
                                  color: visual.rules,
                                  fontWeight: FontWeight.w900,
                                ),
                          ),
                          const SizedBox(height: 3),
                          Text(
                            strings.savedCasesUpdatedHint,
                            style: Theme.of(context).textTheme.bodySmall
                                ?.copyWith(color: visual.mutedForeground),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 10),
            ],
            Text(
              title,
              style: Theme.of(
                context,
              ).textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w800),
            ),
            const SizedBox(height: 5),
            Text(
              summary,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style: Theme.of(
                context,
              ).textTheme.bodySmall?.copyWith(color: visual.mutedForeground),
            ),
            const SizedBox(height: 10),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                FilledButton.tonalIcon(
                  key: ValueKey('open-saved-case-${item.caseId}'),
                  onPressed: () {
                    final current = currentSummary;
                    if (hasUpdate && current != null) {
                      ref
                          .read(savedCasesControllerProvider.notifier)
                          .acknowledgeCurrentVersion(current);
                    }
                    context.push('/case/${item.caseId}');
                  },
                  icon: const Icon(Icons.arrow_forward_rounded, size: 17),
                  label: Text(
                    hasUpdate
                        ? strings.savedCasesOpenUpdated
                        : strings.savedCasesOpen,
                  ),
                ),
                TextButton.icon(
                  key: ValueKey('remove-saved-case-${item.caseId}'),
                  onPressed: () => ref
                      .read(savedCasesControllerProvider.notifier)
                      .remove(item.caseId),
                  icon: const Icon(Icons.bookmark_remove_outlined, size: 17),
                  label: Text(strings.savedCasesRemove),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
