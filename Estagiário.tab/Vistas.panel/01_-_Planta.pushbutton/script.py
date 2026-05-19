# -*- coding: utf-8 -*-
__title__ = "01 - Planta"
__author__ = "BIM Coder"
__version__ = "Versão 1.0"
__doc__ = """
_____________________________________________________________________
Descrição:

Cria uma planta de piso duplicando a vista ativa e enquadrando
em um ambiente selecionado (com offset de 15cm).
_____________________________________________________________________
Passo a passo:

>>> Abra uma planta de piso

>>> Clique no botão

>>> Selecione um ambiente

_____________________________________________________________________
Última atualização:
- [21.04.2026] - VERSÃO 1.0

"""
# ___  __  __  ____    ___   ____   _____  ____
#|_ _||  \/  ||  _ \  / _ \ |  _ \ |_   _|/ ___|
# | | | |\/| || |_) || | | || |_) |  | |  \___ \
# | | | |  | ||  __/ | |_| ||  _ <   | |   ___) |
#|___||_|  |_||_|     \___/ |_| \_\  |_|  |____/
#=================================================

# Importações Revit API
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI.Selection import ObjectType

# Importações pyRevit
from pyrevit import forms, script, revit

# Variáveis globais do Revit
doc   = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument


# 1. Selecionar um ambiente
room = revit.pick_element_by_category(BuiltInCategory.OST_Rooms)

# 2. Obter a BoundingBox do ambiente
bb = room.get_BoundingBox(None)

# 3. Aplicar offset de 15cm na BoundingBox
offset = UnitUtils.ConvertToInternalUnits(15, UnitTypeId.Centimeters)

bb_crop = BoundingBoxXYZ()
bb_crop.Min = XYZ(bb.Min.X - offset, bb.Min.Y - offset, bb.Min.Z)
bb_crop.Max = XYZ(bb.Max.X + offset, bb.Max.Y + offset, bb.Max.Z)


# 4. Criar a planta, renomear e aplicar crop box
t = Transaction(doc, __title__)
t.Start()

# Criar a planta (duplicar a vista ativa)
new_view_id = doc.ActiveView.Duplicate(ViewDuplicateOption.Duplicate)
new_view = doc.GetElement(new_view_id)

# Definir nome
new_view.Name = "Planta - Ambiente {}".format(room.Number)

# Definir crop box
new_view.CropBox = bb_crop
new_view.CropBoxActive = True
new_view.CropBoxVisible = True

t.Commit()
