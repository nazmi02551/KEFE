import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Explicit build/composition switch for visual-only Product Preview treatment.
///
/// Production defaults to false. Preview entrypoints/tests must opt in explicitly;
/// this is never a network/error fallback.
final productPreviewVisualModeProvider = Provider<bool>((ref) => false);
