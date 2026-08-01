import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_content_localizer.dart';
import '../../../core/localization/kefe_strings.dart';
import '../../community_reason/presentation/community_reason_section.dart';
import '../../consensus/presentation/consensus_section.dart';
import '../../progress/presentation/progress_section.dart';
import '../../sharing/presentation/share_section.dart';
import '../application/decision_controller.dart';
import '../domain/decision_models.dart';
import 'perspective_landscape_visual.dart';

class PerspectiveSection extends ConsumerWidget {
  const PerspectiveSection({
    required this.state,
    required this.result,
    required this.reasonPendingModeration,
    required this.onRetry,
    super.key,
  });

  final PerspectiveUiState state;
  final PerspectiveResult? result;
  final bool reasonPendingModeration;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final decision = ref.watch(decisionControllerProvider);
    final sessionId = decision.sessionId;
    final caseVersionId = decision.caseData?.versionId;
    final hasCommittedContext =
        decision.reveal != null && sessionId != null && caseVersionId != null;
    final consensus = hasCommittedContext
        ? ConsensusSection(sessionId: sessionId, caseVersionId: caseVersionId)
        : null;
    final community = hasCommittedContext
        ? CommunityReasonSection(
            sessionId: sessionId,
            caseVersionId: caseVersionId,
          )
        : null;
    final share = hasCommittedContext
        ? ShareSection(sessionId: sessionId)
        : null;

    if (state == PerspectiveUiState.idle) {
      if (!hasCommittedContext) return const SizedBox.shrink();
      return Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          ?consensus,
          if (community != null) ...[const SizedBox(height: 20), community],
          if (share != null) ...[const SizedBox(height: 20), share],
        ],
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        KefeSurface(
          key: const ValueKey('perspective-section'),
          tone: KefeSurfaceTone.raised,
          accent: visual.rules,
          padding: const EdgeInsets.all(18),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              _PerspectiveHeader(strings: strings),
              if (reasonPendingModeration) ...[
                const SizedBox(height: 14),
                Semantics(
                  liveRegion: true,
                  child: _MethodNote(
                    key: const ValueKey('reason-pending-moderation'),
                    icon: Icons.shield_outlined,
                    text: strings.reasonPendingModeration,
                    accent: visual.attention,
                  ),
                ),
              ],
              const SizedBox(height: 18),
              switch (state) {
                PerspectiveUiState.loading => _LoadingState(strings: strings),
                PerspectiveUiState.errorRetryable => _RetryState(
                  strings: strings,
                  onRetry: onRetry,
                ),
                PerspectiveUiState.ready ||
                PerspectiveUiState.clusterPending ||
                PerspectiveUiState.degradedCurated => _LoadedState(
                  state: state,
                  result: result,
                ),
                PerspectiveUiState.idle => const SizedBox.shrink(),
              },
            ],
          ),
        ),
        if (consensus != null) ...[const SizedBox(height: 20), consensus],
        if (community != null) ...[const SizedBox(height: 20), community],
        const SizedBox(height: 20),
        const ProgressSection(),
        if (share != null) ...[const SizedBox(height: 20), share],
      ],
    );
  }
}

class _PerspectiveHeader extends StatelessWidget {
  const _PerspectiveHeader({required this.strings});

  final KefeStrings strings;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: 44,
          height: 44,
          decoration: BoxDecoration(
            color: visual.subtleRulesSurface,
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: visual.rules.withValues(alpha: 0.22)),
          ),
          child: Icon(Icons.forum_outlined, color: visual.rules),
        ),
        const SizedBox(width: 13),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              KefeEyebrow(strings.perspectiveEyebrow, color: visual.rules),
              const SizedBox(height: 4),
              Text(
                strings.perspectiveTitle,
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.w900,
                  height: 1.15,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _LoadingState extends StatelessWidget {
  const _LoadingState({required this.strings});

  final KefeStrings strings;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    return Semantics(
      label: strings.perspectiveLoading,
      liveRegion: true,
      child: KefeSurface(
        key: const ValueKey('perspective-loading'),
        tone: KefeSurfaceTone.sunken,
        accent: visual.rules,
        padding: const EdgeInsets.all(14),
        borderRadius: 17,
        child: Row(
          children: [
            ExcludeSemantics(
              child: Icon(
                Icons.hourglass_top_rounded,
                color: visual.rules,
                size: 21,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                strings.perspectiveLoading,
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: visual.foreground,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _RetryState extends StatelessWidget {
  const _RetryState({required this.strings, required this.onRetry});

  final KefeStrings strings;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    return Semantics(
      liveRegion: true,
      child: KefeSurface(
        key: const ValueKey('perspective-error'),
        tone: KefeSurfaceTone.sunken,
        accent: visual.empathy,
        padding: const EdgeInsets.all(14),
        borderRadius: 17,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                ExcludeSemantics(
                  child: Icon(
                    Icons.error_outline_rounded,
                    color: visual.empathy,
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    strings.perspectiveUnavailable,
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      color: visual.foreground,
                      height: 1.4,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            OutlinedButton.icon(
              key: const ValueKey('perspective-retry'),
              onPressed: onRetry,
              icon: const Icon(Icons.refresh_rounded),
              label: Text(strings.perspectiveRetry),
            ),
          ],
        ),
      ),
    );
  }
}

class _UnavailableState extends StatelessWidget {
  const _UnavailableState({required this.strings});

  final KefeStrings strings;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    return Semantics(
      liveRegion: true,
      child: KefeSurface(
        key: const ValueKey('perspective-unavailable'),
        tone: KefeSurfaceTone.sunken,
        accent: visual.empathy,
        padding: const EdgeInsets.all(14),
        borderRadius: 17,
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            ExcludeSemantics(
              child: Icon(
                Icons.info_outline_rounded,
                color: visual.empathy,
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: Text(
                strings.perspectiveUnavailable,
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: visual.foreground,
                  height: 1.4,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _LoadedState extends ConsumerWidget {
  const _LoadedState({required this.state, required this.result});

  final PerspectiveUiState state;
  final PerspectiveResult? result;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final snapshot = result;
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

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        if (state == PerspectiveUiState.degradedCurated) ...[
          _MethodNote(
            key: const ValueKey('perspective-curated-note'),
            icon: Icons.verified_outlined,
            text: strings.perspectiveCuratedNote,
            accent: visual.rules,
          ),
          const SizedBox(height: 12),
        ],
        if (state == PerspectiveUiState.clusterPending) ...[
          _MethodNote(
            key: const ValueKey('perspective-cluster-pending'),
            icon: Icons.hourglass_top_rounded,
            text: strings.perspectiveClusterPending,
            accent: visual.attention,
          ),
          const SizedBox(height: 12),
        ],
        if (snapshot.cards.isNotEmpty) ...[
          PerspectiveLandscapeVisual(
            slots: [for (final card in snapshot.cards) card.slot],
          ),
          const SizedBox(height: 14),
        ],
        if (snapshot.cards.isEmpty)
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
                for (var index = 0; index < snapshot.cards.length; index++) ...[
                  _PerspectiveCardView(
                    card: snapshot.cards[index],
                    body: content.text(
                      namespace: KefeContentNamespace.perspectiveBody,
                      id: snapshot.cards[index].id,
                      locale: locale,
                      fallback: snapshot.cards[index].body,
                    ),
                    provenance: content.text(
                      namespace: KefeContentNamespace.perspectiveProvenance,
                      id: snapshot.cards[index].id,
                      locale: locale,
                      fallback: snapshot.cards[index].provenanceLabel,
                    ),
                  ),
                  if (index != snapshot.cards.length - 1)
                    const SizedBox(height: 12),
                ],
              ],
            ),
          ),
        const SizedBox(height: 14),
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

class _MethodNote extends StatelessWidget {
  const _MethodNote({
    required this.icon,
    required this.text,
    required this.accent,
    super.key,
  });

  final IconData icon;
  final String text;
  final Color accent;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: accent.withValues(alpha: visual.isDark ? 0.10 : 0.07),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: accent.withValues(alpha: 0.22)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, size: 18, color: accent),
          const SizedBox(width: 9),
          Expanded(
            child: Text(
              text,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: visual.mutedForeground,
                height: 1.4,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _PerspectiveCardView extends StatelessWidget {
  const _PerspectiveCardView({
    required this.card,
    required this.body,
    required this.provenance,
  });

  final PerspectiveCard card;
  final String body;
  final String provenance;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final theme = context.kefeVisual;
    final visual = _slotVisual(theme, card.slot);
    final label = strings.perspectiveSlotLabel(card.slot);

    return Semantics(
      container: true,
      label: label,
      child: Container(
        key: ValueKey('perspective-card-${card.slot.name}'),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [
              theme.surfaceRaised,
              visual.color.withValues(alpha: theme.isDark ? 0.10 : 0.055),
            ],
          ),
          border: Border.all(color: visual.color.withValues(alpha: 0.28)),
          borderRadius: BorderRadius.circular(18),
          boxShadow: [
            BoxShadow(
              color: visual.color.withValues(
                alpha: theme.isDark ? 0.06 : 0.035,
              ),
              blurRadius: 20,
              offset: const Offset(0, 8),
            ),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                Container(
                  width: 34,
                  height: 34,
                  decoration: BoxDecoration(
                    color: visual.color.withValues(alpha: 0.13),
                    borderRadius: BorderRadius.circular(11),
                    border: Border.all(
                      color: visual.color.withValues(alpha: 0.22),
                    ),
                  ),
                  child: Icon(visual.icon, size: 18, color: visual.color),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    label,
                    style: Theme.of(context).textTheme.labelLarge?.copyWith(
                      color: visual.color,
                      fontWeight: FontWeight.w900,
                      letterSpacing: 0.2,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 13),
            Text(
              body,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                height: 1.5,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 13),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
              decoration: BoxDecoration(
                color: theme.surfaceSunken.withValues(alpha: 0.72),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: theme.border.withValues(alpha: 0.78)),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(
                    Icons.source_outlined,
                    size: 16,
                    color: theme.mutedForeground,
                  ),
                  const SizedBox(width: 7),
                  Expanded(
                    child: Text(
                      '${strings.perspectiveSourceLabel(card.sourceKind)} · $provenance',
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: theme.mutedForeground,
                        height: 1.35,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _MethodologyPill extends StatelessWidget {
  const _MethodologyPill({required this.icon, required this.label});

  final IconData icon;
  final String label;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 7),
      decoration: BoxDecoration(
        color: visual.subtleGoldSurface,
        borderRadius: BorderRadius.circular(99),
        border: Border.all(color: visual.gold.withValues(alpha: 0.20)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 14, color: visual.goldSoft),
          const SizedBox(width: 6),
          Text(
            label,
            style: Theme.of(context).textTheme.labelSmall?.copyWith(
              color: visual.mutedForeground,
              fontWeight: FontWeight.w700,
            ),
          ),
        ],
      ),
    );
  }
}

({Color color, IconData icon}) _slotVisual(
  KefeVisualTheme visual,
  PerspectiveSlot slot,
) => switch (slot) {
  PerspectiveSlot.near => (color: visual.success, icon: Icons.near_me_outlined),
  PerspectiveSlot.opposing => (
    color: visual.empathy,
    icon: Icons.swap_horiz_rounded,
  ),
  PerspectiveSlot.bridge => (color: visual.gold, icon: Icons.hub_outlined),
  PerspectiveSlot.alternativeContext => (
    color: visual.rules,
    icon: Icons.change_circle_outlined,
  ),
};
