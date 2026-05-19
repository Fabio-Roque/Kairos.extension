# -*- coding: utf-8 -*-
__title__ = "Exportar\nVista"
__author__ = "Kairós Arquitetura"
__doc__ = """
Exportador Avançado de Vistas do Revit.
Permite escolher a pasta, o nome exato do arquivo e o tamanho em pixels.
"""

import clr
import sys
import os
import tempfile
import shutil

from Autodesk.Revit.DB import *
from pyrevit import revit, forms

doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
active_view = uidoc.ActiveView

# ── 1. Perguntar o Tamanho em Pixels ─────────────────────────────────────────
tamanho_pixel = forms.ask_for_string(
    prompt="Digite o tamanho em pixels da maior dimensão (horizontal ou vertical).\nEx: 1920 (Full HD), 3840 (4K), 1080 (Quadrado):",
    default="1920",
    title="Kairós - Resolução da Imagem"
)

if not tamanho_pixel:
    sys.exit()

try:
    pixel_size = int(tamanho_pixel)
except:
    forms.alert("Valor inválido. Por favor, digite apenas números inteiros.", exitscript=True)

# ── 2. Escolher o Local e o Nome (Interface Nativa do Windows) ───────────────
caminho_salvar = forms.save_file(
    file_ext='png',
    default_name='{}.png'.format(active_view.Name),
    title='Kairós: Onde deseja salvar a imagem?'
)

if not caminho_salvar:
    sys.exit()

# ── 3. O Truque para Limpar o Nome do Arquivo ────────────────────────────────
# O Revit sempre adiciona sufixos chatos no nome da imagem (ex: "nome - 3D.png").
# Vamos forçar a exportação para a pasta "Temp" do Windows e depois mover.
temp_folder = tempfile.gettempdir()
temp_base_name = "kairos_export_temp"
temp_path_base = os.path.join(temp_folder, temp_base_name)

options = ImageExportOptions()
options.ExportRange = ExportRange.CurrentView
options.FilePath = temp_path_base
options.HLRandWFViewsFileType = ImageFileType.PNG
options.ShadowViewsFileType = ImageFileType.PNG
options.ZoomType = ZoomFitType.FitToPage # Obriga o Revit a respeitar os pixels que você digitou
options.PixelSize = pixel_size
options.ImageResolution = ImageResolution.DPI_300

try:
    with forms.ProgressBar(title="Kairós: Exportando imagem em alta resolução...", cancellable=False):
        doc.ExportImage(options)

    # 4. Encontrar o arquivo na pasta temporária e mover para o destino
    arquivos_gerados = [f for f in os.listdir(temp_folder) if f.startswith(temp_base_name) and f.endswith(".png")]

    if not arquivos_gerados:
        forms.alert("Erro: O Revit falhou ao gerar a imagem temporária.", exitscript=True)

    arquivo_temp_gerado = os.path.join(temp_folder, arquivos_gerados[0])

    # Se você for salvar por cima de uma imagem que já existe, deletamos a antiga primeiro
    if os.path.exists(caminho_salvar):
        os.remove(caminho_salvar)

    # Movemos o arquivo temporário e damos a ele o nome final perfeito
    shutil.move(arquivo_temp_gerado, caminho_salvar)

    # 5. Abrir a imagem final para conferência
    os.startfile(caminho_salvar)
    forms.toast("Imagem exportada perfeitamente!", title="Kairós Automação")

except Exception as e:
    forms.alert("Erro durante a exportação:\n{}".format(str(e)), exitscript=True)