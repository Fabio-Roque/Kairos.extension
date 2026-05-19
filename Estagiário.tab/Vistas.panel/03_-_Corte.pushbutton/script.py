# -*- coding: utf-8 -*-
__title__ = "03 - Corte"
__author__ = "BIM Coder"
__version__ = "Versão 1.0"
__doc__ = """
_____________________________________________________________________
Descrição:

Cria um corte a partir de uma parede (usa ElementId hardcoded
para facilitar a demonstração; descomente o pick para testar).
_____________________________________________________________________
Passo a passo:

>>> Clique no botão

_____________________________________________________________________
Última atualização:
- [25.03.2025] - VERSÃO 1.0

"""
# ___  __  __  ____    ___   ____   _____  ____
#|_ _||  \/  ||  _ \  / _ \ |  _ \ |_   _|/ ___|
# | | | |\/| || |_) || | | || |_) |  | |  \___ \
# | | | |  | ||  __/ | |_| ||  _ <   | |   ___) |
#|___||_|  |_||_|     \___/ |_| \_\  |_|  |____/
#=================================================

# Importações Python e .NET
import clr
import clr
import os, traceback,math,re
clr.AddReference("System")

# Importações Revit API
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *
from Autodesk.Revit.UI.Selection import *

# Importações pyRevit
from pyrevit import forms, script, revit

# Suas Funções/ Snippets personalizados
#from Snippets._selection import pick_by_category
#from Snippets._geometry_operations import element_get_geometry
#from Snippets._transaction import bc_transaction

# Variáveis globais do Revit
doc   = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
app   = __revit__.Application
rvt_year = int(app.VersionNumber)
PATH_SCRIPT = os.path.dirname(__file__)

# Variáveis globais do Revit
doc   = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
app   = __revit__.Application
rvt_year = int(app.VersionNumber)
PATH_SCRIPT = os.path.dirname(__file__)

# Selecionar a parede
wall = revit.pick_element_by_category(BuiltInCategory.OST_Walls)

# Obter a Linha da parede
wall_line = wall.Location.Curve

# Comprimento da Parede
length = wall_line.Length

# Altura da parede
height = wall.get_Parameter(BuiltInParameter.WALL_USER_HEIGHT_PARAM).AsDouble()

# Criar o Transform (Sistema de coordenadas locais do corte)
transform_origin = wall_line.Evaluate(0.5,True)
transform_xaxis = wall_line.Direction
transform_yaxis = XYZ(0,0,1)
transform_zaxis = wall_line.Direction.CrossProduct(transform_yaxis)

t = Transform.Identity
t.Origin = transform_origin
t.BasisX = transform_xaxis
t.BasisY = transform_yaxis
t.BasisZ = transform_zaxis

# Criar a BoundingBox
offset = UnitUtils.ConvertToInternalUnits(10,UnitTypeId.Centimeters) # Offset do Corte
bb = BoundingBoxXYZ() 
bb.Transform = t
bb.Min = XYZ(-length/2 - offset, -offset, 0)
bb.Max = XYZ(length/2 + offset, height + offset, offset)

# Criar o corte
t = Transaction(doc,__title__)
t.Start()

new_section = ViewSection.CreateSection(doc, doc.GetDefaultElementTypeId(ElementTypeGroup.ViewTypeSection),bb)


t.Commit()