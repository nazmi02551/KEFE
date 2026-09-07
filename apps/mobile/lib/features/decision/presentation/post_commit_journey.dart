import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../../community_reason/presentation/community_reason_section.dart';
import '../../consensus/presentation/consensus_section.dart';
import '../../progress/presentation/progress_section.dart';
import '../../progress/presentation/progress_strings.dart';
import '../../sharing/presentation/share_section.dart';
import '../application/decision_controller.dart';
import 'decision_journey_strings.dart';
import 'perspective_section.dart';
import 'reveal_result_card.dart';

enum PostCommitJourneyStageKind {
  result,
  perspectives,
  participation,
  completion,
}

@immutable
class PostCommitJourneyStage {
  const PostCommitJourneyStage(this.kind);

  final PostCommitJourneyStageKind kind;
}

abstract final class PostCommitJourneyResolver {
  static const List<PostCommitJourneyStage> stages = [
    PostCommitJourneyStage(PostCommitJourneyStageKind.result),
    PostCommitJourneyStage(PostCommitJourneyStageKind.perspectives),
    PostCommitJourneyStage(PostCommitJourneyStageKind.participation),
    PostCommitJourneyStage(PostCommitJourneyStageKind.completion),
  ];

  static int clampIndex(int index) => index.clamp(0, stages.length - 1).toInt();
}

class PostCommitJourney extends ConsumerStatefulWidget {
  const PostCommitJourney({
    required this.state,
    required this.sessionId,
    required this.caseVersionId,
    this.completionAction,
    super.key,
  });

  final DecisionState state;
  final String sessionId;
  final String caseVersionId;
  final Widget? completionAction;

  @override
  ConsumerState<PostCommitJourney> createState() => _PostCommitJourneyState();
}

class _PostCommitJourneyState extends ConsumerState<PostCommitJourney> {
  int _stageIndex = 0;

  @override
  void didUpdateWidget(covariant PostCommitJourney oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.sessionId != widget.sessionId ||
        oldWidget.caseVersionId != widget.caseVersionId ||
        oldWidget.state.reveal != widget.state.reveal) {
      _stageIndex = 0;
    }
  }

  void _goTo(int index) {
    final next = PostCommitJourneyResolver.clampIndex(index);
    if (next == _stageIndex) return;
    setState(() => _stageIndex = next);
  }

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final stage = PostCommitJourneyResolver.stages[_stageIndex];
    final total = PostCommitJourneyResolver.stages.length;

    return Column(
      key: const ValueKey('post-commit-journey'),
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        KefeSurface(
          key: const ValueKey('post-commit-stage-header'),
          tone: KefeSurfaceTone.sunken,
          accent: _accentForStage(visual, stage.kind),
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
          borderRadius: 16,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Row(
                children: [
                  Icon(
                    _iconForStage(stage.kind),
                    color: _accentForStage(visual, stage.kind),
                    size: 18,
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      strings.postCommitJourneyTitle(stage.kind.name),
                      style: Theme.of(context).textTheme.labelMedium?.copyWith(
                        color: visual.onSurfaceStrong,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                  ),
                  Text(
                    strings.decisionJourneyProgress(_stageIndex + 1, total),
                    style: Theme.of(context).textTheme.labelMedium?.copyWith(
                      color: _accentForStage(visual, stage.kind),
                      fontWeight: FontWeight.w900,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 10),
              ClipRRect(
                borderRadius: BorderRadius.circular(99),
                child: LinearProgressIndicator(
                  key: const ValueKey('post-commit-journey-progress'),
                  value: (_stageIndex + 1) / total,
                  minHeight: 5,
                  backgroundColor: visual.border.withValues(alpha: 0.45),
                  color: _accentForStage(visual, stage.kind),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 12),
        AnimatedSwitcher(
          duration: KefeMotion.resolve(
            context,
            const Duration(milliseconds: 220),
          ),
          child: KeyedSubtree(
            key: ValueKey('post-commit-stage-${stage.kind.name}'),
            child: _stageContent(stage.kind),
          ),
        ),
        const SizedBox(height: 14),
        _PostCommitNavigation(
          canGoBack: _stageIndex > 0,
          canGoForward: _stageIndex < total - 1,
          onBack: () => _goTo(_stageIndex - 1),
          onForward: () => _goTo(_stageIndex + 1),
        ),
      ],
    );
  }

  Widget _stageContent(PostCommitJourneyStageKind kind) {
    final state = widget.state;
    final controller = ref.read(decisionControllerProvider.notifier);
    return switch (kind) {
      PostCommitJourneyStageKind.result => RevealResultCard(
        reveal: state.reveal!,
        selectedOption: state.selectedOption,
      ),
      PostCommitJourneyStageKind.perspectives => PerspectiveSection(
        state: state.perspectiveState,
        result: state.perspective,
        reasonPendingModeration: state.reasonPendingModeration,
        onRetry: controller.retryPerspective,
        includePostCommitCapabilities: false,
      ),
      PostCommitJourneyStageKind.participation => _ParticipationStage(
        sessionId: widget.sessionId,
        caseVersionId: widget.caseVersionId,
      ),
      PostCommitJourneyStageKind.completion => _CompletionStage(
        sessionId: widget.sessionId,
        completionAction: widget.completionAction,
      ),
    };
  }
}

class _ParticipationStage extends StatefulWidget {
  const _ParticipationStage({
    required this.sessionId,
    required this.caseVersionId,
  });

  final String sessionId;
  final String caseVersionId;

  @override
  State<_ParticipationStage> createState() => _ParticipationStageState();
}

class _ParticipationStageState extends State<_ParticipationStage> {
  int _activeSubstage = 0;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;

    return Column(
      key: const ValueKey('post-commit-participation'),
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Container(
          padding: const EdgeInsets.all(4),
          decoration: BoxDecoration(
            color: visual.surfaceSunken,
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: visual.border.withValues(alpha: 0.6)),
          ),
          child: Row(
            children: [
              Expanded(
                child: _PostCommitTabPill(
                  label: strings.consensusCardTitle,
                  icon: Icons.pie_chart_outline_rounded,
                  selected: _activeSubstage == 0,
                  onTap: () => setState(() => _activeSubstage = 0),
                ),
              ),
              const SizedBox(width: 6),
              Expanded(
                child: _PostCommitTabPill(
                  label: strings.communityTitle,
                  icon: Icons.forum_outlined,
                  selected: _activeSubstage == 1,
                  onTap: () => setState(() => _activeSubstage = 1),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 12),
        if (_activeSubstage == 0) ...[
          ConsensusSection(
            sessionId: widget.sessionId,
            caseVersionId: widget.caseVersionId,
          ),
          const SizedBox(height: 10),
          _SubstagePeekCard(
            key: const ValueKey('community-reason-section'),
            icon: Icons.forum_outlined,
            title: strings.communityTitle,
            subtitle: strings.communityPublishHeading,
            actionLabel: 'İncele ve Yayınla',
            accent: visual.empathy,
            onTap: () => setState(() => _activeSubstage = 1),
          ),
        ] else ...[
          _SubstagePeekCard(
            key: const ValueKey('consensus-section'),
            icon: Icons.pie_chart_outline_rounded,
            title: strings.consensusCardTitle,
            subtitle: strings.communityDistribution,
            actionLabel: 'Konsensüse Dön',
            accent: visual.rules,
            onTap: () => setState(() => _activeSubstage = 0),
          ),
          const SizedBox(height: 10),
          CommunityReasonSection(
            sessionId: widget.sessionId,
            caseVersionId: widget.caseVersionId,
          ),
        ],
      ],
    );
  }
}

class _CompletionStage extends StatefulWidget {
  const _CompletionStage({
    required this.sessionId,
    this.completionAction,
  });

  final String sessionId;
  final Widget? completionAction;

  @override
  State<_CompletionStage> createState() => _CompletionStageState();
}

class _CompletionStageState extends State<_CompletionStage> {
  int _activeSubstage = 0;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;

    return Column(
      key: const ValueKey('post-commit-completion'),
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Container(
          padding: const EdgeInsets.all(4),
          decoration: BoxDecoration(
            color: visual.surfaceSunken,
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: visual.border.withValues(alpha: 0.6)),
          ),
          child: Row(
            children: [
              Expanded(
                child: _PostCommitTabPill(
                  label: strings.shareTitle,
                  icon: Icons.ios_share_rounded,
                  selected: _activeSubstage == 0,
                  onTap: () => setState(() => _activeSubstage = 0),
                ),
              ),
              const SizedBox(width: 6),
              Expanded(
                child: _PostCommitTabPill(
                  label: strings.progressTitle,
                  icon: Icons.trending_up_rounded,
                  selected: _activeSubstage == 1,
                  onTap: () => setState(() => _activeSubstage = 1),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 12),
        if (_activeSubstage == 0) ...[
          ShareSection(sessionId: widget.sessionId),
          const SizedBox(height: 10),
          _SubstagePeekCard(
            key: const ValueKey('my-kefe-progress'),
            icon: Icons.trending_up_rounded,
            title: strings.progressTitle,
            subtitle: strings.journeyTitle,
            actionLabel: 'İlerlemeyi Gör',
            accent: visual.rules,
            onTap: () => setState(() => _activeSubstage = 1),
          ),
        ] else ...[
          _SubstagePeekCard(
            key: const ValueKey('share-section'),
            icon: Icons.ios_share_rounded,
            title: strings.shareTitle,
            subtitle: strings.shareCaseOnlyNote,
            actionLabel: 'Paylaşıma Dön',
            accent: visual.gold,
            onTap: () => setState(() => _activeSubstage = 0),
          ),
          const SizedBox(height: 10),
          const ProgressSection(),
        ],
        if (widget.completionAction != null) ...[
          const SizedBox(height: 14),
          widget.completionAction!,
        ],
      ],
    );
  }
}

class _PostCommitTabPill extends StatelessWidget {
  const _PostCommitTabPill({
    required this.label,
    required this.icon,
    required this.selected,
    required this.onTap,
  });

  final String label;
  final IconData icon;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(10),
        child: AnimatedContainer(
          duration: KefeMotion.resolve(
            context,
            const Duration(milliseconds: 200),
          ),
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
          decoration: BoxDecoration(
            color: selected ? visual.surfaceRaised : Colors.transparent,
            borderRadius: BorderRadius.circular(10),
            boxShadow: selected
                ? [
                    BoxShadow(
                      color: Colors.black.withValues(alpha: 0.12),
                      blurRadius: 6,
                      offset: const Offset(0, 2),
                    ),
                  ]
                : null,
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                icon,
                size: 16,
                color: selected ? visual.goldSoft : visual.mutedForeground,
              ),
              const SizedBox(width: 6),
              Flexible(
                child: Text(
                  label,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: Theme.of(context).textTheme.labelMedium?.copyWith(
                    color: selected
                        ? visual.onSurfaceStrong
                        : visual.mutedForeground,
                    fontWeight: selected ? FontWeight.w900 : FontWeight.w600,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _SubstagePeekCard extends StatelessWidget {
  const _SubstagePeekCard({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.actionLabel,
    required this.accent,
    required this.onTap,
    super.key,
  });

  final IconData icon;
  final String title;
  final String subtitle;
  final String actionLabel;
  final Color accent;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: KefeSurface(
          tone: KefeSurfaceTone.sunken,
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
          borderRadius: 16,
          child: Row(
            children: [
              Container(
                width: 34,
                height: 34,
                decoration: BoxDecoration(
                  color: accent.withValues(alpha: visual.isDark ? 0.15 : 0.08),
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: accent.withValues(alpha: 0.25)),
                ),
                child: Icon(icon, color: accent, size: 18),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: Theme.of(context).textTheme.titleSmall?.copyWith(
                        color: visual.onSurfaceStrong,
                        fontWeight: FontWeight.w800,
                        fontSize: 13,
                      ),
                    ),
                    Text(
                      subtitle,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: visual.mutedForeground,
                        fontSize: 11,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    actionLabel,
                    style: Theme.of(context).textTheme.labelSmall?.copyWith(
                      color: accent,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                  const SizedBox(width: 2),
                  Icon(Icons.chevron_right_rounded, size: 16, color: accent),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _PostCommitNavigation extends StatelessWidget {
  const _PostCommitNavigation({
    required this.canGoBack,
    required this.canGoForward,
    required this.onBack,
    required this.onForward,
  });

  final bool canGoBack;
  final bool canGoForward;
  final VoidCallback onBack;
  final VoidCallback onForward;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    return Row(
      children: [
        if (canGoBack)
          Expanded(
            child: OutlinedButton.icon(
              key: const ValueKey('post-commit-back'),
              onPressed: onBack,
              icon: const Icon(Icons.arrow_back_rounded),
              label: Text(strings.decisionJourneyBack),
            ),
          ),
        if (canGoBack && canGoForward) const SizedBox(width: 10),
        if (canGoForward)
          Expanded(
            flex: canGoBack ? 2 : 1,
            child: FilledButton.icon(
              key: const ValueKey('post-commit-next'),
              onPressed: onForward,
              icon: const Icon(Icons.arrow_forward_rounded),
              label: Text(strings.postCommitJourneyNext),
            ),
          ),
      ],
    );
  }
}

IconData _iconForStage(PostCommitJourneyStageKind kind) => switch (kind) {
  PostCommitJourneyStageKind.result => Icons.insights_rounded,
  PostCommitJourneyStageKind.perspectives => Icons.visibility_outlined,
  PostCommitJourneyStageKind.participation => Icons.forum_outlined,
  PostCommitJourneyStageKind.completion => Icons.route_rounded,
};

Color _accentForStage(
  KefeVisualTheme visual,
  PostCommitJourneyStageKind kind,
) => switch (kind) {
  PostCommitJourneyStageKind.result => visual.gold,
  PostCommitJourneyStageKind.perspectives => visual.rules,
  PostCommitJourneyStageKind.participation => visual.empathy,
  PostCommitJourneyStageKind.completion => visual.success,
};
