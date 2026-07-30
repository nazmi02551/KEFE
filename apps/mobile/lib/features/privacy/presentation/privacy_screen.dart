import 'package:flutter/material.dart';

import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import 'privacy_controls_section.dart';

class PrivacyScreen extends StatelessWidget {
  const PrivacyScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    return Scaffold(
      appBar: AppBar(title: Text(strings.privacyTitle)),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(18),
          children: const [PrivacyControlsSection()],
        ),
      ),
    );
  }
}
