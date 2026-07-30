import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../core/design/kefe_theme.dart';
import 'preview_components.dart';

class WeighPreviewScreen extends StatelessWidget {
  const WeighPreviewScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      bottom: false,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(18, 14, 18, 28),
        children: [
          const PreviewPageHeader(
            eyebrow: 'TARTIM',
            title: 'Kefeyi eline al.',
            icon: Icons.balance_rounded,
          ),
          const SizedBox(height: 18),
          Container(
            padding: const EdgeInsets.all(22),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(24),
              border: Border.all(
                color: KefeColorTokens.gold.withValues(alpha: 0.35),
              ),
              gradient: const LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [
                  Color(0xFF132B4D),
                  Color(0xFF151927),
                  Color(0xFF3A1D25),
                ],
              ),
            ),
            child: Column(
              children: [
                const Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    PreviewScoreOrb(
                      label: 'KURAL',
                      value: '5',
                      color: KefeColorTokens.rules,
                    ),
                    Padding(
                      padding: EdgeInsets.symmetric(horizontal: 18),
                      child: Icon(
                        Icons.balance_rounded,
                        size: 54,
                        color: KefeColorTokens.goldSoft,
                      ),
                    ),
                    PreviewScoreOrb(
                      label: 'EMPATİ',
                      value: '5',
                      color: KefeColorTokens.empathy,
                    ),
                  ],
                ),
                const SizedBox(height: 20),
                Text(
                  'Her tartımda önce kendi kararını ver. Topluluk sonucu Commit’ten sonra açılır.',
                  textAlign: TextAlign.center,
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: KefeColorTokens.textMutedDark,
                    height: 1.45,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 18),
          PreviewActionCaseCard(
            label: 'GÜNLÜK İKİLEM',
            title:
                'Çocuklar uçakta ebeveynleriyle ücretsiz yan yana oturmalı mı?',
            subtitle:
                'Kural, fiyatlandırma, aile bütünlüğü ve orantılılığı birlikte tart.',
            icon: Icons.airplanemode_active_rounded,
            onTap: () =>
                context.push('/case/11111111-1111-4111-8111-111111111116'),
          ),
          const SizedBox(height: 12),
          PreviewActionCaseCard(
            label: 'SPORTS CALL',
            title: 'Bu pozisyonda penaltı kararı doğru muydu?',
            subtitle:
                'Hakem kararı, temasın etkisi ve VAR eşiğini değerlendir.',
            icon: Icons.sports_soccer_rounded,
            onTap: () =>
                context.push('/case/11111111-1111-4111-8111-111111111113'),
          ),
          const SizedBox(height: 12),
          PreviewActionCaseCard(
            label: 'TEKNOLOJİ',
            title: 'YZ şirketlerinin veri toplaması sınırlandırılmalı mı?',
            subtitle:
                'Mahremiyet ve inovasyon arasındaki sınırı kendi kefe değerlerinle tart.',
            icon: Icons.psychology_alt_rounded,
            onTap: () =>
                context.push('/case/11111111-1111-4111-8111-111111111112'),
          ),
        ],
      ),
    );
  }
}
