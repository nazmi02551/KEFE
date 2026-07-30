import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_content_localizer.dart';
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
    final content = ref.watch(kefeContentLocalizerProvider);
    final state = ref.watch(exploreControllerProvider);
    final body = SafeArea(
      bottom: false,
      child: RefreshIndicator(
        onRefresh: ref.read(exploreControllerProvider.notifier).load,
        child: ListView(
          key: const ValueKey('weigh-hub'),
          padding: const EdgeInsets.fromLTRB(20, 18, 20, 34),
          children: [
            _Header(strings: strings),
            const SizedBox(height: 22),
            if (state.loading && state.items.isEmpty)
              KefeSurface(
                tone: KefeSurfaceTone.raised,
                child: Text(strings.loading),
              )
            else if (state.errorCode != null && state.items.isEmpty)
              _ErrorCard(
                message: strings.messageForCode(state.errorCode),
                retryLabel: strings.retry,
                onRetry: ref.read(exploreControllerProvider.notifier).load,
              )
            else if (state.items.isEmpty)
              KefeSurface(
                key: const ValueKey('weigh-hub-empty'),
                tone: KefeSurfaceTone.raised,
                child: Text(strings.weighHubEmpty),
              )
            else ...[
              _FeaturedWeigh(
                item: state.items.first,
                strings: strings,
                content: content,
              ),
              const SizedBox(height: 28),
              Row(
                children: [
                  Expanded(
                    child: Text(
                      strings.weighHubMore,
                      style: Theme.of(context).textTheme.titleLarge?.copyWith(
                        fontWeight: FontWeight.w900,
                        letterSpacing: -0.2,
                      ),
                    ),
                  ),
                  Icon(
                    Icons.arrow_downward_rounded,
                    size: 18,
                    color: context.kefeVisual.mutedForeground,
                  ),
                ],
              ),
              const SizedBox(height: 14),
              for (final item in state.items.skip(1)) ...[
                _WeighCaseTile(
                  item: item,
                  locale: strings.locale,
                  content: content,
                ),
                const SizedBox(height: 12),
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
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              KefeEyebrow(strings.weighHubEyebrow),
              const SizedBox(height: 8),
              Text(
                strings.weighHubTitle,
                style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                  height: 1.04,
                  fontWeight: FontWeight.w900,
                  letterSpacing: -0.7,
                ),
              ),
              const SizedBox(height: 10),
              Text(
                strings.weighHubSubtitle,
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: visual.mutedForeground,
                  height: 1.5,
                ),
              ),
            ],
          ),
        ),
        const SizedBox(width: 16),
        Container(
          width: 52,
          height: 52,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: visual.subtleGoldSurface,
            border: Border.all(color: visual.gold.withValues(alpha: 0.28)),
          ),
          child: Icon(Icons.balance_rounded, color: visual.goldSoft),
        ),
      ],
    );
  }
}

class _FeaturedWeigh extends StatelessWidget {
  const _FeaturedWeigh({
    required this.item,
    required this.strings,
    required this.content,
  });

  final DecisionCaseSummary item;
  final KefeStrings strings;
  final KefeContentLocalizer content;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    final title = content.text(
      namespace: KefeContentNamespace.caseTitle,
      id: item.id,
      locale: strings.locale,
      fallback: item.title,
    );
    final summary = content.text(
      namespace: KefeContentNamespace.caseSummary,
      id: item.id,
      locale: strings.locale,
      fallback: item.summary,
    );

    return KefeSurface(
      key: const ValueKey('weigh-hub-featured'),
      tone: KefeSurfaceTone.premium,
      padding: const EdgeInsets.all(22),
      borderRadius: 26,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          KefeEyebrow(
            strings.weighHubRecommended,
            icon: Icons.auto_awesome_rounded,
          ),
          const SizedBox(height: 16),
          Text(
            title,
            style: Theme.of(context).textTheme.headlineSmall?.copyWith(
              color: visual.onSurfaceStrong,
              fontWeight: FontWeight.w900,
              height: 1.14,
              letterSpacing: -0.4,
            ),
          ),
          const SizedBox(height: 10),
          Text(
            summary,
            style: Theme.of(context).textTheme.bodyLarge?.copyWith(
              color: visual.onSurfaceStrong.withValues(alpha: 0.74),
              height: 1.46,
            ),
          ),
          const SizedBox(height: 22),
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
}

class _WeighCaseTile extends StatelessWidget {
  const _WeighCaseTile({
    required this.item,
    required this.locale,
    required this.content,
  });

  final DecisionCaseSummary item;
  final Locale locale;
  final KefeContentLocalizer content;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    final title = content.text(
      namespace: KefeContentNamespace.caseTitle,
      id: item.id,
      locale: locale,
      fallback: item.title,
    );
    final summary = content.text(
      namespace: KefeContentNamespace.caseSummary,
      id: item.id,
      locale: locale,
      fallback: item.summary,
    );

    return KefeSurface(
      tone: KefeSurfaceTone.raised,
      padding: EdgeInsets.zero,
      child: InkWell(
        key: ValueKey('weigh-case-${item.id}'),
        onTap: () => context.push('/case/${item.id}'),
        borderRadius: BorderRadius.circular(22),
        child: Padding(
          padding: const EdgeInsets.fromLTRB(16, 16, 14, 16),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 44,
                height: 44,
                decoration: BoxDecoration(
                  color: visual.subtleGoldSurface,
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: visual.gold.withValues(alpha: 0.18)),
                ),
                child: Icon(Icons.balance_outlined, color: visual.goldSoft),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w800,
                        height: 1.24,
                      ),
                    ),
                    const SizedBox(height: 6),
                    Text(
                      summary,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: visual.mutedForeground,
                        height: 1.42,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 10),
              Padding(
                padding: const EdgeInsets.only(top: 8),
                child: Icon(
                  Icons.arrow_forward_rounded,
                  color: visual.mutedForeground,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
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
  Widget build(BuildContext context) => KefeSurface(
    tone: KefeSurfaceTone.raised,
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(message),
        const SizedBox(height: 12),
        OutlinedButton(onPressed: onRetry, child: Text(retryLabel)),
      ],
    ),
  );
}
