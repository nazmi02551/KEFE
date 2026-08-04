part of 'context_section.dart';

class _ProgressiveContextContent extends ConsumerStatefulWidget {
  const _ProgressiveContextContent({required this.snapshot});

  final CaseContextSnapshot snapshot;

  @override
  ConsumerState<_ProgressiveContextContent> createState() =>
      _ProgressiveContextContentState();
}

class _ProgressiveContextContentState
    extends ConsumerState<_ProgressiveContextContent> {
  int _index = 0;

  @override
  void didUpdateWidget(covariant _ProgressiveContextContent oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.snapshot.caseVersionId != widget.snapshot.caseVersionId) {
      _index = 0;
    }
  }

  List<ContextJourneyLayer> get _layers => [
    ContextJourneyLayer.essential,
    if (widget.snapshot.detailBlocks.isNotEmpty) ContextJourneyLayer.details,
    if (widget.snapshot.sources.isNotEmpty) ContextJourneyLayer.sources,
  ];

  void _move(int delta) {
    final next = (_index + delta).clamp(0, _layers.length - 1).toInt();
    if (next == _index) return;
    setState(() => _index = next);
  }

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final layer = _layers[_index];
    final accent = switch (layer) {
      ContextJourneyLayer.essential => visual.gold,
      ContextJourneyLayer.details => visual.rules,
      ContextJourneyLayer.sources => visual.success,
    };
    return Column(
      key: const ValueKey('context-progressive-journey'),
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              width: 44,
              height: 44,
              decoration: BoxDecoration(
                color: accent.withValues(alpha: 0.10),
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: accent.withValues(alpha: 0.22)),
              ),
              child: Icon(_icon(layer), color: accent),
            ),
            const SizedBox(width: 13),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  KefeEyebrow(
                    strings.contextJourneyProgress(_index + 1, _layers.length),
                    color: accent,
                  ),
                  const SizedBox(height: 5),
                  Text(
                    strings.contextJourneyTitle(layer),
                    style: Theme.of(context).textTheme.titleLarge?.copyWith(
                      fontWeight: FontWeight.w900,
                      height: 1.18,
                    ),
                  ),
                  const SizedBox(height: 5),
                  Text(
                    strings.contextJourneyHelper(layer),
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: visual.mutedForeground,
                      height: 1.42,
                    ),
                  ),
                ],
              ),
            ),
            if (layer != ContextJourneyLayer.essential)
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 5),
                decoration: BoxDecoration(
                  color: visual.surfaceSunken,
                  borderRadius: BorderRadius.circular(99),
                  border: Border.all(color: visual.border),
                ),
                child: Text(
                  strings.contextJourneyOptional,
                  style: Theme.of(context).textTheme.labelSmall?.copyWith(
                    color: visual.mutedForeground,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
          ],
        ),
        const SizedBox(height: 18),
        AnimatedSwitcher(
          duration: KefeMotion.resolve(
            context,
            const Duration(milliseconds: 200),
          ),
          child: KeyedSubtree(
            key: ValueKey('context-layer-${layer.name}'),
            child: _layerContent(layer),
          ),
        ),
        if (_layers.length > 1) ...[
          const SizedBox(height: 14),
          Row(
            children: [
              if (_index > 0)
                Expanded(
                  child: OutlinedButton.icon(
                    key: const ValueKey('context-journey-back'),
                    onPressed: () => _move(-1),
                    icon: const Icon(Icons.arrow_back_rounded),
                    label: Text(strings.contextJourneyBack),
                  ),
                ),
              if (_index > 0 && _index < _layers.length - 1)
                const SizedBox(width: 10),
              if (_index < _layers.length - 1)
                Expanded(
                  child: FilledButton.icon(
                    key: const ValueKey('context-journey-next'),
                    onPressed: () => _move(1),
                    icon: const Icon(Icons.arrow_forward_rounded),
                    label: Text(strings.contextJourneyNext),
                  ),
                ),
            ],
          ),
        ],
      ],
    );
  }

  Widget _layerContent(ContextJourneyLayer layer) => switch (layer) {
    ContextJourneyLayer.essential => _essential(),
    ContextJourneyLayer.details => _details(),
    ContextJourneyLayer.sources => _sources(),
  };

  Widget _essential() {
    final strings = KefeStrings.of(context);
    final content = ref.watch(kefeContentLocalizerProvider);
    final counts = <String, int>{};
    for (final block in widget.snapshot.blocks) {
      counts.update(
        block.claimStatus,
        (value) => value + 1,
        ifAbsent: () => 1,
      );
    }
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        if (counts.isNotEmpty) ...[
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              for (final entry in counts.entries)
                _StatusSummary(
                  label: strings.contextClaimStatus(entry.key),
                  count: entry.value,
                  color: _statusColor(context, entry.key),
                ),
            ],
          ),
          const SizedBox(height: 16),
        ],
        for (final block in widget.snapshot.essentialBlocks) ...[
          _ContextBlockTile(
            block: block,
            snapshot: widget.snapshot,
            content: content,
            locale: strings.locale,
          ),
          const SizedBox(height: 12),
        ],
      ],
    );
  }

  Widget _details() {
    final strings = KefeStrings.of(context);
    final content = ref.watch(kefeContentLocalizerProvider);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        for (final block in widget.snapshot.detailBlocks) ...[
          _ContextBlockTile(
            block: block,
            snapshot: widget.snapshot,
            content: content,
            locale: strings.locale,
          ),
          const SizedBox(height: 12),
        ],
      ],
    );
  }

  Widget _sources() {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final content = ref.watch(kefeContentLocalizerProvider);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        for (final source in widget.snapshot.sources)
          ListTile(
            key: ValueKey('context-source-${source.id}'),
            contentPadding: const EdgeInsets.symmetric(horizontal: 4),
            leading: Container(
              width: 40,
              height: 40,
              decoration: BoxDecoration(
                color: visual.subtleRulesSurface,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Icon(
                Icons.verified_outlined,
                color: visual.rules,
                size: 20,
              ),
            ),
            title: Text(
              content.text(
                namespace: KefeContentNamespace.contextSourceTitle,
                id: source.id,
                locale: strings.locale,
                fallback: source.title,
              ),
            ),
            subtitle: Text(
              '${content.text(namespace: KefeContentNamespace.contextPublisher, id: source.publisher, locale: strings.locale, fallback: source.publisher)} · ${strings.contextSourceKind(source.sourceKind)}',
              style: TextStyle(color: visual.mutedForeground),
            ),
          ),
      ],
    );
  }

  IconData _icon(ContextJourneyLayer layer) => switch (layer) {
    ContextJourneyLayer.essential => Icons.article_outlined,
    ContextJourneyLayer.details => Icons.subject_rounded,
    ContextJourneyLayer.sources => Icons.verified_outlined,
  };
}
