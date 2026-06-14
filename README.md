# Agente Licitaciones — Speech Psychology SPA
## Deploy en Railway via GitHub (guía paso a paso)

---

## PASO 1 — Subir a GitHub

1. Ve a **github.com** → botón verde **"New"** (repositorio nuevo)
2. Nombre: `agente-licitaciones-speech`
3. Privado ✅ (importante, tiene credenciales)
4. Click **"Create repository"**

En tu PC, abre una terminal en la carpeta del proyecto:
```bash
git init
git add .
git commit -m "Agente licitaciones Speech Psychology SPA"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/agente-licitaciones-speech.git
git push -u origin main
```

---

## PASO 2 — Crear proyecto en Railway

1. Ve a **railway.app** → "Start a New Project"
2. Click **"Deploy from GitHub repo"**
3. Conecta tu cuenta GitHub si no lo has hecho
4. Selecciona el repo `agente-licitaciones-speech`
5. Railway lo detecta automáticamente como Python ✅

---

## PASO 3 — Configurar variables de entorno en Railway

En Railway → tu proyecto → pestaña **"Variables"** → agrega estas:

| Variable | Valor |
|----------|-------|
| `ANTHROPIC_API_KEY` | `C1148555-988E-40E5-9115-809B36F23168` |
| `TWILIO_ACCOUNT_SID` | `ACb2cf54ea628757ed7f0a192c644941dc` |
| `TWILIO_AUTH_TOKEN` | `528c97454ff151fce7c86eedae09852f` |
| `TWILIO_WHATSAPP_FROM` | `whatsapp:+14155238886` |
| `WHATSAPP_DESTINO` | `whatsapp:+56978426971` |
| `SCORE_MINIMO` | `60` |

---

## PASO 4 — Configurar como Worker (no web)

En Railway → tu proyecto → pestaña **"Settings"**:
- **Start command**: `python agente.py`
- **Service type**: Worker

---

## PASO 5 — Deploy

Railway hace el deploy automático. En los logs verás:

```
=======================================================
AGENTE LICITACIONES — SPEECH PSYCHOLOGY SPA
=======================================================
Empresa  : SPEECH PSYCHOLOGY SPA
RUT      : 78.254.509-4
WhatsApp : whatsapp:+56978426971
Score min: 60/100
Deploy   : Railway (worker 24/7)
=======================================================
[HH:MM:SS] Consultando MercadoPublico...
  'salud': 12 encontradas
  'médico': 8 encontradas
  ...
Agente corriendo. Ciclo cada hora + resumen 8:00 AM.
```

Y recibirás un WhatsApp de confirmación con el primer ciclo.

---

## ACTUALIZACIONES FUTURAS

Cada vez que hagas cambios al código, solo:
```bash
git add .
git commit -m "descripcion del cambio"
git push
```
Railway hace el redeploy automático en ~30 segundos.

---

## ESTRUCTURA DEL REPO

```
agente-licitaciones-speech/
├── agente.py           ← Monitor principal (corre 24/7)
├── preparar_anexos.py  ← Llena documentos con firma
├── firma_timbre.png    ← Tu firma y timbre
├── requirements.txt    ← Dependencias Python
├── Procfile            ← Instrucción para Railway
├── runtime.txt         ← Python 3.11
├── .gitignore          ← Excluye archivos temporales
└── README.md           ← Esta guía
```

---

## COSTOS RAILWAY

| Plan | Precio | Incluye |
|------|--------|---------|
| Hobby (gratis) | $0 | 500 horas/mes (~21 días) |
| **Developer** | **$5 USD/mes** | **Ilimitado 24/7** ← recomendado |

Para un agente que corre 24/7 necesitas el plan Developer ($5/mes).

---

## RECORDATORIO TWILIO SANDBOX

El sandbox de WhatsApp expira cada 72 horas.
Para renovar, envía desde tu WhatsApp al +1 415 523 8886:
```
join require-land
```

Para uso permanente sin expiración: activa un número Twilio real (~$1 USD/mes).

---

Speech Psychology SPA · contacto@speechpsychology.cl · +56978426971
