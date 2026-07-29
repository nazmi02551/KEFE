import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/design/kefe_theme.dart';
import '../../../core/localization/kefe_strings.dart';
import '../../decision/domain/decision_models.dart';
import '../application/explore_controller.dart';

class ExploreScreen extends ConsumerStatefulWidget {
  const ExploreScreen({this.embedded = false, super.key});

  final bool embedded;

  @override
  ConsumerState<ExploreScreen> createState() => _ExploreScreenState();
}

class _ExploreScreenState extends ConsumerState<ExploreScreen> {
  @override
  void initState() {
    super.initState();
    Future.microtask(() => ref.read(exploreControllerProvider.notifier).load());
  }

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final state = ref.watch(exploreControllerProvider);
    final body = SafeArea(
      bottom: false,
      child: state.loading
          ? Center(
              child: Semantics(
                label: strings.loading,
                child: const CircularProgressIndicator(),
              ),
            )
          : state.errorCode != null
              ? _ExploreError(
                  message: strings.messageForCode(state.errorCode),
                  retryLabel: strings.retry,
                  onRetry: ref.read(exploreControllerProvider.notifier).load,
                )
              : RefreshIndicator(
                  onRefresh: ref.read(exploreControllerProvider.notifier).load,
                  child: _ExploreList(items: state.items),
                ),
    );

    return widget.embedded ? body : Scaffold(body: body);
  }
}

class _ExploreList extends StatelessWidget {
  const _ExploreList({required this.items});

  final List<DecisionCaseSummary> items;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    if (items.isEmpty) {
      return ListView(
        key: const ValueKey('explore-empty'),
        padding: const EdgeInsets.all(24),
        children: [
          const _ExploreHeader(),
          const SizedBox(height: 32),
          Text(strings.exploreEmpty),
        ],
      );
    }

    final featured = items.first;
    final remaining = items.skip(1).toList(growable: false);
    final categories = <String>[];
    for (final item in items) {
      if (!categories.contains(item.domain)) categories.add(item.domain);
    }

    return ListView(
      key: const ValueKey('explore-list'),
      padding: const EdgeInsets.fromLTRB(18, 12, 18, 28),
      children: [
        const _ExploreHeader(),
        const SizedBox(height: 22),
        _FeaturedCaseCard(item: featured),
        const SizedBox(height: 24),
        _SectionTitle(title: 'Kategoriler', trailing: '${items.length} tartım'),
        const SizedBox(height: 12),
        SizedBox(
          height: 88,
          child: ListView.separated(
            scrollDirection: Axis.horizontal,
            itemCount: categories.length,
            separatorBuilder: (_, _) => const SizedBox(width: 10),
            itemBuilder: (_, index) => _CategoryTile(domain: categories[index]),
          ),
        ),
        const SizedBox(height: 26),
        _SectionTitle(title: 'Trend tartımlar', trailing: strings.exploreIntro),
        const SizedBox(height: 12),
        if (remaining.isEmpty)
          Card(
            child: Padding(
              padding: const EdgeInsets.all(18),
              child: Text(
                'Yeni tartımlar hazırlandıkça burada görünecek.',
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      color: KefeColorTokens.textMutedDark,
                    ),
              ),
            ),
          )
        else
          for (final item in remaining) ...[
            _CaseCard(item: item),
            const SizedBox(height: 12),
          ],
      ],
    );
  }
}

class _ExploreHeader extends StatelessWidget {
  const _ExploreHeader();

  @override
  Widget build(BuildContext context) {
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
                'Bugün dünya\nneyi tartıyor?',
                style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                      height: 1.08,
                      fontWeight: FontWeight.w800,
                    ),
              ),
            ],
          ),
        ),
        DecoratedBox(
          decoration: BoxDecoration(
            color: Theme.of(context).colorScheme.surface,
            shape: BoxShape.circle,
            border: Border.all(
              color: Theme.of(context).colorScheme.outlineVariant,
            ),
          ),
          child: const Padding(
            padding: EdgeInsets.all(11),
            child: Icon(Icons.notifications_none_rounded, size: 21),
          ),
        ),
      ],
    );
  }
}

class _FeaturedCaseCard extends StatelessWidget {
  const _FeaturedCaseCard({required this.item});

  final DecisionCaseSummary item;

  @override
  Widget build(BuildContext context) {
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
                    const _Pill(
                      icon: Icons.bolt_rounded,
                      label: 'ÖNE ÇIKAN',
                      color: KefeColorTokens.goldSoft,
                    ),
                    const Spacer(),
                    Text(
                      _domainLabel(item.domain),
                      style: Theme.of(context).textTheme.labelMedium?.copyWith(
                            color: KefeColorTokens.textMutedDark,
                          ),
                    ),
                  ],
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
                const SizedBox(height: 18),
                Row(
                  children: [
                    Expanded(
                      child: ClipRRect(
                        borderRadius: BorderRadius.circular(99),
                        child: const SizedBox(
                          height: 4,
                          child: LinearProgressIndicator(
                            value: 0.72,
                            backgroundColor: Color(0xFF263A52),
                            valueColor: AlwaysStoppedAnimation(
                              KefeColorTokens.gold,
                            ),
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(width: 16),
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

class _SectionTitle extends StatelessWidget {
  const _SectionTitle({required this.title, required this.trailing});

  final String title;
  final String trailing;

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.end,
      children: [
        Text(
          title,
          style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.w800,
              ),
        ),
        const Spacer(),
        Flexible(
          child: Text(
            trailing,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: Theme.of(context).textTheme.labelSmall?.copyWith(
                  color: KefeColorTokens.textMutedDark,
                ),
          ),
        ),
      ],
    );
  }
}

class _CategoryTile extends StatelessWidget {
  const _CategoryTile({required this.domain});

  final String domain;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 92,
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 12),
      decoration: BoxDecoration(
        color: KefeColorTokens.surfaceDark,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: KefeColorTokens.borderDark),
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            _domainIcon(domain),
            color: KefeColorTokens.goldSoft,
            size: 22,
          ),
          const SizedBox(height: 8),
          Text(
            _domainLabel(domain),
            textAlign: TextAlign.center,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: Theme.of(context).textTheme.labelSmall,
          ),
        ],
      ),
    );
  }
}

class _CaseCard extends StatelessWidget {
  const _CaseCard({required this.item});

  final DecisionCaseSummary item;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final color = _domainColor(item.domain);
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
                  color: color.withValues(alpha: 0.13),
                  borderRadius: BorderRadius.circular(14),
                ),
                child: Icon(_domainIcon(item.domain), color: color),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Wrap(
                      spacing: 7,
                      runSpacing: 7,
                      children: [
                        _Pill(label: _domainLabel(item.domain), color: color),
                        _Pill(
                          label: item.format.replaceAll('_', ' '),
                          color: KefeColorTokens.textMutedDark,
                        ),
                      ],
                    ),
                    const SizedBox(height: 10),
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
                    const SizedBox(height: 10),
                    Row(
                      children: [
                        Text(
                          strings.openCase,
                          style: Theme.of(context).textTheme.labelMedium?.copyWith(
                                color: KefeColorTokens.goldSoft,
                                fontWeight: FontWeight.w800,
                              ),
                        ),
                        const SizedBox(width: 5),
                        const Icon(
                          Icons.arrow_forward_rounded,
                          size: 16,
                          color: KefeColorTokens.goldSoft,
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _Pill extends StatelessWidget {
  const _Pill({required this.label, required this.color, this.icon});

  final String label;
  final Color color;
  final IconData? icon;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.11),
        borderRadius: BorderRadius.circular(99),
        border: Border.all(color: color.withValues(alpha: 0.24)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (icon != null) ...[
            Icon(icon, size: 13, color: color),
            const SizedBox(width: 4),
          ],
          Text(
            label,
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
            const SizedBox(height: 16),
            FilledButton(onPressed: onRetry, child: Text(retryLabel)),
          ],
        ),
      ),
    );
  }
}

String _domainLabel(String domain) => switch (domain) {
      'DAILY_LIFE' => 'Günlük',
      'TECHNOLOGY' => 'Teknoloji',
      'SPORTS' => 'Spor',
      'CIVIC' => 'Civic',
      'WORK_ECONOMY' => 'İş & Ekonomi',
      'EDUCATION' => 'Eğitim',
      _ => domain.replaceAll('_', ' '),
    };

IconData _domainIcon(String domain) => switch (domain) {
      'DAILY_LIFE' => Icons.people_alt_outlined,
      'TECHNOLOGY' => Icons.psychology_alt_outlined,
      'SPORTS' => Icons.sports_soccer_rounded,
      'CIVIC' => Icons.account_balance_outlined,
      'WORK_ECONOMY' => Icons.work_outline_rounded,
      'EDUCATION' => Icons.school_outlined,
      _ => Icons.balance_outlined,
    };

Color _domainColor(String domain) => switch (domain) {
      'TECHNOLOGY' => const Color(0xFF8E7CFF),
      'SPORTS' => const Color(0xFF5ED7A0),
      'CIVIC' => const Color(0xFF5DA5FF),
      'WORK_ECONOMY' => const Color(0xFFF0B35C),
      'EDUCATION' => const Color(0xFFFF7E9B),
      _ => KefeColorTokens.goldSoft,
    };
