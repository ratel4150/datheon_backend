# File: datheon-api/app/services/leads.py
"""
Lead scoring simple basado en reglas + señales del formulario.
Sin ML por ahora — fácil de reemplazar con un modelo real después.
"""

BUDGET_SCORES = {
    ">50k":    1.0,
    "15k-50k": 0.8,
    "5k-15k":  0.5,
    "<5k":     0.2,
}

PROJECT_SCORES = {
    "ai":    1.0,   # mayor valor para Datheon
    "cloud": 0.9,
    "iot":   0.85,
    "saas":  0.8,
    "mobile":0.7,
    "odoo":  0.75,
    "other": 0.4,
}

def score_lead(
    presupuesto: str | None,
    tipo_proyecto: str | None,
    empresa: str | None,
    mensaje: str | None,
) -> dict:
    score = 0.0
    weights = 0.0

    # Presupuesto (peso 40%)
    if presupuesto and presupuesto in BUDGET_SCORES:
        score += BUDGET_SCORES[presupuesto] * 0.4
        weights += 0.4

    # Tipo de proyecto (peso 35%)
    if tipo_proyecto and tipo_proyecto in PROJECT_SCORES:
        score += PROJECT_SCORES[tipo_proyecto] * 0.35
        weights += 0.35

    # Tiene empresa (peso 15%)
    if empresa and len(empresa.strip()) > 2:
        score += 1.0 * 0.15
        weights += 0.15

    # Tiene mensaje detallado (peso 10%)
    if mensaje and len(mensaje.strip()) > 50:
        score += 1.0 * 0.1
        weights += 0.1

    # Normalizar si no todos los campos están presentes
    final_score = score / weights if weights > 0 else 0.3

    # Tier
    if final_score >= 0.75:
        tier = "hot"
        action = "Contactar en menos de 2 horas — alta probabilidad de conversión"
    elif final_score >= 0.45:
        tier = "warm"
        action = "Enviar propuesta personalizada en 24 horas"
    else:
        tier = "cold"
        action = "Agregar a secuencia de nurturing por email"

    return {
        "score": round(final_score, 2),
        "tier": tier,
        "recommended_action": action,
    }
