# llms-txt-generator

Genera el fichero `llms.txt` de un sitio web a partir de su sitemap, para que ChatGPT, Claude, Perplexity y Google AI Overviews entiendan qué contenido tiene y cómo está organizado.

## El problema

`robots.txt` le dice a un rastreador qué **no** puede leer. No existe el equivalente para decirle a un modelo de lenguaje qué **sí** merece la pena leer.

Cuando alguien pregunta a ChatGPT por un servicio, el modelo tiene que deducir de qué va un sitio a partir de HTML lleno de menús, banners de cookies y scripts. La propuesta [llms.txt](https://llmstxt.org/) resuelve eso con un fichero en la raíz del dominio, en Markdown, que resume el sitio y enlaza su contenido relevante con contexto.

Escribirlo a mano es viable con diez páginas. Con doscientas, no.

## Qué hace

1. Localiza los sitemaps del dominio (en `robots.txt` y en las rutas convencionales, resolviendo índices anidados).
2. Extrae las URLs con su `lastmod`.
3. Descarga cada página y saca título, meta description y, si no la hay, el `<h1>`.
4. Clasifica cada URL en secciones (Servicios, Contenido y guías, Casos, Contacto…) según patrones de ruta.
5. Escribe un `llms.txt` en Markdown, agrupado y priorizado.

## Uso

```bash
pip install -r requirements.txt

python generate_llms_txt.py https://ejemplo.com
python generate_llms_txt.py https://ejemplo.com --max-urls 300 --output public/llms.txt
```

| Opción | Por defecto | Para qué |
|---|---|---|
| `--output` / `-o` | `llms.txt` | Ruta del fichero generado |
| `--max-urls` | `100` | Tope de URLs a analizar |
| `--delay` | `0.3` | Segundos entre peticiones, para no saturar el servidor |

Después, sube el fichero a la raíz: `https://ejemplo.com/llms.txt`.

## Ejemplo de salida

```markdown
# Clínica Veterinaria Ejemplo

> Hospital veterinario en Sevilla con urgencias 24 h, cirugía y diagnóstico por imagen.

Este fichero sigue la propuesta llms.txt para orientar a los modelos de lenguaje
sobre el contenido de este sitio.

## Servicios

- [Urgencias 24 horas](https://ejemplo.com/urgencias): Atención veterinaria de urgencia sin cita previa, todos los días del año.
- [Cirugía](https://ejemplo.com/cirugia): Quirófano propio y equipo de anestesia monitorizada.

## Contenido y guías

- [Cómo detectar una torsión gástrica](https://ejemplo.com/blog/torsion-gastrica): Señales de alarma y qué hacer en las primeras horas.
```

## Decisiones de diseño

**Sitemap en lugar de rastreo propio.** Un crawler recursivo es más completo pero mucho más lento y agresivo con el servidor. El sitemap ya contiene las páginas que el sitio considera indexables, que es exactamente el conjunto que interesa.

**Clasificación por patrones de ruta.** Se podría clasificar con un LLM, pero eso añade coste, latencia y una dependencia externa para un problema que las convenciones de URL resuelven bien en la mayoría de sitios. Los patrones están en `SECTION_LABELS`, al principio del fichero, y se amplían en una línea.

**Fallback al `<h1>`.** Muchas páginas no tienen meta description. Sin ese fallback, la mitad de las entradas saldrían sin contexto, que es justo lo que aporta valor al modelo.

**Límite de profundidad en índices anidados.** Los sitemaps pueden referenciarse en círculo. El corte a dos niveles evita el bucle infinito sin renunciar a la estructura habitual de índice → sitemaps por tipo.

## Limitaciones conocidas

- No ejecuta JavaScript, así que en sitios renderizados en cliente los títulos pueden venir vacíos.
- La clasificación por patrones falla en sitios con URLs opacas (`/p/12345`).
- No detecta contenido duplicado ni canonicals; incluye lo que diga el sitemap.

## Requisitos

Python 3.10 o superior y `requests`.

## Licencia

MIT

## Related tools

Part of a set of nine open-source tools I use on client work — all Python, MIT, deterministic, no API keys:

[geo-check](https://github.com/angelmunizpedraza/geo-check) · [render-gap](https://github.com/angelmunizpedraza/render-gap) · [citeable](https://github.com/angelmunizpedraza/citeable) · [serp-to-ai-diff](https://github.com/angelmunizpedraza/serp-to-ai-diff) · [ai-visibility-tracker](https://github.com/angelmunizpedraza/ai-visibility-tracker) · [linkjuice](https://github.com/angelmunizpedraza/linkjuice) · [seo-audit](https://github.com/angelmunizpedraza/seo-audit) · [ga4-report](https://github.com/angelmunizpedraza/ga4-report)

`geo-check` asks whether the AI crawlers are allowed in. `render-gap` asks whether anything was there when they arrived. `citeable` asks whether it was worth quoting.
