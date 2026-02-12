# Auth0 Setup Guide for Agentic Trader Platform

This guide walks you through configuring a free Auth0 tenant to secure the platform.

## Prerequisites
- An Auth0 account (Free tier is sufficient). Sign up at [auth0.com](https://auth0.com).

---

## Step 1: Create a Tenant
1.  Log in to your Auth0 Dashboard.
2.  Click the tenant menu in the top left and select **Create Tenant**.
3.  **Domain**: Choose a unique domain (e.g., `agentic-trader-dev`).
4.  **Region**: Choose a region close to you (e.g., `US` or `EU`).
5.  **Environment Tag**: `Development`.
6.  Click **Create**.

---

## Step 2: Configure API (Backend)
This represents your FastAPI backend.

1.  Go to **Applications** > **APIs**.
2.  Click **Create API**.
3.  **Name**: `Agentic Trader API`.
4.  **Identifier**: `https://api.agentic-trader.com` (This will be your `AUTH0_API_AUDIENCE`).
5.  **Signing Algorithm**: `RS256`.
6.  Click **Create**.

### Enable RBAC (Role Based Access Control)
1.  Click the **Settings** tab of your new API.
2.  Scroll down to **RBAC Settings**.
3.  Toggle **Enable RBAC**: `ON`.
4.  Toggle **Add Permissions in the Access Token**: `ON`.
5.  Click **Save**.

---

## Step 3: Configure Application (Frontend)
This represents your Next.js frontend.

1.  Go to **Applications** > **Applications**.
2.  Click **Create Application**.
3.  **Name**: `Agentic Trader Frontend`.
4.  **Application Type**: `Single Page Web Applications`.
5.  Click **Create**.
6.  Click the **Settings** tab.

### Configure URLs
1.  **Allowed Callback URLs**: `http://localhost:3000/api/auth/callback`
2.  **Allowed Logout URLs**: `http://localhost:3000`
3.  **Allowed Web Origins**: `http://localhost:3000`
4.  Scroll down and click **Save Changes**.

---

## Step 4: Create Roles & Users

### Create Roles
1.  Go to **User Management** > **Roles**.
2.  Create the following roles:
    - `admin`: Full access.
    - `trader`: Can execute trades.
    - `viewer`: Read-only access to dashboard.

### Create Permisssions
1.  Go back to **Applications** > **APIs** > **Agentic Trader API** > **Permissions**.
2.  Add the following permissions:
    - `read:dashboard` (Description: View dashboard metrics)
    - `write:orders` (Description: Place and cancel orders)
    - `admin:system` (Description: Manage settings and users)

### Assign Permissions to Roles
1.  Go to **User Management** > **Roles**.
2.  Click `viewer` > **Permissions** > **Add Permissions** > Select API > Add `read:dashboard`.
3.  Click `trader` > **Permissions** > **Add Permissions** > Select API > Add `read:dashboard`, `write:orders`.
4.  Click `admin` > **Permissions** > **Add Permissions** > Select API > Select **All Permissions**.

### Create a Test User
1.  Go to **User Management** > **Users**.
2.  Click **Create User**.
3.  **Email**: `admin@example.com` (or your email).
4.  **Password**: Set a strong password.
5.  **Connection**: `Username-Password-Authentication`.
6.  Click **Create**.
7.  Go to the **Roles** tab of the new user > **Assign Roles** > Select `admin`.

---

## Step 5: Gather Environment Variables

You will need these values for your `.env` file.

1.  **AUTH0_DOMAIN**:
    - Go to **Applications** > **Applications** > **Agentic Trader Frontend** > **Settings**.
    - Copy **Domain** (e.g., `dev-xyz.us.auth0.com`).
2.  **AUTH0_CLIENT_ID**:
    - Copy **Client ID** from the same page.
3.  **AUTH0_CLIENT_SECRET**:
    - Copy **Client Secret** from the same page.
4.  **AUTH0_API_AUDIENCE**:
    - This is the **Identifier** you set in Step 2 (e.g., `https://api.agentic-trader.com`).

---

## Step 6: Update Local Configuration

Update your `backend/.env` (and `frontend/.env.local` later) with:

```env
AUTH0_DOMAIN=agentictrader.eu.auth0.com
AUTH0_API_AUDIENCE=https://api.agentic-trader.com
AUTH0_ISSUER=https://agentictrader.eu.auth0.com/
AUTH0_ALGORITHM=RS256
```
