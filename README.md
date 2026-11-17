# Inseguridad alimentaria en el Perú, 2025

Mapa de la población con inseguridad alimentaria moderada o severa por departamento

![Mapa de inseguridad alimentaria por departamento, 2025](salida/mapa_inseguridad_alimentaria_2025.png)

## Qué muestra

- En 2025, el 30,5% de la población vivió inseguridad alimentaria moderada o severa.
- Loreto (46,9%) y Puno (43,4%) tienen las cifras más altas; Moquegua (13,7%), la más baja.
- Solo cinco departamentos superan con claridad el promedio nacional: Loreto, Puno, Piura, Ucayali y Lambayeque. "Con claridad" significa que su intervalo de confianza al 95% no se cruza con el nacional; es una regla práctica, no una prueba estadística formal.
- El mapa marca Pariahuanca (Huancayo, Junín), reconocida como Zona de Agrobiodiversidad. La ENAHO no da cifras por distrito: el dato que se muestra es el del departamento de Junín (28,6%).

## Cómo reproducirlo

```bash
pip install -r requirements.txt
python mapa_inseguridad_alimentaria.py
```

El script descarga los límites departamentales y provinciales la primera vez y guarda el mapa en `salida/` (PNG y SVG).

## Datos

`datos/inei_fies_2025_departamentos.csv` tiene una fila por ámbito departamental:

| Columna | Contenido |
| --- | --- |
| `ubigeo_dep`, `clave_mapa` | Código del departamento y clave de unión con la capa del mapa |
| `ia_mod_sev_pct` | Inseguridad alimentaria moderada o severa (% de la población) |
| `ic95_inf`, `ic95_sup`, `cv_pct` | Intervalo de confianza al 95% y coeficiente de variación |
| `frente_al_nacional` | Si el intervalo queda por encima, por debajo o no se distingue del nacional |
| `grupo_ia_severa`, `ia_severa_grupo_inf`, `ia_severa_grupo_sup` | Grupo de inseguridad severa del INEI y su rango |

El INEI publica Lima en tres ámbitos (Lima Metropolitana, Callao y resto de provincias), y el mapa los dibuja por separado.

## Fuentes

- INEI, [Prevalencia de Inseguridad Alimentaria 2025](https://www.gob.pe/institucion/inei/informes-publicaciones/8256358-prevalencia-de-inseguridad-alimentaria-2025), cuadros I.1 e I.3 del anexo estadístico.
- Límites: [juaneladio/peru-geojson](https://github.com/juaneladio/peru-geojson).

Elaborado por Antuané Vera para el curso de Salud con Lupa y FOVIDA sobre seguridad alimentaria, agrobiodiversidad y cambio climático.
