import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../../decision/application/decision_controller.dart';
import '../application/community_reason_controller.dart';

class CommunityReasonSection extends ConsumerStatefulWidget {
  const CommunityReasonSection({
    required this.sessionId,
    required this.caseVersionId,
    super.key,
  });

  final String sessionId;
  final String caseVersionId;

  @override
  ConsumerState<CommunityReasonSection> createState() =>
      _CommunityReasonSectionState();
}

class _CommunityReasonSectionState
    extends ConsumerState<CommunityReasonSection> {
  final _textController = TextEditingController();

  @override
  void initState() {
    super.initState();
    Future.microtask(
      () => ref
          .read(communityReasonControllerProvider.notifier)
          .load(widget.sessionId),
    );
  }

  @override
  void dispose() {
    _textController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (!ref.watch(communityReasonExperienceEnabledProvider)) {
      return const SizedBox.shrink();
    }
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final state = ref.watch(communityReasonControllerProvider);
    final controller = ref.read(communityReasonControllerProvider.notifier);
    final snapshot = state.snapshot;
    final patterns = <MapEntry<String, int>>[
      if (snapshot != null && snapshot.sampleSize > 0)
        ...snapshot.tagPatternCounts.entries.where(
          (entry) => entry.value > 0 && entry.value <= snapshot.sampleSize,
        ),
    ]..sort((left, right) {
      final countOrder = right.value.compareTo(left.value);
      return countOrder != 0 ? countOrder : left.key.compareTo(right.key);
    });
    final decision = ref.watch(decisionControllerProvider);
    final reasonPolicy = _reasonPolicy(decision);
    final tags = reasonPolicy.$1;
    final maxTags = reasonPolicy.$2;

    return KefeSurface(
      key: const ValueKey('community-reason-section'),
      tone: KefeSurfaceTone.raised,
      accent: visual.empathy,
      padding: const EdgeInsets.all(18),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          _CommunityHeader(title: strings.communityTitle),
          const SizedBox(height: 12),
          _ContextNote(
            icon: Icons.shield_outlined,
            text: strings.communityPrivateNote,
            accent: visual.rules,
          ),
          if (patterns.isNotEmpty) ...[
            const SizedBox(height: 16),
            _CommunityPatternSummary(
              patterns: patterns,
              sampleSize: snapshot!.sampleSize,
            ),
          ],
          const SizedBox(height: 18),
          Text(
            strings.communityPublishHeading,
            style: Theme.of(
              context,
            ).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w800),
          ),
          const SizedBox(height: 10),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              for (final tag in tags)
                FilterChip(
                  key: ValueKey('community-reason-tag-$tag'),
                  label: Text(strings.reasonTagLabel(tag)),
                  selected: state.selectedTags.contains(tag),
                  onSelected: (_) =>
                      controller.toggleTag(tag, maxTags: maxTags),
                ),
            ],
          ),
          const SizedBox(height: 12),
          TextField(
            key: const ValueKey('community-reason-text'),
            controller: _textController,
            maxLength: 300,
            minLines: 2,
            maxLines: 4,
            onChanged: controller.setText,
            decoration: InputDecoration(
              labelText: strings.communityOptionalText,
              helperText: strings.communityModerationNote,
            ),
          ),
          const SizedBox(height: 2),
          FilledButton.icon(
            key: const ValueKey('community-reason-publish'),
            onPressed:
                state.selectedTags.isEmpty ||
                    state.uiState == CommunityReasonUiState.submitting
                ? null
                : () async {
                    await controller.publish(widget.sessionId);
                    if (mounted &&
                        ref.read(communityReasonControllerProvider).uiState ==
                            CommunityReasonUiState.ready) {
                      _textController.clear();
                    }
                  },
            icon: Icon(
              state.uiState == CommunityReasonUiState.submitting
                  ? Icons.hourglass_top_rounded
                  : Icons.publish_outlined,
            ),
            label: Text(
              state.uiState == CommunityReasonUiState.submitting
                  ? strings.communitySubmitting
                  : strings.communityPublish,
            ),
          ),
          if (state.receipt != null) ...[
            const SizedBox(height: 12),
            Semantics(
              liveRegion: true,
              child: _ContextNote(
                key: const ValueKey('community-reason-receipt'),
                icon: state.receipt!.moderationState == 'PENDING'
                    ? Icons.schedule_rounded
                    : Icons.verified_outlined,
                text: state.receipt!.moderationState == 'PENDING'
                    ? strings.communityReceiptPending
                    : strings.communityReceiptAllowed,
                accent: state.receipt!.moderationState == 'PENDING'
                    ? visual.attention
                    : visual.success,
              ),
            ),
          ],
          if (state.uiState == CommunityReasonUiState.loading) ...[
            const SizedBox(height: 12),
            Semantics(
              liveRegion: true,
              label: strings.communityTitle,
              child: KefeSurface(
                key: const ValueKey('community-reason-loading'),
                tone: KefeSurfaceTone.sunken,
                accent: visual.rules,
                padding: const EdgeInsets.all(12),
                borderRadius: 16,
                child: Row(
                  children: [
                    Icon(Icons.hourglass_empty_rounded, color: visual.rules),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Container(
                        height: 8,
                        decoration: BoxDecoration(
                          color: visual.rules.withValues(alpha: 0.12),
                          borderRadius: BorderRadius.circular(999),
                          border: Border.all(
                            color: visual.rules.withValues(alpha: 0.18),
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
          if (state.errorCode != null) ...[
            const SizedBox(height: 12),
            _ContextNote(
              key: const ValueKey('community-reason-error'),
              icon: Icons.info_outline_rounded,
              text: strings.communityUnavailable(state.errorCode!),
              accent: visual.attention,
            ),
          ],
          if (state.snapshot != null && state.snapshot!.items.isNotEmpty) ...[
            const SizedBox(height: 20),
            Text(
              strings.communityPublished,
              style: Theme.of(
                context,
              ).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w800),
            ),
            const SizedBox(height: 10),
            for (final item in state.snapshot!.items) ...[
              KefeSurface(
                tone: KefeSurfaceTone.sunken,
                accent: visual.empathy,
                padding: const EdgeInsets.all(14),
                borderRadius: 17,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Wrap(
                      spacing: 6,
                      runSpacing: 6,
                      children: item.tags
                          .map(
                            (tag) => _PatternChip(
                              label: strings.reasonTagLabel(tag),
                            ),
                          )
                          .toList(growable: false),
                    ),
                    if (item.text != null) ...[
                      const SizedBox(height: 10),
                      Text(
                        item.text!,
                        style: Theme.of(
                          context,
                        ).textTheme.bodyMedium?.copyWith(height: 1.45),
                      ),
                    ],
                    const SizedBox(height: 10),
                    Wrap(
                      spacing: 4,
                      runSpacing: 4,
                      children: [
                        _ReactionButton(
                          label: strings.communityResonates,
                          count: item.reactionCounts['RESONATES'] ?? 0,
                          onPressed: () =>
                              controller.react(item.id, 'RESONATES'),
                        ),
                        _ReactionButton(
                          label: strings.communityUseful,
                          count: item.reactionCounts['USEFUL'] ?? 0,
                          onPressed: () => controller.react(item.id, 'USEFUL'),
                        ),
                        IconButton(
                          tooltip: strings.communityReport,
                          onPressed: () => controller.report(item.id),
                          icon: const Icon(Icons.flag_outlined, size: 18),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 9),
            ],
            _ContextNote(
              icon: Icons.science_outlined,
              text: state.snapshot!.methodologyNote,
              accent: visual.gold,
            ),
          ],
        ],
      ),
    );
  }

  (List<String>, int) _reasonPolicy(DecisionState decision) {
    final questions = decision.caseData?.questions ?? const [];
    for (final question in questions) {
      final raw = question.responseSchema['reason'];
      if (raw is Map) {
        final map = raw.cast<String, Object?>();
        final tags = (map['tags'] as List<Object?>? ?? const [])
            .whereType<String>()
            .toList(growable: false);
        final rawMax = map['max_tags'];
        final max = rawMax is int ? rawMax.clamp(1, 5) : 3;
        return (tags, max);
      }
    }
    return (const ['FAIRNESS', 'NEED', 'RULES'], 3);
  }
}

class _CommunityHeader extends StatelessWidget {
  const _CommunityHeader({required this.title});

  final String title;

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
            color: visual.subtleEmpathySurface,
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: visual.empathy.withValues(alpha: 0.22)),
          ),
          child: Icon(Icons.people_alt_outlined, color: visual.empathy),
        ),
        const SizedBox(width: 13),
        Expanded(
          child: Text(
            title,
            style: Theme.of(context).textTheme.titleLarge?.copyWith(
              fontWeight: FontWeight.w900,
              height: 1.15,
            ),
          ),
        ),
      ],
    );
  }
}

class _CommunityPatternSummary extends StatelessWidget {
  const _CommunityPatternSummary({
    required this.patterns,
    required this.sampleSize,
  });

  final List<MapEntry<String, int>> patterns;
  final int sampleSize;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    return KefeSurface(
      key: const ValueKey('community-reason-patterns'),
      tone: KefeSurfaceTone.sunken,
      accent: visual.rules,
      padding: const EdgeInsets.all(15),
      borderRadius: 19,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(
            strings.communityPatternsEyebrow,
            style: Theme.of(context).textTheme.labelSmall?.copyWith(
              color: visual.rules,
              fontWeight: FontWeight.w900,
              letterSpacing: 0.7,
            ),
          ),
          const SizedBox(height: 5),
          Text(
            strings.communityPatternsTitle,
            style: Theme.of(
              context,
            ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w900),
          ),
          const SizedBox(height: 3),
          Text(
            strings.communityPatternsSample(sampleSize),
            key: const ValueKey('community-reason-pattern-sample'),
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: visual.mutedForeground,
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: 14),
          for (final pattern in patterns) ...[
            _CommunityPatternRow(
              tag: pattern.key,
              count: pattern.value,
              sampleSize: sampleSize,
            ),
            if (pattern != patterns.last) const SizedBox(height: 12),
          ],
          const SizedBox(height: 14),
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(Icons.info_outline_rounded, size: 18, color: visual.gold),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  strings.communityPatternsNote,
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: visual.mutedForeground,
                    height: 1.4,
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _CommunityPatternRow extends StatelessWidget {
  const _CommunityPatternRow({
    required this.tag,
    required this.count,
    required this.sampleSize,
  });

  final String tag;
  final int count;
  final int sampleSize;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final label = strings.reasonTagLabel(tag);
    final ratio = (count / sampleSize).clamp(0.0, 1.0).toDouble();
    return Semantics(
      key: ValueKey('community-reason-pattern-$tag'),
      container: true,
      label: strings.communityPatternsSemantics(label, count, sampleSize),
      child: ExcludeSemantics(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    label,
                    style: Theme.of(
                      context,
                    ).textTheme.labelLarge?.copyWith(fontWeight: FontWeight.w800),
                  ),
                ),
                const SizedBox(width: 10),
                Text(
                  strings.communityPatternsValue(count, sampleSize),
                  style: Theme.of(context).textTheme.labelMedium?.copyWith(
                    color: visual.mutedForeground,
                    fontFeatures: const [FontFeature.tabularFigures()],
                    fontWeight: FontWeight.w800,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 7),
            Container(
              height: 8,
              decoration: BoxDecoration(
                color: visual.rules.withValues(alpha: 0.12),
                borderRadius: BorderRadius.circular(999),
                border: Border.all(
                  color: visual.rules.withValues(alpha: 0.18),
                ),
              ),
              clipBehavior: Clip.antiAlias,
              alignment: AlignmentDirectional.centerStart,
              child: FractionallySizedBox(
                widthFactor: ratio,
                heightFactor: 1,
                child: DecoratedBox(
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      colors: [visual.rules, visual.empathy],
                    ),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _ContextNote extends StatelessWidget {
  const _ContextNote({
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
    return KefeSurface(
      tone: KefeSurfaceTone.sunken,
      accent: accent,
      padding: const EdgeInsets.all(12),
      borderRadius: 16,
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, size: 19, color: accent),
          const SizedBox(width: 10),
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

class _PatternChip extends StatelessWidget {
  const _PatternChip({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: visual.surfaceRaised,
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: visual.border),
      ),
      child: Text(
        label,
        style: Theme.of(context).textTheme.labelSmall?.copyWith(
          color: visual.mutedForeground,
          fontWeight: FontWeight.w800,
        ),
      ),
    );
  }
}

class _ReactionButton extends StatelessWidget {
  const _ReactionButton({
    required this.label,
    required this.count,
    required this.onPressed,
  });

  final String label;
  final int count;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) => TextButton.icon(
    onPressed: onPressed,
    icon: const Icon(Icons.add_reaction_outlined, size: 17),
    label: Text('$label · $count'),
  );
}
