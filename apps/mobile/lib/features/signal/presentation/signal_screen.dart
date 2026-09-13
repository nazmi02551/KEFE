import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/kefe_strings.dart';
import '../application/signal_controller.dart';
import '../domain/signal_consensus_card_models.dart';

class SignalScreen extends ConsumerWidget {
  const SignalScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final state = ref.watch(signalControllerProvider);

    return Scaffold(
      backgroundColor: visual.canvas,
      body: CustomScrollView(
        slivers: [
          SliverAppBar(
            backgroundColor: visual.canvas,
            surfaceTintColor: Colors.transparent,
            floating: true,
            snap: true,
            title: Text(
              strings.signalScreenTitle,
              style: TextStyle(
                color: visual.foreground,
                fontWeight: FontWeight.w800,
                fontSize: 20,
              ),
            ),
          ),
          SliverPadding(
            padding: const EdgeInsets.fromLTRB(16, 4, 16, 0),
            sliver: SliverToBoxAdapter(
              child: Text(
                strings.signalScreenSubtitle,
                style: TextStyle(
                  color: visual.mutedForeground,
                  fontSize: 14,
                  height: 1.5,
                ),
              ),
            ),
          ),
          const SliverToBoxAdapter(child: SizedBox(height: 16)),

          // Metodoloji notu
          SliverPadding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            sliver: SliverToBoxAdapter(
              child: KefeSurface(
                tone: KefeSurfaceTone.sunken,
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Icon(
                      Icons.info_outline_rounded,
                      size: 16,
                      color: visual.gold,
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        strings.signalMethodologyNote,
                        style: TextStyle(
                          color: visual.mutedForeground,
                          fontSize: 12,
                          height: 1.5,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
          const SliverToBoxAdapter(child: SizedBox(height: 20)),

          // Sinyaller
          if (state.loading)
            const SliverFillRemaining(
              child: Center(child: CircularProgressIndicator()),
            )
          else if (state.errorCode != null)
            SliverFillRemaining(
              child: _SignalError(
                onRetry: () =>
                    ref.read(signalControllerProvider.notifier).load(),
              ),
            )
          else if (state.cards.isEmpty)
            SliverFillRemaining(
              child: _SignalEmpty(),
            )
          else
            SliverPadding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              sliver: SliverList(
                delegate: SliverChildBuilderDelegate(
                  (context, index) {
                    final card = state.cards[index];
                    return Padding(
                      padding: const EdgeInsets.only(bottom: 12),
                      child: _SignalCardTile(card: card),
                    );
                  },
                  childCount: state.cards.length,
                ),
              ),
            ),

          const SliverToBoxAdapter(child: SizedBox(height: 48)),
        ],
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// Signal card tile
// ---------------------------------------------------------------------------

class _SignalCardTile extends StatelessWidget {
  const _SignalCardTile({required this.card});

  final SignalConsensusCardModel card;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    final strings = KefeStrings.of(context);

    final tierColor = switch (card.confidenceTier) {
      SignalConfidenceTierModel.gold => const Color(0xFFD4AF37),
      SignalConfidenceTierModel.silver => const Color(0xFF9E9E9E),
      SignalConfidenceTierModel.bronze => const Color(0xFFCD7F32),
    };

    final tierLabel = switch (card.confidenceTier) {
      SignalConfidenceTierModel.gold => 'ALTIN',
      SignalConfidenceTierModel.silver => 'GÜMÜŞ',
      SignalConfidenceTierModel.bronze => 'BRONZ',
    };

    return KefeSurface(
      tone: KefeSurfaceTone.raised,
      padding: const EdgeInsets.all(16),
      borderRadius: 20,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Üst satır: case başlığı + tier
          Row(
            children: [
              Expanded(
                child: Text(
                  card.caseTitle,
                  style: TextStyle(
                    color: visual.mutedForeground,
                    fontSize: 11,
                    fontWeight: FontWeight.w600,
                    letterSpacing: 0.4,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              const SizedBox(width: 8),
              Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: tierColor.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(
                    color: tierColor.withValues(alpha: 0.35),
                  ),
                ),
                child: Text(
                  tierLabel,
                  style: TextStyle(
                    color: tierColor,
                    fontSize: 10,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 0.5,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),

          // Uzlaşı metni
          if (card.isProvisional)
            Container(
              margin: const EdgeInsets.only(bottom: 6),
              padding:
                  const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
              decoration: BoxDecoration(
                color: visual.attention.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(6),
              ),
              child: Text(
                strings.signalProvisionalLabel,
                style: TextStyle(
                  color: visual.attention,
                  fontSize: 10,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 0.4,
                ),
              ),
            ),
          Text(
            card.consensusStatement,
            style: TextStyle(
              color: visual.foreground,
              fontSize: 15,
              fontWeight: FontWeight.w600,
              height: 1.4,
            ),
          ),
          const SizedBox(height: 12),

          // Alt satır: anlaşma % ve örneklem
          Row(
            children: [
              // Anlaşma yüzdesi göstergesi
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '${card.agreementPercentage.toStringAsFixed(0)}% Uzlaşı',
                      style: TextStyle(
                        color: visual.gold,
                        fontSize: 13,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    const SizedBox(height: 4),
                    ClipRRect(
                      borderRadius: BorderRadius.circular(4),
                      child: LinearProgressIndicator(
                        value: card.agreementPercentage / 100,
                        backgroundColor:
                            visual.gold.withValues(alpha: 0.15),
                        valueColor: AlwaysStoppedAnimation(visual.gold),
                        minHeight: 5,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 16),
              Text(
                'n=${card.sampleSize}',
                style: TextStyle(
                  color: visual.mutedForeground,
                  fontSize: 12,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// Error + Empty states
// ---------------------------------------------------------------------------

class _SignalError extends StatelessWidget {
  const _SignalError({required this.onRetry});

  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    final strings = KefeStrings.of(context);
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.cloud_off_outlined,
                size: 44, color: visual.mutedForeground),
            const SizedBox(height: 12),
            Text(
              strings.signalLoadError,
              textAlign: TextAlign.center,
              style:
                  TextStyle(color: visual.mutedForeground, fontSize: 14),
            ),
            const SizedBox(height: 16),
            TextButton(
              onPressed: onRetry,
              child: Text(
                strings.retryAction,
                style: TextStyle(
                    color: visual.gold, fontWeight: FontWeight.w700),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _SignalEmpty extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    final strings = KefeStrings.of(context);
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.trending_up_outlined,
                size: 44, color: visual.mutedForeground),
            const SizedBox(height: 12),
            Text(
              strings.signalEmpty,
              textAlign: TextAlign.center,
              style:
                  TextStyle(color: visual.mutedForeground, fontSize: 14),
            ),
          ],
        ),
      ),
    );
  }
}