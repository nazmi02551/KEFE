import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/encrypted_backup_lifecycle_models.dart';

class EncryptedBackupLifecycleCard extends StatelessWidget {
  const EncryptedBackupLifecycleCard({
    required this.backup,
    this.onTap,
    super.key,
  });

  final EncryptedBackupModel backup;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final accent = _statusColor(visual, backup.status);

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(22),
      child: KefeSurface(
        key: ValueKey('enc-backup-${backup.backupId}'),
        tone: KefeSurfaceTone.raised,
        padding: const EdgeInsets.all(18),
        borderRadius: 22,
        accent: accent,
        child: Column(
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
                  child: Icon(Icons.enhanced_encryption_rounded, color: accent, size: 22),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      KefeEyebrow(strings.encBkpEyebrow, color: accent),
                      const SizedBox(height: 2),
                      Text(
                        _statusLabel(strings, backup.status),
                        style: TextStyle(
                          fontSize: 12.5,
                          fontWeight: FontWeight.w800,
                          color: visual.foreground,
                        ),
                      ),
                    ],
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3.5),
                  decoration: BoxDecoration(
                    color: visual.surfaceSunken,
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(color: visual.border.withValues(alpha: 0.5)),
                  ),
                  child: Text(
                    strings.encBkpSizeLabel(backup.encryptedPayloadBytes ~/ 1024),
                    style: TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.w800,
                      color: accent,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: visual.surfaceSunken,
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: visual.border.withValues(alpha: 0.5)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    strings.encBkpKdfLabel(backup.keyDerivationAlgorithm.name),
                    style: TextStyle(
                      fontSize: 10.5,
                      fontWeight: FontWeight.w700,
                      color: visual.gold,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'SHA-256 Digest: ${backup.integrityDigest.substring(0, 16)}...',
                    style: TextStyle(
                      fontSize: 11,
                      fontFamily: 'monospace',
                      color: visual.foreground,
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

  Color _statusColor(KefeVisualSystem visual, EncryptedBackupStatusModel status) => switch (status) {
    EncryptedBackupStatusModel.backupStaged => visual.gold,
    EncryptedBackupStatusModel.encryptedVaultSynced => visual.rules,
    EncryptedBackupStatusModel.restoreVerified => visual.empathy,
  };

  String _statusLabel(KefeStrings strings, EncryptedBackupStatusModel status) => switch (status) {
    EncryptedBackupStatusModel.backupStaged => strings.encBkpStStaged,
    EncryptedBackupStatusModel.encryptedVaultSynced => strings.encBkpStSynced,
    EncryptedBackupStatusModel.restoreVerified => strings.encBkpStVerified,
  };
}
