# -*- coding: utf-8 -*-
__title__ = "Selecionar\nParedes"
__author__ = "Kairós Arquitetura Integrada"
__version__ = "Versão 1.2"
__doc__ = """
_____________________________________________________________________
Descrição:

Abre um filtro elegante para selecionar paredes da vista ativa 
separadas automaticamente por tipo.
_____________________________________________________________________
Passo a passo:

1. Abra a vista onde deseja selecionar as paredes.
2. Clique no botão.
3. Marque os tipos desejados na janela.
4. Clique em Selecionar.
_____________________________________________________________________
Última atualização:
- [11.04.2026] - VERSÃO 1.2
"""

# ___  __  __  ____    ___   ____   _____  ____  
#|_ _||  \/  ||  _ \  / _ \ |  _ \ |_   _|/ ___| 
# | | | |\/| || |_) || | | || |_) |  | |  \___ \ 
# | | | |  | ||  __/ | |_| ||  _ <   | |   ___) |
#|___||_|  |_||_|     \___/ |_| \_\  |_|  |____/ 
#=================================================

# Importações Python e .NET
import clr
import os
clr.AddReference("System")

# Importações Revit API
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory

# Importações pyRevit
from pyrevit import revit, forms, script

# Variáveis globais do Revit
doc         = __revit__.ActiveUIDocument.Document
uidoc       = __revit__.ActiveUIDocument
app         = __revit__.Application
rvt_year    = int(app.VersionNumber)
PATH_SCRIPT = os.path.dirname(__file__)
active_view = doc.ActiveView


# _____  _   _  _   _   ____  _____  ___   ___   _   _  ____  
#|  ___|| | | || \ | | / ___||_   _||_ _| / _ \ | \ | |/ ___| 
#| |_   | | | ||  \| || |      | |   | | | | | ||  \| |\___ \ 
#|  _|  | |_| || |\  || |___   | |   | | | |_| || |\  | ___) |
#|_|     \___/ |_| \_| \____|  |_|  |___| \___/ |_| \_||____/ 
                                                              

# __  __     _    ___  _   _ 
#|  \/  |   / \  |_ _|| \ | |
#| |\/| |  / _ \  | | |  \| |
#| |  | | / ___ \ | | | |\  |
#|_|  |_|/_/   \_\|___||_| \_|
                             

# Exemplo de uso do Output
output = script.get_output()

# 1. Coletar paredes da vista ativa
paredes = (
    FilteredElementCollector(doc, active_view.Id)
    .OfCategory(BuiltInCategory.OST_Walls)
    .WhereElementIsNotElementType()
    .ToElements()
)

if not paredes:
    forms.alert(u'Nenhuma parede encontrada nesta vista.',
                title=u'Kairós - Aviso', exitscript=True)

# 2. Agrupar por tipo
dict_paredes = {}
for parede in paredes:
    nome = parede.Name
    dict_paredes.setdefault(nome, []).append(parede)

# 3. Montar opções com contagem — ex: "Alvenaria 14cm (8 paredes)"
def label(nome):
    n = len(dict_paredes[nome])
    return u'{} ({} parede{})'.format(nome, n, u's' if n != 1 else u'')

mapa_label = {label(n): n for n in dict_paredes}
opcoes     = sorted(mapa_label.keys())

# 4. Caixa de seleção
escolhidos = forms.SelectFromList.show(
    opcoes,
    title=u'Filtro de Paredes - Kairós V1.2',
    button_name=u'Selecionar no Revit',
    multiselect=True
)

if not escolhidos:
    forms.alert(u'Nenhum tipo selecionado.', exitscript=True)

# 5. Montar IDs e selecionar
ids = []
for opcao in escolhidos:
    for parede in dict_paredes[mapa_label[opcao]]:
        ids.append(parede.Id)

revit.get_selection().set_to(ids)

# 6. Feedback
forms.toast(
    u'{} parede{} selecionada{}.'.format(
        len(ids),
        u's' if len(ids) != 1 else u'',
        u's' if len(ids) != 1 else u''
    ),
    title=u'Kairos - Paredes selecionadas'
)