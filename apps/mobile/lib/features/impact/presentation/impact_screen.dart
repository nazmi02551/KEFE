import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/kefe_strings.dart';
import '../application/action_follow_through_controller.dart';
import '../application/institution_response_controller.dart';
import 'action_follow_through_card.dart';
import 'institution_response_card.dart';

class ImpactScreen extends ConsumerWidget {
  const ImpactScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final responseState = ref.watch(institutionResponseControllerProvider);
    final actionState = ref.watch(actionFollowThroughControllerProvider);

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
              strings.impactTitle,
              style: TextStyle(
                color: visual.foreground,
                fontWeight: FontWeight.w800,
                fontSize: 20,
              ),
            ),
          ),
          SliverPadding(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 0),
            sliver: SliverToBoxAdapter(
              child: Text(
                strings.impactSubtitle,
                style: TextStyle(
                  color: visual.mutedForeground,
                  fontSize: 14,
                  height: 1.5,
                ),
              ),
            ),
          ),
          const SliverToBoxAdapter(child: SizedBox(height: 20)),

          // --- Kurumsal Yanıtlar ---
          SliverPadding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            sliver: SliverToBoxAdapter(
              child: _SectionHeader(
                icon: Icons.account_balance_outlined,
                label: strings.impactInstitutionResponsesTitle,
                color: visual.rules,
              ),
            ),
          ),
          const SliverToBoxAdapter(child: SizedBox(height: 10)),

          if (responseState.loading)
            const SliverToBoxAdapter(
              child: Padding(
                padding: EdgeInsets.all(32),
                child: Center(child: CircularProgressIndicator()),
              ),
            )
          else if (responseState.errorCode != null)
            SliverToBoxAdapter(
              child: _ErrorRetry(
                message: strings.impactLoadError,
                onRetry: () => ref
                    .read(institutionResponseControllerProvider.notifier)
                    .load(),
              ),
            )
          else if (responseState.items.isEmpty)
            SliverToBoxAdapter(
              child: _EmptyState(
                icon: Icons.account_balance_outlined,
                message: strings.impactNoResponses,
                color: visual.rules,
              ),
            )
          else
            SliverPadding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              sliver: SliverList(
                delegate: SliverChildBuilderDelegate(
                  (context, index) => Padding(
                    padding: const EdgeInsets.only(bottom: 12),
                    child: InstitutionResponseCard(
                      response: responseState.items[index],
                    ),
                  ),
                  childCount: responseState.items.length,
                ),
              ),
            ),

          const SliverToBoxAdapter(child: SizedBox(height: 24)),

          // --- Eylem Adımları ---
          SliverPadding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            sliver: SliverToBoxAdapter(
              child: _SectionHeader(
                icon: Icons.task_alt_outlined,
                label: strings.impactActionsTitle,
                color: visual.gold,
              ),
            ),
          ),
          const SliverToBoxAdapter(child: SizedBox(height: 10)),

          if (actionState.loading)
            const SliverToBoxAdapter(
              child: Padding(
                padding: EdgeInsets.all(32),
                child: Center(child: CircularProgressIndicator()),
              ),
            )
          else if (actionState.errorCode != null)
            SliverToBoxAdapter(
              child: _ErrorRetry(
                message: strings.impactLoadError,
                onRetry: () => ref
                    .read(actionFollowThroughControllerProvider.notifier)
                    .load(),
              ),
            )
          else if (actionState.actions.isEmpty)
            SliverToBoxAdapter(
              child: _EmptyState(
                icon: Icons.task_alt_outlined,
                message: strings.impactNoActions,
                color: visual.gold,
              ),
            )
          else
            SliverPadding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              sliver: SliverList(
                delegate: SliverChildBuilderDelegate(
                  (context, index) => Padding(
                    padding: const EdgeInsets.only(bottom: 12),
                    child: ActionFollowThroughCard(
                      action: actionState.actions[index],
                    ),
                  ),
                  childCount: actionState.actions.length,
                ),
              ),
            ),

          const SliverToBoxAdapter(child: SizedBox(height: 32)),

          // --- Metodoloji notu ---
          SliverPadding(
            padding: const EdgeInsets.fromLTRB(16, 0, 16, 48),
            sliver: SliverToBoxAdapter(
              child: Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: visual.surface,
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: visual.border),
                ),
                child: Text(
                  strings.impactMethodologyNote,
                  style: TextStyle(
                    color: visual.mutedForeground,
                    fontSize: 12,
                    height: 1.6,
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _SectionHeader extends StatelessWidget {
  const _SectionHeader({
    required this.icon,
    required this.label,
    required this.color,
  });

  final IconData icon;
  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(icon, size: 18, color: color),
        const SizedBox(width: 8),
        Text(
          label,
          style: TextStyle(
            color: color,
            fontWeight: FontWeight.w700,
            fontSize: 15,
          ),
        ),
      ],
    );
  }
}

class _EmptyState extends StatelessWidget {
  const _EmptyState({
    required this.icon,
    required this.message,
    required this.color,
  });

  final IconData icon;
  final String message;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 20),
      child: Column(
        children: [
          Icon(icon, size: 36, color: color.withValues(alpha: 0.35)),
          const SizedBox(height: 10),
          Text(
            message,
            textAlign: TextAlign.center,
            style: TextStyle(
              color: context.kefeVisual.mutedForeground,
              fontSize: 13,
            ),
          ),
        ],
      ),
    );
  }
}

class _ErrorRetry extends StatelessWidget {
  const _ErrorRetry({required this.message, required this.onRetry});

  final String message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    return Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        children: [
          Text(
            message,
            style: TextStyle(color: visual.mutedForeground, fontSize: 13),
          ),
          const SizedBox(height: 12),
          TextButton(
            onPressed: onRetry,
            child: Text(
              KefeStrings.of(context).retryAction,
              style: TextStyle(color: visual.gold, fontWeight: FontWeight.w700),
            ),
          ),
        ],
      ),
    );
  }
}