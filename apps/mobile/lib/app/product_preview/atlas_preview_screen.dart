import 'package:flutter/material.dart';

import '../../core/design/kefe_theme.dart';
import 'preview_components.dart';

class AtlasPreviewScreen extends StatelessWidget {
  const AtlasPreviewScreen({super.key});

  @override
  Widget build(BuildContext context) {
    const countries = [
      ('Türkiye', 7.1),
      ('Almanya', 5.4),
      ('ABD', 6.2),
      ('Japonya', 4.8),
      ('Brezilya', 6.7),
      ('Endonezya', 7.3),
    ];

    return SafeArea(
      bottom: false,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(18, 14, 18, 28),
        children: [
          const PreviewPageHeader(
            eyebrow: 'KEFE ATLAS',
            title: 'Aynı soru,\nfarklı dünyalar.',
            icon: Icons.public_rounded,
          ),
          const SizedBox(height: 14),
          const PreviewNotice(
            text:
                'Atlas sayıları temsili Product Preview verisidir · gerçek ülke sonucu değildir',
          ),
          const SizedBox(height: 18),
          Container(
            height: 230,
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(24),
              border: Border.all(color: KefeColorTokens.borderDark),
              gradient: const RadialGradient(
                center: Alignment(-0.2, -0.25),
                radius: 1.15,
                colors: [
                  Color(0xFF173A67),
                  Color(0xFF1A2338),
                  Color(0xFF391D29),
                ],
              ),
            ),
            child: Stack(
              children: [
                const Align(
                  alignment: Alignment.center,
                  child: Icon(
                    Icons.public_rounded,
                    size: 145,
                    color: Color(0x335DA5FF),
                  ),
                ),
                Align(
                  alignment: Alignment.topLeft,
                  child: Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: const Color(0xAA07111F),
                      borderRadius: BorderRadius.circular(14),
                    ),
                    child: const Text(
                      'SEÇİLEN OLAY\nYZ & kişisel veri\n\nDünya görünümü',
                      style: TextStyle(height: 1.45, fontSize: 12),
                    ),
                  ),
                ),
                const Align(
                  alignment: Alignment.bottomRight,
                  child: Text(
                    '0  ━━━━━━━  10',
                    style: TextStyle(color: KefeColorTokens.textMutedDark),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 22),
          Text(
            'Ülkelere göre ortalamalar',
            style: Theme.of(
              context,
            ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800),
          ),
          const SizedBox(height: 12),
          GridView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 3,
              childAspectRatio: 1.18,
              crossAxisSpacing: 10,
              mainAxisSpacing: 10,
            ),
            itemCount: countries.length,
            itemBuilder: (context, index) {
              final item = countries[index];
              return Card(
                child: Padding(
                  padding: const EdgeInsets.all(12),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text(
                        item.$1,
                        style: Theme.of(context).textTheme.labelSmall,
                      ),
                      const SizedBox(height: 7),
                      Text(
                        item.$2.toStringAsFixed(1),
                        style: Theme.of(context).textTheme.headlineSmall
                            ?.copyWith(
                              color: item.$2 >= 6.5
                                  ? KefeColorTokens.empathy
                                  : KefeColorTokens.rules,
                              fontWeight: FontWeight.w900,
                            ),
                      ),
                    ],
                  ),
                ),
              );
            },
          ),
        ],
      ),
    );
  }
}
