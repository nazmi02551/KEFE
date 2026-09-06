import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/case_objection_models.dart';

class CaseObjectionDialog extends StatefulWidget {
  const CaseObjectionDialog({
    required this.caseVersionId,
    this.onSubmit,
    super.key,
  });

  final String caseVersionId;
  final void Function(ObjectionCategoryModel category, String statement, String? url)?
      onSubmit;

  static Future<void> show(
    BuildContext context, {
    required String caseVersionId,
    void Function(ObjectionCategoryModel category, String statement, String? url)?
        onSubmit,
  }) {
    return showDialog<void>(
      context: context,
      builder: (ctx) => CaseObjectionDialog(
        caseVersionId: caseVersionId,
        onSubmit: onSubmit,
      ),
    );
  }

  @override
  State<CaseObjectionDialog> createState() => _CaseObjectionDialogState();
}

class _CaseObjectionDialogState extends State<CaseObjectionDialog> {
  ObjectionCategoryModel _category = ObjectionCategoryModel.editorialBiasFraming;
  final _statementController = TextEditingController();
  final _urlController = TextEditingController();

  @override
  void dispose() {
    _statementController.dispose();
    _urlController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final accent = visual.attention;

    final isValid = _statementController.text.trim().length >= 20;

    return Dialog(
      backgroundColor: Colors.transparent,
      insetPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 24),
      child: KefeSurface(
        tone: KefeSurfaceTone.raised,
        padding: const EdgeInsets.all(20),
        borderRadius: 24,
        accent: accent,
        child: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Row(
                children: [
                  Container(
                    width: 36,
                    height: 36,
                    decoration: BoxDecoration(
                      color: accent.withValues(alpha: visual.isDark ? 0.18 : 0.10),
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(color: accent.withValues(alpha: 0.3)),
                    ),
                    child: Icon(Icons.report_gmailerrorred_rounded, color: accent, size: 20),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      strings.objectionDialogTitle,
                      style: Theme.of(context).textTheme.titleSmall?.copyWith(
                        fontWeight: FontWeight.w900,
                        letterSpacing: -0.2,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              DropdownButtonFormField<ObjectionCategoryModel>(
                initialValue: _category,
                decoration: InputDecoration(
                  filled: true,
                  fillColor: visual.surfaceSunken,
                  contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                    borderSide: BorderSide(color: visual.border),
                  ),
                ),
                dropdownColor: visual.surface,
                items: ObjectionCategoryModel.values.map((cat) {
                  return DropdownMenuItem(
                    value: cat,
                    child: Text(
                      _categoryLabel(strings, cat),
                      style: TextStyle(fontSize: 12, color: visual.foreground),
                    ),
                  );
                }).toList(),
                onChanged: (val) {
                  if (val != null) setState(() => _category = val);
                },
              ),
              const SizedBox(height: 12),
              TextField(
                controller: _statementController,
                maxLines: 4,
                style: TextStyle(fontSize: 13, color: visual.foreground),
                decoration: InputDecoration(
                  hintText: strings.objectionStatementHint,
                  hintStyle: TextStyle(fontSize: 12, color: visual.mutedForeground),
                  filled: true,
                  fillColor: visual.surfaceSunken,
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                    borderSide: BorderSide(color: visual.border),
                  ),
                ),
                onChanged: (_) => setState(() {}),
              ),
              const SizedBox(height: 10),
              TextField(
                controller: _urlController,
                maxLines: 1,
                style: TextStyle(fontSize: 13, color: visual.foreground),
                decoration: InputDecoration(
                  hintText: strings.objectionEvidenceUrlHint,
                  hintStyle: TextStyle(fontSize: 12, color: visual.mutedForeground),
                  filled: true,
                  fillColor: visual.surfaceSunken,
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                    borderSide: BorderSide(color: visual.border),
                  ),
                ),
              ),
              const SizedBox(height: 16),
              Row(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  TextButton(
                    onPressed: () => Navigator.of(context).pop(),
                    child: Text(strings.methodologyClose),
                  ),
                  const SizedBox(width: 8),
                  ElevatedButton(
                    onPressed: isValid
                        ? () {
                            final url = _urlController.text.trim();
                            widget.onSubmit?.call(
                              _category,
                              _statementController.text.trim(),
                              url.isEmpty ? null : url,
                            );
                            Navigator.of(context).pop();
                          }
                        : null,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: accent,
                      foregroundColor: Colors.white,
                    ),
                    child: Text(strings.objectionSubmitButton),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  String _categoryLabel(KefeStrings strings, ObjectionCategoryModel cat) =>
      switch (cat) {
        ObjectionCategoryModel.editorialBiasFraming => strings.objectionCategoryBias,
        ObjectionCategoryModel.factualInaccuracy => strings.objectionCategoryFactual,
        ObjectionCategoryModel.excludedStakeholder =>
            strings.objectionCategoryStakeholder,
        ObjectionCategoryModel.ambiguousOptions => strings.objectionCategoryAmbiguous,
        ObjectionCategoryModel.depreciatedContext => strings.objectionCategoryDrift,
      };
}
