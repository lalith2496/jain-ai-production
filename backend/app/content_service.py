import io,re
from app.chunking import chunk_text
from app.embedding_service import create_embedding
from app.database import get_connection
def extract_sections(name,raw):
    if name.lower().endswith('.pdf'):
        from pypdf import PdfReader
        r=PdfReader(io.BytesIO(raw)); out=[]
        for i,p in enumerate(r.pages,1):
            t=(p.extract_text() or '').strip()
            if t: out.append({'title':f'Page {i}','body':t})
        return out
    t=raw.decode('utf-8',errors='replace').strip()
    parts=re.split(r'(?m)^#{1,3}\\s+',t)
    if len(parts)>1:
        out=[]
        for p in parts[1:]:
            ls=p.strip().splitlines()
            if ls: out.append({'title':ls[0],'body':'\\n'.join(ls[1:]).strip()})
        return out
    return [{'title':'Full text','body':t}] if t else []
def index_content(cid):
    with get_connection() as c,c.cursor() as x:
        x.execute('SELECT id,body FROM content_sections WHERE content_id=%s ORDER BY section_index',(cid,)); ss=x.fetchall()
        x.execute('DELETE FROM content_chunks WHERE content_id=%s',(cid,)); n=0
        for s in ss:
            for ch in chunk_text(s['body']):
                x.execute('INSERT INTO content_chunks(content_id,section_id,chunk_index,content,embedding) VALUES(%s,%s,%s,%s,%s)',(cid,s['id'],n,ch,create_embedding(ch))); n+=1
        c.commit(); return {'chunks':n}
