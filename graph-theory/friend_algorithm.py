#!/usr/bin/python

from __future__ import division
import pprint
import sqlite3
import csv

sqlite_db = None

def get_db():
    global sqlite_db
    if sqlite_db is None:
        sqlite_db = connect_db()
    return sqlite_db

def connect_db():
    return sqlite3.connect("friends.db")

def insert_friends(edges):
    def normalize_pair(p):
        return ( min(p), max(p) )
    
    db = get_db()
    for vertex_id in edges.keys():
        db.execute(('INSERT INTO vertices (id) VALUES (?)'),
                   [vertex_id])
    
    already_inserted = set()
    
    for first_id, second_id_set in edges.iteritems():
        for second_id in second_id_set:
            pair = normalize_pair((first_id, second_id))
            
            if pair not in already_inserted:
                db.execute(('INSERT INTO '
                            'edges (first_id, second_id) '
                            'VALUES (?, ?)'),
                           [pair[0], pair[1]])
                db.execute(('INSERT INTO '
                            'edges (first_id, second_id) '
                            'VALUES (?, ?)'),
                           [pair[1], pair[0]])
                already_inserted.update([pair])
    
    db.commit()

def is_determinable_many_friends(person_id):
    db = get_db()

    cur = db.execute(('SELECT e2.second_id '
                      'FROM edges AS e1 '
                      'JOIN edges AS e2 ' 
                      '  ON e1.second_id = e2.first_id '
                      'WHERE e1.first_id = :person_id '
                      'GROUP BY e2.second_id '
                      'HAVING COUNT(*) = (SELECT COUNT(*) '
                      '                   FROM edges '
                      '                   WHERE edges.first_id = e1.first_id) '),
                     { "person_id": person_id })
    
    ids = [v[0] for v in cur]
    return len(ids) == 1

def is_determinable_one_friend(person_id):
    db = get_db()
    
    cur = db.execute(('SELECT COUNT(*) = 1 '
                      'FROM (SELECT SUM(e3.second_id != e2.first_id) c '
                      '      FROM edges AS e1 '
                      '      JOIN edges AS e2 '
                      '        ON e1.second_id = e2.first_id '
                      '      JOIN edges AS e3 '
                      '        ON e2.second_id = e3.first_id '
                      '      WHERE e1.first_id = :person_id '
                      '      GROUP BY e2.first_id, e3.second_id '
                      '     ) '
                      'WHERE c = 0 '),
                     { "person_id": person_id })
    
    return cur.fetchone()[0] == 1
    

def is_determinable(person_id):
    db = get_db()
    
    cur = db.execute(('SELECT COUNT(*) FROM edges WHERE first_id = :person_id'),
                     { "person_id": person_id })
    
    num_friends = cur.fetchone()[0]
    
    if num_friends > 1:
        return is_determinable_many_friends(person_id)
    else:
        return is_determinable_one_friend(person_id)

def accuracy_of_graph():
    db = get_db()
    
    cur = db.execute(('SELECT id FROM vertices'))
    person_ids = [v[0] for v in cur]
    
    return [ (person_id, is_determinable(person_id))
             for person_id in person_ids ]

def test_graph_1():
    friends = { 1: { 2, 3, 4 },
                2: { 1, 3 },
                3: { 1, 2, 5, 6 },
                4: { 1, 5, 6 },
                5: { 3, 4, 6 },
                6: { 3, 4, 5, 7 },
                7: { 6 },
                }

    insert_friends(friends)

def test_graph_2():
    friends = { 1: { 5 },
                2: { 6, 7 },
                3: { 6, 7 },
                4: { 6, 7 },
                5: { 1, 6 },
                6: { 2, 3, 4, 5, 7 },
                7: { 2, 3, 4, 6, 8 },
                8: { 7 },
                }
    
    insert_friends(friends)

def test_graph_3():
    friends = { 1: { 4 },
                2: { 4 },
                3: { 4 },
                4: { 1, 2, 3 },
                }
    
    insert_friends(friends)

def show_accuracy_test():
    results = accuracy_of_graph()
    
    for person_id, determinable in results:
        print "%d = %s" % (person_id, str(determinable))

def main():
    headings = ["Num determinable", "Total", "Percentage"]
    for desc, value in zip(headings,
                           accuracy_of_graph()):
        print "%*s %r" % (max(map(len, headings)), desc, value)
        

if __name__ == "__main__":
    main()
