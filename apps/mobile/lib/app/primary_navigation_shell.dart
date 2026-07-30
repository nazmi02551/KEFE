import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../core/design/kefe_theme.dart';
import '../core/localization/kefe_strings.dart';

class PrimaryNavigationShell extends StatelessWidget {
  const PrimaryNavigationShell({
    required this.selectedIndex,
    required this.child,
    this.footer,
    this.floatingActionButton,
    super.key,
  });

  final int selectedIndex;
  final Widget child;
  final Widget? footer;
  final Widget? floatingActionButton;

  static const paths = <String>['/explore', '/weigh', '/activity', '/my-kefe'];

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    return Scaffold(
      body: child,
      floatingActionButton: floatingActionButton,
      bottomNavigationBar: DecoratedBox(
        decoration: const BoxDecoration(
          border: Border(top: BorderSide(color: KefeColorTokens.borderDark)),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ?footer,
            NavigationBar(
              key: const ValueKey('primary-navigation'),
              selectedIndex: selectedIndex,
              onDestinationSelected: (index) => context.go(paths[index]),
              destinations: [
                NavigationDestination(
                  icon: const Icon(Icons.explore_outlined),
                  selectedIcon: const Icon(Icons.explore_rounded),
                  label: strings.primaryNavExplore,
                ),
                NavigationDestination(
                  icon: const Icon(Icons.balance_outlined),
                  selectedIcon: const Icon(Icons.balance_rounded),
                  label: strings.primaryNavWeigh,
                ),
                NavigationDestination(
                  icon: const Icon(Icons.history_outlined),
                  selectedIcon: const Icon(Icons.history_rounded),
                  label: strings.primaryNavActivity,
                ),
                NavigationDestination(
                  icon: const Icon(Icons.person_outline_rounded),
                  selectedIcon: const Icon(Icons.person_rounded),
                  label: strings.primaryNavMyKefe,
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

extension PrimaryNavigationStrings on KefeStrings {
  bool get _primaryNavigationIsTurkish => locale.languageCode == 'tr';

  String get primaryNavExplore =>
      _primaryNavigationIsTurkish ? 'Keşfet' : 'Explore';
  String get primaryNavWeigh =>
      _primaryNavigationIsTurkish ? 'Tartım' : 'Weigh';
  String get primaryNavActivity =>
      _primaryNavigationIsTurkish ? 'Aktivite' : 'Activity';
  String get primaryNavMyKefe => 'My KEFE';
}
