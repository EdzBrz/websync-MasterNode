from app import app, db
db.create_all()
app.run('0.0.0.0',debug=True)
