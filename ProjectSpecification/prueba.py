from flask import Flask, render_template, redirect, session, request, jsonify
from datetime import datetime
from go_analyzer_obo_plus_gaf_finished import GO_Tools
import threading

app = Flask(__name__) #nombre de la pagina

# Globals to hold tools and status
_tools = None
_tools_status = {
    "loading": False,
    "ready": False,
    "message": ""
}
_tools_lock = threading.Lock()

def _load_tools_bg(gaf_path: str, obo_path: str):
    global _tools, _tools_status
    with _tools_lock:
        _tools_status["loading"] = True
        _tools_status["ready"] = False
        _tools_status["message"] = ""
    try:
        # Heavy initialization happens here
        tools = GO_Tools(gaf_path, obo_path)
        message = getattr(tools, "loadGafMessage", "")
        with _tools_lock:
            _tools = tools
            _tools_status["message"] = message
            _tools_status["ready"] = True
    except Exception as ex:
        with _tools_lock:
            _tools_status["message"] = f"Error loading tools: {ex}"
            _tools_status["ready"] = False
    finally:
        with _tools_lock:
            _tools_status["loading"] = False

@app.route ('/')
def index():
    # today_date = datetime.now().strftime("%B %d, %y") #mostrar el tiempo, se actualiza
    # tools = GO_Tools('goa_human.gaf', 'go-basic.obo')

    return render_template('home.html')

@app.route('/start-tools', methods=['POST'])
def start_tools():
    gaf_file = 'goa_human.gaf'
    obo_file = 'go-basic.obo'
    with _tools_lock:
        if _tools_status["loading"] or _tools_status["ready"]:
            return jsonify(started=False, loading=_tools_status["loading"], ready=_tools_status["ready"])
        # Start background thread
        thread = threading.Thread(target=_load_tools_bg, args=(gaf_file, obo_file), daemon=True)
        thread.start()
        return jsonify(started=True, loading=True, ready=False)

@app.route('/tools-status')
def tools_status():
    with _tools_lock:
        return jsonify({
            "loading": _tools_status["loading"],
            "ready": _tools_status["ready"],
            "message": _tools_status["message"]
        })

@app.route('/GafColumnFiltering')
def gaf_column_filtering():
    return render_template('GafColumnFiltering.html')

# @app.route ('/SegundaPagina') #volver al home
# def SegundaPagina():
#     return render_template('SegundaPagina.html')

# @app.route ('/Logout') #manera alternativa de volver al home en caso de Logout
# def Logout():
#     return redirect('/')

if __name__ == '__main__': #close
    app.run()
    
#all FORM requests for html are variables in the 'request.form' dictionary
#an example can be user = request.form['user']\
#however, values in request.forme expire after refreshing, we can solve this using
#session containers that work on HTTP cookies
#an example can be: myuser = 'VincenzoRocco'
#                   session['user'] = myuser

#since both request.forms and sessions are variables, they are expressed with {{ variable }} in the html code