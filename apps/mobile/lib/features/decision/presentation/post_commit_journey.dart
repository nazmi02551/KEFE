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

    return LayoutBuilder(
      builder: (context, constraints) {
        final hasBoundedHeight = constraints.maxHeight.isFinite;
        final content = AnimatedSwitcher(
          duration: KefeMotion.resolve(
            context,
            const Duration(milliseconds: 220),
          ),
          child: KeyedSubtree(
            key: ValueKey('post-commit-stage-${stage.kind.name}'),
            child: SingleChildScrollView(
              physics: const ClampingScrollPhysics(),
              child: _stageContent(stage.kind),
            ),
          ),
        );

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
                          style:
                              Theme.of(context).textTheme.labelMedium?.copyWith(
                            color: visual.onSurfaceStrong,
                            fontWeight: FontWeight.w900,
                          ),
                        ),
                      ),
                      Text(
                        strings.decisionJourneyProgress(_stageIndex + 1, total),
                        style:
                            Theme.of(context).textTheme.labelMedium?.copyWith(
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
            const SizedBox(height: 8),
            if (hasBoundedHeight) Expanded(child: content) else content,
            const SizedBox(height: 8),
            SafeArea(
              top: false,
              child: _PostCommitNavigation(
                canGoBack: _stageIndex > 0,
                canGoForward: _stageIndex < total - 1,
                onBack: () => _goTo(_stageIndex - 1),
                onForward: () => _goTo(_stageIndex + 1),
              ),
            ),
          ],
        );
      },
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

class _ParticipationStage extends StatelessWidget {
  const _ParticipationStage({
    required this.sessionId,
    required this.caseVersionId,
  });

  final String sessionId;
  final String caseVersionId;

  @override
  Widget build(BuildContext context) {
    return Column(
      key: const ValueKey('post-commit-participation'),
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        ConsensusSection(
          sessionId: sessionId,
          caseVersionId: caseVersionId,
        ),
        const SizedBox(height: 12),
        CommunityReasonSection(
          sessionId: sessionId,
          caseVersionId: caseVersionId,
        ),
      ],
    );
  }
}

class _CompletionStage extends StatelessWidget {
  const _CompletionStage({
    required this.sessionId,
    this.completionAction,
  });

  final String sessionId;
  final Widget? completionAction;

  @override
  Widget build(BuildContext context) {
    return Column(
      key: const ValueKey('post-commit-completion'),
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        ShareSection(sessionId: sessionId),
        const SizedBox(height: 12),
        const ProgressSection(),
        if (completionAction != null) ...[
          const SizedBox(height: 12),
          completionAction!,
        ],
      ],
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
