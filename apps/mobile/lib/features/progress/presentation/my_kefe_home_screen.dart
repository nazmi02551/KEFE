import 'package:flutter/material.dart';

import '../../saved_cases/presentation/saved_cases_section.dart';
import 'my_kefe_journey_screen.dart';

class MyKefeHomeScreen extends StatelessWidget {
  const MyKefeHomeScreen({this.embedded = false, super.key});

  final bool embedded;

  @override
  Widget build(BuildContext context) {
    final body = ListView(
      key: const ValueKey('my-kefe-home'),
      padding: const EdgeInsets.fromLTRB(18, 14, 18, 30),
      children: const [
        SavedCasesSection(),
        SizedBox(height: 18),
        _JourneySurface(),
      ],
    );
    return embedded ? body : Scaffold(body: SafeArea(bottom: false, child: body));
  }
}

class _JourneySurface extends StatelessWidget {
  const _JourneySurface();

  @override
  Widget build(BuildContext context) {
    return const SizedBox(
      height: 720,
      child: MyKefeJourneyScreen(embedded: true),
    );
  }
}