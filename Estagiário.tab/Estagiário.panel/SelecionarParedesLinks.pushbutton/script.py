# -*- coding: utf-8 -*-
__title__ = u'Selecionar\nParedes VNC'
__author__ = u"Kairos Arquitetura Integrada"
__version__ = u"Versao 1.0"
__doc__ = u"""
_____________________________________________________________________
Descricao:

Seleciona paredes de vinculos Revit na vista ativa, filtrando por tipo.
_____________________________________________________________________
Passo a passo:

1. Abra uma planta, corte ou fachada
2. Execute o botao
3. Escolha o vinculo desejado
4. Marque os tipos de parede
5. Clique em "Selecionar no Revit"

_____________________________________________________________________
Ultima atualizacao:
- [11.04.2026] - VERSAO 1.0
"""

# ── IMPORTS ───────────────────────────────────────────────────────────────────
import clr
import os
clr.AddReference("System")

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    RevitLinkInstance,
    RevitLinkType,
)
from pyrevit import revit, forms

# ── VARIAVEIS GLOBAIS ─────────────────────────────────────────────────────────
doc         = __revit__.ActiveUIDocument.Document
uidoc       = __revit__.ActiveUIDocument
app         = __revit__.Application
PATH_SCRIPT = os.path.dirname(__file__)
active_view = doc.ActiveView

# ── MAIN ──────────────────────────────────────────────────────────────────────

# 1. Coletar todos os vinculos carregados na vista ativa
links = (
    FilteredElementCollector(doc, active_view.Id)
    .OfClass(RevitLinkInstance)
    .ToElements()
)

if not links:
    forms.alert(u'Nenhum vinculo Revit encontrado na vista ativa.',
                title=u'Kairos - Aviso', exitscript=True)

# 2. Montar dicionario nome_vinculo → LinkInstance
dict_links = {}
for link in links:
    link_doc = link.GetLinkDocument()
    if link_doc is None:
        continue                        # vinculo nao carregado, pula
    nome_link = link_doc.Title
    # se houver dois links com mesmo nome, numera
    chave = nome_link
    contador = 2
    while chave in dict_links:
        chave = u'{} ({})'.format(nome_link, contador)
        contador += 1
    dict_links[chave] = link

if not dict_links:
    forms.alert(u'Nenhum vinculo carregado encontrado.',
                title=u'Kairos - Aviso', exitscript=True)

# 3. Selecionar o vinculo (se houver mais de um)
if len(dict_links) == 1:
    nome_escolhido = list(dict_links.keys())[0]
else:
    nome_escolhido = forms.SelectFromList.show(
        sorted(dict_links.keys()),
        title=u'Escolha o Vinculo',
        button_name=u'Continuar',
        multiselect=False
    )

if not nome_escolhido:
    forms.alert(u'Nenhum vinculo selecionado.', exitscript=True)

link_escolhido = dict_links[nome_escolhido]
link_doc       = link_escolhido.GetLinkDocument()

# 4. Coletar paredes dentro do vinculo escolhido
paredes = (
    FilteredElementCollector(link_doc)
    .OfCategory(BuiltInCategory.OST_Walls)
    .WhereElementIsNotElementType()
    .ToElements()
)

if not paredes:
    forms.alert(u'Nenhuma parede encontrada no vinculo "{}".'.format(nome_escolhido),
                title=u'Kairos - Aviso', exitscript=True)

# 5. Agrupar por tipo
dict_paredes = {}
for parede in paredes:
    nome = parede.Name
    dict_paredes.setdefault(nome, []).append(parede)

# 6. Montar opcoes com contagem
def label(nome):
    n = len(dict_paredes[nome])
    return u'{} ({} parede{})'.format(nome, n, u's' if n != 1 else u'')

mapa_label = {label(n): n for n in dict_paredes}
opcoes     = sorted(mapa_label.keys())

# 7. Caixa de selecao de tipos
escolhidos = forms.SelectFromList.show(
    opcoes,
    title=u'Paredes em: {}'.format(nome_escolhido),
    button_name=u'Selecionar no Revit',
    multiselect=True
)

if not escolhidos:
    forms.alert(u'Nenhum tipo selecionado.', exitscript=True)

# 8. Montar IDs do vinculo e selecionar
#    No Revit, elementos de link sao selecionados via Reference do LinkInstance
from Autodesk.Revit.DB import Reference
from System.Collections.Generic import List
from Autodesk.Revit.UI.Selection import Selection

ids_host = List[Reference]()
ids_para_selecao = []

for opcao in escolhidos:
    for parede in dict_paredes[mapa_label[opcao]]:
        ids_para_selecao.append(parede.Id)

# Selecionar elementos do vinculo via uidoc
uidoc.Selection.SetReferences(
    [link_escolhido.GetReferenceWithId(pid) for pid in ids_para_selecao]
)

# 9. Feedback
forms.toast(
    u'{} parede{} selecionada{} em "{}".'.format(
        len(ids_para_selecao),
        u's' if len(ids_para_selecao) != 1 else u'',
        u's' if len(ids_para_selecao) != 1 else u'',
        nome_escolhido
    ),
    title=u'Kairos - Selecao concluida'
)