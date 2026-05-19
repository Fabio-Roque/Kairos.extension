# -*- coding: utf-8 -*-
import webbrowser
from pyrevit import forms

# URL direta para a página de chat do Gemini
url_gemini = "https://gemini.google.com/app"

try:
    # O Python chama o navegador padrão do seu Windows (Chrome, Edge, etc)
    webbrowser.open(url_gemini)
    
    # Mostra um aviso bonitinho no canto inferior direito do Revit
    forms.toast(
        "Navegador aberto no Gemini Advanced!", 
        title="Assistente Kairós"
    )
except Exception as e:
    forms.alert("Não foi possível abrir o navegador.\nErro: {}".format(e))