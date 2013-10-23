from app import app, db
import server, logging

def initLogger():
   # Log to console and websync.log
   logging.basicConfig(
      format='%(asctime)s %(message)s', 
      datefmt='%Y-%m-%d %H:%M:%S: ', 
      filename='websync.log', 
      level=logging.INFO)

   console = logging.StreamHandler()
   console.setLevel(logging.INFO)
   logging.getLogger().addHandler(console)

initLogger()
db.create_all()
server.start(app, 5000)
