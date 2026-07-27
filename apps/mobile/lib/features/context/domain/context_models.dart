import 'package:flutter/foundation.dart';

@immutable
class CaseContextSource {
  const CaseContextSource({
    required this.id,
    required this.title,
    required this.publisher,
    required this.sourceKind,
    required this.url,
    required this.publishedAt,
  });

  final String id;
  final String title;
  final String publisher;
  final String sourceKind;
  final Uri? url;
  final DateTime? publishedAt;
}

@immutable
class CaseContextBlock {
  const CaseContextBlock({
    required this.id,
    required this.displayOrder,
    required this.disclosureLevel,
    required this.title,
    required this.body,
    required this.claimStatus,
    required this.sourceIds,
  });

  final String id;
  final int displayOrder;
  final String disclosureLevel;
  final String title;
  final String body;
  final String claimStatus;
  final List<String> sourceIds;

  bool get essential => disclosureLevel == 'ESSENTIAL';
}

@immutable
class CaseContextSnapshot {
  const CaseContextSnapshot({
    required this.caseVersionId,
    required this.blocks,
    required this.sources,
  });

  final String caseVersionId;
  final List<CaseContextBlock> blocks;
  final List<CaseContextSource> sources;

  List<CaseContextBlock> get essentialBlocks =>
      blocks.where((block) => block.essential).toList(growable: false);

  List<CaseContextBlock> get detailBlocks =>
      blocks.where((block) => !block.essential).toList(growable: false);

  CaseContextSource? sourceById(String id) {
    for (final source in sources) {
      if (source.id == id) return source;
    }
    return null;
  }
}
