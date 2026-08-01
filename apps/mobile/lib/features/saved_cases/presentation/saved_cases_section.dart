import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/kefe_content_localizer.dart';
import '../../../core/localization/kefe_strings.dart';
import '../application/saved_cases_controller.dart';
import '../domain/saved_case.dart';
import 'saved_case_strings.dart';
import 'saved_cases_state_surface.dart';

class SavedCasesSection extends ConsumerStatefulWidget {
  const SavedCasesSection({this.visible = false, super.key});

  final bool visible;

  @override
  ConsumerState<SavedCasesSection> createState() => _SavedCasesSectionState();
}

class _SavedCasesSectionState extends ConsumerState<SavedCasesSection> {
  @override
  void initState() {
    super.initState();
    if (widget.visible) {
      Future.microtask(
        () => ref.read(savedCasesControllerProvider.notifier).load(),
      );
    }
  }

  @override
  void didUpdateWidget(covariant SavedCasesSection oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (!oldWidget.visible && widget.visible) {
      Future.microtask(
        () => ref.read(savedCasesControllerProvider.notifier).load(),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    if (!widget.visible) return const SizedBox.shrink();

    final strings = KefeStrings.of(context);
    final state = ref.watch(savedCasesControllerProvider);
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
              _SavedCaseTile(item: state.items[index]),
              if (index != state.items.length - 1) const SizedBox(height: 10),
            ],
        ],
      ),
    );
  }
}

class _SavedCaseTile extends ConsumerWidget {
  const _SavedCaseTile({required this.item});

  final SavedCase item;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final locale = Localizations.localeOf(context);
    final localizer = ref.watch(kefeContentLocalizerProvider);
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
      label: title,
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
                  onPressed: () => context.push('/case/${item.caseId}'),
                  icon: const Icon(Icons.arrow_forward_rounded, size: 17),
                  label: Text(strings.savedCasesOpen),
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
