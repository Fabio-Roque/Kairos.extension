# -*- coding: utf-8 -*-
from pyrevit import revit, DB, forms
import json
import clr

# Importações para a interface visual e sistema de Rede
clr.AddReference('PresentationFramework')
clr.AddReference('WindowsBase')
clr.AddReference('System')
from System.Windows import Window
from System.Net import WebClient, WebException
from System.Text import Encoding

doc = revit.doc

# 1. DEFINIÇÃO DA INTERFACE VISUAL (XAML)
UI_XAML = """
<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        Title="Kairós | Assistente IA Privado" Height="550" Width="480" WindowStartupLocation="CenterScreen">
    <Grid Margin="15">
        <Grid.RowDefinitions>
            <RowDefinition Height="*"/>
            <RowDefinition Height="Auto"/>
        </Grid.RowDefinitions>
        
        <Border Grid.Row="0" BorderBrush="#dddddd" BorderThickness="1" CornerRadius="5" Padding="10" Margin="0,0,0,15" Background="#fdfdfd">
            <ScrollViewer x:Name="ChatScroll" VerticalScrollBarVisibility="Auto">
                <TextBlock x:Name="ChatHistory" TextWrapping="Wrap" FontSize="13" Foreground="#333333"/>
            </ScrollViewer>
        </Border>
        
        <Grid Grid.Row="1">
            <Grid.ColumnDefinitions>
                <ColumnDefinition Width="*"/>
                <ColumnDefinition Width="Auto"/>
            </Grid.ColumnDefinitions>
            <TextBox x:Name="InputBox" Grid.Column="0" Height="50" TextWrapping="Wrap" AcceptsReturn="True" Padding="5"/>
            <Button x:Name="BtnSend" Grid.Column="1" Content="Enviar" Width="90" Margin="10,0,0,0" Click="OnSendClick" Background="#00bcd4" Foreground="White" FontWeight="Bold" BorderThickness="0" Cursor="Hand"/>
        </Grid>
    </Grid>
</Window>
"""

# 2. LÓGICA DA JANELA DE CHAT
class KairosAIWindow(forms.WPFWindow):
    def __init__(self, xaml_source):
        forms.WPFWindow.__init__(self, xaml_source, literal_string=True)
        self.ChatHistory.Text = "🤖 Estagiário Kairós: Olá! Agora eu consigo 'ver' o seu modelo Revit. O que vamos analisar hoje?\n\n"

    def sanitize_for_ironpython(self, text):
        if not text: return ""
        return "".join(c for c in text if not (0xD800 <= ord(c) <= 0xDFFF))

    def OnSendClick(self, sender, e):
        user_text = self.InputBox.Text.strip()
        if not user_text:
            return
        
        self.ChatHistory.Text += "👤 Você: " + user_text + "\n"
        self.InputBox.Text = ""
        
        with forms.ProgressBar(title="Estagiário analisando o modelo...") as pb:
            pb.update_progress(50, 100)
            response_text = self.call_ollama(user_text)
            pb.update_progress(100, 100)
        
        self.ChatHistory.Text += "🤖 Estagiário: " + response_text + "\n\n"
        self.ChatScroll.ScrollToEnd()

    # 3. EXTRAÇÃO DE DADOS E CONEXÃO COM OLLAMA
    def call_ollama(self, prompt):
        url = "http://localhost:11434/api/chat"
        safe_prompt = self.sanitize_for_ironpython(prompt)
        
        # --- EXTRAÇÃO DE CONTEXTO DO REVIT (Os "Olhos" da IA) ---
        try:
            project_name = doc.Title
            active_view = doc.ActiveView.Name
            
            # Conta quantas paredes existem no projeto atual
            wall_count = DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Walls).WhereElementIsNotElementType().GetElementCount()
            
            # Conta quantos ambientes existem
            room_count = DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Rooms).WhereElementIsNotElementType().GetElementCount()
        except Exception:
            project_name = "Desconhecido"
            active_view = "Desconhecida"
            wall_count = 0
            room_count = 0

        # --- A INSTRUÇÃO SECRETA (System Prompt) ---
        system_instructions = (
            "Você é o 'Estagiário Kairós', um assistente BIM especialista em Revit. "
            "Você está integrado diretamente no software do usuário através do pyRevit. "
            "Responda sempre em português brasileiro, de forma clara, técnica e objetiva. "
            "AQUI ESTÃO OS DADOS ATUAIS DO MODELO QUE O USUÁRIO ESTÁ TRABALHANDO AGORA:\n"
            "- Nome do Arquivo: {0}\n"
            "- Vista Ativa na tela do usuário: {1}\n"
            "- Total de Paredes modeladas: {2}\n"
            "- Total de Ambientes criados: {3}\n"
            "Use essas informações para responder com contexto caso o usuário pergunte algo sobre o projeto."
        ).format(project_name, active_view, wall_count, room_count)

        # Monta a conversa passando a instrução de sistema PRIMEIRO, e a pergunta do usuário DEPOIS
        data = {
            "model": "llama3.1",
            "messages": [
                {"role": "system", "content": system_instructions},
                {"role": "user", "content": safe_prompt}
            ],
            "stream": False
        }
        
        try:
            json_string = json.dumps(data, ensure_ascii=False)
            bytes_payload = Encoding.UTF8.GetBytes(json_string)
            
            client = WebClient()
            client.Headers.Add("Content-Type", "application/json")
            response_bytes = client.UploadData(url, "POST", bytes_payload)
            response_str = Encoding.UTF8.GetString(response_bytes)
            
            result = json.loads(response_str)
            return result.get("message", {}).get("content", "Sem resposta.")
            
        except WebException as we:
            return "[Erro de Conexão com Ollama] Detalhe: " + str(we)
        except Exception as e:
            return "[Erro no código] Detalhe: " + str(e)

# 4. EXECUÇÃO
if __name__ == '__main__':
    window = KairosAIWindow(UI_XAML)
    window.ShowDialog()