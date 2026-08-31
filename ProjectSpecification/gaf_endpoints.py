from flask import Blueprint, request, jsonify, current_app
import traceback

# Lazy-loaded parser singleton
_parser = None

gaf_bp = Blueprint('gaf', __name__)

def _get_parser():
    global _parser
    if _parser is None:
        # obtiene ruta del GAF desde la configuración de la app o usa el archivo por defecto
        gaf_path = current_app.config.get('GAF_FILEPATH', 'goa_human.gaf')
        try:
            import Gaf_parser_finished as gaf_mod
            _parser = gaf_mod.GafParser(gaf_path)
        except Exception as e:
            # deja la excepción para manejarla en la ruta
            raise
    return _parser

@gaf_bp.route('/gaf/search', methods=['POST'], endpoint='gaf_column_filtering_search')
def gaf_column_filtering_search():
    """
    Espera JSON: { "searcherIndex": <int or string index>, "query": "<search string>" }
    - mapea index a la lista de searchers de GafParser
    - ejecuta el searcher.search(query)
    - llama a parser._display_results(results, searcher, query) para mantener la lógica existente
    - devuelve JSON con los resultados (lista de registros)
    """
    try:
        payload = request.get_json(force=True) or {}
        try:
            idx = int(payload.get('searcherIndex', 0))
        except (TypeError, ValueError):
            return jsonify({'error': 'searcherIndex must be an integer'}), 400

        query = payload.get('query', '') or ''

        parser = _get_parser()

        # obtener keys en orden consistente (mismo orden que uses al renderizar la plantilla)
        keys = list(parser.searchers.keys())
        if idx < 0 or idx >= len(keys):
            return jsonify({'error': 'searcherIndex out of range', 'validRange': [0, len(keys)-1]}), 400

        searcher_key = keys[idx]
        searcher = parser.searchers[searcher_key]

        # ejecutar búsqueda y llamar al método existente
        results_df = searcher.search(query)

        # Llamada al método _display_results tal como solicitaste (imprime en servidor)
        try:
            parser._display_results(results_df, searcher, query)
        except Exception:
            # no detener la respuesta por errores en la impresión; registrar traza
            current_app.logger.exception("Error calling _display_results:")

        # convertir DataFrame a lista de registros JSON-serializables
        try:
            records = results_df.to_dict(orient='records') if hasattr(results_df, 'to_dict') else []
        except Exception:
            # fallback si la conversión falla
            current_app.logger.exception("Error converting results DataFrame to dict")
            records = []

        return jsonify({'count': len(records), 'results': records})
    except Exception as e:
        current_app.logger.error("Unhandled error in gaf_column_filtering_search: %s", e)
        return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500