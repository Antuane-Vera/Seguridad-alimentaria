"""
Mapa de inseguridad alimentaria moderada o severa por departamento, Perú 2025.

Datos:   INEI, Encuesta Nacional de Hogares 2025, módulo FIES (Cuadro I.1 del
         anexo "Prevalencia de Inseguridad Alimentaria 2025").
         Zonas de Agrobiodiversidad reconocidas por el Midagri (datos/zonas_agrobiodiversidad.csv).
Límites: github.com/juaneladio/peru-geojson (se descargan al ejecutar).

Uso:     python mapa_inseguridad_alimentaria.py
Salida:  salida/mapa_inseguridad_alimentaria_2025.png y .svg
"""
import textwrap
from pathlib import Path
from urllib.request import urlretrieve

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import patheffects
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

BASE = Path(__file__).resolve().parent
DATOS = BASE / "datos" / "inei_fies_2025_departamentos.csv"
ZAB = BASE / "datos" / "zonas_agrobiodiversidad.csv"
GEO = BASE / "datos" / "geo"
SALIDA = BASE / "salida"
FUENTE_GEO = "https://raw.githubusercontent.com/juaneladio/peru-geojson/master/"
CAPAS = {"dep": "peru_departamental_simple.geojson", "prov": "peru_provincial_simple.geojson"}

# Clases y colores: un solo tono, de claro a oscuro (más oscuro = más inseguridad).
CORTES = [0, 25, 30, 35, 40, 100]
ETIQUETAS = ["Menos de 25%", "25% a 29,9%", "30% a 34,9%", "35% a 39,9%", "40% o más"]
COLORES = ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]
TINTA, TINTA_2, FONDO = "#0b0b0b", "#52514e", "#fcfcfb"

CRS = "EPSG:32718"  # UTM 18S


def descargar_capas():
    GEO.mkdir(parents=True, exist_ok=True)
    for archivo in CAPAS.values():
        destino = GEO / archivo
        if not destino.exists():
            urlretrieve(FUENTE_GEO + archivo, destino)


def construir_capa():
    """25 departamentos, con Lima separada como la publica el INEI:
    Lima Metropolitana (provincia de Lima) y Lima (resto de provincias)."""
    dep = gpd.read_file(GEO / CAPAS["dep"])
    prov = gpd.read_file(GEO / CAPAS["prov"])

    capa = dep[dep["FIRST_IDDP"] != "15"][["FIRST_IDDP", "geometry"]]
    capa = capa.rename(columns={"FIRST_IDDP": "clave_mapa"})

    lima = prov[prov["FIRST_IDPR"].str.startswith("15")].copy()
    lima["clave_mapa"] = lima["FIRST_IDPR"].where(lima["FIRST_IDPR"] == "1501", "15R")
    lima = lima.dissolve(by="clave_mapa").reset_index()[["clave_mapa", "geometry"]]

    return pd.concat([capa, lima], ignore_index=True)


def fmt(valor):
    return f"{valor:.1f}".replace(".", ",")


def main():
    descargar_capas()
    datos = pd.read_csv(DATOS, dtype={"ubigeo_dep": str, "clave_mapa": str})
    capa = construir_capa().merge(datos, on="clave_mapa", how="left", validate="one_to_one")
    assert capa["ia_mod_sev_pct"].notna().all(), "Hay ámbitos sin dato"
    capa = gpd.GeoDataFrame(capa, crs="EPSG:4326").to_crs(CRS)
    capa["clase"] = pd.cut(capa["ia_mod_sev_pct"], CORTES, right=False, labels=False)

    plt.rcParams["font.family"] = "DejaVu Sans"
    fig, ax = plt.subplots(figsize=(8, 10.4), facecolor=FONDO)
    fig.subplots_adjust(left=0.02, right=0.98, top=0.885, bottom=0.115)
    ax.set_facecolor(FONDO)
    capa.plot(ax=ax, color=[COLORES[int(c)] for c in capa["clase"]], edgecolor=FONDO, linewidth=0.9)
    ax.set_axis_off()
    ax.margins(0.01)

    halo = [patheffects.withStroke(linewidth=2.6, foreground=FONDO)]

    # Etiquetas selectivas: los que superan con claridad el promedio y el más bajo.
    # Los departamentos pequeños llevan la etiqueta sobre el mar, con línea guía.
    fuera = {"Lambayeque": (-150_000, -45_000), "Moquegua": (-170_000, -75_000)}
    rotular = capa[(capa["frente_al_nacional"] == "por encima") | (capa["ambito"] == "Moquegua")]
    for _, fila in rotular.iterrows():
        p = fila.geometry.representative_point()
        texto = f"{fila['ambito']}\n{fmt(fila['ia_mod_sev_pct'])}%"
        estilo = dict(fontsize=8.5, color=TINTA, fontweight="bold", linespacing=1.15, path_effects=halo)
        if fila["ambito"] in fuera:
            dx, dy = fuera[fila["ambito"]]
            ax.annotate(texto, xy=(p.x, p.y), xytext=(p.x + dx, p.y + dy), ha="right", va="center", **estilo,
                        arrowprops=dict(arrowstyle="-", color=TINTA_2, linewidth=0.8, shrinkA=2, shrinkB=0))
        else:
            ax.text(p.x, p.y, texto, ha="center", va="center", **estilo)

    # Zonas de Agrobiodiversidad: un punto por zona, en el distrito donde se ubica.
    # Pariahuanca va destacada; las demás, con punto hueco y nombre en texto regular.
    zab = pd.read_csv(ZAB)
    zab = gpd.GeoDataFrame(zab, geometry=gpd.points_from_xy(zab["lon"], zab["lat"]), crs="EPSG:4326").to_crs(CRS)
    zab["x"], zab["y"] = zab.geometry.x, zab.geometry.y
    guia = dict(arrowstyle="-", color=TINTA_2, linewidth=0.8, shrinkA=2, shrinkB=4)

    otras = zab[zab["destacada"] == 0]
    ax.plot(otras["x"], otras["y"], linestyle="none", marker="o", markersize=5, markerfacecolor=FONDO,
            markeredgecolor=TINTA, markeredgewidth=1.2, zorder=5)

    # Las zonas de Apurímac y las dos de Marcapata están muy juntas: comparten una sola nota.
    otras = otras.assign(grupo=otras["departamento"].where(otras["departamento"] == "Apurímac", otras["distritos"]))
    desplazar = {  # (dx, dy en metros, alineación) según la primera zona del grupo
        "Andenes de Cuyocuyo": (60_000, -10_000, "left"),
        "Parque de la Papa": (40_000, 115_000, "left"),
        "Ccollasuyo": (150_000, 45_000, "left"),
        "Laria": (-250_000, -110_000, "right"),
        "Cotahuasi": (-200_000, -130_000, "right"),
        "Paymakis": (-290_000, -135_000, "right"),
    }
    for grupo, filas in otras.groupby("grupo", sort=False):
        nombres = list(filas["zona"])
        texto = nombres[0] if len(nombres) == 1 else ", ".join(nombres[:-1]) + " y " + nombres[-1]
        if grupo == "Apurímac":
            texto = "Apurímac: " + texto
        texto = textwrap.fill(texto, width=36 if grupo == "Apurímac" else 20)
        gx, gy = filas["x"].mean(), filas["y"].mean()
        dx, dy, alin = desplazar[nombres[0]]
        ax.annotate(texto, xy=(gx, gy), xytext=(gx + dx, gy + dy), fontsize=8, color=TINTA, va="center", ha=alin,
                    linespacing=1.2, path_effects=halo, arrowprops=guia, zorder=6)

    junin = capa.loc[capa["ambito"] == "Junín", "ia_mod_sev_pct"].iloc[0]
    caso = zab[zab["destacada"] == 1].iloc[0]
    ax.plot(caso["x"], caso["y"], marker="o", markersize=8, markerfacecolor=TINTA, markeredgecolor=FONDO,
            markeredgewidth=1.8, zorder=7)
    ax.annotate(f"{caso['zona']}\nJunín: {fmt(junin)}%", xy=(caso["x"], caso["y"]),
                xytext=(caso["x"] - 330_000, caso["y"] - 60_000), fontsize=9.5, fontweight="bold", color=TINTA,
                va="center", ha="right", linespacing=1.2, path_effects=halo, arrowprops=guia, zorder=7)

    nacional = 30.5
    fig.text(0.04, 0.955, "Loreto y Puno tienen la mayor inseguridad alimentaria del país",
             fontsize=14, fontweight="bold", color=TINTA, ha="left")
    fig.text(0.04, 0.943, "Población con inseguridad alimentaria moderada o severa en 2025 "
             f"(promedio nacional: {fmt(nacional)}%)\ny ubicación de las zonas de agrobiodiversidad reconocidas", fontsize=10.5, color=TINTA_2, ha="left", va="top", linespacing=1.35)

    leyenda = [Patch(facecolor=c, edgecolor=FONDO, label=e) for c, e in zip(COLORES, ETIQUETAS)]
    clases = ax.legend(handles=leyenda, loc="upper left", bbox_to_anchor=(0.0, 0.97), frameon=False,
                       fontsize=9.5, labelcolor=TINTA, handlelength=1.4, handleheight=1.2,
                       title="% de la población", title_fontsize=9.5, alignment="left")
    ax.add_artist(clases)
    puntos = [
        Line2D([], [], linestyle="none", marker="o", markersize=8, markerfacecolor=TINTA, markeredgecolor=FONDO,
               markeredgewidth=1.8, label="Pariahuanca"),
        Line2D([], [], linestyle="none", marker="o", markersize=5, markerfacecolor=FONDO, markeredgecolor=TINTA,
               markeredgewidth=1.2, label=f"Otras zonas ({len(zab) - 1})"),
    ]
    ax.legend(handles=puntos, loc="lower left", bbox_to_anchor=(0.0, 0.0), frameon=False, fontsize=9.5,
              labelcolor=TINTA, handlelength=1.4, title="Zonas de Agrobiodiversidad", title_fontsize=9.5,
              alignment="left")

    fig.text(0.04, 0.015,
             "Las cifras son estimaciones de encuesta: solo Loreto, Puno, Piura, Ucayali y Lambayeque superan con claridad el\n"
             "promedio nacional (su intervalo de confianza al 95% no se cruza con el nacional).\n"
             "Las zonas de agrobiodiversidad son las reconocidas por el Midagri a junio de 2026; cada punto marca\n"
             "el distrito donde se ubica la zona, no sus límites.\n"
             "Fuente: INEI, Encuesta Nacional de Hogares 2025, módulo FIES (Cuadro I.1). Límites: juaneladio/peru-geojson.",
             fontsize=8, color=TINTA_2, ha="left", va="bottom", linespacing=1.45)

    SALIDA.mkdir(exist_ok=True)
    for ext in ("png", "svg"):
        fig.savefig(SALIDA / f"mapa_inseguridad_alimentaria_2025_1.{ext}", dpi=200, facecolor=FONDO)
    print("Mapa guardado en", SALIDA)


if __name__ == "__main__":
    main()
