import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/user_discovery_profile_models.dart';

class UserDiscoveryProfileSheet extends StatefulWidget {
  const UserDiscoveryProfileSheet({
    required this.initialProfile,
    this.onSave,
    super.key,
  });

  final UserDiscoveryProfileModel initialProfile;
  final ValueChanged<UserDiscoveryProfileModel>? onSave;

  static Future<UserDiscoveryProfileModel?> show(
    BuildContext context,
    UserDiscoveryProfileModel initialProfile, {
    ValueChanged<UserDiscoveryProfileModel>? onSave,
  }) {
    return showModalBottomSheet<UserDiscoveryProfileModel>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => UserDiscoveryProfileSheet(
        initialProfile: initialProfile,
        onSave: onSave,
      ),
    );
  }

  @override
  State<UserDiscoveryProfileSheet> createState() =>
      _UserDiscoveryProfileSheetState();
}

class _UserDiscoveryProfileSheetState extends State<UserDiscoveryProfileSheet> {
  late List<DomainPreferenceModel> _domains;
  late ComplexityLevelModel _complexity;
  late FreshnessPreferenceModel _freshness;
  late RealEventPreferenceModel _realEvent;
  late double _diversificationBoost;

  @override
  void initState() {
    super.initState();
    _domains = List.from(widget.initialProfile.preferredDomains);
    _complexity = widget.initialProfile.complexityLevel;
    _freshness = widget.initialProfile.freshnessPreference;
    _realEvent = widget.initialProfile.realEventPreference;
    _diversificationBoost = widget.initialProfile.diversificationBoost;
  }

  void _toggleDomain(DomainPreferenceModel domain) {
    setState(() {
      if (_domains.contains(domain)) {
        if (_domains.length > 1) {
          _domains.remove(domain);
        }
      } else {
        _domains.add(domain);
      }
    });
  }

  void _save() {
    final updated = widget.initialProfile.copyWith(
      preferredDomains: _domains,
      complexityLevel: _complexity,
      freshnessPreference: _freshness,
      realEventPreference: _realEvent,
      diversificationBoost: _diversificationBoost,
      updatedAt: DateTime.now().toUtc(),
    );
    widget.onSave?.call(updated);
    Navigator.of(context).pop(updated);
  }

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;

    return Container(
      decoration: BoxDecoration(
        color: visual.surface,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(28)),
        border: Border.all(color: visual.border.withValues(alpha: 0.6)),
      ),
      padding: EdgeInsets.only(
        top: 20,
        left: 20,
        right: 20,
        bottom: MediaQuery.of(context).viewInsets.bottom + 24,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Center(
            child: Container(
              width: 40,
              height: 4,
              decoration: BoxDecoration(
                color: visual.borderStrong,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Icon(Icons.tune_rounded, color: visual.rules, size: 24),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  strings.discProfileSheetTitle,
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w900,
                    letterSpacing: -0.2,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Text(
            strings.discProfileAntiAlgorithmNotice,
            style: TextStyle(
              fontSize: 12,
              color: visual.mutedForeground,
            ),
          ),
          const SizedBox(height: 16),
          Flexible(
            child: SingleChildScrollView(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // Domains Section
                  _buildSectionHeader(visual, strings.discProfileDomainsTitle),
                  const SizedBox(height: 8),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: DomainPreferenceModel.values.map((d) {
                      final isSelected = _domains.contains(d);
                      return ChoiceChip(
                        label: Text(_domainLabel(d)),
                        selected: isSelected,
                        onSelected: (_) => _toggleDomain(d),
                        selectedColor: visual.rules.withValues(
                          alpha: visual.isDark ? 0.25 : 0.15,
                        ),
                        side: BorderSide(
                          color: isSelected ? visual.rules : visual.border,
                        ),
                        labelStyle: TextStyle(
                          fontSize: 12,
                          fontWeight:
                              isSelected ? FontWeight.w800 : FontWeight.w500,
                          color: isSelected ? visual.rules : visual.foreground,
                        ),
                      );
                    }).toList(),
                  ),
                  const SizedBox(height: 18),

                  // Complexity
                  _buildSectionHeader(visual, strings.discProfileComplexityTitle),
                  const SizedBox(height: 8),
                  SegmentedButton<ComplexityLevelModel>(
                    segments: const [
                      ButtonSegment(
                        value: ComplexityLevelModel.introductory,
                        label: Text('Giriş', style: TextStyle(fontSize: 11)),
                      ),
                      ButtonSegment(
                        value: ComplexityLevelModel.balanced,
                        label: Text('Dengeli', style: TextStyle(fontSize: 11)),
                      ),
                      ButtonSegment(
                        value: ComplexityLevelModel.deepDeliberation,
                        label: Text('Derin', style: TextStyle(fontSize: 11)),
                      ),
                    ],
                    selected: {_complexity},
                    onSelectionChanged: (val) {
                      setState(() => _complexity = val.first);
                    },
                  ),
                  const SizedBox(height: 18),

                  // Filter Bubble Resistance
                  KefeSurface(
                    tone: KefeSurfaceTone.raised,
                    padding: const EdgeInsets.all(14),
                    borderRadius: 16,
                    accent: visual.gold,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Text(
                              strings.discProfileDiversityBoostTitle,
                              style: TextStyle(
                                fontSize: 12.5,
                                fontWeight: FontWeight.w800,
                                color: visual.foreground,
                              ),
                            ),
                            Text(
                              '%${(_diversificationBoost * 100).toInt()}',
                              style: TextStyle(
                                fontSize: 13,
                                fontWeight: FontWeight.w900,
                                color: visual.gold,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 4),
                        Text(
                          strings.discProfileDiversityBoostDesc,
                          style: TextStyle(
                            fontSize: 11.5,
                            color: visual.mutedForeground,
                          ),
                        ),
                        Slider(
                          value: _diversificationBoost,
                          min: 0.0,
                          max: 1.0,
                          divisions: 10,
                          activeColor: visual.gold,
                          onChanged: (v) {
                            setState(() => _diversificationBoost = v);
                          },
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 14),
          ElevatedButton(
            onPressed: _save,
            child: Text(strings.discProfileSaveButton),
          ),
        ],
      ),
    );
  }

  Widget _buildSectionHeader(KefeVisualTheme visual, String title) {
    return Text(
      title,
      style: TextStyle(
        fontSize: 12.5,
        fontWeight: FontWeight.w800,
        letterSpacing: -0.1,
        color: visual.foreground,
      ),
    );
  }

  String _domainLabel(DomainPreferenceModel domain) => switch (domain) {
    DomainPreferenceModel.civic => 'Yurttaşlık',
    DomainPreferenceModel.technology => 'Teknoloji & Yapay Zekâ',
    DomainPreferenceModel.bioethics => 'Biyoetik & Sağlık',
    DomainPreferenceModel.environment => 'Çevre & İklim',
    DomainPreferenceModel.justice => 'Hukuk & Adalet',
    DomainPreferenceModel.economic => 'Ekonomi & Paylaşım',
  };
}
