import 'package:flutter/material.dart';

import 'privacy_controls_section.dart';

class PrivacyScreen extends StatelessWidget {
  const PrivacyScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final tr = Localizations.localeOf(context).languageCode == 'tr';
    return Scaffold(
      appBar: AppBar(title: Text(tr ? 'Gizlilik ve veriler' : 'Privacy and data')),
      body: const SafeArea(
        child: ListView(
          padding: EdgeInsets.all(18),
          children: [PrivacyControlsSection()],
        ),
      ),
    );
  }
}
