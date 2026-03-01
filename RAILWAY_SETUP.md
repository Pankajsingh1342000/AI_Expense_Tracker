# Deploy Expense AI Agent to Railway

Deploy your FastAPI expense agent to Railway so it runs 24/7 in the cloud—no manual server startup, no billing account issues. Your Android app will call the deployed URL instead of localhost.

---

## Prerequisites

- **GitHub account** (Railway deploys from GitHub)
- **Railway account** – sign up at [railway.app](https://railway.app)
- **OpenRouter API key** (same one you use locally)

---

## Step 1: Push your code to GitHub

If you haven't already:

```bash
cd "c:\Users\Pankaj Singh\expense_agent"
git init
git add .
git commit -m "Initial commit - Expense AI Agent"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/expense_agent.git
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username. Create the repo on GitHub first if needed.

---

## Step 2: Create a Railway project

1. Go to [railway.app](https://railway.app) and log in.
2. Click **New Project**.
3. Choose **Deploy from GitHub repo**.
4. Select your `expense_agent` repository.
5. Railway will detect it as a Python app and start building.

---

## Step 3: Add environment variables

1. Open your service in Railway.
2. Go to the **Variables** tab.
3. Add:
   - **`OPENROUTER_API_KEY`** – your OpenRouter API key (required)

---

## Step 4: (Recommended) Add a volume for persistent data

Without a volume, SQLite data is lost when Railway redeploys. To keep expenses across deploys:

1. In your service, go to **Settings**.
2. Scroll to **Volumes**.
3. Click **Add Volume**.
4. Mount path: `/data`
5. Save. Railway will set `RAILWAY_VOLUME_MOUNT_PATH` automatically; your app uses it for the database path.

---

## Step 5: Generate a public URL

1. Go to the **Settings** tab of your service.
2. Under **Networking**, click **Generate Domain**.
3. Railway assigns a URL like: `https://expense-agent-production-xxxx.up.railway.app`

This is your **base URL**—your Android app will use it.

---

## Step 6: Deploy

Railway deploys automatically when you push to GitHub. To trigger a deploy:

- Push new commits: `git push origin main`
- Or in the Railway dashboard: **Deployments** → **Redeploy**

---

## Android integration

### Base URL

Use your Railway domain (e.g. `https://expense-agent-production-xxxx.up.railway.app`).

### Endpoint

| Method | Path | Body | Response |
|--------|------|------|----------|
| GET | `/` | — | `{"messege": "Expense AI Agent Running"}` |
| POST | `/ask` | `{"query": "Add 500 for food"}` | `{"response": "Expense added successfully."}` |

### Example (Kotlin / Retrofit)

```kotlin
interface ExpenseApi {
    @POST("/ask")
    suspend fun ask(@Body body: QueryBody): ResponseBody
}

data class QueryBody(val query: String)

// Usage
val api = Retrofit.Builder()
    .baseUrl("https://YOUR-RAILWAY-URL.up.railway.app")
    .build()
    .create(ExpenseApi::class.java)

val response = api.ask(QueryBody(query = "Add 300 for transport"))
```

### Example (HTTP URLConnection)

```kotlin
val url = URL("https://YOUR-RAILWAY-URL.up.railway.app/ask")
val conn = url.openConnection() as HttpURLConnection
conn.requestMethod = "POST"
conn.setRequestProperty("Content-Type", "application/json")
conn.doOutput = true
conn.outputStream.use { it.write("""{"query":"Add 200 for lunch"}""".toByteArray()) }
val response = conn.inputStream.bufferedReader().readText()
```

---

## Summary

| Step | Action |
|------|--------|
| 1 | Push code to GitHub |
| 2 | New Railway project → Deploy from GitHub repo |
| 3 | Add `OPENROUTER_API_KEY` in Variables |
| 4 | (Optional) Add volume, mount path `/data` |
| 5 | Generate Domain under Networking |
| 6 | Use `https://YOUR-APP.up.railway.app/ask` in your Android app |

No billing setup required—Railway offers a free trial with $5 credit. After that, usage-based pricing applies, but for a small expense API it stays low.
