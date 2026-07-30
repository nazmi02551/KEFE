import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/design/kefe_theme.dart';
import '../../../core/localization/internal_alpha_strings.dart';
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
          padding: const EdgeInsets.all(22),
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
                onPressed: () =>
                    ref.invalidate(contextSnapshotProvider(caseVersionId)),
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
            padding: const EdgeInsets.all(18),
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
    final counts = <String, int>{};
    for (final block in snapshot.blocks) {
      counts.update(block.claimStatus, (value) => value + 1, ifAbsent: () => 1);
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Row(
          children: [
            Container(
              width: 40,
              height: 40,
              decoration: BoxDecoration(
                color: KefeColorTokens.gold.withValues(alpha: 0.10),
                borderRadius: BorderRadius.circular(12),
              ),
              child: const Icon(
                Icons.article_outlined,
                color: KefeColorTokens.goldSoft,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    strings.contextEventSummary,
                    style: Theme.of(context).textTheme.labelMedium?.copyWith(
                      color: KefeColorTokens.goldSoft,
                      fontWeight: FontWeight.w900,
                      letterSpacing: 0.6,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    strings.contextHelper,
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: KefeColorTokens.textMutedDark,
                      height: 1.35,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
        if (counts.isNotEmpty) ...[
          const SizedBox(height: 18),
          Text(
            strings.contextInformationStatus,
            style: Theme.of(
              context,
            ).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w800),
          ),
          const SizedBox(height: 10),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              for (final entry in counts.entries)
                _StatusSummary(
                  label: strings.contextClaimStatus(entry.key),
                  count: entry.value,
                  color: _statusColor(entry.key),
                ),
            ],
          ),
        ],
        const SizedBox(height: 18),
        for (final block in snapshot.essentialBlocks) ...[
          _ContextBlockTile(block: block, snapshot: snapshot),
          const SizedBox(height: 12),
        ],
        if (snapshot.detailBlocks.isNotEmpty)
          Theme(
            data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
            child: ExpansionTile(
              key: const ValueKey('context-details'),
              tilePadding: const EdgeInsets.symmetric(horizontal: 4),
              childrenPadding: const EdgeInsets.only(top: 8),
              title: Text(
                strings.contextDetails,
                style: Theme.of(
                  context,
                ).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w800),
              ),
              children: [
                for (final block in snapshot.detailBlocks) ...[
                  _ContextBlockTile(block: block, snapshot: snapshot),
                  const SizedBox(height: 12),
                ],
              ],
            ),
          ),
        if (snapshot.sources.isNotEmpty)
          Theme(
            data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
            child: ExpansionTile(
              key: const ValueKey('context-sources'),
              tilePadding: const EdgeInsets.symmetric(horizontal: 4),
              title: Row(
                children: [
                  Text(
                    strings.contextSources,
                    style: Theme.of(context).textTheme.titleSmall?.copyWith(
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                  const SizedBox(width: 8),
                  _CountBadge(value: snapshot.sources.length),
                ],
              ),
              children: [
                for (final source in snapshot.sources)
                  ListTile(
                    contentPadding: const EdgeInsets.symmetric(horizontal: 4),
                    leading: Container(
                      width: 38,
                      height: 38,
                      decoration: BoxDecoration(
                        color: KefeColorTokens.rules.withValues(alpha: 0.09),
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: const Icon(
                        Icons.verified_outlined,
                        color: KefeColorTokens.rules,
                        size: 20,
                      ),
                    ),
                    title: Text(source.title),
                    subtitle: Text(
                      '${source.publisher} · '
                      '${strings.contextSourceKind(source.sourceKind)}',
                    ),
                  ),
              ],
            ),
          ),
      ],
    );
  }
}

class _StatusSummary extends StatelessWidget {
  const _StatusSummary({
    required this.label,
    required this.count,
    required this.color,
  });

  final String label;
  final int count;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.09),
        borderRadius: BorderRadius.circular(11),
        border: Border.all(color: color.withValues(alpha: 0.22)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 7,
            height: 7,
            decoration: BoxDecoration(color: color, shape: BoxShape.circle),
          ),
          const SizedBox(width: 7),
          Text(
            '$label $count',
            style: Theme.of(context).textTheme.labelSmall?.copyWith(
              color: color,
              fontWeight: FontWeight.w800,
            ),
          ),
        ],
      ),
    );
  }
}

class _ContextBlockTile extends StatelessWidget {
  const _ContextBlockTile({required this.block, required this.snapshot});

  final CaseContextBlock block;
  final CaseContextSnapshot snapshot;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final linkedSources = block.sourceIds
        .map(snapshot.sourceById)
        .whereType<CaseContextSource>()
        .toList(growable: false);
    final statusColor = _statusColor(block.claimStatus);

    return Container(
      decoration: BoxDecoration(
        color: KefeColorTokens.surfaceElevatedDark.withValues(alpha: 0.72),
        border: Border.all(color: Theme.of(context).colorScheme.outlineVariant),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Padding(
        padding: const EdgeInsets.all(15),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: Text(
                    block.title,
                    style: Theme.of(context).textTheme.titleSmall?.copyWith(
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 8,
                    vertical: 5,
                  ),
                  decoration: BoxDecoration(
                    color: statusColor.withValues(alpha: 0.10),
                    borderRadius: BorderRadius.circular(99),
                  ),
                  child: Text(
                    strings.contextClaimStatus(block.claimStatus),
                    style: Theme.of(context).textTheme.labelSmall?.copyWith(
                      color: statusColor,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 9),
            Text(
              block.body,
              style: Theme.of(
                context,
              ).textTheme.bodyMedium?.copyWith(height: 1.45),
            ),
            if (linkedSources.isNotEmpty) ...[
              const SizedBox(height: 11),
              Row(
                children: [
                  const Icon(
                    Icons.link_rounded,
                    size: 15,
                    color: KefeColorTokens.textMutedDark,
                  ),
                  const SizedBox(width: 5),
                  Expanded(
                    child: Text(
                      linkedSources
                          .map((source) => source.publisher)
                          .join(' · '),
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: KefeColorTokens.textMutedDark,
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _CountBadge extends StatelessWidget {
  const _CountBadge({required this.value});

  final int value;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
      decoration: BoxDecoration(
        color: KefeColorTokens.gold.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(99),
      ),
      child: Text(
        '$value',
        style: Theme.of(context).textTheme.labelSmall?.copyWith(
          color: KefeColorTokens.goldSoft,
          fontWeight: FontWeight.w900,
        ),
      ),
    );
  }
}

Color _statusColor(String status) => switch (status) {
  'VERIFIED' => KefeColorTokens.success,
  'CLAIMED' => KefeColorTokens.attention,
  'DISPUTED' => KefeColorTokens.empathy,
  'UNKNOWN' => const Color(0xFF9AA9BC),
  _ => const Color(0xFF9AA9BC),
};
