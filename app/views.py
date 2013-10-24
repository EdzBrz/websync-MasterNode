from flask import Flask, jsonify, request, abort
from app import app, db
from app.models import Node, NodeFile
import datetime, requests, json, logging
from decorators import async
from pprint import pprint
from sqlalchemy.exc import IntegrityError

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
         #TODO: Nodes returns to network when not properly turned off, need to check its files for conflicts
         #pprint('Node already in network!')
         db.session.rollback()
         n = db.session.query(Node).filter(Node.ipaddr==ip).first()
         #conflict_check(n)
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
      db.session.add(nf)
      db.session.commit()
      #pprint('POST From: '+str(nodeURL)+' File: '+str(request.json['fileid']))
      set_sync()
      return jsonify({'File added': nf.fileid }), 201

@app.route('/put/', methods = ['POST'])
def update_file():
   if request.json:
      nodeURL = 'http://'+(request.remote_addr)+':'+str(request.json['port'])+'/'
      ts = datetime.datetime.strptime(request.json['timestamp'], '%Y-%m-%d %H:%M:%S.%f')
      n = db.session.query(Node).filter(Node.ipaddr == nodeURL).first()
      nfs = NodeFile.query.filter(NodeFile.fileid==int(request.json['fileid']))
      for nf in nfs:
         if nf.node == n:
            nf.timestamp = ts
            db.session.commit()
      #pprint('PUT From: '+str(nodeURL)+' File: '+str(request.json['fileid']))
      set_sync()
      return jsonify({'File updated': int(request.json['fileid']) }), 201

@app.route('/delete/', methods = ['POST'])
def delete_file():
   nodeURL = 'http://'+(request.remote_addr)+':'+str(request.json['port'])+'/'
   ts = datetime.datetime.strptime(request.json['timestamp'], '%Y-%m-%d %H:%M:%S.%f')
   nfs = db.session.query(NodeFile).filter(NodeFile.fileid == int(request.json['fileid']))
   for nf in nfs:
      if nf.timestamp > ts:
         abort(400)
      # Mark nodefile for deletion
      if nf.node.ipaddr == nodeURL:
         db.session.delete(nf)
      nf.timestamp = datetime.datetime(1,1,1,1,1,1,1)
   #pprint('DELETE From: '+str(nodeURL)+' File: '+str(request.json['fileid']))
   set_sync()
   db.session.commit()

   # When deleting file, set dummy datetime on deleted fileID. Will be ignored on sync and will be replaced by all time comparisons
   global filestamps
   #pprint(int(request.json['fileid']))
   try:
      filestamps[int(request.json['fileid'])] = datetime.datetime(1,1,1,1,1,1,1)
   except IndexError:
      filestamps.append(datetime.datetime(1,1,1,1,1,1,1))
   return jsonify({'File removed': int(request.json['fileid'])}), 200

@app.route('/next/', methods = ['GET'])
def get_next_file_id():
   return jsonify ({'nextID': (len(filestamps))})

@app.route('/sync/', methods = ['GET'])
def force_sync():
   push_changes()
   return jsonify ({'Syncing': '!'}), 200

# Set sync booleans for all nodes to correct state of node
def set_sync():
# Go through all files on all nodes and update global filestamps array to have all the newest timestamps for all fileIDs
   nodes = Node.query.all()
   global filestamps
   for n in nodes:
      for f in (n.files):
         try:
            if f.timestamp > filestamps[f.fileid]:
               filestamps[f.fileid] = f.timestamp
         except IndexError:
            filestamps.append(f.timestamp)
   #pprint('MasterServer Timestamps: '+str(filestamps))   
# Go through all nodes and files again and set synced bool on node
   for n in nodes:
      # Node has less files than server list
      if len(n.files) < file_count():
         n.synced = False
         #pprint('Node :'+str(n.ipaddr)+' unsynced: has less files than master')
         db.session.add(n)
         continue
      # Iterate over files and compare them to newest
      for f in (n.files):
         if f.timestamp < filestamps[f.fileid] or f.timestamp == datetime.datetime(1,1,1,1,1,1,1):
            n.synced = False
            #pprint('Node '+str(n.ipaddr)+' File: '+str(f.fileid)+' unsynced: older file than master')
            break
         n.synced = True
         #pprint('Node '+str(n.ipaddr)+' File: '+str(f.fileid)+' synced!')
      db.session.add(n)
   db.session.commit()
            
def file_count():
   x = [elem for elem in filestamps if elem != datetime.datetime(1,1,1,1,1,1,1)]
   return len(x)

def file_ids():
   filelist = []
   for elem in filestamps:
      if elem != datetime.datetime(1,1,1,1,1,1,1):
         filelist.append(filestamps.index(elem))
   return filelist

     
#TODO: FIX THIS, query doesnt become empty list even if all nodes are synced
def push_changes():
   receivers = db.session.query(Node).filter(Node.synced == False)
   send_list = []
   files = file_ids()
   #TODO: Sync logic here
   for r in receivers:
      nodefiles = [] 
      for f in r.files:
         nodefiles.append(f.fileid)       
         if f.timestamp < filestamps[f.fileid]:
            send_list.append((r,f.fileid,'put'))

         elif f.timestamp == datetime.datetime(1,1,1,1,1,1,1):
            send_list.append((r,f.fileid,'delete'))

      #pprint('Push Changes: Nodefiles: '+str(nodefiles)+' For node: '+str(r.id))
      postfiles = list(set(files)-set(nodefiles))
      for p in postfiles:
         send_list.append((r,p,'post'))
      
   pprint('Filestamps:'+str(filestamps))
   pprint('Send list: '+str(send_list))
   for s in send_list:
      node_sender(*s)

# Sends one command to a node 
@async 
def node_sender(node, fileid, method):
   headers = {'content-type': 'application/json'}
   #pprint('Node sender: '+str(node.ipaddr)+' Fileid: '+str(fileid)+' Method: '+str(method))
   if method == 'delete':
      data={'global_id':fileid}
      requests.delete(str(node.ipaddr)+'blob/'+str(fileid)+'/', data=json.dumps(data), headers=headers)
   else:   
      data={'nodeurl':node.ipaddr, 'fileid':fileid, 'method': method}
      headers = {'content-type': 'application/json'}
      # Get node with synced file
      # TODO: Add logic for which node has to send, now it only takes the first one with the correct file
      n = db.session.query(NodeFile).filter(NodeFile.fileid == fileid).filter(NodeFile.timestamp == filestamps[fileid]).first()
      if n:
         url = n
         tarURL = url.node.ipaddr + 'mn/'
         requests.get(tarURL, data=json.dumps(data), headers=headers)
      else:
         filestamps[fileid] = datetime.datetime(1,1,1,1,1,1,1)
# Compare timestamps from master and returned node for conflicts
def conflict_check(node):
   timestamp_list = []
   for f in node.files:
      timestamp_list.append(f.timestamp)
      r = requests.get(str(node.ipaddr)+'reconnect')
   
   





