from flask import Flask, render_template, request, session
from flask_session import Session
import sqlite3
import random
import itertools

app = Flask(__name__)
app.secret_key = '8a593bcdcc4580c6fc4563363f681b28'


########################################################################
########################################################################


##########Partie Session#############
#####################################
def verify_credentials(username, password):
    return username == "admin" and password == "secret"

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if verify_credentials(username, password):
            session['logged_in'] = True
            return home()
        else:
            return render_template('login.html', msg='le mot de passe ou le nom d\'utilisateur sont incorrect')
    return render_template('login.html')
@app.route('/')
@app.route('/tournoi/<int:id_tournoi>')
def home(id_tournoi='non_def'):
    if not session.get('logged_in'):
        return login()
    else:
        con = sqlite3.connect("database.db")
        con.row_factory = sqlite3.Row
    
        cur = con.cursor()
        
        # Récupérer les tournois pour le menu déroulant
        cur.execute("SELECT nom, id FROM tournoi")
        tab_list_tournoi = cur.fetchall()

        # Si aucun id_tournoi n'est spécifié, vous pouvez choisir de ne rien afficher ou de définir un comportement par défaut
        if id_tournoi == 'non_def':
            return render_template('index.html', tab_tournoi=tab_list_tournoi, rows=[], tab_equipe=[], id_tournoi = 'non_def')

        # Récupérer les poules du tournoi spécifié
        cur.execute("SELECT * FROM poule WHERE id_tournoi = ?", (id_tournoi,))
        rows = cur.fetchall()
    
        # Récupérer les équipes pour chaque poule récupérée
        tab_equipe = []
        for poule in rows:
            cur.execute("SELECT nom, poule_id, point FROM equipe WHERE poule_id = ? ORDER BY point DESC", (poule["id"],))
            equipe = cur.fetchall()
            tab_equipe.extend(equipe)  # Utilisez extend pour ajouter les équipes à la liste

        con.close()
        return render_template('index.html', rows=rows, tab_equipe=tab_equipe, tab_tournoi=tab_list_tournoi, id_tournoi = id_tournoi)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return login()

#####################################
def repartition_equipes(equipes:list, tab_id:list):
    '''Fonction qui prend en parametre un tableau d'equipes et un tableau contenant les id des poules du tournois,
    renvoi un tableau de tuple avec le nom de l'equipe et son numero de poule. Elle repartit automatiquement
    les équipes dans les poules.'''
    random.shuffle(equipes)
    nombre_de_poules = int(tab_id[0]) - int(tab_id[-1]) + 1
    print(nombre_de_poules)
    equipes_par_poule = len(equipes) // nombre_de_poules
    resultats = []
    if equipes_par_poule < 2:
        return "Merci d'augmenter le nombre d'équipe ou de réduire le nombre de poules"
    ### Répartir les équipes dans les poules autant que possible
    for i in range(nombre_de_poules):
        equipes_poule = equipes[i * equipes_par_poule: (i + 1) * equipes_par_poule]
        for equipe in equipes_poule:
            resultats.append((equipe, tab_id[i]))

    ### Répartir les équipes restantes
    equipes_restantes = equipes[nombre_de_poules * equipes_par_poule:]
    for i in range(len(equipes_restantes)):
        resultats.append((equipes_restantes[i], i % nombre_de_poules + 1))
    return resultats

def generer_matchs(equipes_poule):
    '''Fonction qui prend en paramètre un tableau et renvoi toutes les combinaisons possible par 2
    avec les éléments de ce tableau en supprimant les doublons'''
    matchs = list(itertools.combinations(equipes_poule, 2))
    return matchs

def creer_match(data, tab_id, id_tournoi):
    poules = {}
    for equipe, poule in data:
        if poule not in poules:
            poules[poule] = []
        poules[poule].append(equipe)

    # Convertir le dictionnaire en une liste de listes
    tableau_poules = list(poules.values())
    tab_tuple_match = []
    for i in range( len(tableau_poules)):
        n_poule = "Poule"+str(tab_id[i])
        temp = generer_matchs(tableau_poules[i])
        for match in temp:
            tab_tuple_match.append([match[0], match[1], n_poule, id_tournoi])
    return tab_tuple_match
         
###############################################################################
###############################################################################
###############################################################################
@app.route('/')
def home2():
    '''Fonction qui se charge lorsqu'on va sur la page index.html, page d'accueil'''
    con = sqlite3.connect("database.db")
    con.row_factory = sqlite3.Row
    
    cur = con.cursor()
    cur.execute("SELECT * FROM poule ORDER by id")
    rows = cur.fetchall()
    dict_poules = []
    for i in range(len(rows)):
        result_dict = dict(rows[i])
        dict_poules.append(result_dict)
    
    tab_equipe = []
    for i in range(1, len(dict_poules) + 1):
        script = "SELECT nom, poule_id, point FROM equipe WHERE poule_id ="+str(i) +" ORDER BY point"
        cur = con.cursor()
        cur.execute(script)
        equipe = cur.fetchall()
        for ligne in equipe:
            equipe_dict = dict(ligne)
            equipe_list = list(equipe_dict.values())
            tab_equipe.append(equipe_list)            
    con.close()
    return render_template('index.html', rows=rows, tab_equipe = tab_equipe)

@app.route('/creernouveautournois')
def page_parametre():
    '''Fonction du bouton pour creer un nouveau tournoi qui renvoi vers la page parametre.html qui sert a entrer
    les parametres du tournois'''
    return render_template('parametre.html')
            
@app.route('/entrer_equipes', methods=['POST', 'GET'])
def addclient():
    '''Fonction qui traite le formulaire de parametre.html, et qui renvoi sois vers entrer_equipes.html ou vers
    erreur si un des chiffres est egale à 0'''
    if request.method == 'POST':
        nom = str(request.form['nom'])
        sport = str(request.form['sport'])
        date = int(request.form['date'])
        tuple_infos_tournois = (nom,sport,date)
        with sqlite3.connect('database.db') as con:
                cur = con.cursor()
                cur.execute("INSERT INTO tournoi(nom, sport,date) VALUES (?,?,?)", tuple_infos_tournois)
                
        type_tournoi = str(request.form['type'])
        if type_tournoi == "automatique":
            nb_poule = ""
            nb_poule = int(request.form['nb_poules'])
            nb_equipe = int(request.form['nb_equipes'])

            if nb_poule % 2 != 0:
                return render_template("parametre.html", error_msg="Erreur : Merci d'entrer un nombre de poules pair")
 
            if nb_equipe // nb_poule < 2:
                return render_template("parametre.html", error_msg="Erreur : Il vous faut au moins 3 équipes par poule")
        
            if nb_poule > 0 and nb_equipe > 0:    
                script = """SELECT id FROM tournoi ORDER BY id DESC LIMIT 1"""
                cur.execute(script)
                id_tournoi = cur.fetchone()
                tab = []
                for i in range(1, nb_poule + 1):
                    tab.append(("Poule" + str(i),id_tournoi[0]))
                cur.executemany("INSERT INTO poule(nom, id_tournoi) VALUES (?,?)", tab)
                dernier_id_poule = cur.lastrowid
                con.commit()

                return render_template("entrer_equipes.html", nb_equipe=nb_equipe, nb_poule=nb_poule, id_tournoi=id_tournoi)
            else:
                return render_template("resultat.html", msg="Erreur: Merci de rentrer une valeur plus grande que 0",)
        else:
            return home()
@app.route('/resultats_formulaire_equipes', methods=['POST', 'GET'])
def insert_equipes():
    '''Fonction qui traite le formulaire de entrer_equipes.html, et qui renvoi sois vers
    erreur si il manque une valeur ou alors vers resultat.html avec un succes'''
    if request.method == 'POST':
        nombre_equipe = request.form['nb_equipe']
        nombre_poule = request.form['nb_poule']
        id_tournoi = request.form['id_tournoi'][1]
        print(id_tournoi)
        values = []

        for i in range(1, int(nombre_equipe) + 1):
            nom_champ = "champ" + str(i)
            nom_equipe = request.form[nom_champ]
            if len(nom_equipe) > 0:
                values.append(nom_equipe)
            else:
                return render_template("entrer_equipes.html", msg_error='Erreur, veuillez renseigner tous les champs !', nb_equipe=int(nombre_equipe), nb_poule=int(nombre_poule))

              
        ### Partie pour creer les matchs: ###
        with sqlite3.connect('database.db') as con:
            cur = con.cursor()
        #####################################
            script = """SELECT id FROM poule ORDER BY id DESC LIMIT """+str(nombre_poule)
            cur.execute(script)
            id_poules = cur.fetchall()
            tab_id = []
            for id_poule in id_poules:
                tab_id.append(id_poule[0])
                print(tab_id)
            tuple_equipe_poule = repartition_equipes(values, tab_id)
            print(tuple_equipe_poule)
            cur.executemany("INSERT INTO equipe(nom, poule_id) VALUES (?, ?)", tuple_equipe_poule)
            
            ###################################################
            tableau_tuple_match = creer_match(tuple_equipe_poule, tab_id, id_tournoi) ### Stock dans la valeur, un tableau de tuple contenant le nom de l'équipe 1 et le nom de l'equipe 2
            print(tableau_tuple_match)
            nb_match = len(tableau_tuple_match)
            
            cur.executemany("INSERT INTO match(equipe1, equipe2, n_poule, id_tournoi) VALUES (?, ?, ?, ?)", tableau_tuple_match)
            con.commit()
        return render_template("entrer_matchs.html", nb_match=nb_match, tableau_tuple_match = tableau_tuple_match)



############################################################################
@app.route('/afficher_edit_match', methods=['POST', 'GET'])
def page_edit_match():
    '''Fonction qui traite le formulaire de entrer_equipes.html, et qui renvoi sois vers
    erreur si il manque une valeur ou alors vers resultat.html avec un succes'''
    with sqlite3.connect('database.db') as con:
        cur = con.cursor()
        script = """SELECT equipe1, equipe2, n_poule, date, heurre, lieu FROM match"""
        cur.execute(script)
        tableau_tuple_match = cur.fetchall()
        print(tableau_tuple_match)
        nb_match = len(tableau_tuple_match)
        con.commit()
        
        #####################################
    return render_template("entrer_matchs.html", nb_match=nb_match, tableau_tuple_match = tableau_tuple_match)

@app.route('/set_score_match', methods=['POST', 'GET'])
def page_set_score():
    '''Fonction qui traite le formulaire de entrer_equipes.html, et qui renvoi sois vers
    erreur si il manque une valeur ou alors vers resultat.html avec un succes'''
    with sqlite3.connect('database.db') as con:
        cur = con.cursor()
        script = """SELECT * FROM match"""
        cur.execute(script)
        tableau_tuple_match = cur.fetchall()
        print(tableau_tuple_match)
        nb_match = len(tableau_tuple_match)
        con.commit()
        
        #####################################
    return render_template("definir_score.html", nb_match=nb_match, tableau_tuple_match = tableau_tuple_match)
########################################################
@app.route('/resultats_formulaire_score_matchs', methods=['POST', 'GET'])
def entrer_match_score():
    '''Fonction du formulaire entrer_matchs.html et qui permet d'entrer l'heure la date et lieu de chaque matchs.'''
    if request.method == 'POST':
        nombre_match = request.form['nb_match']
        print( int(nombre_match), type(nombre_match) )
        for i in range( int(nombre_match) ):
            score_equipe1 = request.form['score_equipe1_match'+str(i)]
            score_equipe2 = request.form['score_equipe2_match'+str(i)]
            print(score_equipe1,score_equipe2, i)
            
            with sqlite3.connect('database.db') as con:
                cur = con.cursor()
                script = "UPDATE match SET score_equipe1 = ?, score_equipe2 = ? WHERE id = ?"
                cur.execute(script, (score_equipe1, score_equipe2, i+1))
                con.commit()

        return home()
    
#########################################################################################
@app.route('/resultats_formulaire_matchs', methods=['POST', 'GET'])
def entrer_match_info():
    '''Fonction du formulaire entrer_matchs.html et qui permet d'entrer l'heure la date et lieu de chaque matchs.'''
    if request.method == 'POST':
        nombre_match = request.form['nb_match']
        for i in range(1, int(nombre_match) + 1):
            nom_champ_date = "date_match" + str(i-1)
            nom_champ_heure = "heure_match" + str(i-1)
            nom_champ_lieu = "lieu_match" + str(i-1)

            date_match = request.form[str(nom_champ_date)]
            heure_match = request.form[str(nom_champ_heure)]
            lieu_match = request.form[str(nom_champ_lieu)]
            
            with sqlite3.connect('database.db') as con:
                cur = con.cursor()
                script = "UPDATE match SET date = ?, heurre = ?, lieu = ? WHERE id = ?"
                cur.execute(script, (date_match, heure_match, lieu_match, i))
                con.commit()

        return home()

 
@app.route('/liste_equipes')
def liste_equipes():
    '''Fonction du bouton qui permet d'afficher la liste des équipes et leur poule.'''
    con = sqlite3.connect("database.db")
    con.row_factory = sqlite3.Row
    
    cur = con.cursor()
    cur.execute("SELECT * FROM equipe ORDER by poule_id")

    rows = cur.fetchall()
    return render_template("liste_equipes.html", rows=rows)


@app.route('/edit_matchs')
def afficher_edit_match():
    '''Fonction du bouton qui permet de modifier la liste des matchs'''
    con = sqlite3.connect("database.db")
    con.row_factory = sqlite3.Row
    
    cur = con.cursor()
    cur.execute("SELECT * FROM match ORDER by id")
    rows = cur.fetchall()
    cur.execute("SELECT * FROM poule ORDER by id")
    poules = cur.fetchall()
    return render_template("edit_matchs.html", rows=rows, poules =poules, titre ="Matchs:")

@app.route('/')
@app.route('/liste_matchs/<int:id_tournoi>')
def liste_matchs(id_tournoi='non_def'):
    '''Fonction du bouton qui permet d'afficher la liste des matchs'''
    con = sqlite3.connect("database.db")
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    print(id_tournoi)
    if id_tournoi != 'non_def':
        script = "SELECT * FROM match WHERE id_tournoi = "+str(id_tournoi)
        cur.execute(script)
        print(script)
        rows = cur.fetchall()
        for ligne in rows:
            print(ligne)
    
        cur.execute("SELECT * FROM poule ORDER by id")
        poules = cur.fetchall()
    
        return render_template("liste_matchs.html", rows=rows, poules=poules, titre="Matchs:")

    else:
        # Gérez ici le cas où id_tournoi est 'non_def'
        # Par exemple, vous pouvez choisir d'afficher tous les matchs ou aucun match
        # Dans cet exemple, nous choisissons d'afficher tous les matchs
        script = "SELECT * FROM match"
        cur.execute(script)
        
@app.route('/tri_par_poule', methods=['GET', 'POST'])
def trier_par_poules():
    if request.method == 'POST':
        poule_selectionnee = request.form['poules']
        script = "SELECT * FROM match WHERE n_poule = ?"
        params = (poule_selectionnee,)
        tab_nom_poule = []
        tab_nom_poule.append(poule_selectionnee)
        con = sqlite3.connect("database.db")
        con.row_factory = sqlite3.Row

        cur = con.cursor()
        cur.execute(script, params)
        rows = cur.fetchall()
        cur.execute("SELECT * FROM poule ORDER by id")
        poules = cur.fetchall()
        
    return render_template("liste_matchs.html", rows=rows, poules =poules, titre ="Matchs de la "+str(poule_selectionnee))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=False, use_reloader=True, debug=True)
