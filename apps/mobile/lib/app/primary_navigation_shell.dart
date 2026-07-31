import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../core/design/kefe_visual_system.dart';
import '../core/localization/internal_alpha_strings.dart';
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
    final visual = context.kefeVisual;

    return Scaffold(
      body: child,
      floatingActionButton: floatingActionButton,
      bottomNavigationBar: DecoratedBox(
        key: const ValueKey('primary-navigation-surface'),
        decoration: BoxDecoration(
          color: visual.surfaceRaised,
          border: Border(
            top: BorderSide(
              color: visual.border.withValues(alpha: visual.isDark ? 0.92 : 1),
            ),
          ),
          boxShadow: [
            BoxShadow(
              color: visual.shadow.withValues(alpha: visual.isDark ? 0.28 : 0.1),
              blurRadius: 20,
              offset: const Offset(0, -6),
            ),
          ],
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ?footer,
            NavigationBar(
              key: const ValueKey('primary-navigation'),
              backgroundColor: Colors.transparent,
              elevation: 0,
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

class KefeShellAction extends StatelessWidget {
  const KefeShellAction({
    required this.icon,
    required this.tooltip,
    required this.onPressed,
    this.heroTag,
    super.key,
  });

  final IconData icon;
  final String tooltip;
  final VoidCallback onPressed;
  final Object? heroTag;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;

    return SizedBox.square(
      dimension: 48,
      child: FloatingActionButton.small(
        heroTag: heroTag,
        tooltip: tooltip,
        elevation: 0,
        highlightElevation: 2,
        backgroundColor: visual.surfaceStrong,
        foregroundColor: visual.goldSoft,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: BorderSide(color: visual.gold.withValues(alpha: 0.38)),
        ),
        onPressed: onPressed,
        child: Icon(icon),
      ),
    );
  }
}
