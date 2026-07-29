import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:go_router/go_router.dart';

import '../core/design/kefe_theme.dart';
import '../core/localization/kefe_strings.dart';
import '../features/decision/presentation/decision_flow_screen.dart';
import '../features/explore/presentation/explore_screen.dart';

class ProductPreviewApp extends StatefulWidget {
  const ProductPreviewApp({super.key});

  @override
  State<ProductPreviewApp> createState() => _ProductPreviewAppState();
}

class _ProductPreviewAppState extends State<ProductPreviewApp> {
  late final GoRouter _router = GoRouter(
    initialLocation: '/explore',
    routes: [
      GoRoute(
        path: '/',
        redirect: (_, _) => '/explore',
      ),
      GoRoute(
        path: '/explore',
        builder: (_, _) => const _PreviewShell(
          selectedIndex: 0,
          child: ExploreScreen(embedded: true),
        ),
      ),
      GoRoute(
        path: '/radar',
        builder: (_, _) => const _PreviewShell(
          selectedIndex: 1,
          child: _RadarPreviewScreen(),
        ),
      ),
      GoRoute(
        path: '/weigh',
        builder: (_, _) => const _PreviewShell(
          selectedIndex: 2,
          child: _WeighPreviewScreen(),
        ),
      ),
      GoRoute(
        path: '/atlas',
        builder: (_, _) => const _PreviewShell(
          selectedIndex: 3,
          child: _AtlasPreviewScreen(),
        ),
      ),
      GoRoute(
        path: '/my-kefe',
        builder: (_, _) => const _PreviewShell(
          selectedIndex: 4,
          child: _MyKefePreviewScreen(),
        ),
      ),
      GoRoute(
        path: '/case/:caseId',
        builder: (context, state) => DecisionFlowScreen(
          caseId: state.pathParameters['caseId']!,
        ),
      ),
    ],
  );

  @override
  void dispose() {
    _router.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'KEFE Product Preview',
      debugShowCheckedModeBanner: false,
      theme: KefeTheme.light(),
      darkTheme: KefeTheme.dark(),
      themeMode: ThemeMode.dark,
      routerConfig: _router,
      supportedLocales: KefeStrings.supportedLocales,
      localizationsDelegates: const [
        KefeStringsDelegate(),
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
    );
  }
}

class _PreviewShell extends StatelessWidget {
  const _PreviewShell({required this.selectedIndex, required this.child});

  final int selectedIndex;
  final Widget child;

  static const _paths = ['/explore', '/radar', '/weigh', '/atlas', '/my-kefe'];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: child,
      bottomNavigationBar: DecoratedBox(
        decoration: const BoxDecoration(
          border: Border(top: BorderSide(color: KefeColorTokens.borderDark)),
        ),
        child: NavigationBar(
          selectedIndex: selectedIndex,
          onDestinationSelected: (index) => context.go(_paths[index]),
          destinations: const [
            NavigationDestination(
              icon: Icon(Icons.explore_outlined),
              selectedIcon: Icon(Icons.explore_rounded),
              label: 'Keşfet',
            ),
            NavigationDestination(
              icon: Icon(Icons.radar_outlined),
              selectedIcon: Icon(Icons.radar_rounded),
              label: 'Radar',
            ),
            NavigationDestination(
              icon: _ScaleNavIcon(selected: false),
              selectedIcon: _ScaleNavIcon(selected: true),
              label: 'Tartım',
            ),
            NavigationDestination(
              icon: Icon(Icons.public_outlined),
              selectedIcon: Icon(Icons.public_rounded),
              label: 'Atlas',
            ),
            NavigationDestination(
              icon: Icon(Icons.person_outline_rounded),
              selectedIcon: Icon(Icons.person_rounded),
              label: 'Profil',
            ),
          ],
        ),
      ),
    );
  }
}

class _ScaleNavIcon extends StatelessWidget {
  const _ScaleNavIcon({required this.selected});

  final bool selected;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 42,
      height: 42,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        color: selected
            ? KefeColorTokens.gold
            : KefeColorTokens.gold.withValues(alpha: 0.12),
        border: Border.all(color: KefeColorTokens.gold.withValues(alpha: 0.55)),
      ),
      child: Icon(
        Icons.balance_rounded,
        color: selected ? const Color(0xFF171106) : KefeColorTokens.goldSoft,
        size: 23,
      ),
    );
  }
}

class _RadarPreviewScreen extends StatelessWidget {
  const _RadarPreviewScreen();

  static const _items = [
    (
      rank: '1',
      domain: 'TECH · GLOBAL',
      title: 'YZ şirketlerinin kişisel veri toplaması sınırlandırılmalı mı?',
      signal: 'Yükselen tartışma',
      caseId: '11111111-1111-4111-8111-111111111112',
    ),
    (
      rank: '2',
      domain: 'SPORTS',
      title: 'Tartışmalı penaltı kararı doğru muydu?',
      signal: 'Sports CALL',
      caseId: '11111111-1111-4111-8111-111111111113',
    ),
    (
      rank: '3',
      domain: 'WORK',
      title: 'YZ nedeniyle işten çıkarma öncesi yeniden eğitim zorunlu olmalı mı?',
      signal: 'İş & ekonomi',
      caseId: '11111111-1111-4111-8111-111111111117',
    ),
    (
      rank: '4',
      domain: 'DAILY LIFE',
      title: 'Çocuklar uçakta ebeveynleriyle ücretsiz yan yana oturmalı mı?',
      signal: 'Günlük ikilem',
      caseId: '11111111-1111-4111-8111-111111111116',
    ),
    (
      rank: '5',
      domain: 'EDUCATION',
      title: 'Üniversitelerde üretken YZ kullanımı sınırlandırılmalı mı?',
      signal: 'Eğitim',
      caseId: '11111111-1111-4111-8111-111111111118',
    ),
  ];

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      bottom: false,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(18, 14, 18, 28),
        children: [
          const _PreviewPageHeader(
            eyebrow: 'KEFE RADAR',
            title: 'Dünya şu an\nneyi tartışıyor?',
            icon: Icons.radar_rounded,
          ),
          const SizedBox(height: 14),
          const _PreviewNotice(
            text: 'Canlı trend verisi değil · Product Preview için temsili sıralama',
          ),
          const SizedBox(height: 18),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: const [
              _FilterPill(label: 'Trendler', selected: true),
              _FilterPill(label: 'Yükselen'),
              _FilterPill(label: 'Global'),
              _FilterPill(label: 'Senin için'),
            ],
          ),
          const SizedBox(height: 18),
          for (final item in _items) ...[
            Card(
              child: InkWell(
                borderRadius: BorderRadius.circular(20),
                onTap: () => context.push('/case/${item.caseId}'),
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Container(
                        width: 34,
                        height: 34,
                        alignment: Alignment.center,
                        decoration: const BoxDecoration(
                          shape: BoxShape.circle,
                          color: KefeColorTokens.gold,
                        ),
                        child: Text(
                          item.rank,
                          style: const TextStyle(
                            color: Color(0xFF171106),
                            fontWeight: FontWeight.w900,
                          ),
                        ),
                      ),
                      const SizedBox(width: 13),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              item.domain,
                              style: Theme.of(context).textTheme.labelSmall?.copyWith(
                                    color: KefeColorTokens.goldSoft,
                                    fontWeight: FontWeight.w800,
                                  ),
                            ),
                            const SizedBox(height: 7),
                            Text(
                              item.title,
                              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                                    fontWeight: FontWeight.w800,
                                    height: 1.2,
                                  ),
                            ),
                            const SizedBox(height: 9),
                            Row(
                              children: [
                                Icon(
                                  Icons.trending_up_rounded,
                                  size: 16,
                                  color: Theme.of(context).colorScheme.tertiary,
                                ),
                                const SizedBox(width: 5),
                                Text(
                                  item.signal,
                                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                        color: KefeColorTokens.textMutedDark,
                                      ),
                                ),
                              ],
                            ),
                          ],
                        ),
                      ),
                      const Icon(Icons.chevron_right_rounded),
                    ],
                  ),
                ),
              ),
            ),
            const SizedBox(height: 10),
          ],
        ],
      ),
    );
  }
}

class _WeighPreviewScreen extends StatelessWidget {
  const _WeighPreviewScreen();

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      bottom: false,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(18, 14, 18, 28),
        children: [
          const _PreviewPageHeader(
            eyebrow: 'TARTIM',
            title: 'Kefeyi eline al.',
            icon: Icons.balance_rounded,
          ),
          const SizedBox(height: 18),
          Container(
            padding: const EdgeInsets.all(22),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(24),
              border: Border.all(color: KefeColorTokens.gold.withValues(alpha: 0.35)),
              gradient: const LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [Color(0xFF132B4D), Color(0xFF151927), Color(0xFF3A1D25)],
              ),
            ),
            child: Column(
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    _ScoreOrb(label: 'KURAL', value: '5', color: KefeColorTokens.rules),
                    const Padding(
                      padding: EdgeInsets.symmetric(horizontal: 18),
                      child: Icon(Icons.balance_rounded, size: 54, color: KefeColorTokens.goldSoft),
                    ),
                    _ScoreOrb(label: 'EMPATİ', value: '5', color: KefeColorTokens.empathy),
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
          _ActionCaseCard(
            label: 'GÜNLÜK İKİLEM',
            title: 'Çocuklar uçakta ebeveynleriyle ücretsiz yan yana oturmalı mı?',
            subtitle: 'Kural, fiyatlandırma, aile bütünlüğü ve orantılılığı birlikte tart.',
            icon: Icons.airplanemode_active_rounded,
            onTap: () => context.push('/case/11111111-1111-4111-8111-111111111116'),
          ),
          const SizedBox(height: 12),
          _ActionCaseCard(
            label: 'SPORTS CALL',
            title: 'Bu pozisyonda penaltı kararı doğru muydu?',
            subtitle: 'Hakem kararı, temasın etkisi ve VAR eşiğini değerlendir.',
            icon: Icons.sports_soccer_rounded,
            onTap: () => context.push('/case/11111111-1111-4111-8111-111111111113'),
          ),
          const SizedBox(height: 12),
          _ActionCaseCard(
            label: 'TEKNOLOJİ',
            title: 'YZ şirketlerinin veri toplaması sınırlandırılmalı mı?',
            subtitle: 'Mahremiyet ve inovasyon arasındaki sınırı kendi kefe değerlerinle tart.',
            icon: Icons.psychology_alt_rounded,
            onTap: () => context.push('/case/11111111-1111-4111-8111-111111111112'),
          ),
        ],
      ),
    );
  }
}

class _AtlasPreviewScreen extends StatelessWidget {
  const _AtlasPreviewScreen();

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
          const _PreviewPageHeader(
            eyebrow: 'KEFE ATLAS',
            title: 'Aynı soru,\nfarklı dünyalar.',
            icon: Icons.public_rounded,
          ),
          const SizedBox(height: 14),
          const _PreviewNotice(
            text: 'Atlas sayıları temsili Product Preview verisidir · gerçek ülke sonucu değildir',
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
                colors: [Color(0xFF173A67), Color(0xFF1A2338), Color(0xFF391D29)],
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
            style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800),
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
                      Text(item.$1, style: Theme.of(context).textTheme.labelSmall),
                      const SizedBox(height: 7),
                      Text(
                        item.$2.toStringAsFixed(1),
                        style: Theme.of(context).textTheme.headlineSmall?.copyWith(
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

class _MyKefePreviewScreen extends StatelessWidget {
  const _MyKefePreviewScreen();

  @override
  Widget build(BuildContext context) {
    const dimensions = [
      ('Tartım sayısı', '12'),
      ('Fikir güncellemesi', '3'),
      ('Keşfedilen alan', '5'),
    ];

    return SafeArea(
      bottom: false,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(18, 14, 18, 28),
        children: [
          const _PreviewPageHeader(
            eyebrow: 'MY KEFE',
            title: 'Karar yolculuğun.',
            icon: Icons.person_rounded,
          ),
          const SizedBox(height: 14),
          const _PreviewNotice(
            text: 'Aşağıdaki geçmiş, profil ekranını test etmek için hazırlanmış örnek veridir',
          ),
          const SizedBox(height: 18),
          Row(
            children: [
              for (var i = 0; i < dimensions.length; i++) ...[
                if (i > 0) const SizedBox(width: 10),
                Expanded(
                  child: Card(
                    child: Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 16),
                      child: Column(
                        children: [
                          Text(
                            dimensions[i].$2,
                            style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                                  color: KefeColorTokens.goldSoft,
                                  fontWeight: FontWeight.w900,
                                ),
                          ),
                          const SizedBox(height: 5),
                          Text(
                            dimensions[i].$1,
                            textAlign: TextAlign.center,
                            style: Theme.of(context).textTheme.labelSmall?.copyWith(
                                  color: KefeColorTokens.textMutedDark,
                                ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ],
            ],
          ),
          const SizedBox(height: 20),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(18),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Son 90 gün · karar alanların',
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800),
                  ),
                  const SizedBox(height: 18),
                  const _HistoryBar(label: 'Teknoloji', value: 0.82, count: '4 tartım'),
                  const SizedBox(height: 14),
                  const _HistoryBar(label: 'Günlük yaşam', value: 0.64, count: '3 tartım'),
                  const SizedBox(height: 14),
                  const _HistoryBar(label: 'Spor', value: 0.48, count: '2 tartım'),
                  const SizedBox(height: 14),
                  const _HistoryBar(label: 'Civic', value: 0.36, count: '2 tartım'),
                  const SizedBox(height: 14),
                  const _HistoryBar(label: 'Eğitim', value: 0.22, count: '1 tartım'),
                ],
              ),
            ),
          ),
          const SizedBox(height: 14),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(18),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    width: 46,
                    height: 46,
                    decoration: BoxDecoration(
                      color: KefeColorTokens.gold.withValues(alpha: 0.12),
                      borderRadius: BorderRadius.circular(14),
                    ),
                    child: const Icon(Icons.change_circle_outlined, color: KefeColorTokens.goldSoft),
                  ),
                  const SizedBox(width: 14),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          '3 kararda fikrini güncelledin',
                          style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800),
                        ),
                        const SizedBox(height: 6),
                        Text(
                          'Bu yalnızca gözlenen karar geçmişini özetler; kişilik, ideoloji veya psikolojik profil çıkarmaz.',
                          style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                color: KefeColorTokens.textMutedDark,
                                height: 1.4,
                              ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _PreviewPageHeader extends StatelessWidget {
  const _PreviewPageHeader({
    required this.eyebrow,
    required this.title,
    required this.icon,
  });

  final String eyebrow;
  final String title;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return Row(
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
            border: Border.all(color: KefeColorTokens.gold.withValues(alpha: 0.26)),
          ),
          child: Icon(icon, color: KefeColorTokens.goldSoft),
        ),
      ],
    );
  }
}

class _PreviewNotice extends StatelessWidget {
  const _PreviewNotice({required this.text});

  final String text;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: KefeColorTokens.rules.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: KefeColorTokens.rules.withValues(alpha: 0.22)),
      ),
      child: Row(
        children: [
          const Icon(Icons.visibility_outlined, color: KefeColorTokens.rules, size: 17),
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
}

class _FilterPill extends StatelessWidget {
  const _FilterPill({required this.label, this.selected = false});

  final String label;
  final bool selected;

  @override
  Widget build(BuildContext context) {
    return Container(
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
}

class _ScoreOrb extends StatelessWidget {
  const _ScoreOrb({required this.label, required this.value, required this.color});

  final String label;
  final String value;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(label, style: Theme.of(context).textTheme.labelSmall?.copyWith(color: color)),
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
}

class _ActionCaseCard extends StatelessWidget {
  const _ActionCaseCard({
    required this.label,
    required this.title,
    required this.subtitle,
    required this.icon,
    required this.onTap,
  });

  final String label;
  final String title;
  final String subtitle;
  final IconData icon;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Card(
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
}

class _HistoryBar extends StatelessWidget {
  const _HistoryBar({required this.label, required this.value, required this.count});

  final String label;
  final double value;
  final String count;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Row(
          children: [
            Text(label, style: Theme.of(context).textTheme.bodyMedium),
            const Spacer(),
            Text(
              count,
              style: Theme.of(context).textTheme.labelSmall?.copyWith(
                    color: KefeColorTokens.textMutedDark,
                  ),
            ),
          ],
        ),
        const SizedBox(height: 7),
        ClipRRect(
          borderRadius: BorderRadius.circular(99),
          child: LinearProgressIndicator(
            minHeight: 7,
            value: value,
            backgroundColor: KefeColorTokens.surfaceSoftDark,
            valueColor: const AlwaysStoppedAnimation(KefeColorTokens.gold),
          ),
        ),
      ],
    );
  }
}
