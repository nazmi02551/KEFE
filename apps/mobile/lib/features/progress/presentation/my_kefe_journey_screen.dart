import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_content_localizer.dart';
import '../../../core/localization/kefe_strings.dart';
import '../../saved_cases/presentation/saved_cases_section.dart';
import '../application/progress_controller.dart';
import '../domain/progress_models.dart';
import 'progress_async_state_surface.dart';
import 'progress_strings.dart';

part 'my_kefe_journey_shell.dart';
part 'my_kefe_journey_summary.dart';
part 'my_kefe_journey_details.dart';
part 'my_kefe_journey_support.dart';
