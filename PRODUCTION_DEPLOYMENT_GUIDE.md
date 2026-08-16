# Jain AI — Production Deployment Guide

This is a NEW production-ready copy. The existing local project is not modified.

Recommended first public deployment:

- User frontend: Vercel
- Admin frontend: Vercel
- FastAPI backend: Render
- PostgreSQL + pgvector: Render Postgres
- LLM: Ollama Cloud for the first beta
- Search: Tavily + YouTube

Your local Ollama setup still works. The code switches by environment variables.

---

## A. What changed in this production copy

1. `DATABASE_URL` support for cloud PostgreSQL.
2. Environment-based CORS.
3. Admin password login using a signed HttpOnly session cookie.
4. Admin/crawler/approval endpoints require authentication.
5. Crawler SSRF protections:
   - http/https only
   - blocks localhost/private/link-local/reserved IPs
   - only ports 80/443 by default
   - validates redirects
   - limits response size
6. `/health` liveness endpoint.
7. `/ready` database/config readiness endpoint.
8. Ollama supports:
   - local `http://localhost:11434`
   - direct Ollama Cloud `https://ollama.com` with `OLLAMA_API_KEY`
9. Vercel SPA config for frontend + admin.
10. Render Blueprint (`render.yaml`).
11. Production migration runner.
12. Production schema uses `vector(384)` to match `all-MiniLM-L6-v2`.

---

# PART 1 — PUT THE PROJECT ON GITHUB

Create a new empty GitHub repository, for example:

    jain-ai-production

From this production folder:

    cd /Users/YOUR_USER/Downloads/jain_ai_production_ready

    git init
    git add .
    git commit -m "Production-ready Jain AI"

    git branch -M main
    git remote add origin YOUR_GITHUB_REPOSITORY_URL
    git push -u origin main

Do NOT commit your real `.env`.
The included `.gitignore` blocks it.

---

# PART 2 — CREATE MANAGED POSTGRES ON RENDER

1. Sign in to Render.
2. Choose **New → PostgreSQL**.
3. Name it something like:

       jain-ai-db

4. Choose **Singapore** if your primary audience/backend is in India/Asia.
5. Create the database.
6. In the database dashboard, copy the **Internal Database URL** for the Render backend.
7. You will put this into the backend environment variable:

       DATABASE_URL

The backend pre-deploy migration will run:

- schema
- discovery/graph migration
- library/CMS migration

The schema includes:

    CREATE EXTENSION IF NOT EXISTS vector;

and Render Postgres supports pgvector.

---

# PART 3 — CHOOSE HOW OLLAMA RUNS IN PRODUCTION

## Recommended for your FIRST public beta: Ollama Cloud

This is easier than managing a GPU server.

1. Create/sign in to an Ollama account.
2. Create an Ollama API key.
3. On your Mac test:

       export OLLAMA_API_KEY='YOUR_KEY'

       curl https://ollama.com/api/tags \
         -H "Authorization: Bearer $OLLAMA_API_KEY"

4. Pick a model returned by that endpoint.
5. Test it:

       curl https://ollama.com/api/chat \
         -H "Authorization: Bearer $OLLAMA_API_KEY" \
         -H "Content-Type: application/json" \
         -d '{
           "model": "YOUR_MODEL",
           "messages": [
             {
               "role": "user",
               "content": "Explain Ahimsa in two sentences."
             }
           ],
           "stream": false
         }'

6. In Render backend variables set:

       OLLAMA_URL=https://ollama.com
       OLLAMA_MODEL=YOUR_MODEL
       OLLAMA_API_KEY=YOUR_KEY

The Jain AI code still uses the Ollama API. Only the Ollama host changes.

## If you need your exact local model later

If the exact model you use locally is not listed for direct Ollama Cloud access,
run Ollama on your own Linux/GPU VM instead.

The broad flow is:

    Linux VM
       ↓
    install Ollama
       ↓
    pull model
       ↓
    put Ollama behind a private/authenticated HTTPS endpoint
       ↓
    Render FastAPI calls that endpoint

For a first launch, Ollama Cloud removes an entire server/security layer and is
the safer/easier choice.

---

# PART 4 — DEPLOY FASTAPI ON RENDER

You can use the included `render.yaml` or configure manually.

## Easy manual setup

1. Render → **New → Web Service**
2. Connect the GitHub repo.
3. Select the repository.
4. Settings:

       Name: jain-ai-api
       Region: Singapore
       Root Directory: backend
       Runtime: Python
       Build Command:
         pip install -r requirements.txt

       Pre-Deploy Command:
         python scripts/run_migrations.py

       Start Command:
         uvicorn app.main:app --host 0.0.0.0 --port $PORT

       Health Check Path:
         /health

5. Add environment variables:

       DATABASE_URL=<Render Internal Database URL>

       TAVILY_API_KEY=<your key>
       YOUTUBE_API_KEY=<your key>
       WEB_SEARCH_MODE=always

       OLLAMA_URL=https://ollama.com
       OLLAMA_MODEL=<your chosen cloud model>
       OLLAMA_API_KEY=<your Ollama API key>

       ADMIN_PASSWORD=<a long admin password>

       ADMIN_SESSION_SECRET=<generate a long random value>

       ADMIN_COOKIE_SECURE=true
       ADMIN_COOKIE_SAMESITE=none

For the FIRST backend deploy, temporarily use:

       ALLOWED_ORIGINS=https://example.com

We replace it after Vercel provides the two frontend URLs.

6. Deploy.

After deployment Render provides a URL similar to:

       https://jain-ai-api.onrender.com

Test:

       https://jain-ai-api.onrender.com/health

Expected:

       {"status":"ok", ...}

Then test:

       https://jain-ai-api.onrender.com/ready

---

# PART 5 — DEPLOY USER WEBSITE ON VERCEL

1. Sign in to Vercel.
2. Choose **Add New → Project**.
3. Import your GitHub repository.
4. Set **Root Directory**:

       frontend

5. Framework should be detected as Vite.
6. Build command:

       npm run build

7. Output directory:

       dist

8. Add environment variable:

       VITE_API_URL=https://jain-ai-api.onrender.com

9. Deploy.

Vercel gives a URL such as:

       https://jain-ai-production.vercel.app

Save this URL.

---

# PART 6 — DEPLOY ADMIN WEBSITE ON VERCEL

Create a SECOND Vercel project from the SAME GitHub repository.

1. Vercel → **Add New → Project**
2. Import the same repo.
3. Root Directory:

       admin

4. Build command:

       npm run build

5. Output directory:

       dist

6. Environment variable:

       VITE_API_URL=https://jain-ai-api.onrender.com

7. Deploy.

Example:

       https://jain-ai-admin.vercel.app

The production Admin UI now displays a login page.
The password is the `ADMIN_PASSWORD` stored only on Render.

---

# PART 7 — FIX CORS AFTER BOTH VERCEL URLS EXIST

Go back to the Render FastAPI service.

Set:

    ALLOWED_ORIGINS=https://jain-ai-production.vercel.app,https://jain-ai-admin.vercel.app

Save and redeploy/restart.

Because the admin site and API initially live on different provider domains,
keep:

    ADMIN_COOKIE_SECURE=true
    ADMIN_COOKIE_SAMESITE=none

Now test the Admin URL and sign in.

---

# PART 8 — CUSTOM DOMAIN

A clean final setup is:

    jainlibrary.in
        → Vercel user frontend

    admin.jainlibrary.in
        → Vercel admin frontend

    api.jainlibrary.in
        → Render FastAPI

After these custom domains work, change:

    ALLOWED_ORIGINS=https://jainlibrary.in,https://admin.jainlibrary.in

You can then use:

    ADMIN_COOKIE_SAMESITE=lax

because the frontend/admin/API are under the same site.

Do not expose PostgreSQL or Ollama credentials to Vite.
Only the backend gets secrets.

---

# PART 9 — LOCAL DEVELOPMENT STILL WORKS

Backend `.env` can still contain:

    POSTGRES_HOST=localhost
    POSTGRES_PORT=5432
    POSTGRES_DB=jainai
    POSTGRES_USER=YOUR_LOCAL_USER

    OLLAMA_URL=http://localhost:11434
    OLLAMA_MODEL=qwen3.5:4b

    ALLOWED_ORIGINS=http://localhost:5173,http://localhost:5174

    ADMIN_PASSWORD=local-admin-password
    ADMIN_SESSION_SECRET=local-session-secret
    ADMIN_COOKIE_SECURE=false
    ADMIN_COOKIE_SAMESITE=lax

No Ollama cloud key is required locally.

---

# PART 10 — IMPORTANT PRODUCTION CHECKS

Before announcing the site publicly:

- `/health` returns 200
- `/ready` returns 200
- Chat streaming works
- Tavily search works
- YouTube search works
- Source discovery appears in Admin
- Admin requires login
- Approve & Index works
- pgvector retrieval works
- Knowledge graph extraction works
- Library/Stories/History load
- Book reader works
- Full book rights metadata is correct
- No `.env` or API key is present in GitHub
- `/api/crawl` returns 401 when not logged in
- private/local crawler destinations return 400
- admin logout works

---

# SECURITY NOTE

The crawler protections in this starter block common SSRF targets and validate
redirect destinations. For a high-security deployment, also consider outbound
network egress controls at the hosting/network layer, because DNS rebinding and
other advanced SSRF techniques are best mitigated with both application and
network controls.
