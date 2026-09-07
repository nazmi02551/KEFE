part of 'perspective_section.dart';

class _LoadedState extends ConsumerStatefulWidget {
  const _LoadedState({required this.state, required this.result});

  final PerspectiveUiState state;
  final PerspectiveResult? result;

  @override
  ConsumerState<_LoadedState> createState() => _LoadedStateState();
}

class _LoadedStateState extends ConsumerState<_LoadedState> {
  int _activeCardIndex = 0;

  @override
  void didUpdateWidget(covariant _LoadedState oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.result != widget.result) {
      _activeCardIndex = 0;
    }
  }

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final snapshot = widget.result;
    if (snapshot == null) return _UnavailableState(strings: strings);

    final content = ref.watch(kefeContentLocalizerProvider);
    final locale = Localizations.localeOf(context);
    final methodologyProvenance = content.text(
      namespace: KefeContentNamespace.perspectiveMethodologyProvenance,
      id: snapshot.caseVersionId,
      locale: locale,
      fallback: snapshot.methodology.provenanceNote,
    );
    final sampleKind = content.text(
      namespace: KefeContentNamespace.perspectiveSampleKind,
      id: snapshot.methodology.sampleKind,
      locale: locale,
      fallback: snapshot.methodology.sampleKind,
    );

    final cards = snapshot.cards;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        if (widget.state == PerspectiveUiState.degradedCurated) ...[
          _MethodNote(
            key: const ValueKey('perspective-curated-note'),
            icon: Icons.verified_outlined,
            text: strings.perspectiveCuratedNote,
            accent: visual.rules,
          ),
          const SizedBox(height: 10),
        ],
        if (widget.state == PerspectiveUiState.clusterPending) ...[
          _MethodNote(
            key: const ValueKey('perspective-cluster-pending'),
            icon: Icons.hourglass_top_rounded,
            text: strings.perspectiveClusterPending,
            accent: visual.attention,
          ),
          const SizedBox(height: 10),
        ],
        if (cards.isNotEmpty) ...[
          PerspectiveLandscapeVisual(
            slots: [for (final card in cards) card.slot],
          ),
          const SizedBox(height: 10),
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: Row(
              children: [
                for (var i = 0; i < cards.length; i++) ...[
                  ChoiceChip(
                    key: ValueKey('perspective-tab-${cards[i].slot.name}'),
                    selected: _activeCardIndex == i,
                    label: Text(strings.perspectiveSlotLabel(cards[i].slot)),
                    onSelected: (_) => setState(() => _activeCardIndex = i),
                  ),
                  if (i != cards.length - 1) const SizedBox(width: 8),
                ],
              ],
            ),
          ),
          const SizedBox(height: 10),
        ],
        if (cards.isEmpty)
          KefeSurface(
            tone: KefeSurfaceTone.sunken,
            padding: const EdgeInsets.all(14),
            borderRadius: 17,
            child: Text(
              strings.perspectiveEmpty,
              style: Theme.of(
                context,
              ).textTheme.bodyMedium?.copyWith(color: visual.mutedForeground),
            ),
          )
        else
          KeyedSubtree(
            key: const ValueKey('perspective-card-stack'),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                for (var index = 0; index < cards.length; index++) ...[
                  _PerspectiveCardView(
                    card: cards[index],
                    body: content.text(
                      namespace: KefeContentNamespace.perspectiveBody,
                      id: cards[index].id,
                      locale: locale,
                      fallback: cards[index].body,
                    ),
                    provenance: content.text(
                      namespace: KefeContentNamespace.perspectiveProvenance,
                      id: cards[index].id,
                      locale: locale,
                      fallback: cards[index].provenanceLabel,
                    ),
                  ),
                  if (index != cards.length - 1) const SizedBox(height: 10),
                ],
              ],
            ),
          ),
        const SizedBox(height: 10),
        KefeSurface(
          key: const ValueKey('perspective-methodology-surface'),
          tone: KefeSurfaceTone.sunken,
          padding: EdgeInsets.zero,
          borderRadius: 17,
          child: Theme(
            data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
            child: ExpansionTile(
              key: const ValueKey('perspective-methodology'),
              tilePadding: const EdgeInsets.symmetric(horizontal: 14),
              childrenPadding: const EdgeInsets.fromLTRB(14, 0, 14, 14),
              leading: Icon(Icons.policy_outlined, color: visual.goldSoft),
              title: Text(
                strings.perspectiveMethodology,
                style: Theme.of(
                  context,
                ).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w800),
              ),
              children: [
                Align(
                  alignment: Alignment.centerLeft,
                  child: Text(
                    methodologyProvenance,
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: visual.mutedForeground,
                      height: 1.45,
                    ),
                  ),
                ),
                const SizedBox(height: 11),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: [
                    _MethodologyPill(
                      icon: Icons.layers_outlined,
                      label: sampleKind,
                    ),
                    _MethodologyPill(
                      icon: Icons.groups_2_outlined,
                      label: 'n=${snapshot.methodology.sampleSize}',
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}
