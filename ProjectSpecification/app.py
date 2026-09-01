from datetime import datetime
from go_analyzer_obo_plus_gaf_finished import GO_Tools
import threading
from flask import Flask, render_template, jsonify, current_app
import tools_state

from Gaf_parser_finished import GafParser
from gaf_endpoints import gaf_bp
from obo_endpoints import obo_bp
from neighborhood_endpoints import neighborhood_bp
from similarity_endpoints import similarity_bp
from matrix_endpoints import matrix_bp

app = Flask(__name__)  # nombre de la pagina
app.register_blueprint(gaf_bp)
app.register_blueprint(obo_bp)
app.register_blueprint(neighborhood_bp)
app.register_blueprint(similarity_bp)
app.register_blueprint(matrix_bp)

def _load_tools_bg(gaf_path: str, obo_path: str):
    # Use attributes on the tools_state module to avoid import-time cycles
    # and ensure we mutate the shared state in one place.
    with app.app_context():
        with tools_state._tools_lock:
            tools_state._tools_status["loading"] = True
            tools_state._tools_status["ready"] = False
            tools_state._tools_status["messageGaf"] = ""
            tools_state._tools_status["messageObo"] = ""
        try:
            current_app.logger.info("Loading GO_Tools in background: gaf=%s obo=%s", gaf_path, obo_path)
            tools = GO_Tools(gaf_path, obo_path)
            messageGaf = getattr(tools, "loadGafMessage", "")
            messageObo = getattr(tools, "loadOboMessage", "")
            with tools_state._tools_lock:
                tools_state._tools = tools
                tools_state._tools_status["messageGaf"] = messageGaf
                tools_state._tools_status["messageObo"] = messageObo
                tools_state._tools_status["ready"] = True
            current_app.logger.info("GO_Tools loaded successfully")
        except Exception as ex:
            current_app.logger.exception("Error loading GO_Tools:")
            with tools_state._tools_lock:
                tools_state._tools_status["messageGaf"] = f"Error loading Gaf file: {ex}"
                tools_state._tools_status["messageObo"] = f"Error loading Obo file: {ex}"
                tools_state._tools_status["ready"] = False
        finally:
            with tools_state._tools_lock:
                tools_state._tools_status["loading"] = False


@app.route('/')
def index():
    return render_template('home.html')


@app.route('/start-tools', methods=['POST'])
def start_tools():
    gaf_file = 'goa_human.gaf'
    obo_file = 'go-basic.obo'
    with tools_state._tools_lock:
        if tools_state._tools_status["loading"] or tools_state._tools_status["ready"]:
            return jsonify(started=False, loading=tools_state._tools_status["loading"], ready=tools_state._tools_status["ready"])
        thread = threading.Thread(target=_load_tools_bg, args=(gaf_file, obo_file), daemon=True)
        thread.start()
        return jsonify(started=True, loading=True, ready=False)


@app.route('/tools-status')
def tools_status():
    with tools_state._tools_lock:
        return jsonify({
            "loading": tools_state._tools_status["loading"],
            "ready": tools_state._tools_status["ready"],
            "messageGaf": tools_state._tools_status["messageGaf"],
            "messageObo": tools_state._tools_status["messageObo"]
        })


@app.route('/GafColumnFiltering')
def gaf_column_filtering():
    with tools_state._tools_lock:
        if not tools_state._tools or not tools_state._tools_status["ready"]:
            return render_template('GafColumnFiltering.html', searchers={})
        searchers = getattr(tools_state._tools, "gaf").searchers
    return render_template('GafColumnFiltering.html', searchers=searchers)


@app.route('/OboColumnFiltering')
def obo_column_filtering():
    with tools_state._tools_lock:
        if not tools_state._tools or not tools_state._tools_status["ready"]:
            return render_template('OboColumnFiltering.html', searchers={})
        searchers = getattr(tools_state._tools, "obo").searchers
    return render_template('OboColumnFiltering.html', searchers=searchers)


@app.route('/SimilarityCalculationsViewer')
def similarity_viewer():
    return render_template('SimilarityCalculationsViewer.html')


@app.route('/NeighborhoodViewer')
def neighborhood_viewer():
    return render_template('NeighborhoodViewer.html')


@app.route('/ViewingAnnotationMatrix')
def annotation_matrix_viewer():
    return render_template('ViewingAnnotationMatrix.html')


@app.route('/SoftwareInstructions')
def instructions_viewer():
    return render_template('SoftwareInstructions.html')


if __name__ == '__main__':
    app.run()