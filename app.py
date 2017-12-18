from flask import Flask,request,abort,jsonify
from transform_rule import Transform_Rule
import json

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
tr = Transform_Rule()

@app.route("/transform", methods=['POST'])
def post_transform():
    response = {}
    if request.method != 'POST':
        abort(405, {'message': 'Method not allowed'})
    if request.headers['Content-Type'] != 'application/json':
        abort(400, {'message': 'Content-Type is not application/json'})
    if not request.data:
        abort(400, {'message': 'Invalid request'})

    request_data = json.loads(request.data)

    if not 'sentence' in request_data:
        abort(400, {'message': 'Invalid request'})

    tranform_sentence = tr.fit_rule_table(request_data['sentence'])
    response = {'tranform_sentence': tranform_sentence}
    return json.dumps(response)

@app.route("/learn", methods=['PUT','POST'])
def learning():
    response = {'success': True}

    if request.method not in ['POST','PUT']:
        abort(405, {'message': 'Method not allowed'})
    if request.method == 'POST': 
        if request.headers['Content-Type'] != 'application/json':
            abort(400, {'message': 'Content-Type is not application/json'})
        if not request.data:
            abort(400, {'message': 'Invalid request'})
    
    if request.method == 'PUT':
        tr.put_rule_table()
    # TODO: POSTは{'from_sentence':変換前単語,'to_sentence':変換後単語}で学習できる感じの

    return json.dumps(response)

@app.errorhandler(400)
@app.errorhandler(405)
def error_handler(error):
    """
    abort(400),abort(405) リクエストエラーのハンドラ
    """
    response = jsonify({'message': error.description, 'result': error.code})
    return response, error.code


if __name__ == "__main__":
    app.run()
