import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/localization/kefe_strings.dart';
import '../application/context_controller.dart';
import '../domain/context_models.dart';

class ContextSection extends ConsumerWidget {
  const ContextSection({required this.caseVersionId, super.key});

  final String caseVersionId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final strings = KefeStrings.of(context);
    final contextValue = ref.watch(contextSnapshotProvider(caseVersionId));

    return contextValue.when(
      loading: () => Card(
        key: const ValueKey('context-section'),
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Semantics(
            label: strings.contextLoading,
            child: const Center(child: CircularProgressIndicator()),
          ),
        ),
      ),
      error: (_, _) => Card(
        key: const ValueKey('context-section'),
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(
                strings.contextUnavailable,
                key: const ValueKey('context-error'),
              ),
              const SizedBox(height: 12),
              OutlinedButton(
                onPressed: () => ref.invalidate(
                  contextSnapshotProvider(caseVersionId),
                ),
                child: Text(strings.contextRetry),
              ),
            ],
          ),
        ),
      ),
      data: (snapshot) {
        if (snapshot.blocks.isEmpty && snapshot.sources.isEmpty) {
          return const SizedBox.shrink();
        }
        return Card(
          key: const ValueKey('context-section'),
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: _ContextContent(snapshot: snapshot),
          ),
        );
      },
    );
  }
}

class _ContextContent extends StatelessWidget {
  const _ContextContent({required this.snapshot});

  final CaseContextSnapshot snapshot;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(strings.contextTitle, style: Theme.of(context).textTheme.titleLarge),
        const SizedBox(height: 4),
        Text(strings.contextHelper),
        const SizedBox(height: 16),
        for (final block in snapshot.essentialBlocks) ...[
          _ContextBlockTile(block: block, snapshot: snapshot),
          const SizedBox(height: 12),
        ],
        if (snapshot.detailBlocks.isNotEmpty)
          ExpansionTile(
            key: const ValueKey('context-details'),
            tilePadding: EdgeInsets.zero,
            childrenPadding: const EdgeInsets.only(top: 8),
            title: Text(strings.contextDetails),
            children: [
              for (final block in snapshot.detailBlocks) ...[
                _ContextBlockTile(block: block, snapshot: snapshot),
                const SizedBox(height: 12),
              ],
            ],
          ),
        if (snapshot.sources.isNotEmpty)
          ExpansionTile(
            key: const ValueKey('context-sources'),
            tilePadding: EdgeInsets.zero,
            title: Text(strings.contextSources),
            children: [
              for (final source in snapshot.sources)
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  title: Text(source.title),
                  subtitle: Text(
                    '${source.publisher} · '
                    '${strings.contextSourceKind(source.sourceKind)}',
                  ),
                ),
            ],
          ),
      ],
    );
  }
}

class _ContextBlockTile extends StatelessWidget {
  const _ContextBlockTile({
    required this.block,
    required this.snapshot,
  });

  final CaseContextBlock block;
  final CaseContextSnapshot snapshot;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final linkedSources = block.sourceIds
        .map(snapshot.sourceById)
        .whereType<CaseContextSource>()
        .toList(growable: false);

    return DecoratedBox(
      decoration: BoxDecoration(
        border: Border.all(color: Theme.of(context).colorScheme.outlineVariant),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Wrap(
              spacing: 8,
              runSpacing: 8,
              crossAxisAlignment: WrapCrossAlignment.center,
              children: [
                Text(block.title, style: Theme.of(context).textTheme.titleMedium),
                Chip(label: Text(strings.contextClaimStatus(block.claimStatus))),
              ],
            ),
            const SizedBox(height: 8),
            Text(block.body),
            if (linkedSources.isNotEmpty) ...[
              const SizedBox(height: 10),
              Text(
                linkedSources.map((source) => source.publisher).join(' · '),
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ],
          ],
        ),
      ),
    );
  }
}
