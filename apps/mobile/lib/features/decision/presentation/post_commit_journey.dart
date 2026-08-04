import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/kefe_strings.dart';
import '../../community_reason/presentation/community_reason_section.dart';
import '../../consensus/presentation/consensus_section.dart';
import '../../progress/presentation/progress_section.dart';
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
          padding: const EdgeInsets.all(15),
          borderRadius: 17,
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 42,
                height: 42,
                decoration: BoxDecoration(
                  color: _accentForStage(
                    visual,
                    stage.kind,
                  ).withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(13),
                ),
                child: Icon(
                  _iconForStage(stage.kind),
                  color: _accentForStage(visual, stage.kind),
                  size: 21,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    KefeEyebrow(
                      strings.postCommitJourneyProgress(_stageIndex + 1, total),
                      color: _accentForStage(visual, stage.kind),
                    ),
                    const SizedBox(height: 6),
                    Text(
                      strings.postCommitJourneyTitle(stage.kind.name),
                      style: Theme.of(context).textTheme.titleLarge?.copyWith(
                        fontWeight: FontWeight.w900,
                        height: 1.18,
                      ),
                    ),
                    const SizedBox(height: 5),
                    Text(
                      strings.postCommitJourneyHelper(stage.kind.name),
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: visual.mutedForeground,
                        height: 1.4,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),
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
        const SizedBox(height: 16),
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
      ),
      PostCommitJourneyStageKind.participation => Column(
        key: const ValueKey('post-commit-participation'),
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          ConsensusSection(
            sessionId: widget.sessionId,
            caseVersionId: widget.caseVersionId,
          ),
          const SizedBox(height: 18),
          CommunityReasonSection(
            sessionId: widget.sessionId,
            caseVersionId: widget.caseVersionId,
          ),
        ],
      ),
      PostCommitJourneyStageKind.completion => Column(
        key: const ValueKey('post-commit-completion'),
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const ProgressSection(),
          const SizedBox(height: 18),
          ShareSection(sessionId: widget.sessionId),
          if (widget.completionAction != null) ...[
            const SizedBox(height: 18),
            widget.completionAction!,
          ],
        ],
      ),
    };
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
