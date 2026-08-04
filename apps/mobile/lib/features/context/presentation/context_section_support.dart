part of 'context_section.dart';

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
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withValues(alpha: 0.24)),
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
  const _ContextBlockTile({
    required this.block,
    required this.snapshot,
    required this.content,
    required this.locale,
  });

  final CaseContextBlock block;
  final CaseContextSnapshot snapshot;
  final KefeContentLocalizer content;
  final Locale locale;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final linkedSources = block.sourceIds
        .map(snapshot.sourceById)
        .whereType<CaseContextSource>()
        .toList(growable: false);
    final statusColor = _statusColor(context, block.claimStatus);
    final title = content.text(
      namespace: KefeContentNamespace.contextBlockTitle,
      id: block.id,
      locale: locale,
      fallback: block.title,
    );
    final body = content.text(
      namespace: KefeContentNamespace.contextBlockBody,
      id: block.id,
      locale: locale,
      fallback: block.body,
    );

    return Container(
      decoration: BoxDecoration(
        color: visual.surfaceSunken,
        border: Border.all(color: visual.border.withValues(alpha: 0.86)),
        borderRadius: BorderRadius.circular(17),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: Text(
                    title,
                    style: Theme.of(context).textTheme.titleSmall?.copyWith(
                      fontWeight: FontWeight.w900,
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
              body,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                height: 1.48,
                color: visual.foreground.withValues(alpha: 0.90),
              ),
            ),
            if (linkedSources.isNotEmpty) ...[
              const SizedBox(height: 12),
              Row(
                children: [
                  Icon(
                    Icons.link_rounded,
                    size: 15,
                    color: visual.mutedForeground,
                  ),
                  const SizedBox(width: 6),
                  Expanded(
                    child: Text(
                      linkedSources
                          .map(
                            (source) => content.text(
                              namespace: KefeContentNamespace.contextPublisher,
                              id: source.publisher,
                              locale: locale,
                              fallback: source.publisher,
                            ),
                          )
                          .join(' · '),
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: visual.mutedForeground,
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
    final visual = context.kefeVisual;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: visual.subtleGoldSurface,
        borderRadius: BorderRadius.circular(99),
      ),
      child: Text(
        '$value',
        style: Theme.of(context).textTheme.labelSmall?.copyWith(
          color: visual.goldSoft,
          fontWeight: FontWeight.w900,
        ),
      ),
    );
  }
}

Color _statusColor(BuildContext context, String status) {
  final visual = context.kefeVisual;
  return switch (status) {
    'VERIFIED' => visual.success,
    'CLAIMED' => visual.attention,
    'DISPUTED' => visual.empathy,
    'UNKNOWN' => visual.mutedForeground,
    _ => visual.mutedForeground,
  };
}
