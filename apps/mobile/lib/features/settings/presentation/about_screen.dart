import 'package:flutter/material.dart';

import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/kefe_strings.dart';

class AboutScreen extends StatelessWidget {
  const AboutScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;

    return Scaffold(
      backgroundColor: visual.canvas,
      appBar: AppBar(
        backgroundColor: visual.canvas,
        surfaceTintColor: Colors.transparent,
        title: Text(
          strings.aboutTitle,
          style: TextStyle(
            color: visual.foreground,
            fontWeight: FontWeight.w800,
            fontSize: 18,
          ),
        ),
        iconTheme: IconThemeData(color: visual.foreground),
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 48),
        children: [
          // Logo + başlık
          const SizedBox(height: 12),
          Center(
            child: Container(
              width: 72,
              height: 72,
              decoration: BoxDecoration(
                color: visual.gold.withValues(alpha: 0.12),
                borderRadius: BorderRadius.circular(20),
                border: Border.all(
                  color: visual.gold.withValues(alpha: 0.3),
                  width: 1.5,
                ),
              ),
              child: Center(
                child: Text(
                  'K',
                  style: TextStyle(
                    color: visual.gold,
                    fontSize: 32,
                    fontWeight: FontWeight.w900,
                  ),
                ),
              ),
            ),
          ),
          const SizedBox(height: 12),
          Center(
            child: Text(
              'KEFE',
              style: TextStyle(
                color: visual.foreground,
                fontSize: 24,
                fontWeight: FontWeight.w900,
                letterSpacing: -0.5,
              ),
            ),
          ),
          Center(
            child: Text(
              strings.aboutVersionLabel,
              style: TextStyle(
                color: visual.mutedForeground,
                fontSize: 12,
              ),
            ),
          ),
          const SizedBox(height: 32),

          // Metodoloji başlığı
          Text(
            strings.aboutMethodologyTitle,
            style: TextStyle(
              color: visual.gold,
              fontSize: 13,
              fontWeight: FontWeight.w700,
              letterSpacing: 0.6,
            ),
          ),
          const SizedBox(height: 12),

          _MethodologyCard(
            icon: Icons.lock_clock_outlined,
            color: visual.gold,
            title: strings.aboutCommitFirst,
            description: strings.aboutCommitFirstDesc,
          ),
          const SizedBox(height: 10),
          _MethodologyCard(
            icon: Icons.visibility_off_outlined,
            color: visual.rules,
            title: strings.aboutBlindFirst,
            description: strings.aboutBlindFirstDesc,
          ),
          const SizedBox(height: 10),
          _MethodologyCard(
            icon: Icons.trending_up_outlined,
            color: visual.empathy,
            title: strings.aboutSignalTitle,
            description: strings.aboutSignalDesc,
          ),
          const SizedBox(height: 32),

          // Metodoloji notu
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: visual.surface,
              borderRadius: BorderRadius.circular(14),
              border: Border.all(color: visual.border),
            ),
            child: Text(
              'Kolektif sonuç otomatik olarak Sinyal, gerçek veya otorite sayılmaz. '
              'My KEFE yalnızca gözlemsel veriye dayanır — kişilik, ideoloji veya '
              'nedensel çıkarım yapılmaz.',
              style: TextStyle(
                color: visual.mutedForeground,
                fontSize: 12,
                height: 1.6,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _MethodologyCard extends StatelessWidget {
  const _MethodologyCard({
    required this.icon,
    required this.color,
    required this.title,
    required this.description,
  });

  final IconData icon;
  final Color color;
  final String title;
  final String description;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: visual.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: color.withValues(alpha: 0.2)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 36,
            height: 36,
            decoration: BoxDecoration(
              color: color.withValues(alpha: 0.12),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(icon, size: 18, color: color),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: TextStyle(
                    color: visual.foreground,
                    fontWeight: FontWeight.w700,
                    fontSize: 14,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  description,
                  style: TextStyle(
                    color: visual.mutedForeground,
                    fontSize: 13,
                    height: 1.5,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}