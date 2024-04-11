

from flask import Flask, redirect, render_template, request, url_for, session, jsonify
from flask_session import Session
from datetime import date

import requests
import psycopg2

app = Flask(__name__, static_folder='templates/', static_url_path='')


app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_USE_SIGNER'] = True  # Optionnel : pour signer les cookies de session
Session(app)

db_host = 'localhost'
db_port = 5432 
db_name = 'db_festival'
db_user = 'postgres'    #A changer si different dans votre base de donnée (Utiliser POSTGRES)
db_password = 'achraf-00'    #ca aussi
app.secret_key = 'supersecretkey'

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/logout")
def logout():
    session.pop('id_utilisateur', None)
    return render_template('index.html')

@app.route("/login",methods=['POST','GET'])
def login():
    email = request.form['email']
    password = request.form['password']
    conn = psycopg2.connect(host=db_host, port=db_port, database=db_name, user=db_user, password=db_password)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM connexion WHERE id_utilisateur = %s AND mdp= %s",(email,password))
    user = cursor.fetchone()  # Récupérer une seule ligne du résultat
    
    if user:  # Si un utilisateur correspondant est trouvé
        # Rediriger vers l'URL 'auteur' après une connexion réussie
        session['id_utilisateur'] = user[0]
        conn.close()
        return redirect(url_for('home'))
    
    else:
        # Gérer le cas où aucun utilisateur correspondant n'est trouvé
        error_message = "Adresse e-mail ou mot de passe incorrect."
        return render_template('index.html', error_message=error_message)

#statu voeux
@app.route("/edit_voeux",methods=['POST','GET'])
def edit_voeux():
    # Extraction de la valeur de l'ID de l'ouvrage
    if 'id_utilisateur' in session:
        id_utilisateur = session['id_utilisateur']
        id_voeu = request.form['id_voeu']
        voeu_statut = request.form['voeu_statut']
        conn = psycopg2.connect(host=db_host, port=db_port, database=db_name, user=db_user, password=db_password)
        cursor = conn.cursor()
        cursor.execute("SELECT entite_connectee FROM Connexion WHERE id_utilisateur = %s", (id_utilisateur,))
        role_connected = cursor.fetchone()[0]
        cursor.execute("UPDATE voeux SET statut = %s WHERE id_voeux = %s", (voeu_statut, id_voeu))
        conn.commit()
        cursor.execute("SELECT * FROM voeux", ())
        voeux = cursor.fetchall()
        return render_template('voeux.html', voeux=voeux, role_connected=role_connected)
    else:
        # Si aucun utilisateur n'est connecté, rediriger vers la page de connexion
        return redirect(url_for('login'))

@app.route("/edit_ouvrage",methods=['POST','GET'])
def edit_ouvrage():
    # Extraction de la valeur de l'ID de l'ouvrage
    if 'id_utilisateur' in session:
        id_ouvrage = request.form['id_ouvrage']
        date_actuelle = date.today()
        conn = psycopg2.connect(host=db_host, port=db_port, database=db_name, user=db_user, password=db_password)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ouvrage WHERE id_ouvrage = %s", (id_ouvrage,))
        ouvrage = cursor.fetchone()
        return render_template('edit_ouvrage.html', ouvrage=ouvrage, date_actuelle=date_actuelle)
    else:
        # Si aucun utilisateur n'est connecté, rediriger vers la page de connexion
        return redirect(url_for('login'))
    
@app.route("/edit_ouvrage_done",methods=['POST','GET'])
def edit_ouvrage_done():
    # Extraction de la valeur de l'ID de l'ouvrage
    if 'id_utilisateur' in session:
        id_ouvrage = request.form['id_ouvrage']  
        date_edition = request.form['date_edition'] or None
        lieu_edition = request.form['lieu_edition'] or None
        genre = request.form['genre'] or None 
  
        print('jjjj',id_ouvrage,'dat', date_edition)
        conn = psycopg2.connect(host=db_host, port=db_port, database=db_name, user=db_user, password=db_password)
        cursor = conn.cursor()
        cursor.execute("UPDATE ouvrage SET dateedition = %s, lieuedition = %s, genre = %s WHERE id_ouvrage = %s", (date_edition, lieu_edition, genre, id_ouvrage))
        conn.commit()
        conn.close()
        return redirect(url_for('ouvrages'))

    else:
        # Si aucun utilisateur n'est connecté, rediriger vers la page de connexion
        return redirect(url_for('login'))
@app.route('/home',methods=['POST','GET'])
def home():
    if 'id_utilisateur' in session:
        id_utilisateur = session['id_utilisateur']
        conn = psycopg2.connect(host=db_host, port=db_port, database=db_name, user=db_user, password=db_password)
        cursor = conn.cursor()
        cursor.execute("SELECT entite_connectee FROM Connexion WHERE id_utilisateur = %s", (id_utilisateur,))
        role_connected = cursor.fetchone()[0]

        #switching the home page depending on the connected role
        if role_connected=='auteur':
            cursor.execute("SELECT auteur.nom FROM Connexion INNER JOIN auteur ON Connexion.id_auteur = auteur.id_auteur WHERE Connexion.id_utilisateur = %s", (id_utilisateur,))
            nom_connected = cursor.fetchone()[0]
            conn.close()
            return render_template('auteur.html',auteur_nom=nom_connected,)
        
        elif role_connected=='etablissement':
            cursor.execute("SELECT etablissement.nom, etablissement.idreferent FROM Connexion INNER JOIN etablissement ON Connexion.id_etablissement = etablissement.idetablissement WHERE Connexion.id_utilisateur = %s", (id_utilisateur,))
            row = cursor.fetchone()
            if row is not None:
                nom_connected = row[0]
                referent_connected = row[1]
            conn.close()
            return render_template('etablissement.html',etab_nom=nom_connected, referent_connected=referent_connected)
        
        elif role_connected=='accompagnateur':
            cursor.execute("SELECT accompagnateur.nom FROM Connexion INNER JOIN accompagnateur ON Connexion.id_accompagnateur = accompagnateur.idaccompagnateur WHERE Connexion.id_utilisateur = %s", (id_utilisateur,))
            nom_connected = cursor.fetchone()[0]
            conn.close()
            return render_template('accompagnateur.html',accomp_nom=nom_connected,)
        
        elif role_connected=='interprete':
            cursor.execute("SELECT interprete.nom FROM Connexion INNER JOIN interprete ON Connexion.id_interprete = interprete.id_interprete WHERE Connexion.id_utilisateur = %s", (id_utilisateur,))
            nom_connected = cursor.fetchone()[0]
            conn.close()
            return render_template('interprete.html',interp_nom=nom_connected,)
        elif role_connected=='admin':
            conn.close()
            return render_template('admin.html')
        
        else:
            error_message = "ERROR : le role connecté est inconnu !"
            conn.close()
            return render_template('index.html', error_message=error_message)        
    else:
        # Si aucun utilisateur n'est connecté, rediriger vers la page de connexion
        return redirect(url_for('login'))

@app.route('/profil',methods=['POST','GET'])
def profil():
    if 'id_utilisateur' in session:
        id_utilisateur = session['id_utilisateur']
        conn = psycopg2.connect(host=db_host, port=db_port, database=db_name, user=db_user, password=db_password)
        cursor = conn.cursor()
        cursor.execute("SELECT entite_connectee FROM Connexion WHERE id_utilisateur = %s", (id_utilisateur,))
        role_connected = cursor.fetchone()[0]

        #switching the home page depending on the connected role
        if role_connected=='auteur':
            cursor.execute("SELECT auteur.nom, auteur.prenom, auteur.adresse, auteur.mail FROM Connexion INNER JOIN auteur ON Connexion.id_auteur = auteur.id_auteur WHERE Connexion.id_utilisateur = %s", (id_utilisateur,))
            row = cursor.fetchone()
            if row is not None:
                nom_connected = row[0]
                prenom_connected = row[1]
                adresse_connected = row[2]
                mail_connected = row[3]         
            conn.close()
            return render_template('profil.html',auteur_nom=nom_connected, auteur_prenom=prenom_connected, auteur_adresse=adresse_connected, auteur_mail=mail_connected, role_connected=role_connected)
        
        elif role_connected == 'etablissement':
            cursor.execute("SELECT etablissement.nom, etablissement.idreferent, etablissement.etabtype, etablissement.adresse, connexion.id_utilisateur FROM Connexion INNER JOIN etablissement ON Connexion.id_etablissement = etablissement.idetablissement WHERE Connexion.id_utilisateur = %s", (id_utilisateur,))
            row = cursor.fetchone()
            if row is not None:
                nom_connected = row[0]
                referent_connected = row[1]
                etabtype_connected = row[2]
                adresse_connected = row[3]
                mail_connected = row[4]
                conn.close()
                return render_template('profil.html', etab_nom=nom_connected, referent_connected=referent_connected, etab_type=etabtype_connected, etab_adresse=adresse_connected, etab_mail=mail_connected, role_connected=role_connected)
            
        elif role_connected == 'accompagnateur':
            cursor.execute("SELECT accompagnateur.nom, accompagnateur.prenom, accompagnateur.mail, accompagnateur.tele FROM Connexion INNER JOIN accompagnateur ON Connexion.id_accompagnateur = accompagnateur.idaccompagnateur WHERE Connexion.id_utilisateur = %s", (id_utilisateur,))
            row = cursor.fetchone()
            if row is not None:
                nom_connected = row[0]
                prenom_connected = row[1]
                mail_connected = row[2]
                tele_connected = row[3]
                conn.close()
                return render_template('profil.html', accomp_nom=nom_connected, accomp_prenom=prenom_connected, accomp_mail=mail_connected, accomp_tele=tele_connected, role_connected=role_connected)

        elif role_connected == 'interprete':
            cursor.execute("SELECT interprete.nom, interprete.prenom, interprete.mail, interprete.tel FROM Connexion INNER JOIN interprete ON Connexion.id_interprete = interprete.id_interprete WHERE Connexion.id_utilisateur = %s", (id_utilisateur,))
            row = cursor.fetchone()
            if row is not None:
                nom_connected = row[0]
                prenom_connected = row[1]
                mail_connected = row[2]
                tele_connected = row[3]
                conn.close()
                return render_template('profil.html', interp_nom=nom_connected, interp_prenom=prenom_connected, interp_mail=mail_connected, interp_tele=tele_connected, role_connected=role_connected)
        else:
            error_message = "ERROR : le role connecté est inconnu !"
            conn.close()
            return render_template('index.html', error_message=error_message)        
    else:
        # Si aucun utilisateur n'est connecté, rediriger vers la page de connexion
        error_message = "ERROR : chi haja mahiyach alghandor !"
        return render_template('logout', error_message=error_message)   

#ouvrages auteur
@app.route('/ouvrages',methods=['POST','GET'])
def ouvrages():
    if 'id_utilisateur' in session:
        id_utilisateur = session['id_utilisateur']
        conn = psycopg2.connect(host=db_host, port=db_port, database=db_name, user=db_user, password=db_password)
        cursor = conn.cursor()
        cursor.execute("SELECT entite_connectee FROM Connexion WHERE id_utilisateur = %s", (id_utilisateur,))
        role_connected = cursor.fetchone()[0]

        #switching the home page depending on the connected role
        if role_connected=='auteur':
            cursor.execute("SELECT ouvrage.* FROM ouvrage JOIN RelatAutOuv ON ouvrage.id_ouvrage = RelatAutOuv.id_ouvrage JOIN auteur ON RelatAutOuv.id_auteur = auteur.id_auteur JOIN connexion ON auteur.id_auteur = connexion.id_auteur WHERE connexion.id_utilisateur = %s", (id_utilisateur,))
            result = cursor.fetchall()      
            conn.close()
            return render_template('ouvrages.html',ouvrages=result, role_connected=role_connected)
        
        if role_connected=='etablissement':
            cursor.execute("SELECT ouvrage.* FROM ouvrage", ())
            result = cursor.fetchall()      
            conn.close()
            return render_template('ouvrages.html',ouvrages=result, role_connected=role_connected)
        
        if role_connected=='admin':
            cursor.execute("SELECT auteur.* FROM auteur", ())
            auteurs = cursor.fetchall()   
            cursor.execute("SELECT ouvrage.* FROM ouvrage", ())
            result = cursor.fetchall()      
            conn.close()
            return render_template('ouvrages.html',auteurs=auteurs,ouvrages=result, role_connected=role_connected)
        
        else:
            error_message = "ERROR : le role connecté ne correspand pas !"
            conn.close()
            return render_template('index.html', error_message=error_message)        
    else:
        # Si aucun utilisateur n'est connecté, rediriger vers la page de connexion
        error_message = "ERROR : chi haja mahiyach alghandor !"
        return render_template('logout', error_message=error_message) 
    
#auteurs auteur
@app.route('/auteurs',methods=['POST','GET'])
def auteurs():
    if 'id_utilisateur' in session:
        id_utilisateur = session['id_utilisateur']
        conn = psycopg2.connect(host=db_host, port=db_port, database=db_name, user=db_user, password=db_password)
        cursor = conn.cursor()
        cursor.execute("SELECT entite_connectee FROM Connexion WHERE id_utilisateur = %s", (id_utilisateur,))
        role_connected = cursor.fetchone()[0] 
        
        if role_connected=='admin':
            cursor.execute("SELECT auteur.* FROM auteur", ())
            result = cursor.fetchall()      
            conn.close()
            return render_template('auteurs.html',auteurs=result, role_connected=role_connected)
        
        else:
            error_message = "ERROR : le role connecté ne correspand pas !"
            conn.close()
            return render_template('index.html', error_message=error_message)        
    else:
        # Si aucun utilisateur n'est connecté, rediriger vers la page de connexion
        error_message = "ERROR : chi haja mahiyach alghandor !"
        return render_template('logout', error_message=error_message)
    
#etablissements auteur
@app.route('/etablissements',methods=['POST','GET'])
def etablissements():
    if 'id_utilisateur' in session:
        id_utilisateur = session['id_utilisateur']
        conn = psycopg2.connect(host=db_host, port=db_port, database=db_name, user=db_user, password=db_password)
        cursor = conn.cursor()
        cursor.execute("SELECT entite_connectee FROM Connexion WHERE id_utilisateur = %s", (id_utilisateur,))
        role_connected = cursor.fetchone()[0] 
        
        if role_connected=='admin':
            cursor.execute("SELECT etablissement.* FROM etablissement", ())
            result = cursor.fetchall()      
            conn.close()
            return render_template('etablissements.html',etablissements=result, role_connected=role_connected)
        
        else:
            error_message = "ERROR : le role connecté ne correspand pas !"
            conn.close()
            return render_template('index.html', error_message=error_message)        
    else:
        # Si aucun utilisateur n'est connecté, rediriger vers la page de connexion
        error_message = "ERROR : chi haja mahiyach alghandor !"
        return render_template('logout', error_message=error_message)

#accompagnateurs
@app.route('/accompagnateurs',methods=['POST','GET'])
def accompagnateurs():
    if 'id_utilisateur' in session:
        id_utilisateur = session['id_utilisateur']
        conn = psycopg2.connect(host=db_host, port=db_port, database=db_name, user=db_user, password=db_password)
        cursor = conn.cursor()
        cursor.execute("SELECT entite_connectee FROM Connexion WHERE id_utilisateur = %s", (id_utilisateur,))
        role_connected = cursor.fetchone()[0] 
        
        if role_connected=='admin':
            cursor.execute("SELECT accompagnateur.* FROM accompagnateur", ())
            result = cursor.fetchall()      
            conn.close()
            return render_template('accompagnateurs.html',accompagnateurs=result, role_connected=role_connected)
        
        else:
            error_message = "ERROR : le role connecté ne correspand pas !"
            conn.close()
            return render_template('index.html', error_message=error_message)        
    else:
        # Si aucun utilisateur n'est connecté, rediriger vers la page de connexion
        error_message = "ERROR : chi haja mahiyach alghandor !"
        return render_template('logout', error_message=error_message)

#interpretes
@app.route('/interpretes',methods=['POST','GET'])
def interpretes():
    if 'id_utilisateur' in session:
        id_utilisateur = session['id_utilisateur']
        conn = psycopg2.connect(host=db_host, port=db_port, database=db_name, user=db_user, password=db_password)
        cursor = conn.cursor()
        cursor.execute("SELECT entite_connectee FROM Connexion WHERE id_utilisateur = %s", (id_utilisateur,))
        role_connected = cursor.fetchone()[0] 
        
        if role_connected=='admin':
            cursor.execute("SELECT interprete.* FROM interprete", ())
            result = cursor.fetchall()      
            conn.close()
            return render_template('interpretes.html',interpretes=result, role_connected=role_connected)
        
        else:
            error_message = "ERROR : le role connecté ne correspand pas !"
            conn.close()
            return render_template('index.html', error_message=error_message)        
    else:
        # Si aucun utilisateur n'est connecté, rediriger vers la page de connexion
        error_message = "ERROR : chi haja mahiyach alghandor !"
        return render_template('logout', error_message=error_message)



#dispo auteur par admin
@app.route('/admin_planning',methods=['POST','GET'])
def admin_planning():
    date_actuelle = date.today()
    id_auteur= request.form['id_auteur']
    if 'id_utilisateur' in session:
        id_utilisateur = session['id_utilisateur']
        conn = psycopg2.connect(host=db_host, port=db_port, database=db_name, user=db_user, password=db_password)
        cursor = conn.cursor()
        cursor.execute("SELECT entite_connectee FROM Connexion WHERE id_utilisateur = %s", (id_utilisateur,))
        role_connected = cursor.fetchone()[0]

        if role_connected=='admin':
            cursor.execute("SELECT auteur.* FROM auteur", ())
            auteurs = cursor.fetchall() 
            cursor.execute("SELECT disponibiliteauteur.date_disponibilite, disponibiliteauteur.disponible, disponibiliteauteur.nb_interventions_par_jour, disponibiliteauteur.id_disponibilite FROM  disponibiliteauteur WHERE disponibiliteauteur.id_auteur = %s ORDER BY disponibiliteauteur.date_disponibilite DESC", (id_auteur,))
            dispos = cursor.fetchall() 
            conn.close()
            return render_template('planning.html', dispos=dispos, date_actuelle=date_actuelle, auteurs=auteurs, role_connected=role_connected)
        
        else:
            error_message = "ERROR : le role connecté ne correspand pas !"
            conn.close()
            return render_template('index.html', error_message=error_message)        
    else:
        # Si aucun utilisateur n'est connecté, rediriger vers la page de connexion
        error_message = "ERROR : chi haja mahiyach alghandor !"
        return render_template('logout', error_message=error_message) 
    
#dispos auteur
@app.route('/planning',methods=['POST','GET'])
def planning():
    date_actuelle = date.today()
    if 'id_utilisateur' in session:
        id_utilisateur = session['id_utilisateur']
        conn = psycopg2.connect(host=db_host, port=db_port, database=db_name, user=db_user, password=db_password)
        cursor = conn.cursor()
        cursor.execute("SELECT entite_connectee FROM Connexion WHERE id_utilisateur = %s", (id_utilisateur,))
        role_connected = cursor.fetchone()[0]

        #switching the home page depending on the connected role
        if role_connected=='auteur':
            cursor.execute("SELECT disponibiliteauteur.date_disponibilite, disponibiliteauteur.disponible, disponibiliteauteur.nb_interventions_par_jour, disponibiliteauteur.id_disponibilite FROM Connexion INNER JOIN disponibiliteauteur ON Connexion.id_auteur = disponibiliteauteur.id_auteur WHERE Connexion.id_utilisateur = %s ORDER BY disponibiliteauteur.date_disponibilite DESC", (id_utilisateur,))
            dispos = cursor.fetchall() 
            conn.close()
            return render_template('planning.html', dispos=dispos, date_actuelle=date_actuelle, role_connected=role_connected)
        elif role_connected=='admin':
            cursor.execute("SELECT auteur.* FROM auteur", ())
            auteurs = cursor.fetchall() 
            cursor.execute("SELECT disponibiliteauteur.date_disponibilite, disponibiliteauteur.disponible, disponibiliteauteur.nb_interventions_par_jour, disponibiliteauteur.id_disponibilite FROM Connexion INNER JOIN disponibiliteauteur ON Connexion.id_auteur = disponibiliteauteur.id_auteur WHERE Connexion.id_utilisateur = %s ORDER BY disponibiliteauteur.date_disponibilite DESC", (id_utilisateur,))
            dispos = cursor.fetchall() 
            conn.close()
            return render_template('planning.html', dispos=dispos, date_actuelle=date_actuelle, auteurs=auteurs, role_connected=role_connected)
        
        else:
            error_message = "ERROR : le role connecté ne correspand pas !"
            conn.close()
            return render_template('index.html', error_message=error_message)        
    else:
        # Si aucun utilisateur n'est connecté, rediriger vers la page de connexion
        error_message = "ERROR : chi haja mahiyach alghandor !"
        return render_template('logout', error_message=error_message) 
    

@app.route("/add_interv",methods=['POST','GET'])
def add_interv():
    # Extraction de la valeur de l'ID de l'ouvrage
    if 'id_utilisateur' in session:
        id_utilisateur = session['id_utilisateur']
        conn = psycopg2.connect(host=db_host, port=db_port, database=db_name, user=db_user, password=db_password)
        cursor = conn.cursor()
        cursor.execute("select entite_connectee FROM Connexion WHERE id_utilisateur = %s", (id_utilisateur,))
        role_connected = cursor.fetchone()[0]
        date = request.form['date']
        duree = request.form['duree']
        etat = request.form['etat'] or None
        nombre_eleves = request.form['nombre_eleves']
        id_etablissement = request.form['id_etablissement'] 
        id_edition = 1 
        id_interprete = request.form['id_interprete']
        id_accompagnateur = request.form['id_accompagnateur']
        id_auteur = request.form['id_auteur']
        cursor.execute("INSERT INTO Intervention (Idate, duree, etat, nb_eleves, id_etablissement, id_interprete, id_accompagnateur, id_edition, id_auteur) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);", (date, duree, etat, nombre_eleves, id_etablissement, id_interprete, id_accompagnateur,id_edition ,id_auteur))
        conn.commit()
        conn.close()
        return redirect(url_for('intervention', role_connected=role_connected))

    else:
        # Si aucun utilisateur n'est connecté, rediriger vers la page de connexion
        return redirect(url_for('login'))
    
@app.route("/add_ouvrage",methods=['POST','GET'])
def add_ouvrage():
    # Extraction de la valeur de l'ID de l'ouvrage
    if 'id_utilisateur' in session:
        id_utilisateur = session['id_utilisateur']
        conn = psycopg2.connect(host=db_host, port=db_port, database=db_name, user=db_user, password=db_password)
        cursor = conn.cursor()
        cursor.execute("select entite_connectee FROM Connexion WHERE id_utilisateur = %s", (id_utilisateur,))
        role_connected = cursor.fetchone()[0]
        titre = request.form['titre_ouvrage']
        id_auteur = request.form['id_auteur']
        cursor.execute("INSERT INTO ouvrage(titre) VALUES (%s);", (titre,))
        cursor.execute("select id_ouvrage from ouvrage where titre =%s;", (titre,))
        id_ouvrage = cursor.fetchone()[0]
        cursor.execute("INSERT INTO relatautouv (id_ouvrage,id_auteur) VALUES (%s,%s);", (id_ouvrage,id_auteur))
        conn.commit()
        conn.close()
        return redirect(url_for('ouvrages', role_connected=role_connected))

    else:
        # Si aucun utilisateur n'est connecté, rediriger vers la page de connexion
        return redirect(url_for('login'))


@app.route("/planning_add",methods=['POST','GET'])
def planning_add():
    # Extraction de la valeur de l'ID de l'ouvrage
    if 'id_utilisateur' in session:
        id_utilisateur = session['id_utilisateur']
        conn = psycopg2.connect(host=db_host, port=db_port, database=db_name, user=db_user, password=db_password)
        cursor = conn.cursor()
        cursor.execute("select entite_connectee FROM Connexion WHERE id_utilisateur = %s", (id_utilisateur,))
        role_connected = cursor.fetchone()[0]
        cursor.execute("SELECT id_auteur FROM Connexion WHERE Connexion.id_utilisateur = %s ", (id_utilisateur,))
        id_auteur = cursor.fetchone()[0]
        date_disponibilite = request.form['date_disponibilite']
        if 'disponibilite' in request.form:
            disponibilite = True
        else :
            disponibilite = False
        cursor.execute("INSERT INTO disponibiliteauteur(id_auteur, date_disponibilite, disponible) VALUES(%s, %s, %s)", (id_auteur, date_disponibilite, disponibilite))
        conn.commit()
        conn.close()
        return redirect(url_for('planning', role_connected=role_connected))

    else:
        # Si aucun utilisateur n'est connecté, rediriger vers la page de connexion
        return redirect(url_for('login'))
 

@app.route("/add_langue",methods=['POST','GET'])
def add_langue():
    # Extraction de la valeur de l'ID de l'ouvrage
    if 'id_utilisateur' in session:
        id_utilisateur = session['id_utilisateur']
        conn = psycopg2.connect(host=db_host, port=db_port, database=db_name, user=db_user, password=db_password)
        cursor = conn.cursor()
        cursor.execute("select entite_connectee FROM Connexion WHERE id_utilisateur = %s", (id_utilisateur,))
        role_connected = cursor.fetchone()[0]
        langue_choisi = request.form['langue_choisi']
        autre_langue_choisi = request.form['autre_langue_choisi']
        if autre_langue_choisi:
            choix = autre_langue_choisi
        else:
            choix = langue_choisi
        cursor.execute("SELECT COUNT(*) FROM langue WHERE  nom_langue= %s", (choix,))
        existe = cursor.fetchone()[0]  # Récupérer une seule ligne du résultat
        if existe == 0:
            cursor.execute("insert into langue(nom_langue) values(%s)", (choix,))
            cursor.execute("SELECT num_langue FROM langue WHERE  nom_langue= %s", (choix,))
            num_choix = cursor.fetchone()[0]  # Récupérer une seule ligne du résultatZ
        else:
            cursor.execute("SELECT num_langue FROM langue WHERE  nom_langue= %s", (choix,))
            num_choix = cursor.fetchone()[0]  # Récupérer une seule ligne du résultatZ

        if role_connected=='auteur':
            cursor.execute("select id_auteur FROM Connexion WHERE id_utilisateur = %s", (id_utilisateur,))
            id_auteur = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM parle2 WHERE  num_langue= %s AND id_auteur =%s", (num_choix,id_auteur))
            existe2 = cursor.fetchone()[0]  # Récupérer une seule ligne du résultat
            if existe2 ==0:
                cursor.execute("insert into parle2(id_auteur,num_langue) values(%s,%s) ", (id_auteur,num_choix,))
                conn.commit()
                return redirect(url_for('langues', role_connected=role_connected))
            else:
                error_message = "ERROR : la langue renseigné est déjà ajouté!"
                conn.close()
                return render_template('langues.html', error_message=error_message)
        elif role_connected=='interprete':
            cursor.execute("select id_auteur FROM Connexion WHERE id_utilisateur = %s", (id_utilisateur,))
            id_interprete = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM parle1 WHERE  num_langue= %s AND id_interprete =%s", (num_choix,id_interprete))
            existe1 = cursor.fetchone()[0]  # Récupérer une seule ligne du résultat
            if existe1 ==0:
                cursor.execute("select id_interprete FROM Connexion WHERE id_utilisateur = %s", (id_utilisateur,))
                id_interprete = cursor.fetchone()[0]
                cursor.execute("insert into parle1(id_interprete,num_langue) values(%s,%s) ", (id_interprete, num_choix,))
                conn.commit()
                return redirect(url_for('langues', role_connected=role_connected))
            else:
                error_message = "ERROR : la langue renseigné est déjà ajouté!"
                conn.close()
                return render_template('langues.html', error_message=error_message)

            
                  
    else:
        # Si aucun utilisateur n'est connecté, rediriger vers la page de connexion
        return redirect(url_for('logout'))
    
@app.route("/ouvrage_choix",methods=['POST','GET'])
def ouvrage_choix():
    # Extraction de la valeur de l'ID de l'ouvrage
    if 'id_utilisateur' in session:
        id_utilisateur = session['id_utilisateur']
        conn = psycopg2.connect(host=db_host, port=db_port, database=db_name, user=db_user, password=db_password)
        cursor = conn.cursor()
        cursor.execute("select entite_connectee FROM Connexion WHERE id_utilisateur = %s", (id_utilisateur,))
        role_connected = cursor.fetchone()[0]
        cursor.execute("select id_etablissement from Connexion WHERE Connexion.id_utilisateur = %s ", (id_utilisateur,))
        id_etablissement = cursor.fetchone()[0]
        priorite = request.form['priorite']
        id_ouvrage_choisi = request.form['id_ouvrage_choisi']
        cursor.execute("select titre FROM ouvrage WHERE id_ouvrage = %s", (id_ouvrage_choisi,))
        titre_ouvrage = cursor.fetchone()[0]
        cursor.execute("INSERT INTO voeux(voeux, priorite, id_etablissement, id_ouvrage) VALUES(%s, %s, %s, %s)", (titre_ouvrage, priorite, id_etablissement, id_ouvrage_choisi))
        cursor.execute("select id_voeux FROM voeux WHERE id_ouvrage = %s", (id_ouvrage_choisi,))
        id_voeux = cursor.fetchone()[0]
        cursor.execute("UPDATE ouvrage SET id_voeux = %s WHERE id_ouvrage = %s", (id_voeux,id_ouvrage_choisi))
        conn.commit()
        conn.close()
        return redirect(url_for('ouvrages', role_connected=role_connected))

    else:
        # Si aucun utilisateur n'est connecté, rediriger vers la page de connexion
        return redirect(url_for('login'))

@app.route("/delete_dispo",methods=['POST','GET'])
def delete_dispo():
    id_utilisateur = session['id_utilisateur']
    # Extraction de la valeur de l'ID de l'ouvrage
    if  request.method == 'POST':
        data = request.json
        dispo_id = data.get('id')
        conn = psycopg2.connect(host=db_host, port=db_port, database=db_name, user=db_user, password=db_password)
        cursor = conn.cursor()
        cursor.execute("select entite_connectee FROM Connexion WHERE id_utilisateur = %s", (id_utilisateur,))
        role_connected = cursor.fetchone()[0]
        cursor.execute("DELETE FROM disponibiliteauteur WHERE id_disponibilite = %s", (dispo_id,))
        conn.commit()
        conn.close()
        return redirect(url_for('planning', role_connected=role_connected))
    else:
        error_message = "erreur id n'est pas envoyé !"
        return redirect(url_for('planning'),error_message=error_message)

#intervention etab/auteur
@app.route('/intervention',methods=['POST','GET'])
def intervention():
    if 'id_utilisateur' in session:
        id_utilisateur = session['id_utilisateur']
        conn = psycopg2.connect(host=db_host, port=db_port, database=db_name, user=db_user, password=db_password)
        cursor = conn.cursor()
        cursor.execute("select entite_connectee FROM Connexion WHERE id_utilisateur = %s", (id_utilisateur,))
        role_connected = cursor.fetchone()[0]
        date_actuelle = date.today()

        #switching the home page depending on the connected role
        if role_connected=='etablissement':
            cursor.execute("select id_etablissement FROM Connexion WHERE id_utilisateur = %s", (id_utilisateur,))
            id_etablissement = cursor.fetchone()[0]
            
            cursor.execute("SELECT intervention.* FROM intervention WHERE id_etablissement = %s", (id_etablissement,))
            result = cursor.fetchall()      
            conn.close()
            return render_template('intervention.html',interventions=result, role_connected=role_connected)
        elif role_connected=='auteur':
            cursor.execute("select id_auteur FROM Connexion WHERE id_utilisateur = %s", (id_utilisateur,))
            id_auteur = cursor.fetchone()[0]
            cursor.execute("SELECT Intervention.id_intervention, Intervention.Idate,Intervention.duree,Intervention.etat,Intervention.nb_eleves,etablissement.nom AS nom_etablissement,etablissement.adresse AS adresse_etablissement,Intervention.id_edition,Intervention.id_auteur FROM Intervention INNER JOIN etablissement ON Intervention.id_etablissement = etablissement.idetablissement WHERE id_auteur = %s", (id_auteur,))
            result = cursor.fetchall()      
            conn.close()
            return render_template('intervention.html',interventions=result, role_connected=role_connected)
        elif role_connected=='accompagnateur':
            cursor.execute("select id_accompagnateur FROM Connexion WHERE id_utilisateur = %s", (id_utilisateur,))
            id_accompagnateur = cursor.fetchone()[0]
            cursor.execute("SELECT intervention.* FROM intervention WHERE id_accompagnateur = %s", (id_accompagnateur,))
            result = cursor.fetchall()      
            conn.close()
            return render_template('intervention.html',interventions=result, role_connected=role_connected)
        elif role_connected=='interprete':
            cursor.execute("select id_interprete FROM Connexion WHERE id_utilisateur = %s", (id_utilisateur,))
            id_interprete = cursor.fetchone()[0]
            cursor.execute("SELECT intervention.* FROM intervention WHERE id_interprete = %s", (id_interprete,))
            result = cursor.fetchall()      
            conn.close()
            return render_template('intervention.html',interventions=result, role_connected=role_connected)
        elif role_connected=='admin':
            cursor.execute('SELECT * from etablissement')
            etablissements = cursor.fetchall() 
            cursor.execute('SELECT * from auteur')
            auteurs = cursor.fetchall()
            cursor.execute('SELECT * from accompagnateur')
            accompagnateurs = cursor.fetchall() 
            cursor.execute('SELECT * from interprete')
            interpretes = cursor.fetchall()       
            cursor.execute("SELECT intervention.* FROM intervention", ())
            result = cursor.fetchall()      
            conn.close()
            return render_template('intervention.html',date_actuelle=date_actuelle,accompagnateurs=accompagnateurs, interpretes=interpretes,etablissements=etablissements, auteurs=auteurs, interventions=result, role_connected=role_connected)
        else:
            error_message = "ERROR : le role connecté ne correspand pas !"
            conn.close()
            return render_template('index.html', error_message=error_message)        
    else:
        # Si aucun utilisateur n'est connecté, rediriger vers la page de connexion
        error_message = "ERROR : chi haja mahiyach alghandor !"
        return render_template('logout', error_message=error_message) 

#langues interprete/auteur
@app.route('/langues',methods=['POST','GET'])
def langues():
    if 'id_utilisateur' in session:
        id_utilisateur = session['id_utilisateur']
        conn = psycopg2.connect(host=db_host, port=db_port, database=db_name, user=db_user, password=db_password)
        cursor = conn.cursor()
        cursor.execute("select entite_connectee FROM Connexion WHERE id_utilisateur = %s", (id_utilisateur,))
        role_connected = cursor.fetchone()[0]

        #switching the home page depending on the connected role

        if role_connected=='auteur':
            cursor.execute("select id_auteur FROM Connexion WHERE id_utilisateur = %s", (id_utilisateur,))
            id_auteur = cursor.fetchone()[0]
            cursor.execute("SELECT L.num_langue, L.nom_langue FROM Langue L JOIN Parle2 P ON L.num_langue = P.num_langue WHERE P.id_auteur= %s", (id_auteur,))
            result = cursor.fetchall() 
            conn.close()
            return render_template('langues.html',langues=result, role_connected=role_connected)
        
        elif role_connected=='interprete':
            cursor.execute("select id_interprete FROM Connexion WHERE id_utilisateur = %s", (id_utilisateur,))
            id_interprete = cursor.fetchone()[0]
            cursor.execute("SELECT L.num_langue, L.nom_langue FROM Langue L JOIN Parle1 P ON L.num_langue = P.num_langue WHERE P.id_interprete= %s", (id_interprete,))
            result = cursor.fetchall() 
            conn.close()
            return render_template('langues.html',langues=result, role_connected=role_connected)
        
        else:
            error_message = "ERROR : le role connecté ne correspand pas !"
            conn.close()
            return render_template('index.html', error_message=error_message)        
    else:
        # Si aucun utilisateur n'est connecté, rediriger vers la page de connexion
        error_message = "ERROR : chi haja mahiyach alghandor !"
        return render_template('logout', error_message=error_message) 

#voeux etab
@app.route('/voeux',methods=['POST','GET'])
def voeux():
    if 'id_utilisateur' in session:
        id_utilisateur = session['id_utilisateur']

        conn = psycopg2.connect(host=db_host, port=db_port, database=db_name, user=db_user, password=db_password)
        cursor = conn.cursor()
        cursor.execute("select entite_connectee FROM Connexion WHERE id_utilisateur = %s", (id_utilisateur,))
        role_connected = cursor.fetchone()[0]

        #switching the home page depending on the connected role
        if role_connected=='etablissement':
            cursor.execute("select id_etablissement FROM Connexion WHERE id_utilisateur = %s", (id_utilisateur,))
            id_etablissement = cursor.fetchone()[0]
            cursor.execute("SELECT voeux.* FROM voeux WHERE id_etablissement = %s", (id_etablissement,))
            result = cursor.fetchall()      
            conn.close()
            return render_template('voeux.html',voeux=result, role_connected=role_connected)
        elif role_connected=='admin':
            cursor.execute("SELECT voeux.* FROM voeux", ())
            result = cursor.fetchall()      
            conn.close()
            return render_template('voeux.html',voeux=result, role_connected=role_connected)
        else:
            error_message = "ERROR : le role connecté ne correspand pas !"
            conn.close()
            return render_template('index.html', error_message=error_message)        
    else:
        # Si aucun utilisateur n'est connecté, rediriger vers la page de connexion
        error_message = "ERROR : chi haja mahiyach alghandor !"
        return render_template('logout', error_message=error_message) 
    
#langues
# @app.route('/voeux',methods=['POST','GET'])
# def voeux():
#     if 'id_utilisateur' in session:
#         id_utilisateur = session['id_utilisateur']
#         conn = psycopg2.connect(host=db_host, port=db_port, database=db_name, user=db_user, password=db_password)
#         cursor = conn.cursor()
#         cursor.execute("select entite_connectee FROM Connexion WHERE id_utilisateur = %s", (id_utilisateur,))
#         role_connected = cursor.fetchone()[0]

#         #switching the home page depending on the connected role
#         if role_connected=='etablissement':
#             cursor.execute("select id_etablissement FROM Connexion WHERE id_utilisateur = %s", (id_utilisateur,))
#             id_etablissement = cursor.fetchone()[0]
#             cursor.execute("SELECT voeux.* FROM voeux WHERE id_etablissement = %s", (id_etablissement,))
#             result = cursor.fetchall()      
#             conn.close()
#             return render_template('voeux.html',voeux=result, role_connected=role_connected)
#         else:
#             error_message = "ERROR : le role connecté ne correspand pas !"
#             conn.close()
#             return render_template('index.html', error_message=error_message)        
#     else:
#         # Si aucun utilisateur n'est connecté, rediriger vers la page de connexion
#         error_message = "ERROR : chi haja mahiyach alghandor !"
#         return render_template('logout', error_message=error_message) 
   

@app.route('/signup',methods=['POST','GET'])
def signup(): 
    return render_template('signup.html')

@app.route('/signup_done',methods=['POST','GET'])
def signup_done():
    password = request.form['password']
    email = request.form['email']  
    role = request.form['role']
    conn = psycopg2.connect(host=db_host, port=db_port, database=db_name, user=db_user, password=db_password)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM connexion WHERE id_utilisateur = %s", (email,))
    existe = cursor.fetchone()[0]  # Récupérer une seule ligne du résultat
    if existe == 0:
            if role == "auteur":
                nom_auteur = request.form['nom_auteur']
                prenom_auteur = request.form['prenom_auteur']
                adresse_auteur = request.form['adresse_auteur']  
                cursor.execute("INSERT INTO auteur (nom, prenom, adresse, mail) VALUES (%s, %s, %s, %s)", (nom_auteur, prenom_auteur, adresse_auteur, email))
                cursor.execute("SELECT id_auteur FROM auteur WHERE mail = %s", (email,))
                id_auteur = cursor.fetchone()[0]  # Récupérer une seule ligne du résultat
                cursor.execute("INSERT INTO connexion (id_utilisateur, mdp, entite_connectee, id_auteur) VALUES (%s, %s, %s, %s)", (email, password, role, id_auteur))
                print("L'auteur " ,nom_auteur," a été ajouté avec succès.")
                #session user
                
                cursor.execute("SELECT id_utilisateur FROM connexion WHERE id_utilisateur = %s AND mdp= %s",(email,password))
                user = cursor.fetchone()[0]  # Récupérer une seule ligne du résultat
                session['id_utilisateur'] = user
                print("fff", session['id_utilisateur'])
                conn.commit()
                conn.close()
                return redirect(url_for('home', role_connected=role))
                    
            elif role == "etablissement":
                nom_etab = request.form['nom_etab']
                etab_type = request.form['etab_type']  
                adresse_etab = request.form['adresse_etab']  
                idreferent = request.form['idreferent']  
                nom_ref = request.form['nom_ref']  
                prenom_ref = request.form['prenom_ref'] 
                telephone_ref = request.form['telephone_ref']
                cursor.execute("INSERT INTO referent (idreferent, nom, prenom, mail, tele) VALUES (%s, %s, %s, %s, %s)", (idreferent, nom_ref, prenom_ref, email, telephone_ref))
                cursor.execute("INSERT INTO etablissement (nom, etabtype, adresse, idreferent) VALUES (%s, %s, %s, %s)", (nom_etab, etab_type, adresse_etab, idreferent))
                cursor.execute("SELECT idetablissement FROM etablissement WHERE idreferent = %s", (idreferent,))
                id_etablissement = cursor.fetchone()[0]  # Récupérer une seule ligne du résultat
                cursor.execute("INSERT INTO connexion (id_utilisateur, mdp, entite_connectee, id_etablissement) VALUES (%s, %s, %s, %s)", (email, password, role, id_etablissement))
                print("L'établissement a été ajouté avec succès.")
                #session user
                cursor.execute("SELECT id_utilisateur FROM connexion WHERE id_utilisateur = %s AND mdp= %s",(email,password))
                user = cursor.fetchone()[0]  # Récupérer une seule ligne du résultat
                session['id_utilisateur'] = user
                print("fff", session['id_utilisateur'])
                conn.commit()
                conn.close()
                return redirect(url_for('home', role_connected=role))
        
            elif role == "accompagnateur":
                nom_accomp = request.form['nom_accomp_interp']
                prenom_accomp = request.form['prenom_accomp_interp']
                telephone_accomp = request.form['telephone_accomp_interp']
                cursor.execute("INSERT INTO accompagnateur (nom, prenom, mail, tele) VALUES (%s, %s, %s, %s)", (nom_accomp, prenom_accomp, email, telephone_accomp))
                cursor.execute("SELECT idaccompagnateur FROM accompagnateur WHERE mail = %s", (email,))
                id_accompagnateur = cursor.fetchone()[0]  # Récupérer une seule ligne du résultat
                cursor.execute("INSERT INTO connexion (id_utilisateur, mdp, entite_connectee, id_accompagnateur) VALUES (%s, %s, %s, %s)", (email, password, role, id_accompagnateur))
                print("L'accompagnateur a été ajouté avec succès.")
                #session user
                cursor.execute("SELECT * FROM connexion WHERE id_utilisateur = %s AND mdp= %s",(email,password))
                user = cursor.fetchone()  # Récupérer une seule ligne du résultat
                session['id_utilisateur'] = user[0]
                conn.commit()
                conn.close()
                return redirect(url_for('home', role_connected=role))

            elif role == "interprete":
                nom_interp = request.form['nom_accomp_interp']
                prenom_interp = request.form['prenom_accomp_interp']
                telephone_interp = request.form['telephone_accomp_interp']
                cursor.execute("INSERT INTO interprete (nom, prenom, mail, tel) VALUES (%s, %s, %s, %s)", (nom_interp, prenom_interp, email, telephone_interp))
                cursor.execute("SELECT id_interprete FROM interprete WHERE mail = %s", (email,))
                id_interprete = cursor.fetchone()[0]  # Récupérer une seule ligne du résultat
                cursor.execute("INSERT INTO connexion (id_utilisateur, mdp, entite_connectee, id_interprete) VALUES (%s, %s, %s, %s)", (email, password, role, id_interprete))
                print("L'interprète a été ajouté avec succès.")
                #session user
                cursor.execute("SELECT * FROM connexion WHERE id_utilisateur = %s AND mdp= %s",(email,password))
                user = cursor.fetchone()  # Récupérer une seule ligne du résultat
                session['id_utilisateur'] = user[0]
                conn.commit()
                conn.close()
                return redirect(url_for('home', role_connected=role))
            else:
                error_message = "Le rôle fourni n'existe pas !"
                conn.close()
                return render_template('index.html', error_message=error_message)
    else:
            # Si un utilisateur est déjà enregistré, rediriger vers la page d'accueil
            error_message = "cet utilisateur est déjà inscrit!"
            conn.close()
            return render_template('index.html', error_message=error_message)
    
if __name__ == '__main__':
     
      app.run(debug=True)