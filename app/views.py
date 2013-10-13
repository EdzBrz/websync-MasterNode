from flask import Flask, jsonify, request, abort
from app import app, db
from app.models import Node
from pprint import pprint

@app.route('/', methods = ['GET'])
def all_nodes():
   ns = Node.query.all()
   nsdict = []
   for n in ns:
      nsdict.append(n.to_dict())
   return jsonify ({'Nodes': nsdict})

# POST containing JSON field {'ip': 'ip:port' }
@app.route('/', methods = ['POST'])
def add_node():
   if request.json and 'ip' in request.json:
      pprint('asdasd')
      n = Node(ipaddr=request.json['ip'])
      db.session.add(n)
      db.session.commit()
      return jsonify ({'Node': n.id}), 201
   else:
      abort(400)


# Used for newly created CoreOS VM on OpenStack to get correct docker container
@app.route('/docker', methods = ['GET'])
def get_docker():
   return ""
