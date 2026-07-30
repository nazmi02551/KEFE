import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

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
    final tr = Localizations.localeOf(context).languageCode == 'tr';
    return Scaffold(
      appBar: AppBar(title: const Text('KEFE')),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(20),
          children: [
            if (_loading)
              const Center(child: CircularProgressIndicator())
            else if (_share == null) ...[
              Text(
                tr
                    ? 'Bu paylaşım artık kullanılamıyor.'
                    : 'This share is no longer available.',
                key: const ValueKey('public-share-error'),
              ),
              if (_errorCode != null) Text(_errorCode!),
              const SizedBox(height: 12),
              OutlinedButton(
                onPressed: _load,
                child: Text(tr ? 'Tekrar dene' : 'Try again'),
              ),
            ] else ...[
              Text(
                tr ? 'Bir KEFE vakası paylaşıldı' : 'A KEFE case was shared',
                style: Theme.of(context).textTheme.labelLarge,
              ),
              const SizedBox(height: 8),
              Text(
                _share!.title,
                key: const ValueKey('public-share-title'),
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                  fontWeight: FontWeight.w900,
                ),
              ),
              const SizedBox(height: 10),
              Text(_share!.summary),
              const SizedBox(height: 12),
              Chip(label: Text(_share!.primaryDomain)),
              const SizedBox(height: 18),
              Text(
                tr
                    ? 'Paylaşan kişinin kararı burada gösterilmez. Önce aynı vakayı kendin tart ve kararını sabitle; topluluk sonucu ancak kendi Commit’inden sonra açılır.'
                    : 'The sender’s decision is never shown here. Weigh the same case and Commit first; collective results unlock only after your own Commit.',
              ),
              const SizedBox(height: 16),
              FilledButton.icon(
                key: const ValueKey('public-share-weigh'),
                onPressed: () => context.go('/case/${_share!.caseId}'),
                icon: const Icon(Icons.balance_rounded),
                label: Text(tr ? 'Ben de tartayım' : 'Weigh it myself'),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
