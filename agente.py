#!/usr/bin/env python3
"""
Agente de Licitaciones - Speech Psychology SPA
Monitor MercadoPublico + Análisis IA + Alertas WhatsApp
Deploy: Railway (worker 24/7)
"""

import os
import json
import time
import requests
import schedule
import anthropic
from datetime import datetime
from twilio.rest import Client
from pathlib import Path

# ============================================================
# CONFIGURACIÓN SPEECH PSYCHOLOGY SPA
# ============================================================
EMPRESA = {
    "razon_social": "SPEECH PSYCHOLOGY SPA",
    "rut": "78.254.509-4",
    "giro": "Servicios de Atención de Salud Humana Médicos y No Médicos",
    "codigo_actividad": "869091",
    "direccion": "Vic. Mackenna Pte. 6843 Of. 504 Torre A, La Florida",
    "comuna": "La Florida",
    "region": "Metropolitana",
    "representante_legal": "Jorge Ignacio Miranda López",
    "rut_rep_legal": "18.953.982-7",
    "cargo_rep_legal": "Representante Legal",
    "profesion_rep_legal": "Fonoaudiólogo",
    "email": "contacto@speechpsychology.cl",
    "telefono": "+56978426971",
    "tipo_empresa": "Sociedad por Acciones (SpA)",
    "segmento": "Micro Empresa",
    "inicio_actividades": "22-09-2025",
}

# ============================================================
# CREDENCIALES — desde variables de entorno de Railway
# ============================================================
ANTHROPIC_API_KEY    = os.environ.get("ANTHROPIC_API_KEY", "")
TWILIO_ACCOUNT_SID   = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN    = os.environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_FROM = os.environ.get("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
WHATSAPP_DESTINO     = os.environ.get("WHATSAPP_DESTINO",     "whatsapp:+56978426971")
TOKEN_MERCADOPUBLICO = os.environ.get("TOKEN_MERCADOPUBLICO", "")
SCORE_MINIMO_ALERTA  = int(os.environ.get("SCORE_MINIMO", "60"))

# ============================================================
# KEYWORDS — búsqueda espaciada para evitar límite API 429
# ============================================================
API_MERCADOPUBLICO = "https://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json"

KEYWORDS_BUSQUEDA = [
    "salud",
    "enfermeria",
    "kinesiologo",
    "fonoaudiologo",
    "TENS",
    "auxiliar servicio",
    "prestaciones salud",
    "atencion primaria",
    "medico",
    "clinico",
]

ARCHIVO_PROCESADAS = Path("/tmp/licitaciones_procesadas.json")


def cargar_procesadas():
    if ARCHIVO_PROCESADAS.exists():
        with open(ARCHIVO_PROCESADAS) as f:
            return json.load(f)
    return {}


def guardar_procesada(codigo, datos):
    procesadas = cargar_procesadas()
    procesadas[codigo] = {
        "fecha": datetime.now().isoformat(),
        "titulo": datos.get("Nombre", "")[:80],
        "score": datos.get("score", 0)
    }
    with open(ARCHIVO_PROCESADAS, "w") as f:
        json.dump(procesadas, f, ensure_ascii=False, indent=2)


def obtener_licitaciones_salud():
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Consultando MercadoPublico...")
    licitaciones = []
    codigos_vistos = set()

    for keyword in KEYWORDS_BUSQUEDA:
        try:
            params = {"nombre": keyword, "estado": "publicada"}
            if TOKEN_MERCADOPUBLICO:
                params["ticket"] = TOKEN_MERCADOPUBLICO

            resp = requests.get(API_MERCADOPUBLICO, params=params, timeout=15)

            if resp.status_code == 200:
                nuevas = resp.json().get("Listado", [])
                print(f"  '{keyword}': {len(nuevas)} encontradas")
                for lit in nuevas:
                    codigo = lit.get("CodigoExterno", "")
                    if codigo and codigo not in codigos_vistos:
                        codigos_vistos.add(codigo)
                        licitaciones.append(lit)
            elif resp.status_code == 429:
                print(f"  '{keyword}': límite API alcanzado, esperando 30s...")
                time.sleep(30)
                # Reintentar una vez
                resp2 = requests.get(API_MERCADOPUBLICO, params=params, timeout=15)
                if resp2.status_code == 200:
                    nuevas = resp2.json().get("Listado", [])
                    print(f"  '{keyword}' (reintento): {len(nuevas)} encontradas")
                    for lit in nuevas:
                        codigo = lit.get("CodigoExterno", "")
                        if codigo and codigo not in codigos_vistos:
                            codigos_vistos.add(codigo)
                            licitaciones.append(lit)
            elif resp.status_code == 203:
                print(f"  '{keyword}': sin resultados (203)")
            else:
                print(f"  '{keyword}': Error {resp.status_code}")

        except Exception as e:
            print(f"  Error '{keyword}': {e}")

        # Pausa de 8 segundos entre cada keyword para no saturar la API
        time.sleep(8)

    print(f"  Total únicas: {len(licitaciones)}")
    return licitaciones


def analizar_con_ia(licitacion):
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    prompt = f"""Eres experto en licitaciones públicas de salud en Chile (MercadoPublico).

EMPRESA POSTULANTE:
- Razón Social: {EMPRESA['razon_social']}
- RUT: {EMPRESA['rut']}
- Giro: {EMPRESA['giro']}
- Tipo: {EMPRESA['tipo_empresa']} ({EMPRESA['segmento']})
- Inicio actividades: {EMPRESA['inicio_actividades']}
- Profesionales: Fonoaudiólogos, TENS, Kinesiólogos, Enfermeros, Auxiliares

LICITACIÓN:
{json.dumps(licitacion, ensure_ascii=False, indent=2)[:2000]}

Responde SOLO en JSON válido (sin texto extra):
{{
  "score": <0-100>,
  "conveniente": <true/false>,
  "resumen": "<2 oraciones>",
  "fortalezas": ["<f1>", "<f2>"],
  "riesgos": ["<r1>"],
  "documentos_requeridos": ["<doc1>", "<doc2>", "<doc3>"],
  "monto_estimado": "<monto CLP o No especificado>",
  "plazo_postulacion": "<días o fecha cierre>",
  "recomendacion": "<Postular / Revisar / No postular>"
}}

Scoring: 80-100=Excelente, 60-79=Buena, 40-59=Con riesgos, 0-39=No alineada"""

    try:
        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}]
        )
        texto = msg.content[0].text.strip()
        if "```" in texto:
            for parte in texto.split("```"):
                p = parte.strip().lstrip("json").strip()
                if p.startswith("{"):
                    texto = p
                    break
        return json.loads(texto)
    except Exception as e:
        print(f"  Error IA: {e}")
        return {
            "score": 50, "conveniente": True,
            "resumen": "No se pudo analizar automáticamente.",
            "fortalezas": ["Relacionada con salud"],
            "riesgos": ["Revisar manualmente"],
            "documentos_requeridos": ["Ver bases en portal"],
            "monto_estimado": "Ver portal",
            "plazo_postulacion": "Ver portal",
            "recomendacion": "Revisar con cuidado"
        }


def enviar_whatsapp(licitacion, analisis):
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    score = analisis.get("score", 0)
    nivel = "🟢 ALTA OPORTUNIDAD" if score >= 80 else ("🟡 BUENA OPORTUNIDAD" if score >= 60 else "🟠 REVISAR")
    nombre    = licitacion.get("Nombre", "Sin nombre")[:80]
    organismo = licitacion.get("Nombre Organismo", "No especificado")[:50]
    codigo    = licitacion.get("CodigoExterno", "")
    docs      = analisis.get("documentos_requeridos", [])[:3]
    docs_txt  = "\n".join([f"  • {d}" for d in docs]) if docs else "  • Ver bases"
    url = f"https://www.mercadopublico.cl/Procurement/Modules/RFB/DetailsAcquisition.aspx?idlicitacion={codigo}"

    cuerpo = f"""{nivel} — Score: {score}/100

*{nombre}*

🏥 {organismo}
💰 {analisis.get('monto_estimado','Ver portal')}
⏰ Plazo: {analisis.get('plazo_postulacion','Ver portal')}
📋 {codigo}

*Documentos clave:*
{docs_txt}

*Recomendación:* {analisis.get('recomendacion','Revisar')}

👉 {url}

_Speech Psychology SPA · Agente Licitaciones_"""

    try:
        msg = client.messages.create(
            from_=TWILIO_WHATSAPP_FROM,
            body=cuerpo,
            to=WHATSAPP_DESTINO
        )
        print(f"  WhatsApp enviado ✓ ({msg.sid[:20]}...)")
        return True
    except Exception as e:
        print(f"  Error WhatsApp: {e}")
        return False


def procesar_ciclo():
    print(f"\n{'='*55}")
    print(f"CICLO — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*55}")
    procesadas   = cargar_procesadas()
    licitaciones = obtener_licitaciones_salud()
    nuevas = alertas = 0

    for lit in licitaciones:
        codigo = lit.get("CodigoExterno", "")
        if not codigo or codigo in procesadas:
            continue
        nuevas += 1
        print(f"\n[Nueva] {codigo}: {lit.get('Nombre','')[:55]}...")
        print("  Analizando con IA...")
        analisis = analizar_con_ia(lit)
        score = analisis.get("score", 0)
        print(f"  Score: {score}/100 — {analisis.get('recomendacion','')}")
        lit["score"] = score
        guardar_procesada(codigo, lit)
        if score >= SCORE_MINIMO_ALERTA:
            enviar_whatsapp(lit, analisis)
            alertas += 1
        time.sleep(2)

    print(f"\nResumen: {nuevas} nuevas · {alertas} alertas enviadas\n")


def resumen_diario():
    procesadas = cargar_procesadas()
    hoy   = datetime.now().strftime("%Y-%m-%d")
    hoy_p = {k: v for k, v in procesadas.items() if v.get("fecha","").startswith(hoy)}
    alta  = sum(1 for v in hoy_p.values() if v.get("score",0) >= 80)
    media = sum(1 for v in hoy_p.values() if 60 <= v.get("score",0) < 80)
    baja  = sum(1 for v in hoy_p.values() if v.get("score",0) < 60)
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    cuerpo = f"""📊 *RESUMEN DIARIO — {hoy}*
Speech Psychology SPA

Licitaciones analizadas hoy: {len(hoy_p)}

🟢 Alta oportunidad: {alta}
🟡 Buena oportunidad: {media}
🔴 No convenientes: {baja}

_Agente activo 24/7 en Railway_"""
    try:
        client.messages.create(from_=TWILIO_WHATSAPP_FROM, body=cuerpo, to=WHATSAPP_DESTINO)
        print("Resumen diario enviado.")
    except Exception as e:
        print(f"Error resumen: {e}")


def main():
    print("="*55)
    print("AGENTE LICITACIONES — SPEECH PSYCHOLOGY SPA")
    print("="*55)
    print(f"Empresa  : {EMPRESA['razon_social']}")
    print(f"RUT      : {EMPRESA['rut']}")
    print(f"WhatsApp : {WHATSAPP_DESTINO}")
    print(f"Score min: {SCORE_MINIMO_ALERTA}/100")
    print("="*55)

    procesar_ciclo()

    schedule.every(1).hours.do(procesar_ciclo)
    schedule.every().day.at("08:00").do(resumen_diario)

    print("Agente corriendo. Ciclo cada hora + resumen 8:00 AM.\n")
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()
