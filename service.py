import logging
import json
import sqlite3
import time
from urllib.parse import parse_qs
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config

logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename='service.log',level=logging.DEBUG
                    )
logger = logging.getLogger('')
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
logger.addHandler(console)

server_scheme = 'http'
server_host = 'localhost'
server_port = 4000

if server_port is None:
    server = '%s://%s' % (server_scheme, server_host)
else:
    server = '%s://%s:%s' % (server_scheme, server_host, server_port)

from wsgiref.simple_server import make_server
from pyramid.config import Configurator
from pyramid.response import Response

DBNAME = 'annotation.db'

def read(sql):    
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()
    cur.execute(sql)
    result = cur.fetchall()
    cur.close()
    conn.close()
    return result

def write(sql):
    print (sql)
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()
    cur.execute(sql)
    cur.close()
    conn.commit()
    conn.close()

def escape_single_quote(str):
    return str.replace("'", "''")

@view_config( route_name='search' )
def search(request):
    qs = parse_qs(request.query_string)
    uri = qs['uri'][0]
    print (uri)
    sql = f""" select * from annotation where uri = '{uri}' """
    results = read(sql)
    total = len(results)
    rows = []
    for result in results:
        anno = result[2].replace('\n', '\\n')
        rows.append(json.loads(anno))
    payload = json.dumps({
        "total": total,
        "rows": rows
        })
    r = Response(body=payload, content_type='application/json', charset='utf-8')
    return r

@view_config( route_name='create_annotation' )
def create_annotation(request):
    id = str(time.time()).replace('.','')
    anno_json = escape_single_quote(request.text)
    obj = json.loads(anno_json)
    uri = obj['uri']
    obj["id"] = id
    anno_json = json.dumps(obj)
    sql =   f""" insert into annotation (id, uri, anno) values( '{id}', '{uri}', '{anno_json}') """
    write(sql)
    r = Response(body=f'{anno_json}', content_type='application/json', charset='UTF-8')
    return r

def get_annotation(id):
    sql = f""" select anno from annotation where id = '{id}' """
    anno = read(sql)[0][0]
    r = Response(body=f"{anno}", content_type='application/json', charset='UTF-8')
    return r    

def delete_annotation(id):
    sql = f""" delete from annotation where id = '{id}' """
    write(sql)
    r = Response(body=f""" {{"id":"{id}", "deleted": true}} """)
    return r    

def update_annotation(id, request):
    anno_json = escape_single_quote(request.text)
    sql = f""" update annotation set anno = '{anno_json}' where id = '{id}' """
    write(sql)
    return get_annotation(id)
    return r    

@view_config( route_name='annotations' )
def annotations(request):
    id = request.matchdict['id']
    if request.method == 'GET':
        return get_annotation(id)
    if request.method == 'PATCH':
        return update_annotation(id, request)
    if request.method == 'DELETE':
        return delete_annotation(id)

def get_anno_count(uri):
    sql = f""" select count(*) from annotation where uri = '{uri}' """
    r = read(sql)[0][0]
    return r

@view_config( route_name='badge' )
def badge(request):
    qs = parse_qs(request.query_string)
    uri = qs['uri'][0]
    anno_count = get_anno_count(uri)
    if anno_count is None:
        anno_count = 0
    r = Response(f"""{{"total":{anno_count}}}""")
    return r

config = Configurator()

config.scan()

config.add_route('badge', '/badge')
config.add_route('search', '/search')
config.add_route('create_annotation', '/create_annotation')
config.add_route('annotations', '/annotations/{id}')

app = config.make_wsgi_app()

if __name__ == '__main__': 
    print(f'listening on {server_host}:{server_port}')
    server = make_server(server_host, server_port, app)
    server.serve_forever()
    
