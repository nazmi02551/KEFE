import 'dart:convert';

import 'package:http/http.dart' as http;

import '../../decision/data/http_decision_repository.dart';
import '../domain/signal_consensus_card_models.dart';
import 'signal_repository.dart';

class HttpSignalRepository implements SignalRepository {
  HttpSignalRepository({required this.baseUrl, http.Client? client})
    : _client = client ?? http.Client();

  final String baseUrl;
  final http.Client _client;

  @override
  Future<List<SignalConsensusCardModel>> fetchSignalConsensusCards() async {
    final uri = Uri.parse('$baseUrl/v1/signals/consensus-cards');
    final response = await _client.get(
      uri,
      headers: {'Accept': 'application/json'},
    );

    if (response.statusCode != 200) {
      throw ApiFailure('FAILED_TO_FETCH_SIGNAL_CARDS', response.statusCode);
    }

    final body = jsonDecode(utf8.decode(response.bodyBytes)) as List<dynamic>;
    return body
        .map(
          (item) =>
              SignalConsensusCardModel.fromJson(item as Map<String, dynamic>),
        )
        .toList(growable: false);
  }
}
