import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../../decision/data/decision_repository.dart';
import '../../decision/data/http_decision_repository.dart';
import '../application/share_controller.dart';
import '../data/share_repository.dart';

class PublicShareScreen extends ConsumerStatefulWidget {
  const PublicShareScreen({required this.token, super.key});

  final String token;

  @override
  ConsumerState<PublicShareScreen> createState() => _PublicShareScreenState();
}

class _PublicShareScreenState extends ConsumerState<PublicShareScreen> {
  PublicShare? _share;
  String? _errorCode;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    Future.microtask(_load);
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _errorCode = null;
    });
    try {
      final share = await ref.read(shareRepositoryProvider).read(widget.token);
      if (!mounted) return;
      setState(() {
        _share = share;
        _loading = false;
      });
    } on ApiFailure catch (error) {
      if (!mounted) return;
      setState(() {
        _errorCode = error.code;
        _loading = false;
      });
    } on ClientTransportFailure catch (error) {
      if (!mounted) return;
      setState(() {
        _errorCode = error.code;
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;

    return Scaffold(
      appBar: AppBar(
        backgroundColor: visual.surfaceRaised,
        foregroundColor: visual.foreground,
        title: Text(strings.appName),
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(1),
          child: Divider(height: 1, thickness: 1, color: visual.border),
        ),
      ),
      body: SafeArea(
        child: ListView(
          key: const ValueKey('public-share-screen'),
          padding: const EdgeInsets.fromLTRB(18, 18, 18, 32),
          children: [
            if (_loading)
              KefeSurface(
                key: const ValueKey('public-share-loading'),
                tone: KefeSurfaceTone.raised,
                child: Semantics(
                  label: strings.loading,
                  child: Row(
                    children: [
                      Icon(Icons.hourglass_top_rounded, color: visual.goldSoft),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          strings.loading,
                          style: Theme.of(context).textTheme.bodyLarge
                              ?.copyWith(fontWeight: FontWeight.w700),
                        ),
                      ),
                    ],
                  ),
                ),
              )
            else if (_share == null)
              KefeSurface(
                key: const ValueKey('public-share-error-surface'),
                tone: KefeSurfaceTone.raised,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Icon(
                      Icons.link_off_rounded,
                      size: 40,
                      color: visual.mutedForeground,
                    ),
                    const SizedBox(height: 12),
                    Text(
                      strings.publicShareUnavailable,
                      key: const ValueKey('public-share-error'),
                      textAlign: TextAlign.center,
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                    if (_errorCode != null) ...[
                      const SizedBox(height: 8),
                      Text(
                        _errorCode!,
                        textAlign: TextAlign.center,
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: visual.mutedForeground,
                        ),
                      ),
                    ],
                    const SizedBox(height: 16),
                    OutlinedButton.icon(
                      onPressed: _load,
                      icon: const Icon(Icons.refresh_rounded),
                      label: Text(strings.publicShareRetry),
                    ),
                  ],
                ),
              )
            else
              _PublicShareReady(share: _share!),
          ],
        ),
      ),
    );
  }
}

class _PublicShareReady extends StatelessWidget {
  const _PublicShareReady({required this.share});

  final PublicShare share;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        KefeSurface(
          key: const ValueKey('public-share-case-surface'),
          tone: KefeSurfaceTone.premium,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Icon(Icons.balance_rounded, color: visual.onSurfaceStrong),
                  const SizedBox(width: 9),
                  Expanded(
                    child: Text(
                      strings.publicShareEyebrow,
                      style: Theme.of(context).textTheme.labelLarge?.copyWith(
                        color: visual.onSurfaceStrong,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 14),
              Text(
                share.title,
                key: const ValueKey('public-share-title'),
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                  color: visual.onSurfaceStrong,
                  fontWeight: FontWeight.w900,
                  height: 1.15,
                ),
              ),
              const SizedBox(height: 10),
              Text(
                share.summary,
                style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                  color: visual.onSurfaceStrong.withValues(alpha: 0.88),
                  height: 1.45,
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 14),
        KefeSurface(
          key: const ValueKey('public-share-blind-first-surface'),
          tone: KefeSurfaceTone.raised,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  DecoratedBox(
                    decoration: BoxDecoration(
                      color: visual.rules.withValues(alpha: 0.10),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(
                        color: visual.rules.withValues(alpha: 0.22),
                      ),
                    ),
                    child: SizedBox.square(
                      dimension: 38,
                      child: Icon(
                        Icons.visibility_off_outlined,
                        size: 20,
                        color: visual.rules,
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      strings.publicShareBlindFirst,
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: visual.foreground,
                        fontWeight: FontWeight.w700,
                        height: 1.45,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 14),
              Align(
                alignment: Alignment.centerLeft,
                child: DecoratedBox(
                  decoration: BoxDecoration(
                    color: visual.rules.withValues(alpha: 0.08),
                    borderRadius: BorderRadius.circular(99),
                    border: Border.all(
                      color: visual.rules.withValues(alpha: 0.20),
                    ),
                  ),
                  child: Padding(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 11,
                      vertical: 7,
                    ),
                    child: Text(
                      strings.domainName(share.primaryDomain),
                      style: Theme.of(context).textTheme.labelMedium?.copyWith(
                        color: visual.rules,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 16),
              FilledButton.icon(
                key: const ValueKey('public-share-weigh'),
                onPressed: () => context.go('/case/${share.caseId}'),
                icon: const Icon(Icons.balance_rounded),
                label: Text(strings.publicShareWeigh),
              ),
            ],
          ),
        ),
      ],
    );
  }
}
