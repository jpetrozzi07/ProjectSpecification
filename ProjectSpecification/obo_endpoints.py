from flask import Blueprint, request, jsonify, current_app
import traceback
import math
import numpy as np

# Lazy-loaded parser singleton
_parser = None

obo_bp = Blueprint('obo', __name__)

def _get_parser():
    global _parser
    if _parser is None:
        # obtiene ruta del GAF desde la configuración de la app o usa el archivo por defecto
        obo_path = current_app.config.get('OBO_FILEPATH', 'go-basic.obo')
        try:
            import obo_parser as obo_mod
            _parser = obo_mod.OboParser(obo_path)
        except Exception as e:
            # deja la excepción para manejarla en la ruta
            raise
    return _parser

def _sanitize_value(v):
    # Convierte numpy scalars a tipos nativos
    if isinstance(v, np.generic):
        try:
            v = v.item()
        except Exception:
            # fallback a string si no se puede convertir
            return str(v)
    # Reemplaza NaN e Inf por None (que se serializa a null en JSON)
    if isinstance(v, float):
        if math.isnan(v) or math.isinf(v):
            return None
        return v
    # Deja pasar dicts/lists para procesarlos recursivamente
    if isinstance(v, dict):
        return {k: _sanitize_value(val) for k, val in v.items()}
    if isinstance(v, list):
        return [_sanitize_value(i) for i in v]
    return v

def _sanitize_record(rec):
    if isinstance(rec, dict):
        return {k: _sanitize_value(v) for k, v in rec.items()}
    if isinstance(rec, list):
        return [_sanitize_value(i) for i in rec]
    return _sanitize_value(rec)

@obo_bp.route('/obo/search', methods=['POST'], endpoint='obo_column_filtering_search')
def obo_column_filtering_search():
    """
    Espera JSON: { "searcherIndex": <int or string index>, "query": "<search string>" }
    - mapea index a la lista de searchers de OboParser
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

        # Sanitize: reemplaza NaN/Inf y convierte numpy scalars para producir JSON válido
        try:
            sanitized = [_sanitize_record(r) for r in records]
        except Exception:
            current_app.logger.exception("Error sanitizing records before jsonify")
            sanitized = records  # enviar lo que haya como último recurso

        return jsonify({'count': len(sanitized), 'results': sanitized})
    except Exception as e:
        current_app.logger.error("Unhandled error in obo_column_filtering_search: %s", e)
        return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500