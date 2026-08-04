import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/config/experience_presentation_config.dart';
import '../../../core/design/kefe_active_journey.dart';
import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/design/product_preview_visual_mode.dart';
import '../../../core/localization/kefe_strings.dart';
import '../../context/presentation/context_section.dart';
import '../../onboarding/application/onboarding_controller.dart';
import '../application/decision_controller.dart';
import '../domain/decision_models.dart';
import 'case_hero_header.dart';
import 'decision_flow_screen.dart';
import 'decision_journey_stage_resolver.dart';
import 'decision_journey_strings.dart';
import 'decision_subjourney.dart';
import 'post_commit_journey.dart';
import 'reflection_step.dart';

part 'decision_experience_shell.dart';
part 'decision_experience_active_step.dart';
part 'decision_experience_surfaces.dart';
