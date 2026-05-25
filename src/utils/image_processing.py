import cv2

def applica_visione_notturna(immagine):
    """
    Applica un filtro per migliorare la visibilità in condizioni di scarsa luminosità.
    Utilizza lo spazio colore LAB e l'algoritmo CLAHE.
    """
    lab = cv2.cvtColor(immagine, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    
    # Applica CLAHE al canale della luminosità (L)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    cl = clahe.apply(l)

    limg = cv2.merge((cl, a, b))
    return cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
