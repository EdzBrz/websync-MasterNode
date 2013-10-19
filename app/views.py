from flask import Flask, jsonify, request, abort
from app import app, db
from app.models import Node, NodeFile
import datetime
from decorators import async
from pprint import pprint
from sqlalchemy.exc import IntegrityError

# Index-1 is FileID and element is timestamp for the newest version of the file
filestamps = []

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
      ip = 'http://'+(request.remote_addr)+(':')+str(request.json['port'])+('/')
      try:   
         n = Node(ipaddr=ip)
         db.session.add(n)
         db.session.commit()         
      except IntegrityError:
         #TODO: Nodes returns to network when not properly turned off, need to check its files for sync
         pprint('Node already in network!')
         db.session.rollback()
         n = db.session.query(Node).filter(Node.ipaddr==ip).first()
      return jsonify ({'Node': n.id}), 201 
   else:
      abort(400)

@app.route('/<int:id>/', methods = ['DELETE'])
def delete_node(id):
   n = Node.query.get(id)
   for nf in n.files:
      db.session.delete(nf)
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
      db.session.add(n)
      db.session.add(nf)
      db.session.commit()
      set_sync()
      return jsonify({'File added': nf.fileid }), 201

@app.route('/put/', methods = ['POST'])
def update_file():
   return ""

@app.route('/delete/', methods = ['POST'])
def delete_file():
   nodeURL = 'http://'+(request.remote_addr)+':'+str(request.json['port'])+'/'
   ts = datetime.datetime.strptime(request.json['timestamp'], '%Y-%m-%d %H:%M:%S.%f')
   nfs = db.session.query(NodeFile).filter(NodeFile.fileid == int(request.json['fileid']))
   for nf in nfs:
      if nf.timestamp > ts:
         abort(400)
      db.session.delete(nf)
   db.session.commit()

   # When deleting file, set dummy datetime on deleted fileID. Will be ignored on sync and will be replaced by all time comparisons
   global filestamps
   filestamps[int(request.json['fileid'])-1] = datetime.datetime(1,1,1,1,1,1,1)
   set_sync()

   return jsonify({'File removed': int(request.json['fileid'])}), 201

# Used for newly created CoreOS VM on OpenStack to get correct docker container
# Might use dockers own repo system for this though
@app.route('/docker', methods = ['GET'])
def get_docker():
   return ""

# Set sync booleans for all nodes to correct state of node
@async
def set_sync():
# Go through all files on all nodes and update global filestamps array to have all the newest timestamps for all fileIDs
   nodes = Node.query.all()
   global filestamps
   for n in nodes:
      for f in (n.files):
         try:
            if f.timestamp > filestamps[f.fileid-1]:
               filestamps[f.fileid-1] = f.timestamp
         except IndexError:
            filestamps.append(f.timestamp)
   pprint(filestamps)

# Go through all nodes and files again and set synced bool on node
   for n in nodes:
      # Node has less files than server list
      if len(n.files) < file_count():
         n.synced = False
         db.session.add(n)
         continue
      # 
      for f in (n.files):
         if f.timestamp < filestamps[f.fileid-1]:
            n.synced = False
            pprint('unsynced')
            break
         n.synced = True
         pprint('synced')
      db.session.add(n)
   db.session.commit()
            

def file_count():
   x = [elem for elem in filestamps if elem != datetime.datetime(1,1,1,1,1,1,1)]
   return len(x)
     
#TODO: FIX THIS, query doesnt become empty list even if all nodes are synced
def check_sync():
   derp = db.session.query(Node).filter(Node.synced == 'false')
   if derp:
      pprint('Starting Sync')
   else:
      pprint('Nothing to see here')
   
   
