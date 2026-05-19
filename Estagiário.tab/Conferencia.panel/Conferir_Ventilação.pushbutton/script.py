# -*- coding: utf-8 -*-
__title__ = "Conferência de Ventilação"
__author__ = "Seu nome"
__version__ = "Versão 1.0"
__doc__ = """
_____________________________________________________________________
Descrição:

Confere se os ambientes possuem ventilação mínima de 1/6 da área do
ambiente, com base na área das janelas hospedadas em cada ambiente.
_____________________________________________________________________
Passo a passo:

1. O script coleta todas as janelas do documento ativo.
2. Para cada janela, identifica o ambiente (FromRoom) que ela ventila.
3. Soma as áreas das janelas de cada ambiente.
4. Compara com 1/6 da área do ambiente.
5. Marca o parâmetro Comentários do ambiente como:
   - 'ATENDE À NORMA' quando a soma das áreas das janelas >= 1/6 da área do ambiente.
   - 'NÃO ATENDE' caso contrário.
_____________________________________________________________________
Última atualização:
- [29.04.2026] - VERSÃO 1.0

"""
# ___  __  __  ____    ___   ____   _____  ____
#|_ _||  \/  ||  _ \  / _ \ |  _ \ |_   _|/ ___|
# | | | |\/| || |_) || | | || |_) |  | |  \___ \
# | | | |  | ||  __/ | |_| ||  _ <   | |   ___) |
#|___||_|  |_||_|     \___/ |_| \_\  |_|  |____/
#=================================================

# Importações Python e .NET
import clr
import os, traceback
clr.AddReference("System")

# Importações Revit API
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *
from Autodesk.Revit.UI.Selection import *

# Importações pyRevit
from pyrevit import forms, script

# Variáveis globais do Revit
doc   = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
app   = __revit__.Application
rvt_year = int(app.VersionNumber)
PATH_SCRIPT = os.path.dirname(__file__)


# _____  _   _  _   _   ____  _____  ___   ___   _   _  ____
#|  ___|| | | || \ | | / ___||_   _||_ _| / _ \ | \ | |/ ___|
#| |_   | | | ||  \| || |      | |   | | | | | ||  \| |\___ \
#|  _|  | |_| || |\  || |___   | |   | | | |_| || |\  | ___) |
#|_|     \___/ |_| \_| \____|  |_|  |___| \___/ |_| \_||____/

def m2_from_ft2(value_ft2):
    # Revit armazena áreas internamente em pés² (ft²). Converte para m².
    return value_ft2 * 0.092903


# __  __     _     ___  _   _
#|  \/  |   / \   |_ _|| \ | |
#| |\/| |  / _ \   | | |  \| |
#| |  | | / ___ \  | | | |\  |
#|_|  |_|/_/   \_\|___||_| \_|

output = script.get_output()
output.print_md("# Conferência de Ventilação")
output.print_md("## Verificando se cada ambiente possui ventilação >= 1/6 da área...")

try:
    # ========================================================
    # ETAPA 2 — Buscar todas as Janelas do Documento Ativo
    # ========================================================
    janelas = FilteredElementCollector(doc)\
                .OfCategory(BuiltInCategory.OST_Windows)\
                .WhereElementIsNotElementType()\
                .ToElements()

    if not janelas:
        forms.alert("Nenhuma janela encontrada no documento.", exitscript=True)

    # ========================================================
    # ETAPA 3 — Obter o ambiente de cada janela (FromRoom)
    # ETAPA 4 — Relacionar janelas x ambientes
    # ETAPA 5 — Dicionário de ambientes
    # ETAPA 6 — Lista de janelas por ambiente
    # ========================================================
    # ambientes_dict = { room_id : {"room": Room, "janelas": [janela1, janela2, ...]} }
    ambientes_dict = {}

    for janela in janelas:
        try:
            # FromRoom do Revit precisa de uma fase. Usamos a última fase do projeto.
            fases = doc.Phases
            fase_atual = fases[fases.Size - 1]

            ambiente = janela.get_FromRoom(fase_atual)
            if ambiente is None:
                # Se não achar pela FromRoom, tenta ToRoom (lado oposto)
                ambiente = janela.get_ToRoom(fase_atual)

            if ambiente is None:
                continue  # janela sem ambiente associado, ignora

            room_id = ambiente.Id.IntegerValue
            if room_id not in ambientes_dict:
                ambientes_dict[room_id] = {"room": ambiente, "janelas": []}
            ambientes_dict[room_id]["janelas"].append(janela)

        except Exception as e:
            output.print_md("- Erro ao processar janela `{}`: {}".format(janela.Id, e))

    if not ambientes_dict:
        forms.alert("Nenhuma janela está associada a um ambiente.", exitscript=True)

    # ========================================================
    # Inicia uma única Transaction para gravar os comentários
    # ========================================================
    t = Transaction(doc, "Conferência de Ventilação")
    t.Start()

    output.print_md("## Resultado por ambiente")

    contador_atende = 0
    contador_nao_atende = 0

    for room_id, dados in ambientes_dict.items():
        ambiente = dados["room"]
        lista_janelas = dados["janelas"]

        # ========================================================
        # ETAPA 7 — Ler parâmetro nativo da Área do Ambiente
        # ========================================================
        param_area_amb = ambiente.get_Parameter(BuiltInParameter.ROOM_AREA)
        if param_area_amb is None:
            continue
        area_ambiente_ft2 = param_area_amb.AsDouble()
        area_ambiente_m2 = m2_from_ft2(area_ambiente_ft2)

        # ========================================================
        # ETAPA 8 — Ler parâmetro nativo da Área de cada Janela
        # Soma de todas as janelas que ventilam aquele ambiente
        # ========================================================
        soma_area_janelas_ft2 = 0.0
        detalhe_janelas = []
        for j in lista_janelas:
            param_area_jan = j.get_Parameter(BuiltInParameter.HOST_AREA_COMPUTED)
            if param_area_jan is None:
                continue
            area_j_ft2 = param_area_jan.AsDouble()
            soma_area_janelas_ft2 += area_j_ft2
            detalhe_janelas.append((j, m2_from_ft2(area_j_ft2)))

        soma_area_janelas_m2 = m2_from_ft2(soma_area_janelas_ft2)
        area_minima_m2 = area_ambiente_m2 / 6.0

        # ========================================================
        # ETAPA 12 — Mostrar dedução dos cálculos
        # ========================================================
        nome_amb = ambiente.LookupParameter("Name").AsString() if ambiente.LookupParameter("Name") else "Ambiente"
        numero_amb = ambiente.Number if hasattr(ambiente, "Number") else "-"

        output.print_md("---")
        output.print_md("### Ambiente: **{} - {}**".format(numero_amb, nome_amb))
        output.print_md("- Área do ambiente: **{:.2f} m²**".format(area_ambiente_m2))
        output.print_md("- Área mínima de ventilação (1/6): **{:.2f} m²**".format(area_minima_m2))
        output.print_md("- Soma da área das janelas: **{:.2f} m²**".format(soma_area_janelas_m2))
        output.print_md("- Janelas no ambiente: **{}**".format(len(lista_janelas)))
        for j, area_m2 in detalhe_janelas:
            output.print_md("  - Janela Id `{}` → {:.2f} m²".format(j.Id, area_m2))

        # ========================================================
        # ETAPA 9 — IF / ELSE: Área das janelas > 1/6 da área do ambiente?
        # ETAPA 10 / ETAPA 11 — Caminhos por ambiente (atende / não atende)
        # ========================================================
        atende = soma_area_janelas_m2 >= area_minima_m2

        if atende:
            # ETAPA 13 — Definir Comentários como 'ATENDE À NORMA'
            status_txt = "ATENDE À NORMA"
            contador_atende += 1
            output.print_md("- ✅ **{}**".format(status_txt))
        else:
            # ETAPA 14 — Definir Comentários como 'NÃO ATENDE'
            status_txt = "NÃO ATENDE"
            contador_nao_atende += 1
            output.print_md("- ❌ **{}**".format(status_txt))

        # Grava o comentário no AMBIENTE
        try:
            p_com = ambiente.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
            if p_com is not None and not p_com.IsReadOnly:
                p_com.Set(status_txt)
        except Exception as e:
            output.print_md("  - Erro ao gravar comentário no ambiente `{}`: {}".format(ambiente.Id, e))

    t.Commit()

    # ========================================================
    # Resumo final
    # ========================================================
    output.print_md("---")
    output.print_md("## Resumo")
    output.print_md("- Ambientes que **ATENDEM**: **{}**".format(contador_atende))
    output.print_md("- Ambientes que **NÃO ATENDEM**: **{}**".format(contador_nao_atende))

except Exception as e:
    if 't' in dir() and t.HasStarted() and not t.HasEnded():
        t.RollBack()
    output.print_md("### ERRO: {}".format(str(e)))
    output.print_md("```\n{}\n```".format(traceback.format_exc()))

output.print_md("## Operação concluída!")
