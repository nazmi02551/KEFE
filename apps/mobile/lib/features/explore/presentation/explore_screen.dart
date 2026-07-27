import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/localization/kefe_strings.dart';
import '../../decision/domain/decision_models.dart';
import '../application/explore_controller.dart';

class ExploreScreen extends ConsumerStatefulWidget {
  const ExploreScreen({super.key});

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

    return Scaffold(
      appBar: AppBar(title: Text(strings.exploreTitle)),
      body: SafeArea(
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
      ),
    );
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
          Text(strings.exploreIntro, style: Theme.of(context).textTheme.headlineSmall),
          const SizedBox(height: 20),
          Text(strings.exploreEmpty),
        ],
      );
    }

    return ListView.separated(
      key: const ValueKey('explore-list'),
      padding: const EdgeInsets.all(20),
      itemCount: items.length + 1,
      separatorBuilder: (_, _) => const SizedBox(height: 12),
      itemBuilder: (context, index) {
        if (index == 0) {
          return Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: Text(
              strings.exploreIntro,
              style: Theme.of(context).textTheme.headlineSmall,
            ),
          );
        }
        return _CaseCard(item: items[index - 1]);
      },
    );
  }
}

class _CaseCard extends StatelessWidget {
  const _CaseCard({required this.item});

  final DecisionCaseSummary item;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    return Card(
      key: ValueKey('explore-case-${item.id}'),
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: () => context.push('/case/${item.id}'),
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  Chip(label: Text(item.format)),
                  Chip(label: Text(item.domain)),
                ],
              ),
              const SizedBox(height: 12),
              Text(item.title, style: Theme.of(context).textTheme.titleLarge),
              const SizedBox(height: 8),
              Text(item.summary),
              const SizedBox(height: 16),
              Align(
                alignment: Alignment.centerRight,
                child: Text(
                  strings.openCase,
                  style: Theme.of(context).textTheme.labelLarge,
                ),
              ),
            ],
          ),
        ),
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
