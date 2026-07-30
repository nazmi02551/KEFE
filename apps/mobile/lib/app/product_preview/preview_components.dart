import 'package:flutter/material.dart';

import '../../core/design/kefe_theme.dart';

class PreviewPageHeader extends StatelessWidget {
  const PreviewPageHeader({
    required this.eyebrow,
    required this.title,
    required this.icon,
    super.key,
  });

  final String eyebrow;
  final String title;
  final IconData icon;

  @override
  Widget build(BuildContext context) => Row(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Expanded(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              eyebrow,
              style: Theme.of(context).textTheme.labelMedium?.copyWith(
                color: KefeColorTokens.goldSoft,
                fontWeight: FontWeight.w900,
                letterSpacing: 1.15,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              title,
              style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                fontWeight: FontWeight.w900,
                height: 1.08,
              ),
            ),
          ],
        ),
      ),
      Container(
        width: 48,
        height: 48,
        decoration: BoxDecoration(
          color: KefeColorTokens.gold.withValues(alpha: 0.12),
          shape: BoxShape.circle,
          border: Border.all(
            color: KefeColorTokens.gold.withValues(alpha: 0.26),
          ),
        ),
        child: Icon(icon, color: KefeColorTokens.goldSoft),
      ),
    ],
  );
}

class PreviewNotice extends StatelessWidget {
  const PreviewNotice({required this.text, super.key});

  final String text;

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
    decoration: BoxDecoration(
      color: KefeColorTokens.rules.withValues(alpha: 0.08),
      borderRadius: BorderRadius.circular(12),
      border: Border.all(color: KefeColorTokens.rules.withValues(alpha: 0.22)),
    ),
    child: Row(
      children: [
        const Icon(
          Icons.visibility_outlined,
          color: KefeColorTokens.rules,
          size: 17,
        ),
        const SizedBox(width: 8),
        Expanded(
          child: Text(
            text,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: KefeColorTokens.textMutedDark,
            ),
          ),
        ),
      ],
    ),
  );
}

class PreviewFilterPill extends StatelessWidget {
  const PreviewFilterPill({
    required this.label,
    this.selected = false,
    super.key,
  });

  final String label;
  final bool selected;

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
    decoration: BoxDecoration(
      color: selected ? KefeColorTokens.gold : KefeColorTokens.surfaceDark,
      borderRadius: BorderRadius.circular(99),
      border: Border.all(
        color: selected ? KefeColorTokens.gold : KefeColorTokens.borderDark,
      ),
    ),
    child: Text(
      label,
      style: Theme.of(context).textTheme.labelMedium?.copyWith(
        color: selected ? const Color(0xFF171106) : KefeColorTokens.textLight,
        fontWeight: FontWeight.w800,
      ),
    ),
  );
}

class PreviewScoreOrb extends StatelessWidget {
  const PreviewScoreOrb({
    required this.label,
    required this.value,
    required this.color,
    super.key,
  });

  final String label;
  final String value;
  final Color color;

  @override
  Widget build(BuildContext context) => Column(
    children: [
      Text(
        label,
        style: Theme.of(context).textTheme.labelSmall?.copyWith(color: color),
      ),
      const SizedBox(height: 5),
      Container(
        width: 58,
        height: 58,
        alignment: Alignment.center,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          color: color.withValues(alpha: 0.10),
          border: Border.all(color: color.withValues(alpha: 0.45)),
        ),
        child: Text(
          value,
          style: Theme.of(context).textTheme.headlineSmall?.copyWith(
            color: color,
            fontWeight: FontWeight.w900,
          ),
        ),
      ),
    ],
  );
}

class PreviewActionCaseCard extends StatelessWidget {
  const PreviewActionCaseCard({
    required this.label,
    required this.title,
    required this.subtitle,
    required this.icon,
    required this.onTap,
    super.key,
  });

  final String label;
  final String title;
  final String subtitle;
  final IconData icon;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => Card(
    child: InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(20),
      child: Padding(
        padding: const EdgeInsets.all(17),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              width: 48,
              height: 48,
              decoration: BoxDecoration(
                color: KefeColorTokens.gold.withValues(alpha: 0.10),
                borderRadius: BorderRadius.circular(14),
              ),
              child: Icon(icon, color: KefeColorTokens.goldSoft),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    label,
                    style: Theme.of(context).textTheme.labelSmall?.copyWith(
                      color: KefeColorTokens.goldSoft,
                      fontWeight: FontWeight.w900,
                    ),
                  ),
                  const SizedBox(height: 7),
                  Text(
                    title,
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.w800,
                      height: 1.2,
                    ),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    subtitle,
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: KefeColorTokens.textMutedDark,
                      height: 1.35,
                    ),
                  ),
                ],
              ),
            ),
            const Icon(Icons.chevron_right_rounded),
          ],
        ),
      ),
    ),
  );
}
