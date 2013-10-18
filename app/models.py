from app import db

class Node(db.Model):
   id = db.Column(db.Integer, primary_key=True)
   ipaddr = db.Column(db.String(), unique=True)   # 111.111.111.111:11111 is 21 chars total
   synced = db.Column(db.Boolean, default=False)
   
   def to_dict(self):
      return dict(
         id = self.id,
         ipaddr = self.ipaddr,
         synced = self.synced,
         files = str(self.files)
      )

   def __repr__(self):
      return '<Node %s>' % (self.ipaddr)

class NodeFile(db.Model):
   id = db.Column(db.Integer, primary_key=True)
   fileid = db.Column(db.Integer)
   timestamp = db.Column(db.DateTime)
   node_id = db.Column(db.Integer, db.ForeignKey('node.id'), nullable=False)
   node = db.relationship('Node', backref='files')
   
   def __repr__(self):
      return 'File %s' % (self.fileid)
