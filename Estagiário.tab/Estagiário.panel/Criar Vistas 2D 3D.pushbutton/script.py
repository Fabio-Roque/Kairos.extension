# -*- coding: utf-8 -*-
__title__ = "Criar Vistas\nDetalhamento"
__author__ = "Kairós Arquitetura / BIM Coder"
__version__ = "Versão 6.4 Master BIM"
__doc__ = """
Gera o pacote de detalhamento completo com offsets inteligentes.
Usa Projeção de Matrizes (Transform.Inverse) para calcular os 8 vértices do ambiente,
garantindo que a elevação nunca vaze pelo modelo (mesmo com shafts ou portas abertas).
"""

import clr
import sys

clr.AddReference("System")

from Autodesk.Revit.DB import *
from pyrevit import revit, forms

doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument

# ============================================================
# FUNÇÃO DE LIMPEZA VISUAL MANUAL (Caso não use Template)
# ============================================================
def aplicar_grafico_padrao(vista):
    try:
        vista.DisplayStyle = DisplayStyle.HiddenLine
        cat_levels = Category.GetCategory(doc, BuiltInCategory.OST_Levels)
        if cat_levels and vista.CanCategoryBeHidden(cat_levels.Id):
            vista.SetCategoryHidden(cat_levels.Id, True)
    except:
        pass

# ============================================================
# FUNÇÃO PARA SELECIONAR MODELO DE VISTA
# ============================================================
def selecionar_template(nome_categoria, view_type_enum):
    templates = [v for v in FilteredElementCollector(doc).OfClass(View).WhereElementIsNotElementType().ToElements() if v.IsTemplate]
    templates_compativeis = [t for t in templates if t.ViewType == view_type_enum]
    
    if not templates_compativeis:
        return None
        
    opcoes = {"< Nenhum >": None}
    for t in sorted(templates_compativeis, key=lambda x: x.Name):
        opcoes[t.Name] = t
        
    escolha = forms.SelectFromList.show(
        sorted(opcoes.keys()),
        title='Selecione o Modelo para: {}'.format(nome_categoria),
        button_name='Selecionar',
        multiselect=False
    )
    
    if escolha and escolha != "< Nenhum >":
        return opcoes[escolha]
    return None

# ============================================================
# 1. MENU DE SELEÇÃO UX
# ============================================================
opcoes_vista = [
    "1. Planta Baixa Ampliada (2D)", 
    "2. Elevações Internas (4 faces)", 
    "3. Vista Isométrica (3D)"
]

escolhas = forms.SelectFromList.show(
    opcoes_vista,
    title='Kairós - O que deseja gerar?',
    button_name='Próximo',
    multiselect=True
)

if not escolhas:
    sys.exit()

gerar_planta = any("Planta" in e for e in escolhas)
gerar_elev = any("Elevações" in e for e in escolhas)
gerar_3d = any("3D" in e for e in escolhas)

# ============================================================
# 2. SELEÇÃO DE AMBIENTES E PREFIXO
# ============================================================
ambientes = revit.pick_elements_by_category(
    BuiltInCategory.OST_Rooms,
    message='Kairós: Selecione os ambientes para detalhar'
)

if not ambientes:
    sys.exit()

prefixo_usuario = forms.ask_for_string(
    prompt="Digite o identificador (Ex: Apto 04). Será o prefixo das vistas e irá para os Comentários:",
    title="Kairós - Identificação",
    default=""
)

if prefixo_usuario is None:
    sys.exit()

prefixo_usuario = prefixo_usuario.strip()

# ============================================================
# 3. ESCOLHA DOS VIEW TEMPLATES
# ============================================================
template_planta = None
template_elev = None
template_3d = None

if gerar_planta:
    template_planta = selecionar_template("Plantas Baixas", ViewType.FloorPlan)
if gerar_elev:
    template_elev = selecionar_template("Elevações Internas", ViewType.Elevation)
if gerar_3d:
    template_3d = selecionar_template("Vistas 3D", ViewType.ThreeD)

# ============================================================
# 4. BUSCAR TIPOS DE VISTA NO PROJETO
# ============================================================
vft_planta = None
vft_elev = None
vft_3d = None

tipos_vista = FilteredElementCollector(doc).OfClass(ViewFamilyType)

for vft in tipos_vista:
    if vft.ViewFamily == ViewFamily.FloorPlan and not vft_planta:
        vft_planta = vft
    if vft.ViewFamily == ViewFamily.Elevation and not vft_elev:
        vft_elev = vft
    if vft.ViewFamily == ViewFamily.ThreeDimensional and not vft_3d:
        vft_3d = vft

# ============================================================
# 5. PROCESSAMENTO E CRIAÇÃO DAS VISTAS
# ============================================================
vistas_criadas = 0

t = Transaction(doc, "Kairós: Detalhamento com Matriz Absoluta")
t.Start()

try:
    with forms.ProgressBar(title="Projetando Matrizes de Corte...", cancellable=True) as pb:
        for idx, element in enumerate(ambientes):
            if pb.cancelled:
                break
                
            nome_ambiente = element.get_Parameter(BuiltInParameter.ROOM_NAME).AsString()
            nivel_ambiente = element.Level
            
            if not nivel_ambiente:
                continue

            if prefixo_usuario:
                p_coment = element.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
                if p_coment and not p_coment.IsReadOnly:
                    p_coment.Set(prefixo_usuario)

            # BoundingBox Global do Ambiente
            bbox = element.get_BoundingBox(None)
            if not bbox:
                continue

            # ── OFFSETS (Convertidos para Pés) ──
            offset_lat = 0.35 / 0.3048    
            offset_bottom = 0.15 / 0.3048 
            offset_top_2d = 0.60 / 0.3048 
            offset_top_3d = 0.15 / 0.3048 

            # Cálculo de coordenadas absolutas expandidas da Caixa do Ambiente
            X_min_G = bbox.Min.X - offset_lat
            X_max_G = bbox.Max.X + offset_lat
            Y_min_G = bbox.Min.Y - offset_lat
            Y_max_G = bbox.Max.Y + offset_lat
            Z_min_G = bbox.Min.Z - offset_bottom
            Z_max_2d_G = bbox.Max.Z + offset_top_2d
            
            min_pt = XYZ(X_min_G, Y_min_G, Z_min_G)
            
            # Caixa 2D/Elevação e Caixa 3D
            max_pt_2d = XYZ(X_max_G, Y_max_G, Z_max_2d_G)
            bbox_2d = BoundingBoxXYZ()
            bbox_2d.Min = min_pt
            bbox_2d.Max = max_pt_2d

            max_pt_3d = XYZ(X_max_G, Y_max_G, bbox.Max.Z + offset_top_3d)
            bbox_3d = BoundingBoxXYZ()
            bbox_3d.Min = min_pt
            bbox_3d.Max = max_pt_3d

            centro = (min_pt + max_pt_2d) / 2
            nome_base = "{} - {}".format(prefixo_usuario, nome_ambiente) if prefixo_usuario else nome_ambiente

            # ── 1. CRIAR PLANTA 2D ──
            if gerar_planta:
                nome_vista_2d = "Planta - " + nome_base
                if not any(v.Name == nome_vista_2d for v in FilteredElementCollector(doc).OfClass(View).WhereElementIsNotElementType()):
                    vista_planta = ViewPlan.Create(doc, vft_planta.Id, nivel_ambiente.Id)
                    vista_planta.Name = nome_vista_2d
                    vista_planta.CropBoxActive = True
                    vista_planta.CropBoxVisible = True
                    vista_planta.CropBox = bbox_2d
                    
                    if template_planta:
                        vista_planta.ViewTemplateId = template_planta.Id
                    else:
                        aplicar_grafico_padrao(vista_planta)
                    vistas_criadas += 1

            # ── 2. CRIAR ELEVAÇÕES (MATRIZ BLINDADA) ──
            if gerar_elev:
                marker = ElevationMarker.CreateElevationMarker(doc, vft_elev.Id, centro, 50)
                
                # Aumentei a profundidade para garantir que cubra qualquer tamanho de sala, 
                # mesmo cortando a diagonal máxima da caixa.
                profundidade_visao = max((X_max_G - X_min_G), (Y_max_G - Y_min_G)) + offset_lat

                # Mapeia os 8 Vértices Globais do Caixote Exato do Ambiente
                vertices_ambiente = [
                    XYZ(X_min_G, Y_min_G, Z_min_G), XYZ(X_max_G, Y_min_G, Z_min_G),
                    XYZ(X_max_G, Y_max_G, Z_min_G), XYZ(X_min_G, Y_max_G, Z_min_G),
                    XYZ(X_min_G, Y_min_G, Z_max_2d_G), XYZ(X_max_G, Y_min_G, Z_max_2d_G),
                    XYZ(X_max_G, Y_max_G, Z_max_2d_G), XYZ(X_min_G, Y_max_G, Z_max_2d_G)
                ]

                for i in range(4): 
                    nome_final_elev = "Elevação {} - {}".format(i+1, nome_base)
                    if not any(v.Name == nome_final_elev for v in FilteredElementCollector(doc).OfClass(View).WhereElementIsNotElementType()):
                        v_elev = marker.CreateElevation(doc, doc.ActiveView.Id, i)
                        v_elev.Name = nome_final_elev
                        
                        doc.Regenerate()
                        
                        # O PULO DO GATO: Transforma o Caixote Global para a Visão Local da Elevação
                        crop_atual = v_elev.CropBox
                        transformacao = crop_atual.Transform
                        transformacao_inversa = transformacao.Inverse
                        
                        # Projeta os 8 vértices na tela 2D da elevação
                        vertices_locais = [transformacao_inversa.OfPoint(pt) for pt in vertices_ambiente]
                        
                        # Acha as bordas perfeitas ignorando onde o Revit tentou ancorar
                        local_x_min = min(pt.X for pt in vertices_locais)
                        local_x_max = max(pt.X for pt in vertices_locais)
                        local_y_min = min(pt.Y for pt in vertices_locais)
                        local_y_max = max(pt.Y for pt in vertices_locais)
                        
                        # Cria e impõe uma Caixa de Corte novinha em folha
                        nova_caixa = BoundingBoxXYZ()
                        nova_caixa.Transform = transformacao
                        nova_caixa.Min = XYZ(local_x_min, local_y_min, crop_atual.Min.Z)
                        nova_caixa.Max = XYZ(local_x_max, local_y_max, crop_atual.Max.Z)
                        
                        v_elev.CropBox = nova_caixa
                        v_elev.CropBoxActive = True
                        v_elev.CropBoxVisible = True
                        
                        try:
                            p_clip = v_elev.get_Parameter(BuiltInParameter.VIEWER_BOUND_ACTIVE_FAR)
                            if p_clip and not p_clip.IsReadOnly: p_clip.Set(1) 
                                
                            p_far = v_elev.get_Parameter(BuiltInParameter.VIEWER_BOUND_OFFSET_FAR)
                            if p_far and not p_far.IsReadOnly: p_far.Set(profundidade_visao)
                        except:
                            pass 
                            
                        if template_elev:
                            v_elev.ViewTemplateId = template_elev.Id
                        else:
                            aplicar_grafico_padrao(v_elev)
                        vistas_criadas += 1

            # ── 3. CRIAR VISTA 3D ──
            if gerar_3d:
                nome_vista_3d = "3D - " + nome_base
                if not any(v.Name == nome_vista_3d for v in FilteredElementCollector(doc).OfClass(View).WhereElementIsNotElementType()):
                    vista_3d = View3D.CreateIsometric(doc, vft_3d.Id)
                    vista_3d.Name = nome_vista_3d
                    vista_3d.SetSectionBox(bbox_3d)
                    
                    if template_3d:
                        vista_3d.ViewTemplateId = template_3d.Id
                    else:
                        aplicar_grafico_padrao(vista_3d)
                    vistas_criadas += 1

            pb.update_progress(idx + 1, len(ambientes))

    t.Commit()
    forms.toast('{} vistas geradas com matriz geométrica absoluta!'.format(vistas_criadas), title='Kairós Automação')

except Exception as erro:
    t.RollBack()
    forms.alert("Erro ao executar o script:\n" + str(erro))