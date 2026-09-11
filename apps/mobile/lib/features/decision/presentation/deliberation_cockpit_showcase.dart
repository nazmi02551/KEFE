import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/kefe_strings.dart';

@immutable
class DeliberationFeatureItem {
  const DeliberationFeatureItem({
    required this.titleTr,
    required this.titleEn,
    required this.subtitleTr,
    required this.subtitleEn,
    required this.icon,
    required this.accentGetter,
  });

  final String titleTr;
  final String titleEn;
  final String subtitleTr;
  final String subtitleEn;
  final IconData icon;
  final Color Function(KefeVisualSystem visual) accentGetter;

  /// Returns the locale-appropriate title (English fallback for unsupported locales).
  String localizedTitle(String languageCode) =>
      languageCode == 'tr' ? titleTr : titleEn;

  /// Returns the locale-appropriate subtitle (English fallback for unsupported locales).
  String localizedSubtitle(String languageCode) =>
      languageCode == 'tr' ? subtitleTr : subtitleEn;
}

const List<DeliberationFeatureItem> kefeDeliberationFeatures = [
  DeliberationFeatureItem(
    titleTr: 'Sentetik Astroturfing Kalkanı',
    titleEn: 'Synthetic Astroturfing Shield',
    subtitleTr: 'Aktif Bot Koruması & Anomali Filtresi',
    subtitleEn: 'Active Bot Protection & Anomaly Filter',
    icon: Icons.shield_outlined,
    accentGetter: _getRulesColor,
  ),
  DeliberationFeatureItem(
    titleTr: '3-Eksenli Etik Denge',
    titleEn: 'Tri-Axial Ethical Balance',
    subtitleTr: 'Kurallar • Merhamet • Toplumsal Fayda',
    subtitleEn: 'Rules • Empathy • Public Utility',
    icon: Icons.balance_rounded,
    accentGetter: _getGoldColor,
  ),
  DeliberationFeatureItem(
    titleTr: 'Kriptografik Karar Makbuzu',
    titleEn: 'Cryptographic Decision Receipt',
    subtitleTr: 'SHA-256 İmzalı & Denetlenebilir',
    subtitleEn: 'SHA-256 Signed & Auditable',
    icon: Icons.receipt_long_outlined,
    accentGetter: _getBurgundyColor,
  ),
  DeliberationFeatureItem(
    titleTr: 'Bilişsel Derinlik & Esneklik',
    titleEn: 'Epistemic Depth & Flexibility',
    subtitleTr: '"Ne Fikrimi Değiştirir?" Koşulları',
    subtitleEn: '"What Would Change My Mind?" Stance',
    icon: Icons.psychology_alt_outlined,
    accentGetter: _getEmpathyColor,
  ),
  DeliberationFeatureItem(
    titleTr: 'Canlı Sinyal Tazeliği',
    titleEn: 'Live Signal Freshness',
    subtitleTr: '90 Gün Yarılanma Ömrü & Yıpranma Modeli',
    subtitleEn: '90-Day Half-Life & Decay Model',
    icon: Icons.bolt_rounded,
    accentGetter: _getGoldColor,
  ),
  DeliberationFeatureItem(
    titleTr: 'Doğrulanmış Kurumsal Yanıt',
    titleEn: 'Verified Institution Response',
    subtitleTr: 'Kamu Politikası & Yönetmelik Taahhütleri',
    subtitleEn: 'Public Policy & Regulatory Commitments',
    icon: Icons.account_balance_outlined,
    accentGetter: _getRulesColor,
  ),
];

Color _getRulesColor(KefeVisualSystem visual) => visual.rules;
Color _getGoldColor(KefeVisualSystem visual) => visual.goldSoft;
Color _getBurgundyColor(KefeVisualSystem visual) => visual.burgundy;
Color _getEmpathyColor(KefeVisualSystem visual) => visual.empathy;

class DeliberationCockpitShowcase extends StatefulWidget {
  const DeliberationCockpitShowcase({
    this.compact = false,
    super.key,
  });

  final bool compact;

  @override
  State<DeliberationCockpitShowcase> createState() =>
      _DeliberationCockpitShowcaseState();
}

class _DeliberationCockpitShowcaseState
    extends State<DeliberationCockpitShowcase> {
  int _selectedFeature = 0;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final lang = strings.locale.languageCode;
    final visual = context.kefeVisual;
    final active = kefeDeliberationFeatures[_selectedFeature];
    final activeColor = active.accentGetter(visual);

    return Semantics(
      container: true,
      label: lang == 'tr'
          ? 'Anayasal Müzakere ve Güvence Kokpiti'
          : 'Constitutional Deliberation & Assurance Cockpit',
      child: KefeSurface(
        key: const ValueKey('deliberation-cockpit-showcase'),
        tone: KefeSurfaceTone.premium,
        accent: activeColor,
        padding: const EdgeInsets.all(16),
        borderRadius: 22,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              children: [
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                  decoration: BoxDecoration(
                    color: activeColor.withValues(alpha: visual.isDark ? 0.20 : 0.12),
                    borderRadius: BorderRadius.circular(99),
                    border: Border.all(
                      color: activeColor.withValues(alpha: 0.35),
                    ),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(active.icon, color: activeColor, size: 15),
                      const SizedBox(width: 6),
                      Text(
                        lang == 'tr' ? 'ANAYASAL GÜVENCELER' : 'CONSTITUTIONAL GUARANTEES',
                        style: TextStyle(
                          color: activeColor,
                          fontSize: 10.5,
                          fontWeight: FontWeight.w900,
                          letterSpacing: 0.8,
                        ),
                      ),
                    ],
                  ),
                ),
                const Spacer(),
                Text(
                  '${_selectedFeature + 1}/${kefeDeliberationFeatures.length}',
                  style: Theme.of(context).textTheme.labelSmall?.copyWith(
                        color: Colors.white.withValues(alpha: 0.60),
                        fontWeight: FontWeight.w700,
                      ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Text(
              active.localizedTitle(lang),
              key: const ValueKey('deliberation-active-title'),
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    color: Colors.white,
                    fontWeight: FontWeight.w900,
                    height: 1.18,
                    letterSpacing: -0.2,
                  ),
            ),
            const SizedBox(height: 4),
            Text(
              active.localizedSubtitle(lang),
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: Colors.white.withValues(alpha: 0.76),
                    height: 1.35,
                  ),
            ),
            const SizedBox(height: 14),
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              physics: const BouncingScrollPhysics(),
              child: Row(
                children: [
                  for (var i = 0; i < kefeDeliberationFeatures.length; i++) ...[
                    _PillButton(
                      item: kefeDeliberationFeatures[i],
                      isSelected: i == _selectedFeature,
                      visual: visual,
                      onTap: () => setState(() => _selectedFeature = i),
                    ),
                    if (i != kefeDeliberationFeatures.length - 1)
                      const SizedBox(width: 8),
                  ],
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _PillButton extends StatelessWidget {
  const _PillButton({
    required this.item,
    required this.isSelected,
    required this.visual,
    required this.onTap,
  });

  final DeliberationFeatureItem item;
  final bool isSelected;
  final KefeVisualSystem visual;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final lang = KefeStrings.of(context).locale.languageCode;
    final color = item.accentGetter(visual);
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(14),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 180),
        padding: const EdgeInsets.symmetric(horizontal: 11, vertical: 7),
        decoration: BoxDecoration(
          color: isSelected
              ? color.withValues(alpha: 0.24)
              : Colors.white.withValues(alpha: 0.10),
          borderRadius: BorderRadius.circular(14),
          border: Border.all(
            color: isSelected ? color : Colors.white.withValues(alpha: 0.18),
            width: isSelected ? 1.5 : 1.0,
          ),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              item.icon,
              size: 14,
              color: isSelected ? color : Colors.white.withValues(alpha: 0.70),
            ),
            const SizedBox(width: 6),
            Text(
              item.localizedTitle(lang),
              style: TextStyle(
                fontSize: 11,
                fontWeight: isSelected ? FontWeight.w800 : FontWeight.w600,
                color: isSelected ? color : Colors.white.withValues(alpha: 0.90),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class CaseDeliberationBadgesRow extends StatelessWidget {
  const CaseDeliberationBadgesRow({super.key});

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final lang = strings.locale.languageCode;
    final visual = context.kefeVisual;

    return Wrap(
      spacing: 6,
      runSpacing: 6,
      children: [
        _Badge(
          icon: Icons.shield_outlined,
          label: lang == 'tr' ? 'Bot Kalkanı' : 'Bot Shield',
          color: visual.rules,
          bgColor: visual.subtleRulesSurface,
        ),
        _Badge(
          icon: Icons.balance_rounded,
          label: lang == 'tr' ? '3-Eksenli' : 'Tri-Axial',
          color: visual.goldSoft,
          bgColor: visual.subtleGoldSurface,
        ),
        _Badge(
          icon: Icons.receipt_long_outlined,
          label: lang == 'tr' ? 'Makbuz' : 'Receipt',
          color: visual.burgundy,
          bgColor: visual.burgundy.withValues(alpha: 0.12),
        ),
        _Badge(
          icon: Icons.psychology_alt_outlined,
          label: lang == 'tr' ? 'Esneklik' : 'Flexibility',
          color: visual.empathy,
          bgColor: visual.subtleEmpathySurface,
        ),
      ],
    );
  }
}

class _Badge extends StatelessWidget {
  const _Badge({
    required this.icon,
    required this.label,
    required this.color,
    required this.bgColor,
  });

  final IconData icon;
  final String label;
  final Color color;
  final Color bgColor;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 3),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withValues(alpha: 0.28)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 11, color: color),
          const SizedBox(width: 4),
          Text(
            label,
            style: TextStyle(
              fontSize: 10,
              fontWeight: FontWeight.w800,
              color: color,
            ),
          ),
        ],
      ),
    );
  }
}
