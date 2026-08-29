import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/kefe_strings.dart';
import '../application/decision_controller.dart';
import '../data/decision_repository.dart';
import '../domain/decision_models.dart';
import 'case_version_history_strings.dart';

final publicCaseVersionHistoryProvider =
    FutureProvider.family<List<PublicCaseVersion>, String>((ref, caseId) {
      return ref
          .watch(decisionRepositoryProvider)
          .fetchPublicCaseHistory(caseId);
    });

class CaseVersionHistorySection extends ConsumerWidget {
  const CaseVersionHistorySection({required this.caseId, super.key});

  final String caseId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final history = ref.watch(publicCaseVersionHistoryProvider(caseId));

    Widget unavailable() => KefeSurface(
      key: const ValueKey('case-history-unavailable'),
      tone: KefeSurfaceTone.raised,
      accent: visual.empathy,
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(
            strings.caseHistoryUnavailable,
            style: Theme.of(
              context,
            ).textTheme.bodyMedium?.copyWith(height: 1.4),
          ),
          const SizedBox(height: 10),
          Align(
            alignment: AlignmentDirectional.centerStart,
            child: TextButton.icon(
              key: const ValueKey('case-history-retry'),
              onPressed: () =>
                  ref.invalidate(publicCaseVersionHistoryProvider(caseId)),
              icon: const Icon(Icons.refresh_rounded),
              label: Text(strings.caseHistoryRetry),
            ),
          ),
        ],
      ),
    );
    return history.when(
      loading: () => KefeSurface(
        key: const ValueKey('case-history-loading'),
        tone: KefeSurfaceTone.raised,
        padding: const EdgeInsets.all(16),
        child: Semantics(
          liveRegion: true,
          label: strings.caseHistoryLoading,
          child: Row(
            children: [
              SizedBox.square(
                dimension: 18,
                child: CircularProgressIndicator(
                  strokeWidth: 2,
                  color: visual.rules,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(child: Text(strings.caseHistoryLoading)),
            ],
          ),
        ),
      ),
      error: (_, _) => unavailable(),
      data: (versions) {
        if (versions.isEmpty) {
          return unavailable();
        }
        return KefeSurface(
          key: const ValueKey('case-history-section'),
          tone: KefeSurfaceTone.raised,
          accent: visual.rules,
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  ExcludeSemantics(
                    child: Icon(Icons.history_rounded, color: visual.rules),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          strings.caseHistoryTitle,
                          style: Theme.of(context).textTheme.titleSmall
                              ?.copyWith(fontWeight: FontWeight.w900),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          strings.caseHistoryHelper,
                          style: Theme.of(context).textTheme.bodySmall
                              ?.copyWith(
                                color: visual.mutedForeground,
                                height: 1.4,
                              ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              if (versions.length == 1) ...[
                _VersionTile(version: versions.single),
                const SizedBox(height: 8),
                Text(
                  strings.caseHistorySingle,
                  key: const ValueKey('case-history-single'),
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: visual.mutedForeground,
                  ),
                ),
              ] else
                Theme(
                  data: Theme.of(
                    context,
                  ).copyWith(dividerColor: Colors.transparent),
                  child: ExpansionTile(
                    key: const ValueKey('case-history-expand'),
                    tilePadding: EdgeInsets.zero,
                    childrenPadding: EdgeInsets.zero,
                    title: Text(
                      strings.caseHistoryCount(versions.length),
                      style: Theme.of(context).textTheme.titleSmall?.copyWith(
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                    children: [
                      for (final version in versions)
                        _VersionTile(version: version),
                    ],
                  ),
                ),
            ],
          ),
        );
      },
    );
  }
}

class _VersionTile extends StatelessWidget {
  const _VersionTile({required this.version});

  final PublicCaseVersion version;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final label = version.isCurrent
        ? strings.caseHistoryCurrent
        : strings.caseHistoryPrevious;
    return Container(
      key: ValueKey('case-history-version-${version.versionNo}'),
      width: double.infinity,
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: visual.surfaceSunken,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(
          color: version.isCurrent
              ? visual.rules.withValues(alpha: 0.38)
              : visual.border,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '$label · ${strings.caseHistoryVersion(version.versionNo)}',
            style: Theme.of(context).textTheme.labelLarge?.copyWith(
              color: version.isCurrent ? visual.rules : visual.foreground,
              fontWeight: FontWeight.w900,
            ),
          ),
          if (version.publishedAt != null) ...[
            const SizedBox(height: 3),
            Text(
              strings.caseHistoryPublished(version.publishedAt!),
              style: Theme.of(
                context,
              ).textTheme.labelSmall?.copyWith(color: visual.mutedForeground),
            ),
          ],
          const SizedBox(height: 7),
          Text(
            version.title,
            style: Theme.of(
              context,
            ).textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w800),
          ),
          if (version.summary.isNotEmpty) ...[
            const SizedBox(height: 4),
            Text(
              version.summary,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: visual.mutedForeground,
                height: 1.35,
              ),
            ),
          ],
        ],
      ),
    );
  }
}
