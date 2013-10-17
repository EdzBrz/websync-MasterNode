from flask import Flask, jsonify, request, abort
from app import app, db
from app.models import Node

@app.route('/', methods = ['GET'])
def all_nodes():
   ns = Node.query.all()
   nsdict = []
   for n in ns:
      nsdict.append(n.to_dict())
   return jsonify ({'Nodes': nsdict})

# POST containing JSON field {'port': <port number> }
@app.route('/', methods = ['POST'])
def add_node():
   if request.json:
      n = Node(ipaddr='http://'+(request.remote_addr)+(':')+str(request.json['port'])+('/'))
      db.session.add(n)
      db.session.commit()
      return jsonify ({'Node': n.id}), 201

   else:
      abort(400)

@app.route('/<int:id>/', methods = ['DELETE'])
def delete_node(id):
   n = Node.query.get(id)
   db.session.delete(n)
   db.session.commit()
   return jsonify ( {'Deleted Node':id} ), 200

# Used for newly created CoreOS VM on OpenStack to get correct docker container
# Might use dockers own repo system for this though
@app.route('/docker', methods = ['GET'])
def get_docker():
   return ""
