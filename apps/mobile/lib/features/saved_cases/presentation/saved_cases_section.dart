import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/design/kefe_theme.dart';
import '../../../core/localization/kefe_strings.dart';
import '../application/saved_cases_controller.dart';
import '../domain/saved_case.dart';
import 'saved_case_strings.dart';

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

    return Card(
      key: const ValueKey('saved-cases-section'),
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              children: [
                const Icon(
                  Icons.bookmark_added_outlined,
                  color: KefeColorTokens.goldSoft,
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        strings.savedCasesTitle,
                        style: Theme.of(context).textTheme.titleMedium
                            ?.copyWith(fontWeight: FontWeight.w900),
                      ),
                      const SizedBox(height: 3),
                      Text(
                        strings.savedCasesSubtitle,
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: KefeColorTokens.textMutedDark,
                        ),
                      ),
                    ],
                  ),
                ),
                if (state.items.isNotEmpty)
                  Text(
                    '${state.items.length}',
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      color: KefeColorTokens.goldSoft,
                      fontWeight: FontWeight.w900,
                    ),
                  ),
              ],
            ),
            const SizedBox(height: 14),
            if (state.uiState == SavedCasesUiState.loading &&
                state.items.isEmpty)
              const LinearProgressIndicator()
            else if (state.items.isEmpty)
              Text(
                strings.savedCasesEmpty,
                key: const ValueKey('saved-cases-empty'),
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: KefeColorTokens.textMutedDark,
                ),
              )
            else
              for (var index = 0; index < state.items.length; index++) ...[
                _SavedCaseTile(item: state.items[index]),
                if (index != state.items.length - 1) const Divider(height: 22),
              ],
          ],
        ),
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
    return Semantics(
      container: true,
      label: item.title,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            item.title,
            style: Theme.of(
              context,
            ).textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w800),
          ),
          const SizedBox(height: 5),
          Text(
            item.summary,
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: KefeColorTokens.textMutedDark,
            ),
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
    );
  }
}
