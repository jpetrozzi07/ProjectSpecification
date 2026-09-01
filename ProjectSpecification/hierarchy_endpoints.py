from flask import Flask, render_template, request

app = Flask(__name__)


@app.route('/hierarchy')
def hierarchy():
 
    return render_template('HierarchySearch.html')

@app.route('/search_hierarchy', methods=['POST'])
def search_hierarchy():
 
    if request.method == 'POST':
        go_id = request.form.get('go_id')
 
        return render_template('HierarchySearch.html', searched_go=go_id)
    return render_template('HierarchySearch.html')