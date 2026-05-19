# -*- coding: utf-8 -*-
from pyrevit import revit, DB, forms, script, HOST_APP
import os
import json
import clr

# Importações para a interface WPF e Imagens
clr.AddReference('PresentationFramework')
clr.AddReference('PresentationCore')
clr.AddReference('WindowsBase')
clr.AddReference('System.Drawing')
from System.Windows import Window
from System.Collections.ObjectModel import ObservableCollection
from System.Drawing import Size
from System.Drawing.Imaging import ImageFormat
from System.IO import MemoryStream
from System.Windows.Media.Imaging import BitmapImage
from System.Windows.Media import BrushConverter

doc = revit.doc
bc = BrushConverter()

# --- SUPRESSOR DE AVISOS DO REVIT (AUTO-CLICKER) ---
def auto_dismiss_dialog(sender, args):
    try:
        args.OverrideResult(1) 
    except:
        pass

# --- SISTEMA DE BANCO DE DADOS EXTERNO (JSON) ---
CACHE_DIR = os.path.join(os.getenv('APPDATA'), 'Kairos_BIM_Cache')
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

file_name_clean = "".join(x for x in doc.Title if x.isalnum() or x in " _-")
CACHE_FILE = os.path.join(CACHE_DIR, "{}_family_sizes.json".format(file_name_clean))

def load_database():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                data = json.load(f)
                if "families" in data:
                    return data
        except Exception as e:
            print("Erro ao ler banco de dados: {}".format(e))
    return {"removed_mb": 0.0, "families": {}}

def save_database(data_dict):
    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump(data_dict, f)
    except Exception as e:
        print("Erro ao salvar banco de dados: {}".format(e))

KAIROS_DB = load_database()
KAIROS_FAMILY_CACHE = KAIROS_DB["families"]
KAIROS_REMOVED_SIZE = float(KAIROS_DB.get("removed_mb", 0.0))

# 1. DEFINIÇÃO DA INTERFACE VISUAL (XAML)
UI_XAML = """
<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        Title="Kairós | Auditoria de Famílias" Height="700" Width="650" WindowStartupLocation="CenterScreen">
    <Grid Margin="15">
        <Grid.RowDefinitions>
            <RowDefinition Height="Auto"/>
            <RowDefinition Height="Auto"/>
            <RowDefinition Height="Auto"/>
            <RowDefinition Height="Auto"/>
            <RowDefinition Height="*"/>
            <RowDefinition Height="Auto"/>
        </Grid.RowDefinitions>

        <TextBlock Text="Selecione as famílias para analisar tamanho, renomear ou remover (Anotações e 2D estão protegidos):" FontWeight="Bold" Margin="0,0,0,10"/>

        <Grid Grid.Row="1" Margin="0,0,0,10">
            <Grid.ColumnDefinitions>
                <ColumnDefinition Width="Auto"/>
                <ColumnDefinition Width="*"/>
            </Grid.ColumnDefinitions>
            <TextBlock Text="Pesquisar:" VerticalAlignment="Center" FontWeight="SemiBold" Margin="0,0,10,0"/>
            <TextBox x:Name="SearchBox" Grid.Column="1" Height="25" VerticalContentAlignment="Center" TextChanged="OnSearchTextChanged"/>
        </Grid>

        <Border Grid.Row="2" Background="#f4f4f4" Padding="12" Margin="0,0,0,15" CornerRadius="5" BorderBrush="#dddddd" BorderThickness="1">
            <Grid>
                <Grid.ColumnDefinitions>
                    <ColumnDefinition Width="*"/>
                    <ColumnDefinition Width="*"/>
                </Grid.ColumnDefinitions>
                <StackPanel Grid.Column="0">
                    <TextBlock x:Name="TxtTotalFam" Text="Total de Famílias (3D): 0" FontWeight="SemiBold"/>
                    <TextBlock x:Name="TxtSelecionadas" Text="Selecionadas (Global): 0" Margin="0,5,0,0"/>
                </StackPanel>
                <StackPanel Grid.Column="1">
                    <TextBlock x:Name="TxtTamanhoSel" Text="Tamanho Selecionado: 0.00 MB" FontWeight="SemiBold"/>
                    <TextBlock x:Name="TxtRemovido" Text="Total Removido (Projeto): 0.00 MB" Foreground="#c0392b" Margin="0,5,0,0"/>
                </StackPanel>
            </Grid>
        </Border>

        <StackPanel Grid.Row="3" Orientation="Horizontal" Margin="0,0,0,10">
            <Button Content="Selecionar Visíveis" Width="120" Height="25" Margin="0,0,10,0" Click="OnSelectAllClick"/>
            <Button Content="Desmarcar Visíveis" Width="120" Height="25" Margin="0,0,10,0" Click="OnDeselectAllClick"/>
            <Button Content="Desmarcar Usadas" Width="120" Height="25" Click="OnDeselectUsedClick"/>
        </StackPanel>

        <ListBox x:Name="FamilyList" Grid.Row="4" ScrollViewer.HorizontalScrollBarVisibility="Disabled">
            <ListBox.ItemTemplate>
                <DataTemplate>
                    <Grid Margin="5">
                        <Grid.ColumnDefinitions>
                            <ColumnDefinition Width="Auto"/>
                            <ColumnDefinition Width="50"/>
                            <ColumnDefinition Width="*"/>
                        </Grid.ColumnDefinitions>
                        
                        <CheckBox IsChecked="{Binding IsSelected}" Click="OnCheckChanged" VerticalAlignment="Center" Margin="0,0,10,0"/>
                        
                        <Image Grid.Column="1" Width="40" Height="40" Source="{Binding Icon}" Margin="0,0,5,0"/>
                        
                        <StackPanel Grid.Column="2" VerticalAlignment="Center" Margin="10,0,0,0">
                            <WrapPanel VerticalAlignment="Center" Margin="0,0,0,3">
                                <TextBlock Text="{Binding Name}" FontWeight="SemiBold" TextWrapping="Wrap" VerticalAlignment="Center"/>
                                <Border Background="{Binding UsageColor}" CornerRadius="3" Margin="8,0,0,0" Padding="5,2" VerticalAlignment="Center">
                                    <TextBlock Text="{Binding UsageText}" FontSize="10" FontWeight="Bold" Foreground="{Binding UsageTextColor}"/>
                                </Border>
                            </WrapPanel>
                            <TextBlock Text="{Binding SizeText}" FontSize="11" Foreground="#666666"/>
                        </StackPanel>
                    </Grid>
                </DataTemplate>
            </ListBox.ItemTemplate>
        </ListBox>

        <StackPanel Grid.Row="5" Orientation="Horizontal" HorizontalAlignment="Right" Margin="0,15,0,0">
            <Button x:Name="BtnCalc" Content="Calcular Tamanho" Width="130" Height="30" Margin="0,0,10,0" Click="OnCalculateSizeClick"/>
            <Button x:Name="BtnRename" Content="Renomear" Width="100" Height="30" Margin="0,0,10,0" Click="OnRenameClick"/>
            <Button x:Name="BtnDelete" Content="Remover" Width="100" Height="30" Background="#e74c3c" Foreground="White" BorderThickness="0" Click="OnDeleteClick"/>
        </StackPanel>
    </Grid>
</Window>
"""

def get_image_source(bitmap):
    if not bitmap: return None
    ms = MemoryStream()
    bitmap.Save(ms, ImageFormat.Png)
    ms.Position = 0
    bi = BitmapImage()
    bi.BeginInit()
    bi.StreamSource = ms
    bi.EndInit()
    return bi

class FamilyItem(object):
    def __init__(self, family):
        self.ElementId = family.Id
        self.Name = family.Name
        self.IsSelected = False
        self.FamilyObj = family
        self.Icon = None
        self.size_mb = 0.0
        
        # --- VERIFICAÇÃO DE USO NO PROJETO ---
        inst_count = 0
        for sym_id in family.GetFamilySymbolIds():
            filter = DB.FamilyInstanceFilter(doc, sym_id)
            inst_count += DB.FilteredElementCollector(doc).WherePasses(filter).GetElementCount()
            
        self.is_used = inst_count > 0
            
        if self.is_used:
            self.UsageText = "{} instâncias".format(inst_count)
            self.UsageColor = bc.ConvertFromString("#e8f5e9") 
            self.UsageTextColor = bc.ConvertFromString("#2e7d32") 
        else:
            self.UsageText = "Não utilizada"
            self.UsageColor = bc.ConvertFromString("#ffebee") 
            self.UsageTextColor = bc.ConvertFromString("#c62828") 
            
        # --- RECUPERAÇÃO DO TAMANHO (JSON) ---
        fam_key = str(family.Id)
        if fam_key in KAIROS_FAMILY_CACHE:
            self.size_mb = float(KAIROS_FAMILY_CACHE[fam_key])
            self.SizeText = "Tamanho: {:.2f} MB".format(self.size_mb)
        else:
            self.SizeText = "Tamanho: (Aguardando Cálculo)"
        
        # --- IMAGEM DE PRÉ-VISUALIZAÇÃO ---
        symbol_ids = family.GetFamilySymbolIds()
        if symbol_ids.Count > 0:
            first_id = list(symbol_ids)[0] 
            symbol = doc.GetElement(first_id)
            bmp = symbol.GetPreviewImage(Size(40, 40))
            self.Icon = get_image_source(bmp)

class FamilyManagerWindow(forms.WPFWindow):
    def __init__(self, xaml_source):
        forms.WPFWindow.__init__(self, xaml_source, literal_string=True)
        self.all_families = [] 
        self.family_data = ObservableCollection[object]() 
        
        self.populate_list()
        self.FamilyList.ItemsSource = self.family_data
        self.update_stats()

    def populate_list(self):
        families = DB.FilteredElementCollector(doc).OfClass(DB.Family).ToElements()
        
        ignore_bics = []
        bics_to_ignore = [
            "OST_ProfileFamilies", 
            "OST_Profiles", 
            "OST_TitleBlocks", 
            "OST_DetailComponents"
        ]
        
        for bic_name in bics_to_ignore:
            if hasattr(DB.BuiltInCategory, bic_name):
                ignore_bics.append(int(getattr(DB.BuiltInCategory, bic_name)))
        
        for fam in sorted(families, key=lambda x: x.Name):
            if fam.IsEditable: 
                cat = fam.FamilyCategory
                if cat:
                    # Protege TUDO que for Anotação
                    if cat.CategoryType == DB.CategoryType.Annotation:
                        continue
                    
                    # Correção: Extrai o ID da categoria de forma segura para Revit 2024, 2025 e 2026
                    cat_id_val = cat.Id.Value if hasattr(cat.Id, "Value") else cat.Id.IntegerValue
                    
                    # Protege as categorias da lista manual
                    if cat_id_val in ignore_bics:
                        continue
                
                item = FamilyItem(fam)
                self.all_families.append(item)
                self.family_data.Add(item)

    def OnSearchTextChanged(self, sender, e):
        search_text = self.SearchBox.Text.lower()
        self.family_data.Clear() 
        
        for item in self.all_families:
            if search_text in item.Name.lower():
                self.family_data.Add(item)
        
        self.update_stats()

    def update_stats(self):
        total_fam = len(self.all_families)
        selected_items = [f for f in self.all_families if f.IsSelected]
        qtd_sel = len(selected_items)
        total_sel_mb = float(sum([f.size_mb for f in selected_items]))
        
        self.TxtTotalFam.Text = "Total de Famílias (3D): {}".format(total_fam)
        self.TxtSelecionadas.Text = "Selecionadas (Global): {}".format(qtd_sel)
        self.TxtTamanhoSel.Text = "Tamanho Selecionado: {:.2f} MB".format(total_sel_mb)
        self.TxtRemovido.Text = "Total Removido (Projeto): {:.2f} MB".format(float(KAIROS_REMOVED_SIZE))

    def OnCheckChanged(self, sender, e):
        self.update_stats()

    def get_selected_items(self):
        return [item for item in self.all_families if item.IsSelected]

    def OnSelectAllClick(self, sender, e):
        for item in self.family_data: item.IsSelected = True
        self.FamilyList.Items.Refresh()
        self.update_stats()

    def OnDeselectAllClick(self, sender, e):
        for item in self.family_data: item.IsSelected = False
        self.FamilyList.Items.Refresh()
        self.update_stats()

    def OnDeselectUsedClick(self, sender, e):
        for item in self.family_data:
            if item.is_used:
                item.IsSelected = False
        self.FamilyList.Items.Refresh()
        self.update_stats()

    def OnCalculateSizeClick(self, sender, e):
        selected = self.get_selected_items()
        if not selected:
            forms.alert("Selecione famílias para calcular.")
            return

        temp_dir = os.environ.get('TEMP')
        HOST_APP.uiapp.DialogBoxShowing += auto_dismiss_dialog
        
        try:
            with forms.ProgressBar(title="Calculando...", cancellable=True) as pb:
                for idx, item in enumerate(selected):
                    if pb.cancelled:
                        forms.alert("Cálculo cancelado. O progresso feito até aqui foi salvo automaticamente.", warn_icon=False)
                        break

                    if item.size_mb > 0:
                        pb.update_progress(idx + 1, len(selected))
                        continue
                    
                    try:
                        fam_doc = doc.EditFamily(item.FamilyObj)
                        if fam_doc:
                            temp_path = os.path.join(temp_dir, item.Name + ".rfa")
                            fam_doc.SaveAs(temp_path)
                            size_mb = float(os.path.getsize(temp_path) / (1024.0 * 1024.0))
                            
                            item.size_mb = size_mb
                            item.SizeText = "Tamanho: {:.2f} MB".format(size_mb)
                            
                            KAIROS_FAMILY_CACHE[str(item.ElementId)] = size_mb
                            
                            fam_doc.Close(False)
                            if os.path.exists(temp_path): os.remove(temp_path)
                    except:
                        item.SizeText = "Erro (Protegida/Sistema)"
                    
                    pb.update_progress(idx + 1, len(selected))
        
        finally:
            HOST_APP.uiapp.DialogBoxShowing -= auto_dismiss_dialog
            KAIROS_DB["families"] = KAIROS_FAMILY_CACHE
            KAIROS_DB["removed_mb"] = KAIROS_REMOVED_SIZE
            save_database(KAIROS_DB)
            
            self.FamilyList.Items.Refresh()
            self.update_stats()

    def OnDeleteClick(self, sender, e):
        global KAIROS_REMOVED_SIZE
        selected = self.get_selected_items()
        if not selected: return
        
        to_delete = [item for item in selected if not item.is_used]
        skipped_count = len(selected) - len(to_delete)

        if not to_delete:
            if skipped_count > 0:
                forms.alert("Todas as famílias selecionadas estão em uso no projeto e foram bloqueadas para exclusão.", title="Proteção Kairós")
            return
        
        with revit.Transaction("Remover Famílias Kairós"):
            for item in to_delete:
                if item.size_mb > 0:
                    KAIROS_REMOVED_SIZE += float(item.size_mb)
                
                KAIROS_FAMILY_CACHE.pop(str(item.ElementId), None)
                doc.Delete(item.ElementId)
                
                if item in self.all_families: self.all_families.remove(item)
                if item in self.family_data: self.family_data.Remove(item)
        
        KAIROS_DB["families"] = KAIROS_FAMILY_CACHE
        KAIROS_DB["removed_mb"] = KAIROS_REMOVED_SIZE
        save_database(KAIROS_DB)
        
        liberacao = float(sum([f.size_mb for f in to_delete]))
        msg_final = "{} famílias deletadas com sucesso!\nLiberação estimada: {:.2f} MB".format(len(to_delete), liberacao)
        
        if skipped_count > 0:
            msg_final += "\n\n⚠️ {} famílias foram protegidas e mantidas no modelo por estarem em uso.".format(skipped_count)
            
        forms.alert(msg_final)
        self.update_stats()

    def OnRenameClick(self, sender, e):
        selected = self.get_selected_items()
        if not selected: return
        item = selected[0]
        new_name = forms.ask_for_string(default=item.Name, prompt="Novo nome:")
        if new_name:
            with revit.Transaction("Renomear Kairós"):
                item.FamilyObj.Name = new_name
            self.FamilyList.Items.Refresh()

if __name__ == '__main__':
    window = FamilyManagerWindow(UI_XAML)
    window.ShowDialog()