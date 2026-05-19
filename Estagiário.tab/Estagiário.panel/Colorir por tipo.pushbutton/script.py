# -*- coding: utf-8 -*-
__title__ = "Colorir Famílias\npor Tipo"
__version__ = "1.0"
__doc__ = "Colore os elementos da vista ativa por tipo de família, de acordo com a categoria escolhida pelo usuário."

from Autodesk.Revit.DB import *
from pyrevit import forms

doc   = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument

# ─────────────────────────────────────────────
# ETAPA 2 — Formulário: seleção da categoria
# ─────────────────────────────────────────────

# Mapeamento nome amigável → BuiltInCategory
CATEGORIAS = {
    "Paredes"             : BuiltInCategory.OST_Walls,
    "Portas"              : BuiltInCategory.OST_Doors,
    "Janelas"             : BuiltInCategory.OST_Windows,
    "Pisos"               : BuiltInCategory.OST_Floors,
    "Pilares"             : BuiltInCategory.OST_StructuralColumns,
    "Vigas"               : BuiltInCategory.OST_StructuralFraming,
    "Tetos"               : BuiltInCategory.OST_Ceilings,
    "Móveis"              : BuiltInCategory.OST_Furniture,
    "Equipamentos"        : BuiltInCategory.OST_MechanicalEquipment,
    "Luminárias"          : BuiltInCategory.OST_LightingFixtures,
    "Dutos"               : BuiltInCategory.OST_DuctCurves,
    "Tubulações"          : BuiltInCategory.OST_PipeCurves,
    "Eletrodutos"         : BuiltInCategory.OST_Conduit,
}

categoria_nome = forms.SelectFromList.show(
    sorted(CATEGORIAS.keys()),
    title="Colorir Famílias por Tipo",
    prompt="Selecione a categoria a colorir:",
    multiselect=False
)

if not categoria_nome:
    forms.alert("Nenhuma categoria selecionada.", exitscript=True)

bic = CATEGORIAS[categoria_nome]

# ─────────────────────────────────────────────
# ETAPA 3 — Buscar elementos na vista ativa
# ─────────────────────────────────────────────

elementos = (
    FilteredElementCollector(doc, doc.ActiveView.Id)
    .OfCategory(bic)
    .WhereElementIsNotElementType()
    .ToElements()
)

if not elementos:
    forms.alert("Nenhum elemento encontrado para a categoria '{}'.".format(categoria_nome), exitscript=True)

# ─────────────────────────────────────────────
# ETAPA 4 — Mapear tipo → cor
# ─────────────────────────────────────────────

# Paleta de cores variadas (R, G, B)
PALETA = [
    (52,  152, 219),   # azul
    (231, 76,  60 ),   # vermelho
    (46,  204, 113),   # verde
    (230, 126, 34 ),   # laranja
    (155, 89,  182),   # roxo
    (26,  188, 156),   # turquesa
    (241, 196, 15 ),   # amarelo
    (236, 240, 241),   # branco-acinzentado
    (52,  73,  94 ),   # azul-escuro
    (211, 84,  0  ),   # laranja-escuro
    (39,  174, 96 ),   # verde-escuro
    (142, 68,  173),   # roxo-escuro
]

# Descobrir todos os tipos únicos
tipos_unicos = {}
for el in elementos:
    tipo_id = el.GetTypeId()
    if tipo_id not in tipos_unicos:
        tipo = doc.GetElement(tipo_id)
        tipos_unicos[tipo_id] = tipo

# Associar cada tipo_id a uma cor da paleta
cor_por_tipo = {}
for i, tipo_id in enumerate(tipos_unicos.keys()):
    r, g, b = PALETA[i % len(PALETA)]
    cor_por_tipo[tipo_id] = Color(r, g, b)

# ─────────────────────────────────────────────
# ETAPA 5 — Obter padrão sólido e aplicar cores
# ─────────────────────────────────────────────

# Buscar o primeiro FillPatternElement com IsSolidFill == True
padrao_solido = None
for fp in FilteredElementCollector(doc).OfClass(FillPatternElement).ToElements():
    if fp.GetFillPattern().IsSolidFill:
        padrao_solido = fp
        break

if not padrao_solido:
    forms.alert("Padrão de preenchimento sólido não encontrado no projeto.", exitscript=True)

try:
    t = Transaction(doc, "Colorir Famílias por Tipo")
    t.Start()

    for el in elementos:
        tipo_id = el.GetTypeId()
        cor     = cor_por_tipo.get(tipo_id)
        if not cor:
            continue

        ogs = OverrideGraphicSettings()
        ogs.SetSurfaceForegroundPatternId(padrao_solido.Id)
        ogs.SetSurfaceForegroundPatternColor(cor)

        doc.ActiveView.SetElementOverrides(el.Id, ogs)

    t.Commit()

except Exception as e:
    if t.HasStarted() and not t.HasEnded():
        t.RollBack()
    forms.alert("Erro ao aplicar cores:\n{}".format(str(e)), exitscript=True)

# ─────────────────────────────────────────────
# ETAPA 6 — Mensagem de conclusão
# ─────────────────────────────────────────────

forms.alert(
    "Tipos encontrados: {}".format(len(tipos_unicos)),
    warn_icon=False
)