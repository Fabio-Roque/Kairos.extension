# -*- coding: utf-8 -*-
__title__ = "02 - Vista 3D"
__author__ = "BIM Coder"
__version__ = "Versão 1.0"
__doc__ = """
_____________________________________________________________________
Descrição:

Cria uma vista 3D isométrica enquadrada em um ambiente
selecionado (com offset de 15cm) via SectionBox.
_____________________________________________________________________
Passo a passo:

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

bb_section = BoundingBoxXYZ()
bb_section.Min = XYZ(bb.Min.X - offset, bb.Min.Y - offset, bb.Min.Z - offset)
bb_section.Max = XYZ(bb.Max.X + offset, bb.Max.Y + offset, bb.Max.Z + offset)


# 4. Obter o ViewFamilyType de vista 3D
view_types = FilteredElementCollector(doc).OfClass(ViewFamilyType).ToElements()
view_type_3d = [vt for vt in view_types if vt.ViewFamily == ViewFamily.ThreeDimensional][0]


# 5. Criar a vista 3D, renomear e aplicar section box
t = Transaction(doc, __title__)
t.Start()

# Criar a vista 3D
new_view = View3D.CreateIsometric(doc, view_type_3d.Id)

# Definir nome
new_view.Name = "3D - Ambiente {}".format(room.Number)

# Definir section box
new_view.SetSectionBox(bb_section)

t.Commit()
