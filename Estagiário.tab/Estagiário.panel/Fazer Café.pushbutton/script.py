# -*- coding: utf-8 -*-
from pyrevit import forms
import time

# 1. Cria a barra de progresso compatível com pyRevit 6.1
# O título da janela já serve para avisar o que está acontecendo
with forms.ProgressBar(title="Máquina Kairós: Moendo e preparando seu café...", cancellable=True) as pb:
    for i in range(100):
        time.sleep(0.04) # Simula o preparo
        
        # O comando correto é apenas (valor_atual, valor_maximo)
        pb.update_progress(i + 1, 100)

# 2. Mensagem Final
forms.alert(
    "O processo foi concluído com sucesso!\n\n"
    "Pode ir até a copa que o seu café estará pronto.\n"
    "Aproveite a pausa, Fabio!", 
    title="Café Pronto!", 
    warn_icon=False
)