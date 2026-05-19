# -*- coding: utf-8 -*-
__title__ = "Cotar\nInterno"
__author__ = "Kairós Arquitetura"
__version__ = "Versão 5.1"
__doc__ = """
Gera múltiplas cotas internas (Apenas Paredes).
Utiliza Scanner de múltiplos feixes para ignorar vazios de esquadrias
e garantir a cota da espessura da parede.
"""

import clr
import sys
clr.AddReference("System")

from System.Collections.Generic import List
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI.Selection import ISelectionFilter, ObjectType
from Autodesk.Revit.Exceptions import OperationCanceledException
from pyrevit import revit, forms

doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
active_view = uidoc.ActiveView

# ── 0. Filtro de Seleção ─────────────────────────────────────────────────────
class FiltroDeLinhas(ISelectionFilter):
    def AllowElement(self, elem):
        return isinstance(elem, DetailLine) or isinstance(elem, ModelLine)
    def AllowReference(self, reference, position):
        return True

# ── 1. Seleção das Linhas Guia (Sem Menus) ──────────────────────────────────
linhas_selecionadas = []
selecao_previa = uidoc.Selection.GetElementIds()

if selecao_previa:
    for e_id in selecao_previa:
        el = doc.GetElement(e_id)
        if isinstance(el, DetailLine) or isinstance(el, ModelLine):
            linhas_selecionadas.append(el)

if not linhas_selecionadas:
    resp = forms.alert("Desenhou as linhas guia?", options=["Sim, selecionar", "Não, desenhar"])
    if resp == "Não, desenhar": sys.exit()
    try:
        ref_linhas = uidoc.Selection.PickObjects(ObjectType.Element, FiltroDeLinhas(), "Kairós: Selecione as linhas guia")
        for ref in ref_linhas: linhas_selecionadas.append(doc.GetElement(ref.ElementId))
    except OperationCanceledException: sys.exit()

if not linhas_selecionadas: sys.exit()

# ── 2. Coleta Exclusiva de Paredes ───────────────────────────────────────────
paredes_na_vista = (
    FilteredElementCollector(doc, active_view.Id)
    .OfCategory(BuiltInCategory.OST_Walls)
    .WhereElementIsNotElementType()
    .ToElements()
)

# ── 3. Configuração de Geometria ─────────────────────────────────────────────
opt_basica = Options()
opt_basica.ComputeReferences = True
opt_basica.IncludeNonVisibleObjects = False
opt_basica.View = active_view

opt_cortina = Options()
opt_cortina.ComputeReferences = True
opt_cortina.IncludeNonVisibleObjects = True
opt_cortina.View = active_view

cotas_geradas = 0
total_linhas = len(linhas_selecionadas)

t = Transaction(doc, "Kairós: Cotagem Interna 5.1")
t.Start()

try:
    with forms.ProgressBar(title="Escaneando paredes...", cancellable=True) as pb:
        for i, linha in enumerate(linhas_selecionadas):
            if pb.cancelled: break
            
            curva = linha.GeometryCurve
            direcao = curva.Direction
            linha_infinita = Line.CreateUnbound(curva.GetEndPoint(0), direcao)
            
            # O PULO DO GATO: Scanner de 3 níveis de altura (0.10m, 1.20m, 2.50m) convertido para Pés
            alturas_scan = [0.328, 3.937, 8.202]
            linhas_scan = []
            
            for h in alturas_scan:
                translacao_Z = Transform.CreateTranslation(XYZ(0, 0, h))
                linhas_scan.append(curva.CreateTransformed(translacao_Z))
            
            ref_array = ReferenceArray()
            refs_adicionadas = set()

            for parede in paredes_na_vista:
                is_curtain = False
                if hasattr(parede, "WallType") and str(parede.WallType.Kind) == "Curtain":
                    is_curtain = True
                    
                geom = parede.get_Geometry(opt_cortina if is_curtain else opt_basica)
                if not geom: continue
                
                solidos = []
                for obj in geom:
                    if isinstance(obj, Solid): 
                        solidos.append(obj)
                    elif isinstance(obj, GeometryInstance): 
                        solidos.extend([s for s in obj.GetInstanceGeometry() if isinstance(s, Solid)])
                
                for s in solidos:
                    if s.Faces.Size == 0: continue
                    for face in s.Faces:
                        if isinstance(face, PlanarFace):
                            
                            if abs(face.FaceNormal.Z) > 0.001:
                                continue
                            
                            # Dispara os 3 feixes contra a face da parede
                            hit = False
                            for linha_scan in linhas_scan:
                                res = face.Intersect(linha_scan)
                                if res == SetComparisonResult.Overlap or res == SetComparisonResult.Subset:
                                    hit = True
                                    break # Bateu em um feixe, já é suficiente para cotar!

                            if hit:
                                prod_escalar = face.FaceNormal.DotProduct(direcao)
                                if abs(prod_escalar) > 0.999:
                                    if face.Reference:
                                        rep = face.Reference.ConvertToStableRepresentation(doc)
                                        if rep not in refs_adicionadas:
                                            ref_array.Append(face.Reference)
                                            refs_adicionadas.add(rep)

            if ref_array.Size >= 2:
                try:
                    doc.Create.NewDimension(active_view, linha_infinita, ref_array)
                    doc.Delete(linha.Id)
                    cotas_geradas += 1
                except Exception as ex_cota:
                    print("Aviso: Linha ignorada devido a geometria irregular.")
                
            pb.update_progress(i + 1, len(linhas_selecionadas))
            
    t.Commit()
    forms.toast("{} cota(s) gerada(s) com sucesso.".format(cotas_geradas), title="Kairos")
    
except Exception as e:
    t.RollBack()
    forms.alert("Erro fatal: {}".format(str(e)))