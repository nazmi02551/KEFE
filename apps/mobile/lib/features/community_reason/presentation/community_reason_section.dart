import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

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
    final state = ref.watch(communityReasonControllerProvider);
    final controller = ref.read(communityReasonControllerProvider.notifier);
    final decision = ref.watch(decisionControllerProvider);
    final reasonPolicy = _reasonPolicy(decision);
    final tags = reasonPolicy.$1;
    final maxTags = reasonPolicy.$2;

    return Card(
      key: const ValueKey('community-reason-section'),
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              children: [
                const Icon(Icons.people_alt_outlined),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    strings.communityTitle,
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              strings.communityPrivateNote,
            ),
            if (state.snapshot != null &&
                state.snapshot!.tagPatternCounts.isNotEmpty) ...[
              const SizedBox(height: 14),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: state.snapshot!.tagPatternCounts.entries
                    .map(
                      (entry) => Chip(
                        label: Text(
                          '${strings.reasonTagLabel(entry.key)} · ${entry.value}',
                        ),
                      ),
                    )
                    .toList(growable: false),
              ),
            ],
            const SizedBox(height: 14),
            Text(
              strings.communityPublishHeading,
              style: Theme.of(context).textTheme.titleSmall,
            ),
            const SizedBox(height: 8),
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
            const SizedBox(height: 10),
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
            FilledButton(
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
              child: Text(
                state.uiState == CommunityReasonUiState.submitting
                    ? strings.communitySubmitting
                    : strings.communityPublish,
              ),
            ),
            if (state.receipt != null) ...[
              const SizedBox(height: 10),
              Semantics(
                liveRegion: true,
                child: Text(
                  state.receipt!.moderationState == 'PENDING'
                      ? strings.communityReceiptPending
                      : strings.communityReceiptAllowed,
                  key: const ValueKey('community-reason-receipt'),
                ),
              ),
            ],
            if (state.uiState == CommunityReasonUiState.loading) ...[
              const SizedBox(height: 12),
              const LinearProgressIndicator(),
            ],
            if (state.errorCode != null) ...[
              const SizedBox(height: 10),
              Text(
                strings.communityUnavailable(state.errorCode!),
              ),
            ],
            if (state.snapshot != null && state.snapshot!.items.isNotEmpty) ...[
              const SizedBox(height: 18),
              Text(
                strings.communityPublished,
                style: Theme.of(context).textTheme.titleSmall,
              ),
              const SizedBox(height: 8),
              for (final item in state.snapshot!.items) ...[
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    border: Border.all(
                      color: Theme.of(context).colorScheme.outlineVariant,
                    ),
                    borderRadius: BorderRadius.circular(14),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Wrap(
                        spacing: 6,
                        children: item.tags
                            .map(
                              (tag) => Chip(
                                label: Text(strings.reasonTagLabel(tag)),
                              ),
                            )
                            .toList(growable: false),
                      ),
                      if (item.text != null) ...[
                        const SizedBox(height: 6),
                        Text(item.text!),
                      ],
                      const SizedBox(height: 8),
                      Wrap(
                        spacing: 4,
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
                            onPressed: () =>
                                controller.react(item.id, 'USEFUL'),
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
                const SizedBox(height: 8),
              ],
              Text(
                state.snapshot!.methodologyNote,
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ],
          ],
        ),
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
