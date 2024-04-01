

from flask import Flask, redirect, render_template, request, url_for
import requests
import psycopg2

app = Flask(__name__, static_folder='templates/', static_url_path='')

db_host = 'localhost'
db_port = 5432 
db_name = 'DATABASe_NOM'
db_user = 'postgres'    #A changer si different dans votre base de donnée (Utiliser POSTGRES)
db_password = '1234'    #ca aussi



@app.route('/',methods=['POST','GET'])
def home():
      
    message = "hello"
 
    return render_template('index.html',message = message)

@app.route('/auteur',methods=['POST','GET'])
def auteur():
    conn = psycopg2.connect(host=db_host, port=db_port, database=db_name, user=db_user, password=db_password)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM auteur")
    result = cursor.fetchall()

    return render_template('auteur.html', result=result)

if __name__ == '__main__':
     
      app.run(debug=True)