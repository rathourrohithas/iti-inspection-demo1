# Practice site on Render — step-by-step

This puts a **training copy** of the ITI Inspection Portal on the internet, at an address such as `https://iti-inspection-demo.onrender.com`. Staff can then practise with it. It takes about 30 minutes and needs no programming.

The practice site:
- shows a "Practice site" banner;
- lists the sample logins on its sign-in page;
- loads 10 sample ITIs (marked "Sample") with inspections in different stages.

**Use sample data only. This is not a government server.**

## What you need
- A **GitHub** account (free): https://github.com/signup
- A **Render** account (free): https://render.com — sign up with the GitHub account.
- The file `ITI_Inspection_Portal.zip`.

## Step 1 — Put the portal on GitHub (10 minutes)
1. Unzip `ITI_Inspection_Portal.zip` on your computer. You get a folder `iti_portal`.
2. On GitHub, click **New repository**. Name it `iti-inspection-demo`, choose **Private**, and click **Create repository**.
3. On the new repository page, click **uploading an existing file**.
4. Open the `iti_portal` folder, select **everything inside it** (not the folder itself) and drag it into the browser. Wait for the upload to finish, then click **Commit changes**.
5. Check that `render.yaml`, `manage.py` and `requirements.txt` appear at the top level of the repository.

## Step 2 — Create the site on Render (10 minutes)
1. In Render, click **New** → **Blueprint**.
2. Connect GitHub when asked, and choose the `iti-inspection-demo` repository.
3. Render reads `render.yaml` and shows two items: the web service `iti-inspection-demo` and the database `iti-inspection-demo-db`. Click **Apply** / **Deploy Blueprint**.
4. Wait until the web service shows **Live**. The first build takes about 5–10 minutes.
5. Open the web service. The address at the top (`https://iti-inspection-demo.onrender.com` or similar) is the practice link to share with staff.

## Step 3 — Try it
- Open the link. The sign-in page lists the practice logins. The password for all of them is `Sample@2026pass`.
  - `sample.admin` — Directorate administrator: schedule, users, ITIs, settings, dashboard.
  - `sample.viewer` — Directorate officer: dashboard and records, read-only.
  - `sample.lead1` to `sample.lead3` — team leaders.
  - `sample.mem1` to `sample.mem3` — team members.
- To give each trainee their own login, sign in as `sample.admin` and use **Users** → **Add user**.

## Using your own sub-domain (optional)
- To have an address like `demo-itiportal.<your-domain>`:
  1. In Render, open the web service → **Settings** → **Custom Domains** → **Add**, and enter the name.
  2. Render shows a **CNAME** record. Ask the administrator of that domain to add it.
  3. Render issues the HTTPS certificate automatically.
- `gov.in` names are allotted through NIC. Use a government sub-domain only once the site is on approved government hosting.

## Things to know about the free plan
- **First open is slow:** the site sleeps after 15 minutes without visitors, and the first visit after that takes about a minute to load. Open the link a minute before a training session.
- **Monthly limit:** free hours are limited each month (750 per workspace), which is enough for one site running all month.
- **Database expires after 30 days:** the free database is deleted after a 14-day grace period. Before then, either upgrade it to a paid plan from the Render dashboard, or delete and recreate it. Recreating gives a fresh practice site.
- **Uploaded photos are temporary:** they can disappear when the site restarts. Typed entries are kept in the database.
- **Paid plan:** for a longer pilot, the paid "Starter" plans remove the sleep and the database expiry. See current prices at https://render.com/pricing.

## Resetting the practice data
- In Render, open the web service → **Shell**, and run:
  ```
  python manage.py seed_demo --reset
  ```
- This removes every inspection of a sample ITI or with a sample officer on its team, and the sample users, then creates them again. ITIs and users you added yourself are kept.

## Removing the practice site
- In Render, delete the web service and the database.
- On GitHub, delete the repository.
