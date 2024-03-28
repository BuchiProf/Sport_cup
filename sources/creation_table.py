############################################
# Le programme qui créé la base de donnée  #
# (à n'éxécuter qu'une seule fois)         #
############################################
import sqlite3

conn = sqlite3.connect('database.db')
# par défaut les clé étrangères sont désactivées donc on active ici le booléen
conn.execute("PRAGMA foreign_keys = 1")
print("Base de donnée ouverte")

conn.execute('CREATE TABLE if not exists tournoi(id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE, nom TEXT, sport  TEXT, date TEXT)')
conn.execute('CREATE TABLE if not exists poule(id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE, nom  TEXT, id_tournoi, FOREIGN KEY(id_tournoi) REFERENCES tournoi(id))')
conn.execute("CREATE TABLE if not exists equipe(id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE, nom  TEXT, point INTEGER DEFAULT 0, poule_id INTEGER , FOREIGN KEY(poule_id) REFERENCES poule(id))")
conn.execute("CREATE TABLE if not exists match(id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE, id_tournoi INTEGER, n_poule TEXT, equipe1  TEXT, equipe2 TEXT, score_equipe1 INTEGER, score_equipe2 INTEGER, date TEXT  DEFAULT NULL, heurre TEXT DEFAULT NULL, lieu TEXT DEFAULT NULL, FOREIGN KEY(equipe1) REFERENCES equipe(nom),FOREIGN KEY(equipe2) REFERENCES equipe(nom))")

print("Table créée")
conn.close()