# -*- coding: utf-8 -*-
from pyrevit import revit, DB, forms
import os
import clr

# Importações para a interface WPF e caixas de diálogo do Windows
clr.AddReference('PresentationFramework')
clr.AddReference('WindowsBase')
clr.AddReference('System.Windows.Forms')
from System.Windows import Window
from System.Windows.Forms import FolderBrowserDialog

doc = revit.doc
uidoc = revit.uidoc

# 1. DEFINIÇÃO DA INTERFACE VISUAL (XAML)
UI_XAML = """
<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        Title="Kairós | Biblioteca de Famílias" Height="600" Width="400" WindowStartupLocation="CenterScreen" Topmost="True">
    <Grid Margin="15">
        <Grid.RowDefinitions>
            <RowDefinition Height="Auto"/>
            <RowDefinition Height="Auto"/>
            <RowDefinition Height="*"/>
        </Grid.RowDefinitions>
        
        <Button Content="Selecionar Pasta do Servidor" Height="35" Background="#00bcd4" Foreground="White" FontWeight="Bold" BorderThickness="0" Cursor="Hand" Click="OnSelectFolderClick"/>
        
        <TextBlock x:Name="TxtFolderPath" Grid.Row="1" Text="Nenhuma pasta selecionada." Foreground="Gray" Margin="0,10,0,10" TextWrapping="Wrap" FontSize="11"/>
        
        <ListBox x:Name="FamilyList" Grid.Row="2" MouseDoubleClick="OnFamilyDoubleClick" BorderBrush="#dddddd">
            <ListBox.ItemTemplate>
                <DataTemplate>
                    <Grid Margin="2">
                        <TextBlock Text="{Binding Name}" Padding="5" FontSize="13" FontWeight="SemiBold"/>
                    </Grid>
                </DataTemplate>
            </ListBox.ItemTemplate>
        </ListBox>
    </Grid>
</Window>
"""

# Classe simples para armazenar o nome e o caminho do arquivo
class FamilyFile(object):
    def __init__(self, name, path):
        self.Name = name
        self.Path = path

# 2. LÓGICA DA JANELA DE BIBLIOTECA
class LibraryWindow(forms.WPFWindow):
    def __init__(self, xaml_source):
        forms.WPFWindow.__init__(self, xaml_source, literal_string=True)
        self.files_data = []

    def OnSelectFolderClick(self, sender, e):
        # Abre a caixa amarela nativa do Windows para escolher a pasta
        dialog = FolderBrowserDialog()
        dialog.Description = "Selecione a pasta onde estão as famílias da Kairós"
        
        if dialog.ShowDialog() == System.Windows.Forms.DialogResult.OK:
            folder_path = dialog.SelectedPath
            self.TxtFolderPath.Text = "Pasta atual: " + folder_path
            self.load_families_from_folder(folder_path)

    def load_families_from_folder(self, folder_path):
        self.files_data = []
        if os.path.exists(folder_path):
            # Varre a pasta procurando apenas arquivos do Revit (.rfa)
            for f in os.listdir(folder_path):
                if f.lower().endswith('.rfa'):
                    clean_name = f.replace('.rfa', '').replace('.RFA', '')
                    self.files_data.append(FamilyFile(clean_name, os.path.join(folder_path, f)))
        
        self.FamilyList.ItemsSource = self.files_data

    # --- O PULO DO GATO: INSERÇÃO COM DUPLO CLIQUE ---
    def OnFamilyDoubleClick(self, sender, e):
        selected_item = self.FamilyList.SelectedItem
        if not selected_item:
            return
        
        # 1. Esconde a janela para liberar a tela do Revit para o usuário clicar
        self.Hide()
        
        try:
            # 2. Carrega a família e pega o tipo dela
            family_symbol = self.load_and_get_symbol(selected_item.Path)
            
            if family_symbol:
                # 3. Chama a ferramenta nativa do Revit que gruda o objeto no mouse!
                # Nota: Isso congela o código até o usuário apertar ESC no Revit.
                uidoc.PromptForFamilyInstancePlacement(family_symbol)
                
        except Exception as ex:
            # Quando o usuário aperta ESC para terminar de inserir, o Revit lança um erro de "Cancelamento". 
            # Nós apenas ignoramos esse "erro" pois é o comportamento normal.
            pass
        
        # 4. Mostra a janela da biblioteca de volta para ele pegar outra família
        self.Show()

    def load_and_get_symbol(self, path):
        family_symbol = None
        
        # O Revit exige que carregamentos de arquivo sejam feitos dentro de Transações
        t = DB.Transaction(doc, "Carregar Família da Biblioteca")
        t.Start()
        
        try:
            # Truque do Python para lidar com o parâmetro "out" do C# no método LoadFamily
            family_loaded = clr.Reference[DB.Family]()
            success = doc.LoadFamily(path, family_loaded)
            
            if success:
                fam = family_loaded.Value
            else:
                # Se success for Falso, significa que a família JÁ ESTAVA carregada no projeto.
                # Precisamos encontrá-la no banco de dados para pegar o símbolo mesmo assim.
                fam_name = os.path.basename(path).replace(".rfa", "").replace(".RFA", "")
                fam = None
                collector = DB.FilteredElementCollector(doc).OfClass(DB.Family)
                for f in collector:
                    if f.Name == fam_name:
                        fam = f
                        break
            
            if fam:
                # Pega o primeiro Tipo (Symbol) dentro da Família
                symbol_ids = fam.GetFamilySymbolIds()
                if symbol_ids.Count > 0:
                    family_symbol = doc.GetElement(symbol_ids[0])
                    
                    # O Revit exige que o Tipo seja "Ativado" na memória antes de ser inserido no 3D
                    if not family_symbol.IsActive:
                        family_symbol.Activate()
        
            t.Commit()
            return family_symbol
            
        except Exception as e:
            t.RollBack()
            forms.alert("Erro ao tentar carregar a família: " + str(e))
            return None

# 3. EXECUÇÃO
if __name__ == '__main__':
    window = LibraryWindow(UI_XAML)
    window.Show()