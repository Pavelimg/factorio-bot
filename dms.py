from sqlite3 import connect
con = connect("db.db")
cur = con.cursor()


def db_request(request: str):
    req = cur.execute(request)
    con.commit()
    return req