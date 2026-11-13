// Abratel Suporte: lista de atendentes na tela inicial (abaixo do ID e da senha).
// Copiado para flutter/lib/desktop/widgets/ pelo aplicar-marca.py, que troca o marcador de kAbratelPortal pelo endereço do portal
// (ex.: https://suporte.exemplo.com.br/empresa), vindo do secret HALLO_PORTAL. Lê GET <portal>/api/tecnicos, a mesma lista pública do portal, e o botão
// abre o portal no navegador com o ID deste computador (e o atendente escolhido) já preenchidos.
import 'dart:async';
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_hbb/common.dart';
import 'package:http/http.dart' as http;
import 'package:url_launcher/url_launcher.dart';

const String kAbratelPortal = '__HALLO_PORTAL__';

class _Atendente {
  final int id;
  final String nome;
  final String especialidade;
  final String codigo;
  final String texto;
  _Atendente(this.id, this.nome, this.especialidade, this.codigo, this.texto);
}

class AbratelAtendentes extends StatefulWidget {
  const AbratelAtendentes({Key? key}) : super(key: key);

  @override
  State<AbratelAtendentes> createState() => _AbratelAtendentesState();
}

class _AbratelAtendentesState extends State<AbratelAtendentes> {
  static const _ordem = <String, int>{
    'disponivel': 0,
    'ocupado': 1,
    'pausa': 2,
    'offline': 3,
    'fora': 4,
  };
  List<_Atendente> _lista = [];
  bool _carregou = false;
  bool _erro = false;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _carregar();
    _timer = Timer.periodic(const Duration(seconds: 20), (_) => _carregar());
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  Future<void> _carregar() async {
    try {
      final r = await http
          .get(Uri.parse('$kAbratelPortal/api/tecnicos'))
          .timeout(const Duration(seconds: 10));
      if (r.statusCode != 200) throw Exception('HTTP ${r.statusCode}');
      final dados = jsonDecode(utf8.decode(r.bodyBytes)) as List<dynamic>;
      final lista = <_Atendente>[];
      for (final e in dados) {
        final m = e as Map<String, dynamic>;
        final d = (m['disponibilidade'] as Map<String, dynamic>?) ?? {};
        lista.add(_Atendente(
          (m['id'] as num).toInt(),
          '${m['nome'] ?? ''}',
          '${m['especialidade'] ?? ''}',
          '${d['codigo'] ?? ''}',
          '${d['texto'] ?? ''}',
        ));
      }
      lista.sort((a, b) => (_ordem[a.codigo] ?? 9).compareTo(_ordem[b.codigo] ?? 9));
      if (!mounted) return;
      setState(() {
        _lista = lista;
        _carregou = true;
        _erro = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _carregou = true;
        _erro = true;
      });
    }
  }

  Color _cor(String codigo) {
    switch (codigo) {
      case 'disponivel':
        return Colors.green;
      case 'ocupado':
        return Colors.orange;
      case 'pausa':
        return Colors.amber;
      default:
        return Colors.grey;
    }
  }

  void _pedirSuporte([int? atendente]) {
    final id = gFFI.serverModel.serverId.text.replaceAll(RegExp(r'\D'), '');
    final params = <String, String>{};
    if (id.isNotEmpty) params['id'] = id;
    if (atendente != null) params['tecnico'] = '$atendente';
    final uri = Uri.parse('$kAbratelPortal/')
        .replace(queryParameters: params.isEmpty ? null : params);
    launchUrl(uri, mode: LaunchMode.externalApplication);
  }

  @override
  Widget build(BuildContext context) {
    final pequeno = Theme.of(context).textTheme.bodySmall;
    final online = _lista.where((a) => a.codigo == 'disponivel').length;
    final linhas = <Widget>[];
    if (!_carregou) {
      linhas.add(Text('Carregando...', style: pequeno));
    } else if (_erro) {
      linhas.add(Text('Sem conexão com o portal de suporte.', style: pequeno));
    } else if (_lista.isEmpty) {
      linhas.add(Text('Nenhum atendente cadastrado.', style: pequeno));
    } else {
      for (final a in _lista) {
        final detalhe =
            a.especialidade.isNotEmpty ? '${a.texto} · ${a.especialidade}' : a.texto;
        linhas.add(InkWell(
          onTap: () => _pedirSuporte(a.id),
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: 4),
            child: Row(
              children: [
                Container(
                  width: 9,
                  height: 9,
                  decoration: BoxDecoration(
                      color: _cor(a.codigo), shape: BoxShape.circle),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(a.nome, overflow: TextOverflow.ellipsis),
                      Text(detalhe,
                          style: pequeno, overflow: TextOverflow.ellipsis),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ));
      }
    }
    return Container(
      margin: const EdgeInsets.only(left: 20, right: 11, top: 14, bottom: 6),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Expanded(
                child: Text('Atendentes',
                    style: TextStyle(fontWeight: FontWeight.bold)),
              ),
              if (_carregou && !_erro) Text('$online online', style: pequeno),
            ],
          ),
          const SizedBox(height: 6),
          ...linhas,
          const SizedBox(height: 8),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: () => _pedirSuporte(),
              child: const Text('Pedir suporte'),
            ),
          ),
        ],
      ),
    );
  }
}
