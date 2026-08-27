import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/experience_hub_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../../decision/application/decision_controller.dart';
import '../../decision/data/decision_repository.dart';
import '../../decision/domain/decision_models.dart';

class ExperienceHubScreen extends ConsumerStatefulWidget {
  const ExperienceHubScreen({
    this.previewRadarEnabled = false,
    this.previewAtlasEnabled = false,
    super.key,
  });

  final bool previewRadarEnabled;
  final bool previewAtlasEnabled;

  @override
  ConsumerState<ExperienceHubScreen> createState() =>
      _ExperienceHubScreenState();
}

class _ExperienceHubScreenState extends ConsumerState<ExperienceHubScreen> {
  bool _loading = true;
  String? _errorCode;
  DecisionCaseSummary? _todayCase;
  DecisionCaseSummary? _dilemmaCase;
  DecisionCaseSummary? _sportsCall;
  DecisionCaseSummary? _communityCase;

  @override
  void initState() {
    super.initState();
    Future.microtask(_load);
  }

  Future<void> _load() async {
    if (mounted) {
      setState(() {
        _loading = true;
        _errorCode = null;
      });
    }
    try {
      final cases = await ref
          .read(decisionRepositoryProvider)
          .fetchExploreCases(limit: 50);
      DecisionCaseSummary? dilemma;
      DecisionCaseSummary? sports;
      DecisionCaseSummary? community;
      DecisionCaseSummary? today;
      for (final item in cases) {
        final isDilemma = item.format == 'DILEMMA';
        final isSports =
            item.format == 'SPORTS_CALL' || item.domain == 'SPORTS';
        if (today == null && item.isRealEvent) {
          today = item;
        }
        if (dilemma == null && isDilemma) {
          dilemma = item;
        }
        if (sports == null && isSports) {
          sports = item;
        }
        if (community == null && !isSports) {
          community = item;
        }
        if (today != null &&
            dilemma != null &&
            sports != null &&
            community != null) {
          break;
        }
      }
      community ??= cases.isNotEmpty ? cases.first : null;
      if (!mounted) return;
      setState(() {
        _todayCase = today;
        _dilemmaCase = dilemma;
        _sportsCall = sports;
        _communityCase = community;
        _loading = false;
      });
    } on ClientTransportFailure catch (error) {
      if (!mounted) return;
      setState(() {
        _errorCode = error.code;
        _loading = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _errorCode = 'DEPENDENCY_TEMPORARILY_UNAVAILABLE';
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final previewExperiencesEnabled =
        widget.previewRadarEnabled || widget.previewAtlasEnabled;

    return Scaffold(
      appBar: AppBar(title: Text(strings.experienceHubTitle)),
      body: SafeArea(
        child: ListView(
          key: const ValueKey('experience-hub'),
          padding: const EdgeInsets.fromLTRB(18, 16, 18, 30),
          children: [
            Text(
              strings.experienceHubSubtitle,
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                color: visual.mutedForeground,
                height: 1.35,
              ),
            ),
            const SizedBox(height: 20),
            _ExperienceCard(
              cardKey: const ValueKey('experience-standard'),
              icon: Icons.balance_rounded,
              title: strings.experienceStandardTitle,
              body: strings.experienceStandardBody,
              actionLabel: strings.experienceStandardAction,
              onPressed: () => context.go('/explore'),
            ),
            const SizedBox(height: 14),
            if (!_loading && _errorCode == null)
              if (_todayCase != null)
                _ExperienceCard(
                  cardKey: const ValueKey('experience-today'),
                  icon: Icons.today_rounded,
                  title: strings.experienceTodayTitle,
                  body:
                      '${strings.experienceTodayBody}\n\n${_todayCase!.title}',
                  actionLabel: strings.experienceTodayAction,
                  onPressed: () => context.push('/case/${_todayCase!.id}'),
                )
              else
                _ExperienceCard(
                  cardKey: const ValueKey('experience-today-empty'),
                  icon: Icons.today_rounded,
                  title: strings.experienceTodayTitle,
                  body: strings.experienceTodayEmpty,
                ),
            const SizedBox(height: 14),
            if (!_loading && _errorCode == null)
              if (_dilemmaCase != null)
                _ExperienceCard(
                  cardKey: const ValueKey('experience-dilemma'),
                  icon: Icons.alt_route_rounded,
                  title: strings.experienceDilemmaTitle,
                  body:
                      '${strings.experienceDilemmaBody}\n\n${_dilemmaCase!.title}',
                  actionLabel: strings.experienceDilemmaAction,
                  onPressed: () => context.push('/case/${_dilemmaCase!.id}'),
                )
              else
                _ExperienceCard(
                  cardKey: const ValueKey('experience-dilemma-empty'),
                  icon: Icons.alt_route_rounded,
                  title: strings.experienceDilemmaTitle,
                  body: strings.experienceDilemmaEmpty,
                ),
            if (!_loading && _errorCode == null && _communityCase != null) ...[
              const SizedBox(height: 14),
              _ExperienceCard(
                cardKey: const ValueKey('experience-community'),
                icon: Icons.groups_2_outlined,
                title: strings.experienceCommunityTitle,
                body:
                    '${strings.experienceCommunityBody}\n\n${_communityCase!.title}',
                actionLabel: strings.experienceCommunityAction,
                onPressed: () => context.push('/case/${_communityCase!.id}'),
              ),
            ],
            const SizedBox(height: 14),
            if (_loading)
              KefeSurface(
                key: const ValueKey('experience-sports-loading'),
                tone: KefeSurfaceTone.raised,
                child: Row(
                  children: [
                    const SizedBox.square(
                      dimension: 22,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    ),
                    const SizedBox(width: 12),
                    Expanded(child: Text(strings.experienceLoading)),
                  ],
                ),
              )
            else if (_errorCode != null)
              KefeSurface(
                key: const ValueKey('experience-sports-error'),
                tone: KefeSurfaceTone.raised,
                accent: visual.attention,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Text(strings.messageForCode(_errorCode)),
                    const SizedBox(height: 10),
                    OutlinedButton.icon(
                      onPressed: _load,
                      icon: const Icon(Icons.refresh_rounded),
                      label: Text(strings.experienceRetry),
                    ),
                  ],
                ),
              )
            else if (_sportsCall != null)
              _ExperienceCard(
                cardKey: const ValueKey('experience-sports-call'),
                icon: Icons.sports_soccer_rounded,
                title: strings.experienceSportsTitle,
                body:
                    '${strings.experienceSportsBody}\n\n${_sportsCall!.title}',
                actionLabel: strings.experienceSportsAction,
                onPressed: () => context.push('/case/${_sportsCall!.id}'),
              )
            else
              _ExperienceCard(
                cardKey: const ValueKey('experience-sports-empty'),
                icon: Icons.sports_soccer_rounded,
                title: strings.experienceSportsTitle,
                body: strings.experienceSportsEmpty,
              ),
            if (widget.previewRadarEnabled) ...[
              const SizedBox(height: 14),
              _ExperienceCard(
                cardKey: const ValueKey('experience-radar'),
                icon: Icons.radar_rounded,
                title: strings.experienceRadarTitle,
                body: strings.experienceRadarBody,
                statusLabel: strings.experiencePreviewStatus,
                actionLabel: strings.experienceRadarAction,
                onPressed: () => context.push('/radar'),
              ),
            ],
            const SizedBox(height: 14),
            _ExperienceCard(
              cardKey: const ValueKey('experience-atlas'),
              icon: Icons.public_rounded,
              title: strings.experienceAtlasTitle,
              body: strings.experienceAtlasBody,
              statusLabel: widget.previewAtlasEnabled
                  ? strings.experiencePreviewStatus
                  : strings.experienceAtlasStatus,
              actionLabel: widget.previewAtlasEnabled
                  ? strings.experienceAtlasAction
                  : null,
              onPressed: widget.previewAtlasEnabled
                  ? () => context.push('/atlas')
                  : null,
            ),
            const SizedBox(height: 14),
            KefeSurface(
              key: const ValueKey('experience-truth-note'),
              tone: KefeSurfaceTone.sunken,
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(Icons.verified_outlined, color: visual.goldSoft),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      previewExperiencesEnabled
                          ? strings.experiencePreviewTruthNote
                          : strings.experienceProductionTruthNote,
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: visual.mutedForeground,
                        height: 1.45,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _ExperienceCard extends StatelessWidget {
  const _ExperienceCard({
    required this.cardKey,
    required this.icon,
    required this.title,
    required this.body,
    this.actionLabel,
    this.statusLabel,
    this.onPressed,
  });

  final Key cardKey;
  final IconData icon;
  final String title;
  final String body;
  final String? actionLabel;
  final String? statusLabel;
  final VoidCallback? onPressed;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    return KefeSurface(
      key: cardKey,
      tone: KefeSurfaceTone.raised,
      padding: const EdgeInsets.all(18),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 46,
                height: 46,
                decoration: BoxDecoration(
                  color: visual.subtleGoldSurface,
                  borderRadius: BorderRadius.circular(14),
                ),
                child: Icon(icon, color: visual.goldSoft),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                    if (statusLabel != null) ...[
                      const SizedBox(height: 6),
                      Text(
                        statusLabel!,
                        style: Theme.of(context).textTheme.labelMedium
                            ?.copyWith(
                              color: visual.goldSoft,
                              fontWeight: FontWeight.w800,
                            ),
                      ),
                    ],
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),
          Text(
            body,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: visual.mutedForeground,
              height: 1.45,
            ),
          ),
          if (actionLabel != null && onPressed != null) ...[
            const SizedBox(height: 16),
            FilledButton.icon(
              onPressed: onPressed,
              icon: const Icon(Icons.arrow_forward_rounded),
              label: Text(actionLabel!),
            ),
          ],
        ],
      ),
    );
  }
}
