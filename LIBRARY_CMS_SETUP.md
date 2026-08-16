# Jain AI Library + Content CMS

1. From project root run:
   psql -d jainai -f database/migration_library_cms.sql
2. Backend:
   cd backend
   source .venv/bin/activate
   pip install -r requirements.txt
   uvicorn app.main:app --reload --port 8000
3. Frontend:
   cd frontend && npm install && npm run dev
4. Admin:
   cd admin && npm install && npm run dev

User UI adds Library, Stories and History while the existing Chat component and chat styling are left intact.
Admin Content CMS accepts text-based PDF, TXT and Markdown files and indexes them with the existing local embedding service.
