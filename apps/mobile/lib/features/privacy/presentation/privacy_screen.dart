import 'package:flutter/material.dart';

import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import 'privacy_controls_section.dart';

class PrivacyScreen extends StatelessWidget {
  const PrivacyScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;

    return Scaffold(
      appBar: AppBar(
        backgroundColor: visual.surfaceRaised,
        foregroundColor: visual.foreground,
        title: Text(strings.privacyTitle),
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(1),
          child: Divider(height: 1, thickness: 1, color: visual.border),
        ),
      ),
      body: SafeArea(
        child: ListView(
          key: const ValueKey('privacy-screen'),
          padding: const EdgeInsets.fromLTRB(18, 18, 18, 32),
          children: const [PrivacyControlsSection()],
        ),
      ),
    );
  }
}
