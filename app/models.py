from app import db

class Node(db.Model):
   id = db.Column(db.Integer, primary_key=True)
   ipaddr = db.Column(db.String(21), unique=True)   # 111.111.111.111:11111 is 21 chars total
   synced = db.Column(db.Boolean, default=False)
   
   to_dict(self):
      return dict(
         id = self.id,
         ipaddr = self.ipaddr,
         synced = self.synced
      )

   def __repr__(self):
      return '<Node %s>' % (self.ipaddr)
