import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/explore_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../../decision/domain/decision_models.dart';
import '../../media_presentation/domain/case_media_models.dart';
import '../../media_presentation/presentation/case_media_surface.dart';
import '../../saved_cases/application/saved_cases_controller.dart';
import '../../saved_cases/presentation/saved_case_strings.dart';
import '../application/explore_controller.dart';

class DiscoveryExploreScreen extends ConsumerStatefulWidget {
  const DiscoveryExploreScreen({this.embedded = false, super.key});

  final bool embedded;

  @override
  ConsumerState<DiscoveryExploreScreen> createState() =>
      _DiscoveryExploreScreenState();
}

class _DiscoveryExploreScreenState
    extends ConsumerState<DiscoveryExploreScreen> {
  final _queryController = TextEditingController();
  String? _domain;
  bool _savedOnly = false;

  @override
  void initState() {
    super.initState();
    Future.microtask(() async {
      await Future.wait([
        ref.read(exploreControllerProvider.notifier).load(),
        ref.read(savedCasesControllerProvider.notifier).load(),
      ]);
    });
  }

  @override
  void dispose() {
    _queryController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final explore = ref.watch(exploreControllerProvider);
    final saved = ref.watch(savedCasesControllerProvider);
    final filtered = _filter(
      explore.items,
      saved.items.map((item) => item.caseId).toSet(),
    );
    final domains = explore.items.map((item) => item.domain).toSet().toList()
      ..sort();

    final body = SafeArea(
      bottom: false,
      child: explore.loading && explore.items.isEmpty
          ? _ExploreLoading(label: strings.loading)
          : explore.errorCode != null && explore.items.isEmpty
          ? _ExploreError(
              message: strings.messageForCode(explore.errorCode),
              retryLabel: strings.retry,
              onRetry: ref.read(exploreControllerProvider.notifier).load,
            )
          : RefreshIndicator(
              onRefresh: () async {
                await Future.wait([
                  ref.read(exploreControllerProvider.notifier).load(),
                  ref.read(savedCasesControllerProvider.notifier).load(),
                ]);
              },
              child: ListView(
                key: const ValueKey('explore-list'),
                padding: const EdgeInsets.fromLTRB(18, 14, 18, 30),
                children: [
                  const _ExploreHeader(),
                  const SizedBox(height: 20),
                  _DiscoveryControls(
                    queryController: _queryController,
                    domains: domains,
                    selectedDomain: _domain,
                    savedOnly: _savedOnly,
                    onQueryChanged: (_) => setState(() {}),
                    onDomainChanged: (value) => setState(() => _domain = value),
                    onSavedOnlyChanged: (value) =>
                        setState(() => _savedOnly = value),
                    onClear: _clearFilters,
                  ),
                  const SizedBox(height: 20),
                  if (explore.items.isEmpty)
                    _ExploreEmpty(message: strings.exploreMoreComing)
                  else if (filtered.isEmpty)
                    _NoResults(onClear: _clearFilters)
                  else ...[
                    _FeaturedCaseCard(
                      item: filtered.first,
                      saved: saved.contains(filtered.first.id),
                    ),
                    const SizedBox(height: 26),
                    _SectionTitle(
                      title: strings.exploreTrendingWeighs,
                      trailing: strings.exploreCaseCount(filtered.length),
                    ),
                    const SizedBox(height: 12),
                    if (filtered.length == 1)
                      _MoreComing(message: strings.exploreMoreComing)
                    else
                      for (final item in filtered.skip(1)) ...[
                        _CaseCard(item: item, saved: saved.contains(item.id)),
                        const SizedBox(height: 12),
                      ],
                  ],
                ],
              ),
            ),
    );

    return widget.embedded ? body : Scaffold(body: body);
  }

  void _clearFilters() {
    _queryController.clear();
    setState(() {
      _domain = null;
      _savedOnly = false;
    });
  }

  List<DecisionCaseSummary> _filter(
    List<DecisionCaseSummary> items,
    Set<String> savedIds,
  ) {
    final query = _queryController.text.trim().toLowerCase();
    return items
        .where((item) {
          final matchesQuery =
              query.isEmpty ||
              item.title.toLowerCase().contains(query) ||
              item.summary.toLowerCase().contains(query);
          final matchesDomain = _domain == null || item.domain == _domain;
          final matchesSaved = !_savedOnly || savedIds.contains(item.id);
          return matchesQuery && matchesDomain && matchesSaved;
        })
        .toList(growable: false);
  }
}

class _DiscoveryControls extends StatelessWidget {
  const _DiscoveryControls({
    required this.queryController,
    required this.domains,
    required this.selectedDomain,
    required this.savedOnly,
    required this.onQueryChanged,
    required this.onDomainChanged,
    required this.onSavedOnlyChanged,
    required this.onClear,
  });

  final TextEditingController queryController;
  final List<String> domains;
  final String? selectedDomain;
  final bool savedOnly;
  final ValueChanged<String> onQueryChanged;
  final ValueChanged<String?> onDomainChanged;
  final ValueChanged<bool> onSavedOnlyChanged;
  final VoidCallback onClear;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final hasFilters =
        queryController.text.isNotEmpty || selectedDomain != null || savedOnly;

    return Semantics(
      container: true,
      label: strings.exploreDiscoveryLabel,
      child: KefeSurface(
        key: const ValueKey('explore-discovery-controls'),
        tone: KefeSurfaceTone.raised,
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            TextField(
              key: const ValueKey('explore-search-field'),
              controller: queryController,
              onChanged: onQueryChanged,
              textInputAction: TextInputAction.search,
              decoration: InputDecoration(
                hintText: strings.exploreSearchHint,
                hintStyle: TextStyle(color: visual.mutedForeground),
                prefixIcon: Icon(
                  Icons.search_rounded,
                  color: visual.mutedForeground,
                ),
                suffixIcon: queryController.text.isEmpty
                    ? null
                    : IconButton(
                        tooltip: strings.exploreClearFilters,
                        onPressed: onClear,
                        icon: const Icon(Icons.close_rounded),
                      ),
                filled: true,
                fillColor: visual.surfaceSunken,
                enabledBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(17),
                  borderSide: BorderSide(color: visual.border),
                ),
                focusedBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(17),
                  borderSide: BorderSide(color: visual.rules, width: 1.6),
                ),
              ),
            ),
            const SizedBox(height: 14),
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                children: [
                  ChoiceChip(
                    key: const ValueKey('domain-filter-all'),
                    label: Text(strings.exploreAllDomains),
                    selected: selectedDomain == null,
                    onSelected: (_) => onDomainChanged(null),
                  ),
                  for (final domain in domains) ...[
                    const SizedBox(width: 8),
                    ChoiceChip(
                      key: ValueKey('domain-filter-$domain'),
                      label: Text(strings.domainLabel(domain)),
                      selected: selectedDomain == domain,
                      onSelected: (_) => onDomainChanged(domain),
                    ),
                  ],
                ],
              ),
            ),
            const SizedBox(height: 10),
            Wrap(
              spacing: 8,
              runSpacing: 6,
              crossAxisAlignment: WrapCrossAlignment.center,
              children: [
                FilterChip(
                  key: const ValueKey('saved-only-filter'),
                  avatar: const Icon(Icons.bookmark_outline_rounded, size: 18),
                  label: Text(strings.exploreSavedOnly),
                  selected: savedOnly,
                  onSelected: onSavedOnlyChanged,
                ),
                if (hasFilters)
                  TextButton(
                    key: const ValueKey('clear-explore-filters'),
                    onPressed: onClear,
                    child: Text(strings.exploreClearFilters),
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _ExploreHeader extends StatelessWidget {
  const _ExploreHeader();

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;

    return LayoutBuilder(
      builder: (context, constraints) {
        final textScale = MediaQuery.textScalerOf(context).scale(1);
        final stacked = constraints.maxWidth < 320 || textScale > 1.35;
        final title = Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            KefeEyebrow(
              strings.appName,
              icon: Icons.balance_rounded,
              color: visual.goldSoft,
            ),
            const SizedBox(height: 10),
            Text(
              strings.exploreWorldQuestion,
              style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                height: 1.08,
                fontWeight: FontWeight.w900,
                letterSpacing: -0.6,
              ),
            ),
          ],
        );
        final motif = ExcludeSemantics(
          child: Container(
            width: 54,
            height: 54,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: visual.subtleGoldSurface,
              border: Border.all(color: visual.gold.withValues(alpha: 0.28)),
            ),
            child: Icon(Icons.travel_explore_rounded, color: visual.goldSoft),
          ),
        );

        if (stacked) {
          return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [motif, const SizedBox(height: 14), title],
          );
        }
        return Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(child: title),
            const SizedBox(width: 18),
            motif,
          ],
        );
      },
    );
  }
}

class _FeaturedCaseCard extends StatelessWidget {
  const _FeaturedCaseCard({required this.item, required this.saved});

  final DecisionCaseSummary item;
  final bool saved;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;

    return Semantics(
      button: true,
      label: item.title,
      child: KefeSurface(
        key: const ValueKey('explore-featured-surface'),
        tone: KefeSurfaceTone.premium,
        padding: EdgeInsets.zero,
        borderRadius: 26,
        accent: visual.gold,
        child: InkWell(
          key: ValueKey('explore-case-${item.id}'),
          onTap: () => context.push('/case/${item.id}'),
          borderRadius: BorderRadius.circular(26),
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Row(
                  children: [
                    Flexible(
                      child: Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 11,
                          vertical: 7,
                        ),
                        decoration: BoxDecoration(
                          color: visual.gold.withValues(alpha: 0.14),
                          borderRadius: BorderRadius.circular(99),
                          border: Border.all(
                            color: visual.gold.withValues(alpha: 0.28),
                          ),
                        ),
                        child: KefeEyebrow(
                          strings.exploreFeatured,
                          icon: Icons.auto_awesome_rounded,
                        ),
                      ),
                    ),
                    const Spacer(),
                    _SaveButton(item: item, saved: saved, premium: true),
                  ],
                ),
                const SizedBox(height: 14),
                CaseMediaSurface(
                  caseVersionId: item.versionId,
                  slot: CaseMediaSlot.exploreCard,
                  borderRadius: 17,
                ),
                const SizedBox(height: 18),
                Text(
                  item.title,
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(
                    color: visual.onSurfaceStrong,
                    fontWeight: FontWeight.w900,
                    height: 1.18,
                    letterSpacing: -0.3,
                  ),
                ),
                const SizedBox(height: 9),
                Text(
                  item.summary,
                  maxLines: 3,
                  overflow: TextOverflow.ellipsis,
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: visual.onSurfaceStrong.withValues(alpha: 0.74),
                    height: 1.42,
                  ),
                ),
                const SizedBox(height: 17),
                Row(
                  children: [
                    Flexible(
                      child: Text(
                        strings.domainLabel(item.domain),
                        style: Theme.of(context).textTheme.labelMedium
                            ?.copyWith(
                              color: visual.goldSoft,
                              fontWeight: FontWeight.w900,
                            ),
                      ),
                    ),
                    const Spacer(),
                    Icon(Icons.arrow_forward_rounded, color: visual.goldSoft),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _CaseCard extends StatelessWidget {
  const _CaseCard({required this.item, required this.saved});

  final DecisionCaseSummary item;
  final bool saved;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;

    return Semantics(
      button: true,
      label: item.title,
      child: KefeSurface(
        tone: KefeSurfaceTone.raised,
        padding: EdgeInsets.zero,
        borderRadius: 22,
        child: InkWell(
          key: ValueKey('explore-case-${item.id}'),
          borderRadius: BorderRadius.circular(22),
          onTap: () => context.push('/case/${item.id}'),
          child: Padding(
            padding: const EdgeInsets.fromLTRB(16, 16, 10, 16),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                ExcludeSemantics(
                  child: Container(
                    width: 48,
                    height: 48,
                    decoration: BoxDecoration(
                      color: visual.subtleRulesSurface,
                      borderRadius: BorderRadius.circular(15),
                      border: Border.all(
                        color: visual.rules.withValues(alpha: 0.20),
                      ),
                    ),
                    child: Icon(_domainIcon(item.domain), color: visual.rules),
                  ),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        strings.domainLabel(item.domain),
                        style: Theme.of(context).textTheme.labelSmall?.copyWith(
                          color: visual.goldSoft,
                          fontWeight: FontWeight.w900,
                        ),
                      ),
                      const SizedBox(height: 7),
                      Text(
                        item.title,
                        style: Theme.of(context).textTheme.titleMedium
                            ?.copyWith(
                              fontWeight: FontWeight.w900,
                              height: 1.22,
                            ),
                      ),
                      const SizedBox(height: 6),
                      Text(
                        item.summary,
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: visual.mutedForeground,
                          height: 1.40,
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 6),
                _SaveButton(item: item, saved: saved),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _SaveButton extends ConsumerWidget {
  const _SaveButton({
    required this.item,
    required this.saved,
    this.premium = false,
  });

  final DecisionCaseSummary item;
  final bool saved;
  final bool premium;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final foreground = premium ? visual.goldSoft : visual.gold;

    return Semantics(
      button: true,
      label: saved ? strings.savedCasesRemove : strings.savedCasesSave,
      child: IconButton(
        key: ValueKey('save-case-${item.id}'),
        tooltip: saved ? strings.savedCasesRemove : strings.savedCasesSave,
        style: IconButton.styleFrom(
          foregroundColor: foreground,
          backgroundColor: premium
              ? visual.onSurfaceStrong.withValues(alpha: 0.08)
              : visual.subtleGoldSurface,
          side: BorderSide(color: foreground.withValues(alpha: 0.20)),
        ),
        onPressed: () =>
            ref.read(savedCasesControllerProvider.notifier).toggle(item),
        icon: Icon(
          saved ? Icons.bookmark_rounded : Icons.bookmark_border_rounded,
        ),
      ),
    );
  }
}

class _ExploreLoading extends StatelessWidget {
  const _ExploreLoading({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Semantics(
          liveRegion: true,
          label: label,
          child: ExcludeSemantics(
            child: KefeSurface(
              key: const ValueKey('explore-loading'),
              tone: KefeSurfaceTone.raised,
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.hourglass_top_rounded, color: visual.goldSoft),
                  const SizedBox(width: 12),
                  Flexible(child: Text(label)),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _ExploreEmpty extends StatelessWidget {
  const _ExploreEmpty({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    return KefeSurface(
      key: const ValueKey('explore-empty'),
      tone: KefeSurfaceTone.raised,
      child: Column(
        children: [
          Icon(Icons.inbox_outlined, size: 34, color: visual.mutedForeground),
          const SizedBox(height: 12),
          Text(message, textAlign: TextAlign.center),
        ],
      ),
    );
  }
}

class _NoResults extends StatelessWidget {
  const _NoResults({required this.onClear});

  final VoidCallback onClear;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    return KefeSurface(
      key: const ValueKey('explore-no-results'),
      tone: KefeSurfaceTone.raised,
      child: Column(
        children: [
          Icon(Icons.search_off_rounded, size: 34, color: visual.rules),
          const SizedBox(height: 12),
          Text(strings.exploreNoResults, textAlign: TextAlign.center),
          const SizedBox(height: 14),
          OutlinedButton.icon(
            onPressed: onClear,
            icon: const Icon(Icons.refresh_rounded),
            label: Text(strings.exploreClearFilters),
          ),
        ],
      ),
    );
  }
}

class _MoreComing extends StatelessWidget {
  const _MoreComing({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    return KefeSurface(
      key: const ValueKey('explore-more-coming'),
      tone: KefeSurfaceTone.sunken,
      child: Row(
        children: [
          Icon(Icons.auto_awesome_outlined, color: visual.goldSoft),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              message,
              style: Theme.of(
                context,
              ).textTheme.bodyMedium?.copyWith(color: visual.mutedForeground),
            ),
          ),
        ],
      ),
    );
  }
}

class _SectionTitle extends StatelessWidget {
  const _SectionTitle({required this.title, required this.trailing});

  final String title;
  final String trailing;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    return LayoutBuilder(
      builder: (context, constraints) {
        final stacked =
            constraints.maxWidth < 300 ||
            MediaQuery.textScalerOf(context).scale(1) > 1.35;
        final titleWidget = Text(
          title,
          style: Theme.of(
            context,
          ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w900),
        );
        final trailingWidget = Text(
          trailing,
          style: Theme.of(context).textTheme.labelSmall?.copyWith(
            color: visual.mutedForeground,
            fontWeight: FontWeight.w700,
          ),
        );

        if (stacked) {
          return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [titleWidget, const SizedBox(height: 4), trailingWidget],
          );
        }
        return Row(
          children: [
            Expanded(child: titleWidget),
            const SizedBox(width: 12),
            trailingWidget,
          ],
        );
      },
    );
  }
}

class _ExploreError extends StatelessWidget {
  const _ExploreError({
    required this.message,
    required this.retryLabel,
    required this.onRetry,
  });

  final String message;
  final String retryLabel;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: KefeSurface(
          key: const ValueKey('explore-error'),
          tone: KefeSurfaceTone.raised,
          accent: visual.attention,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.cloud_off_outlined, size: 34, color: visual.attention),
              const SizedBox(height: 12),
              Text(message, textAlign: TextAlign.center),
              const SizedBox(height: 14),
              OutlinedButton.icon(
                onPressed: onRetry,
                icon: const Icon(Icons.refresh_rounded),
                label: Text(retryLabel),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

IconData _domainIcon(String domain) => switch (domain) {
  'DAILY_LIFE' => Icons.people_alt_outlined,
  'TECHNOLOGY' => Icons.memory_rounded,
  'SPORTS' => Icons.sports_soccer_rounded,
  'CIVIC' => Icons.account_balance_outlined,
  'WORK_ECONOMY' => Icons.work_outline_rounded,
  'EDUCATION' => Icons.school_outlined,
  _ => Icons.balance_outlined,
};
