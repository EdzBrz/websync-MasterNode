from flask import Flask, jsonify, request, abort
from app import app, db
from app.models import Node, NodeFile
import datetime
from pprint import pprint

@app.route('/', methods = ['GET'])
@app.route('/nodes', methods = ['GET'])
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

@app.route('/post/', methods = ['POST'])
def add_file():
   if request.json:
      nodeURL = 'http://'+(request.remote_addr)+':'+str(request.json['port'])+'/'
      ts = datetime.datetime.strptime(request.json['timestamp'], '%Y-%m-%d %H:%M:%S.%f')
      n = db.session.query(Node).filter(Node.ipaddr == nodeURL).first()
      nf = NodeFile(fileid=int(request.json['fileid']), timestamp=ts, node_id=n.id)
      db.session.add(nf)
      db.session.commit()
      return jsonify({'File added': nf.fileid }), 201

# 2013-10-18 14:24:33.399822
#ns = db.session.query(Node).filter(Node.ipaddr != 'http://'+(request.remote_addr)+':'+str(request.json['port'])+'/'))

@app.route('/put/', methods = ['POST'])
def update_file():
   return ""

@app.route('/delete/', methods = ['POST'])
def delete_file():
   nodeURL = 'http://'+(request.remote_addr)+':'+str(request.json['port'])+'/'
   n = db.session.query(Node).filter(Node.ipaddr == nodeURL).first()
   nf = db.session.query(Nodefile).filter(node_id=='')
   return ""

# Used for newly created CoreOS VM on OpenStack to get correct docker container
# Might use dockers own repo system for this though
@app.route('/docker', methods = ['GET'])
def get_docker():
   return ""
