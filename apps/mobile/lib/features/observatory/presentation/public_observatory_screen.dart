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
    final strings = Localizations.of<KefeStrings>(context, KefeStrings) ??
        const KefeStrings(Locale('tr'));
    final visual = context.kefeVisual;
    final isTr = strings.isTr;
    final signalState = ref.watch(signalControllerProvider);
    final impactState = ref.watch(institutionResponseControllerProvider);

    return Scaffold(
      appBar: AppBar(
        title: Text(
          isTr ? 'Kamusal Gözlemevi' : 'Public Observatory',
        ),
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
                              isTr
                                  ? 'KAMUSAL GÖZLEMEVİ (CAP-016 & CAP-049)'
                                  : 'PUBLIC OBSERVATORY (CAP-016 & CAP-049)',
                              color: visual.gold,
                            ),
                            const SizedBox(height: 3),
                            Text(
                              isTr
                                  ? 'Sinyal ve Etki Takip Masası'
                                  : 'Signal & Impact Desk',
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
                    isTr
                        ? 'Ön-karar manipülasyonlarından arındırılmış kamusal uzlaşı odakları ve yetkili kamu kurumlarının resmi taahhütleri.'
                        : 'Methodology-qualified public consensus signals and official commitments from verified authorities.',
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
                    isTr
                        ? 'Nitelikli Topluluk Uzlaşı Sinyalleri'
                        : 'Qualified Community Consensus Signals',
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
              isTr
                  ? 'Bireysel oylardan bağımsız, bot ve astroturfing filtrelerinden geçmiş sertifikalı uzlaşı haritaları.'
                  : 'Certified societal consensus patterns filtered from bot manipulation and astroturfing.',
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
                  isTr
                      ? 'Şu anda yayımlanmış kamusal uzlaşı sinyali bulunmuyor.'
                      : 'No public consensus signals currently published.',
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
                    isTr
                        ? 'Doğrulanmış Kurum Yanıtları ve Taahhütler'
                        : 'Verified Institution Responses & Pledges',
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
              isTr
                  ? 'Uzlaşı sinyallerine bakanlıklar, belediyeler ve sivil toplum kuruluşlarınca verilen resmi yanıtlar.'
                  : 'Official responses from ministries, municipalities, and verified institutions.',
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
                  isTr
                      ? 'Henüz doğrulanmış bir kurumsal yanıt kaydı yok.'
                      : 'No verified institutional response records yet.',
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
