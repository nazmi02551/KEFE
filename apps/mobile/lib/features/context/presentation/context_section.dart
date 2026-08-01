import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_content_localizer.dart';
import '../../../core/localization/kefe_strings.dart';
import '../application/context_controller.dart';
import '../domain/context_models.dart';

class ContextSection extends ConsumerWidget {
  const ContextSection({required this.caseVersionId, super.key});

  final String caseVersionId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final contextValue = ref.watch(contextSnapshotProvider(caseVersionId));

    return contextValue.when(
      loading: () => KefeSurface(
        key: const ValueKey('context-section'),
        tone: KefeSurfaceTone.raised,
        accent: visual.rules,
        padding: const EdgeInsets.all(18),
        child: Semantics(
          key: const ValueKey('context-loading'),
          liveRegion: true,
          label: strings.contextLoading,
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
                  strings.contextLoading,
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: visual.foreground,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
      error: (_, _) => KefeSurface(
        key: const ValueKey('context-section'),
        tone: KefeSurfaceTone.raised,
        accent: visual.empathy,
        child: Semantics(
          liveRegion: true,
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
                      strings.contextUnavailable,
                      key: const ValueKey('context-error'),
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
                key: const ValueKey('context-retry'),
                onPressed: () =>
                    ref.invalidate(contextSnapshotProvider(caseVersionId)),
                icon: const Icon(Icons.refresh_rounded),
                label: Text(strings.contextRetry),
              ),
            ],
          ),
        ),
      ),
      data: (snapshot) {
        if (snapshot.blocks.isEmpty && snapshot.sources.isEmpty) {
          return const SizedBox.shrink();
        }
        return KefeSurface(
          key: const ValueKey('context-section'),
          tone: KefeSurfaceTone.raised,
          padding: const EdgeInsets.all(19),
          child: _ContextContent(snapshot: snapshot),
        );
      },
    );
  }
}

class _ContextContent extends ConsumerWidget {
  const _ContextContent({required this.snapshot});

  final CaseContextSnapshot snapshot;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final content = ref.watch(kefeContentLocalizerProvider);
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
              width: 44,
              height: 44,
              decoration: BoxDecoration(
                color: visual.subtleGoldSurface,
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: visual.gold.withValues(alpha: 0.18)),
              ),
              child: Icon(Icons.article_outlined, color: visual.goldSoft),
            ),
            const SizedBox(width: 13),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  KefeEyebrow(strings.contextEventSummary),
                  const SizedBox(height: 4),
                  Text(
                    strings.contextHelper,
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: visual.mutedForeground,
                      height: 1.42,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
        if (counts.isNotEmpty) ...[
          const SizedBox(height: 20),
          Text(
            strings.contextInformationStatus,
            style: Theme.of(
              context,
            ).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w900),
          ),
          const SizedBox(height: 11),
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
        ],
        const SizedBox(height: 18),
        for (final block in snapshot.essentialBlocks) ...[
          _ContextBlockTile(
            block: block,
            snapshot: snapshot,
            content: content,
            locale: strings.locale,
          ),
          const SizedBox(height: 12),
        ],
        if (snapshot.detailBlocks.isNotEmpty)
          Theme(
            data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
            child: ExpansionTile(
              key: const ValueKey('context-details'),
              tilePadding: const EdgeInsets.symmetric(horizontal: 4),
              childrenPadding: const EdgeInsets.only(top: 8),
              iconColor: visual.goldSoft,
              collapsedIconColor: visual.mutedForeground,
              title: Text(
                strings.contextDetails,
                style: Theme.of(
                  context,
                ).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w800),
              ),
              children: [
                for (final block in snapshot.detailBlocks) ...[
                  _ContextBlockTile(
                    block: block,
                    snapshot: snapshot,
                    content: content,
                    locale: strings.locale,
                  ),
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
              iconColor: visual.goldSoft,
              collapsedIconColor: visual.mutedForeground,
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
