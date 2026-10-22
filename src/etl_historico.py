import pandas as pd
def extraer_datos(rutacsv, rutajson):
    # esto lee el csv y el json y lo devuelve
    ah = pd.readcsv(rutacsv)
