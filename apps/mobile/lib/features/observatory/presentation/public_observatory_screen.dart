import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/kefe_strings.dart';
import '../../impact/application/institution_response_controller.dart';
import '../../impact/presentation/institution_response_card.dart';
import '../../signal/application/signal_controller.dart';
import '../../signal/presentation/signal_consensus_card.dart';
import '../localization/observatory_strings.dart';

class PublicObservatoryScreen extends ConsumerStatefulWidget {
  const PublicObservatoryScreen({super.key});

  @override
  ConsumerState<PublicObservatoryScreen> createState() =>
      _PublicObservatoryScreenState();
}

class _PublicObservatoryScreenState
    extends ConsumerState<PublicObservatoryScreen> {
  @override
  void initState() {
    super.initState();
    Future.microtask(() {
      ref.read(signalControllerProvider.notifier).load();
      ref.read(institutionResponseControllerProvider.notifier).load();
    });
  }

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final signalState = ref.watch(signalControllerProvider);
    final impactState = ref.watch(institutionResponseControllerProvider);

    return Scaffold(
      appBar: AppBar(
        title: Text(strings.observatoryScreenTitle),
      ),
      body: SafeArea(
        child: ListView(
          key: const ValueKey('public-observatory-screen'),
          padding: const EdgeInsets.fromLTRB(18, 16, 18, 32),
          children: [
            KefeSurface(
              tone: KefeSurfaceTone.premium,
              accent: visual.gold,
              padding: const EdgeInsets.all(20),
              borderRadius: 24,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Row(
                    children: [
                      Container(
                        width: 44,
                        height: 44,
                        decoration: BoxDecoration(
                          color: visual.subtleGoldSurface,
                          borderRadius: BorderRadius.circular(14),
                          border: Border.all(
                            color: visual.gold.withValues(alpha: 0.3),
                          ),
                        ),
                        child: Icon(Icons.public_rounded, color: visual.goldSoft),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            KefeEyebrow(
                              strings.observatoryEyebrow,
                              color: visual.gold,
                            ),
                            const SizedBox(height: 3),
                            Text(
                              strings.observatoryHeaderTitle,
                              style: Theme.of(context)
                                  .textTheme
                                  .titleMedium
                                  ?.copyWith(
                                    fontWeight: FontWeight.w900,
                                    letterSpacing: -0.2,
                                  ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Text(
                    strings.observatoryHeaderBody,
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                          color: visual.mutedForeground,
                          height: 1.45,
                        ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),
            Row(
              children: [
                Expanded(
                  child: Text(
                    strings.observatorySignalsSectionTitle,
                    style: Theme.of(context).textTheme.titleLarge?.copyWith(
                          fontWeight: FontWeight.w900,
                          letterSpacing: -0.2,
                        ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 6),
            Text(
              strings.observatorySignalsSectionBody,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: visual.mutedForeground,
                    height: 1.4,
                  ),
            ),
            const SizedBox(height: 14),
            if (signalState.cards.isEmpty)
              KefeSurface(
                tone: KefeSurfaceTone.sunken,
                padding: const EdgeInsets.all(16),
child: Text(
                    strings.observatorySignalsEmpty,
                  style: TextStyle(color: visual.mutedForeground),
                ),
              )
            else
              for (final card in signalState.cards) ...[
                SignalConsensusCard(
                  signal: card,
                  onTap: () => context.push('/case/${card.caseVersionId}'),
                ),
                const SizedBox(height: 12),
              ],
            const SizedBox(height: 26),
            Row(
              children: [
                Expanded(
                  child: Text(
                    strings.observatoryInstitutionSectionTitle,
                    style: Theme.of(context).textTheme.titleLarge?.copyWith(
                          fontWeight: FontWeight.w900,
                          letterSpacing: -0.2,
                        ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 6),
            Text(
              strings.observatoryInstitutionSectionBody,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: visual.mutedForeground,
                    height: 1.4,
                  ),
            ),
            const SizedBox(height: 14),
            if (impactState.items.isEmpty)
              KefeSurface(
                tone: KefeSurfaceTone.sunken,
                padding: const EdgeInsets.all(16),
child: Text(
                    strings.observatoryInstitutionEmpty,
                  style: TextStyle(color: visual.mutedForeground),
                ),
              )
            else
              for (final item in impactState.items) ...[
                InstitutionResponseCard(response: item),
                const SizedBox(height: 12),
              ],
          ],
        ),
      ),
    );
  }
}
