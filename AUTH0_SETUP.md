# Auth0 Setup Guide for Agentic Trader

Deze guide helpt je bij het configureren van Auth0 voor de Agentic Trader applicatie.

## Stap 1: Auth0 Account Aanmaken

1. Ga naar https://auth0.com/signup
2. Maak een gratis account aan (of log in met bestaand account)
3. Kies een tenant naam (bijv. `agentic-trader-dev`)

## Stap 2: Application Configureren

### 2.1 Create Application
1. In Auth0 Dashboard → "Applications" → "Create Application"
2. Naam: `Agentic Trader`
3. Type: **Single Page Web Applications**
4. Klik "Create"

### 2.2 Application Settings
Ga naar de "Settings" tab van je nieuwe application:

**Allowed Callback URLs:**
```
http://localhost:5180/callback
```

**Allowed Logout URLs:**
```
http://localhost:5180/login
```

**Allowed Web Origins:**
```
http://localhost:5180
```

**Allowed Origins (CORS):**
```
http://localhost:5180
```

Klik "Save Changes" onderaan de pagina.

## Stap 3: API Configureren

### 3.1 Create API
1. Ga naar "APIs" → "Create API"
2. Naam: `Agentic Trader API`
3. Identifier: `https://api.agentic-trader.com`
4. Signing Algorithm: **RS256**
5. Klik "Create"

### 3.2 API Permissions (Scopes)
In de API settings, ga naar "Permissions" tab en voeg toe:
- `read:profile` - Lees gebruikersprofiel
- `write:trades` - Plaats trades
- `read:portfolio` - Lees portfolio

## Stap 4: Environment Variables

Kopieer de volgende waarden van je Auth0 dashboard:

### Van Application Settings:
- **Domain** (bijv. `dev-xxx.us.auth0.com`)
- **Client ID** (bijv. `abc123def456ghi789`)

### Van API Settings:
- **Audience** (bijv. `https://api.agentic-trader.com`)

## Stap 5: Configuratie Toepassen

Update het `.env.auth0` bestand:

```bash
# Auth0 Configuration
VITE_AUTH0_DOMAIN=dev-xxx.us.auth0.com
VITE_AUTH0_CLIENT_ID=your_client_id_here
VITE_AUTH0_AUDIENCE=https://api.agentic-trader.com
```

## Stap 6: Stack Starten

```bash
# Stop bestaande containers
docker-compose -f docker/docker-compose.stack.yml down

# Start met Auth0 configuratie
docker-compose -f docker/docker-compose.auth0.yml --env-file .env.auth0 up -d
```

## Stap 7: Testen

1. Open http://localhost:5180/login
2. Klik op "Sign In" of "Try Demo Account"
3. Je wordt doorgestuurd naar Auth0 login pagina
4. Maak een test gebruiker aan in Auth0 (of gebruik bestaande)
5. Na login wordt je terug gestuurd naar de app

## Troubleshooting

### "Invalid token" error
- Controleer of de Audience correct is in zowel frontend als backend
- Controleer of de JWKS URL bereikbaar is

### CORS errors
- Zorg dat http://localhost:5180 is toegevoegd aan Allowed Web Origins
- Controleer ook Allowed Origins (CORS)

### "Unauthorized" error
- Controleer of de gebruiker is toegevoegd aan de Auth0 database
- Controleer of de email is geverifieerd (indien vereist)

## Productie Configuratie

Voor productie deployment:

1. **Custom Domain**: Gebruik je eigen domein in Auth0
2. **HTTPS**: Zorg dat alle URLs https:// gebruiken
3. **Client Secret**: Voor backend-validatie (niet nodig voor SPA)
4. **Rules/Actions**: Voeg custom claims toe zoals tenant_id

### Auth0 Actions (voor tenant_id)

Ga naar "Actions" → "Library" → "Create Action":

```javascript
exports.onExecutePostLogin = async (event, api) => {
  const namespace = 'https://agentic-trader';

  if (event.authorization) {
    api.idToken.setCustomClaim(`${namespace}/tenant_id`, event.user.user_metadata?.tenant_id || 'default');
    api.idToken.setCustomClaim(`${namespace}/roles`, event.user.app_metadata?.roles || ['user']);
  }
};
```

Deploy de action en voeg toe aan de Login flow.

## Belangrijke URLs

| Omgeving | URL |
|----------|-----|
| Auth0 Login | `https://{DOMAIN}/authorize` |
| Auth0 Token | `https://{DOMAIN}/oauth/token` |
| JWKS | `https://{DOMAIN}/.well-known/jwks.json` |
| User Info | `https://{DOMAIN}/userinfo` |

## Ondersteuning

Bij problemen:
1. Controleer Auth0 Logs (Monitoring → Logs)
2. Controleer browser console voor errors
3. Controleer backend logs: `docker logs agentic_trader_api`
