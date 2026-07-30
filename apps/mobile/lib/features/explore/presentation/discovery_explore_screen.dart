import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/design/kefe_theme.dart';
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
      saved.items.map((e) => e.caseId).toSet(),
    );
    final domains = explore.items.map((item) => item.domain).toSet().toList()
      ..sort();

    final body = SafeArea(
      bottom: false,
      child: explore.loading && explore.items.isEmpty
          ? Center(
              child: Semantics(
                label: strings.loading,
                child: const CircularProgressIndicator(),
              ),
            )
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
                padding: const EdgeInsets.fromLTRB(18, 12, 18, 28),
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
                    onClear: () {
                      _queryController.clear();
                      setState(() {
                        _domain = null;
                        _savedOnly = false;
                      });
                    },
                  ),
                  const SizedBox(height: 20),
                  if (filtered.isEmpty)
                    _NoResults(
                      onClear: () {
                        _queryController.clear();
                        setState(() {
                          _domain = null;
                          _savedOnly = false;
                        });
                      },
                    )
                  else ...[
                    _FeaturedCaseCard(
                      item: filtered.first,
                      saved: saved.contains(filtered.first.id),
                    ),
                    const SizedBox(height: 24),
                    _SectionTitle(
                      title: strings.exploreTrendingWeighs,
                      trailing: strings.exploreCaseCount(filtered.length),
                    ),
                    const SizedBox(height: 12),
                    if (filtered.length == 1)
                      Card(
                        child: Padding(
                          padding: const EdgeInsets.all(18),
                          child: Text(
                            strings.exploreMoreComing,
                            style: Theme.of(context).textTheme.bodyMedium
                                ?.copyWith(
                                  color: KefeColorTokens.textMutedDark,
                                ),
                          ),
                        ),
                      )
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
    final hasFilters =
        queryController.text.isNotEmpty || selectedDomain != null || savedOnly;
    return Semantics(
      container: true,
      label: strings.exploreDiscoveryLabel,
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
              prefixIcon: const Icon(Icons.search_rounded),
              suffixIcon: queryController.text.isEmpty
                  ? null
                  : IconButton(
                      tooltip: strings.exploreClearFilters,
                      onPressed: onClear,
                      icon: const Icon(Icons.close_rounded),
                    ),
              filled: true,
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(18),
              ),
            ),
          ),
          const SizedBox(height: 12),
          SizedBox(
            height: 42,
            child: ListView(
              scrollDirection: Axis.horizontal,
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
          const SizedBox(height: 8),
          Row(
            children: [
              Expanded(
                child: FilterChip(
                  key: const ValueKey('saved-only-filter'),
                  avatar: const Icon(Icons.bookmark_outline_rounded, size: 18),
                  label: Text(strings.exploreSavedOnly),
                  selected: savedOnly,
                  onSelected: onSavedOnlyChanged,
                ),
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
    );
  }
}

class _ExploreHeader extends StatelessWidget {
  const _ExploreHeader();

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  const Icon(
                    Icons.balance_rounded,
                    color: KefeColorTokens.goldSoft,
                    size: 26,
                  ),
                  const SizedBox(width: 9),
                  Text(
                    'KEFE',
                    style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                      fontWeight: FontWeight.w900,
                      letterSpacing: 1.6,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              Text(
                strings.exploreWorldQuestion,
                style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                  height: 1.08,
                  fontWeight: FontWeight.w800,
                ),
              ),
            ],
          ),
        ),
        const CircleAvatar(
          backgroundColor: KefeColorTokens.surfaceDark,
          foregroundColor: KefeColorTokens.goldSoft,
          child: Icon(Icons.tune_rounded),
        ),
      ],
    );
  }
}

class _FeaturedCaseCard extends ConsumerWidget {
  const _FeaturedCaseCard({required this.item, required this.saved});

  final DecisionCaseSummary item;
  final bool saved;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final strings = KefeStrings.of(context);
    return Semantics(
      button: true,
      label: item.title,
      child: InkWell(
        key: ValueKey('explore-case-${item.id}'),
        onTap: () => context.push('/case/${item.id}'),
        borderRadius: BorderRadius.circular(24),
        child: Ink(
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(24),
            border: Border.all(
              color: KefeColorTokens.gold.withValues(alpha: 0.28),
            ),
            gradient: const LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [Color(0xFF24183E), Color(0xFF102641), Color(0xFF271A22)],
            ),
          ),
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Row(
                  children: [
                    Chip(label: Text(strings.exploreFeatured)),
                    const Spacer(),
                    _SaveButton(item: item, saved: saved),
                  ],
                ),
                const SizedBox(height: 12),
                CaseMediaSurface(
                  caseVersionId: item.versionId,
                  slot: CaseMediaSlot.exploreCard,
                  borderRadius: 16,
                ),
                const SizedBox(height: 18),
                Text(
                  item.title,
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(
                    fontWeight: FontWeight.w800,
                    height: 1.18,
                  ),
                ),
                const SizedBox(height: 9),
                Text(
                  item.summary,
                  maxLines: 3,
                  overflow: TextOverflow.ellipsis,
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: KefeColorTokens.textMutedDark,
                    height: 1.35,
                  ),
                ),
                const SizedBox(height: 16),
                Row(
                  children: [
                    Text(
                      strings.domainLabel(item.domain),
                      style: Theme.of(context).textTheme.labelMedium?.copyWith(
                        color: KefeColorTokens.goldSoft,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                    const Spacer(),
                    const Icon(
                      Icons.arrow_forward_rounded,
                      color: KefeColorTokens.goldSoft,
                    ),
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
    return Card(
      child: InkWell(
        key: ValueKey('explore-case-${item.id}'),
        borderRadius: BorderRadius.circular(20),
        onTap: () => context.push('/case/${item.id}'),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 48,
                height: 48,
                decoration: BoxDecoration(
                  color: KefeColorTokens.gold.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(14),
                ),
                child: Icon(
                  _domainIcon(item.domain),
                  color: KefeColorTokens.goldSoft,
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
                        color: KefeColorTokens.goldSoft,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                    const SizedBox(height: 7),
                    Text(
                      item.title,
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w800,
                        height: 1.2,
                      ),
                    ),
                    const SizedBox(height: 6),
                    Text(
                      item.summary,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: KefeColorTokens.textMutedDark,
                        height: 1.35,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              _SaveButton(item: item, saved: saved),
            ],
          ),
        ),
      ),
    );
  }
}

class _SaveButton extends ConsumerWidget {
  const _SaveButton({required this.item, required this.saved});

  final DecisionCaseSummary item;
  final bool saved;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final strings = KefeStrings.of(context);
    return Semantics(
      button: true,
      label: saved ? strings.savedCasesRemove : strings.savedCasesSave,
      child: IconButton(
        key: ValueKey('save-case-${item.id}'),
        tooltip: saved ? strings.savedCasesRemove : strings.savedCasesSave,
        onPressed: () =>
            ref.read(savedCasesControllerProvider.notifier).toggle(item),
        icon: Icon(
          saved ? Icons.bookmark_rounded : Icons.bookmark_border_rounded,
          color: KefeColorTokens.goldSoft,
        ),
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
    return Card(
      key: const ValueKey('explore-no-results'),
      child: Padding(
        padding: const EdgeInsets.all(22),
        child: Column(
          children: [
            const Icon(Icons.search_off_rounded, size: 34),
            const SizedBox(height: 12),
            Text(strings.exploreNoResults, textAlign: TextAlign.center),
            const SizedBox(height: 12),
            OutlinedButton(
              onPressed: onClear,
              child: Text(strings.exploreClearFilters),
            ),
          ],
        ),
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
    return Row(
      children: [
        Text(
          title,
          style: Theme.of(
            context,
          ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800),
        ),
        const Spacer(),
        Text(
          trailing,
          style: Theme.of(context).textTheme.labelSmall?.copyWith(
            color: KefeColorTokens.textMutedDark,
          ),
        ),
      ],
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
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(message, textAlign: TextAlign.center),
            const SizedBox(height: 12),
            OutlinedButton(onPressed: onRetry, child: Text(retryLabel)),
          ],
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
