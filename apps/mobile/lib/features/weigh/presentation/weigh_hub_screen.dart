import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/design/kefe_theme.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../../decision/domain/decision_models.dart';
import '../../explore/application/explore_controller.dart';

class WeighHubScreen extends ConsumerStatefulWidget {
  const WeighHubScreen({this.embedded = false, super.key});

  final bool embedded;

  @override
  ConsumerState<WeighHubScreen> createState() => _WeighHubScreenState();
}

class _WeighHubScreenState extends ConsumerState<WeighHubScreen> {
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
      child: RefreshIndicator(
        onRefresh: ref.read(exploreControllerProvider.notifier).load,
        child: ListView(
          key: const ValueKey('weigh-hub'),
          padding: const EdgeInsets.fromLTRB(18, 14, 18, 30),
          children: [
            _Header(strings: strings),
            const SizedBox(height: 18),
            if (state.loading && state.items.isEmpty)
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(20),
                  child: Text(strings.loading),
                ),
              )
            else if (state.errorCode != null && state.items.isEmpty)
              _ErrorCard(
                message: strings.messageForCode(state.errorCode),
                retryLabel: strings.retry,
                onRetry: ref.read(exploreControllerProvider.notifier).load,
              )
            else if (state.items.isEmpty)
              Card(
                key: const ValueKey('weigh-hub-empty'),
                child: Padding(
                  padding: const EdgeInsets.all(20),
                  child: Text(strings.weighHubEmpty),
                ),
              )
            else ...[
              _FeaturedWeigh(item: state.items.first, strings: strings),
              const SizedBox(height: 22),
              Text(
                strings.weighHubMore,
                style: Theme.of(
                  context,
                ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w900),
              ),
              const SizedBox(height: 12),
              for (final item in state.items.skip(1)) ...[
                _WeighCaseTile(item: item, strings: strings),
                const SizedBox(height: 10),
              ],
            ],
          ],
        ),
      ),
    );

    return widget.embedded ? body : Scaffold(body: body);
  }
}

class _Header extends StatelessWidget {
  const _Header({required this.strings});

  final KefeStrings strings;

  @override
  Widget build(BuildContext context) => Row(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Expanded(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              strings.weighHubEyebrow,
              style: Theme.of(context).textTheme.labelMedium?.copyWith(
                color: KefeColorTokens.goldSoft,
                fontWeight: FontWeight.w900,
                letterSpacing: 1.1,
              ),
            ),
            const SizedBox(height: 7),
            Text(
              strings.weighHubTitle,
              style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                height: 1.08,
                fontWeight: FontWeight.w900,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              strings.weighHubSubtitle,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                color: KefeColorTokens.textMutedDark,
                height: 1.4,
              ),
            ),
          ],
        ),
      ),
      const CircleAvatar(
        backgroundColor: Color(0x222CC9BC),
        foregroundColor: KefeColorTokens.goldSoft,
        child: Icon(Icons.balance_rounded),
      ),
    ],
  );
}

class _FeaturedWeigh extends StatelessWidget {
  const _FeaturedWeigh({required this.item, required this.strings});

  final DecisionCaseSummary item;
  final KefeStrings strings;

  @override
  Widget build(BuildContext context) => Container(
    key: const ValueKey('weigh-hub-featured'),
    padding: const EdgeInsets.all(20),
    decoration: BoxDecoration(
      borderRadius: BorderRadius.circular(24),
      border: Border.all(color: KefeColorTokens.gold.withValues(alpha: 0.3)),
      gradient: const LinearGradient(
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
        colors: [Color(0xFF132B4D), Color(0xFF151927), Color(0xFF3A1D25)],
      ),
    ),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(
          strings.weighHubRecommended,
          style: Theme.of(context).textTheme.labelMedium?.copyWith(
            color: KefeColorTokens.goldSoft,
            fontWeight: FontWeight.w900,
          ),
        ),
        const SizedBox(height: 10),
        Text(
          item.title,
          style: Theme.of(context).textTheme.titleLarge?.copyWith(
            fontWeight: FontWeight.w900,
            height: 1.2,
          ),
        ),
        const SizedBox(height: 8),
        Text(
          item.summary,
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
            color: KefeColorTokens.textMutedDark,
            height: 1.4,
          ),
        ),
        const SizedBox(height: 18),
        FilledButton.icon(
          key: ValueKey('start-weigh-${item.id}'),
          onPressed: () => context.push('/case/${item.id}'),
          icon: const Icon(Icons.balance_rounded),
          label: Text(strings.weighHubStart),
        ),
      ],
    ),
  );
}

class _WeighCaseTile extends StatelessWidget {
  const _WeighCaseTile({required this.item, required this.strings});

  final DecisionCaseSummary item;
  final KefeStrings strings;

  @override
  Widget build(BuildContext context) => Card(
    child: ListTile(
      key: ValueKey('weigh-case-${item.id}'),
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      leading: const CircleAvatar(
        backgroundColor: Color(0x1FD9B66F),
        foregroundColor: KefeColorTokens.goldSoft,
        child: Icon(Icons.balance_outlined),
      ),
      title: Text(
        item.title,
        style: const TextStyle(fontWeight: FontWeight.w800),
      ),
      subtitle: Text(
        item.summary,
        maxLines: 2,
        overflow: TextOverflow.ellipsis,
      ),
      trailing: const Icon(Icons.arrow_forward_rounded),
      onTap: () => context.push('/case/${item.id}'),
    ),
  );
}

class _ErrorCard extends StatelessWidget {
  const _ErrorCard({
    required this.message,
    required this.retryLabel,
    required this.onRetry,
  });

  final String message;
  final String retryLabel;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) => Card(
    child: Padding(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(message),
          const SizedBox(height: 12),
          OutlinedButton(onPressed: onRetry, child: Text(retryLabel)),
        ],
      ),
    ),
  );
}
