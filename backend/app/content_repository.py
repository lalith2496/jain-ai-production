import re
from app.database import get_connection
def slugify(v): return re.sub(r'[^a-zA-Z0-9]+','-',v.lower()).strip('-') or 'content'
def list_content(content_type=None,status='published',limit=200):
    w=[]; p=[]
    if content_type: w.append('content_type=%s'); p.append(content_type)
    if status: w.append('status=%s'); p.append(status)
    q='SELECT * FROM content_items'+((' WHERE '+' AND '.join(w)) if w else '')+' ORDER BY featured DESC,updated_at DESC LIMIT %s'; p.append(limit)
    with get_connection() as c, c.cursor() as x: x.execute(q,p); return x.fetchall()
def get_content(key):
    f='id' if str(key).isdigit() else 'slug'
    with get_connection() as c, c.cursor() as x:
        x.execute(f'SELECT * FROM content_items WHERE {f}=%s',(key,)); i=x.fetchone()
        if not i: return None
        x.execute('SELECT * FROM content_sections WHERE content_id=%s ORDER BY section_index',(i['id'],)); i['sections']=x.fetchall(); return i
def create_content(d,sections):
    with get_connection() as c, c.cursor() as x:
        base=slugify(d['title']); slug=base; n=2
        while True:
            x.execute('SELECT 1 FROM content_items WHERE slug=%s',(slug,))
            if not x.fetchone(): break
            slug=f'{base}-{n}'; n+=1
        x.execute('INSERT INTO content_items(content_type,title,slug,author,language,category,summary,rights_status,rights_note,status,reading_minutes) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id',(d['content_type'],d['title'],slug,d.get('author'),d.get('language','English'),d.get('category'),d.get('summary'),d.get('rights_status','original'),d.get('rights_note'),d.get('status','draft'),d.get('reading_minutes',0)))
        cid=x.fetchone()['id']
        for n,s in enumerate(sections,1): x.execute('INSERT INTO content_sections(content_id,section_index,title,body) VALUES(%s,%s,%s,%s)',(cid,n,s.get('title') or f'Section {n}',s['body']))
        c.commit()
    return get_content(cid)
def set_status(cid,status):
    with get_connection() as c,c.cursor() as x:
        x.execute('UPDATE content_items SET status=%s,updated_at=NOW() WHERE id=%s RETURNING *',(status,cid)); r=x.fetchone(); c.commit(); return r
