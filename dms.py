from sqlite3 import connect
con = connect("db.db")
cur = con.cursor()


def db_request(request: str):
    return cur.execute(request)
