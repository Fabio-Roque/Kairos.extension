# -*- coding: utf-8 -*-
__title__ = "Exportar\nPDF Vetorial"
__author__ = "Kairós Arquitetura"
__doc__ = """
Exportador de Vistas para PDF Vetorizado.
Substitui o DWG para envio ao CorelDraw/Illustrator, garantindo que
preenchimentos sólidos sejam exportados como polígonos perfeitos em vez de hachuras.
"""

import clr
import sys
import os

clr.AddReference("System")
from System.Collections.Generic import List

from Autodesk.Revit.DB import *
from pyrevit import revit, forms

doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
active_view = uidoc.ActiveView

# ── 1. Escolher o Local e o Nome ─────────────────────────
caminho_salvar = forms.save_file(
    file_ext='pdf',
    default_name='{}.pdf'.format(active_view.Name),
    title='Kairós: Onde salvar o PDF para o CorelDraw?'
)

if not caminho_salvar:
    sys.exit()

pasta_destino = os.path.dirname(caminho_salvar)
nome_final_pdf = os.path.basename(caminho_salvar)
nome_sem_ext = os.path.splitext(nome_final_pdf)[0]

# Deleta arquivo existente para evitar erro do Windows
if os.path.exists(caminho_salvar):
    try:
        os.remove(caminho_salvar)
    except:
        forms.alert("O arquivo já existe e está aberto. Feche-o antes de exportar novamente.", exitscript=True)

# ── 2. Exportação PDF Nativa da API ──────────────────────
view_collection = List[ElementId]()
view_collection.Add(active_view.Id)

options = PDFExportOptions()
options.FileName = nome_sem_ext
options.Combine = True # Ao combinar, o Revit respeita perfeitamente o nome que você digitou

try:
    with forms.ProgressBar(title="Kairós: Vetorizando formas para o Corel...", cancellable=False):
        doc.Export(pasta_destino, view_collection, options)

    os.startfile(caminho_salvar)
    forms.toast("PDF Vetorial gerado! Arraste para o CorelDraw.", title="Kairós Automação")

except Exception as e:
    forms.alert("Erro durante a exportação:\n{}".format(str(e)), exitscript=True)