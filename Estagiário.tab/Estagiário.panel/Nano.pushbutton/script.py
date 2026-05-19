# -*- coding: utf-8 -*-
__title__ = "Exportar\nPNG"
__author__ = "Kairós Arquitetura"
__doc__ = """
Captura a vista 3D atual e renderiza usando o motor Stable Diffusion (Stability AI).
"""

import clr
import sys
import os
import base64
import json

clr.AddReference("System")
clr.AddReference("System.Drawing")
from System.Net import WebRequest, WebException
from System.Text import Encoding
from System.IO import StreamReader
from System.Drawing import Image, Bitmap, Graphics

from Autodesk.Revit.DB import *
from pyrevit import revit, forms

doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
active_view = uidoc.ActiveView

# ── 1. Pergunta do Usuário ───────────────────────────────────────────────────
prompt_usuario = forms.ask_for_string(
    prompt="Descreva os materiais, iluminação e estilo do render:",
    title="Kairós AI Render",
    default="Fotografia realista de arquitetura, design moderno, iluminação natural, texturas de alta qualidade, 8k, octane render"
)

if not prompt_usuario:
    sys.exit()

# Força a leitura correta de acentos (ç, ã, é) no Windows
if isinstance(prompt_usuario, str):
    try:
        prompt_usuario = prompt_usuario.decode('cp1252')
    except:
        pass

# ── 2. O Fotógrafo do Revit (Agora blindado contra JPG) ──────────────────────
desktop_path = r"C:\Users\fabio\OneDrive\Área de Trabalho"
img_name = "Kairos_Base_Revit"
img_path_base = os.path.join(desktop_path, img_name)

options = ImageExportOptions()
options.ExportRange = ExportRange.CurrentView
options.FilePath = img_path_base
# Obriga o Revit a usar PNG tanto em Linha Oculta quanto em Realista/Sombreado
options.HLRandWFViewsFileType = ImageFileType.PNG
options.ShadowViewsFileType = ImageFileType.PNG 
options.ImageResolution = ImageResolution.DPI_150
options.ZoomType = ZoomFitType.Zoom
options.Zoom = 100

try:
    doc.ExportImage(options)
    
    # Procura por imagens geradas, seja .png ou .jpg (caso o Revit teime)
    arquivos = [f for f in os.listdir(desktop_path) if f.startswith(img_name) and (f.endswith(".png") or f.endswith(".jpg") or f.endswith(".jpeg"))]
    
    if not arquivos:
        forms.alert("Erro: O Revit não gerou a imagem na Área de Trabalho.", exitscript=True)
        
    imagem_exportada = os.path.join(desktop_path, arquivos[0])
    
except Exception as e:
    forms.alert("Erro na exportação do Revit: {}".format(str(e)), exitscript=True)

# ── 3. Redimensionamento Obrigatório para a IA ───────────────────────────────
imagem_redimensionada = os.path.join(desktop_path, "Kairos_Base_1024.png")
original_img = Image.FromFile(imagem_exportada)
resized_img = Bitmap(1024, 512)
g = Graphics.FromImage(resized_img)
g.DrawImage(original_img, 0, 0, 1024, 512)
resized_img.Save(imagem_redimensionada)
g.Dispose()
original_img.Dispose()

# ── 4. Codificando para Base64 ───────────────────────────────────────────────
with open(imagem_redimensionada, "rb") as image_file:
    base64_data = base64.b64encode(image_file.read()).decode('utf-8')

# ── 5. Conexão com o Motor de Render (Stability AI) ──────────────────────────
# 🚨 COLE SUA CHAVE NOVA AQUI 🚨
API_KEY = "sk-4RCv9eUxb0l4WkRSfdJQ8uxcnakNjao65liWPpobVedzTa8J"
URL = "https://api.stability.ai/v1/generation/stable-diffusion-v1-5/image-to-image"

payload = {
    "init_image": base64_data,
    "init_image_mode": "IMAGE_STRENGTH",
    "image_strength": 0.45, 
    "text_prompts": [
        {
            "text": prompt_usuario,
            "weight": 1
        }
    ],
    "cfg_scale": 7,
    "samples": 1,
    "steps": 30
}

# ── 6. O Mensageiro (Envio e Retorno) ────────────────────────────────────────
try:
    with forms.ProgressBar(title="Kairós AI: Renderizando sua vista...", cancellable=False):
        req = WebRequest.Create(URL)
        req.Method = "POST"
        req.ContentType = "application/json"
        req.Accept = "application/json"
        req.Headers.Add("Authorization", "Bearer " + API_KEY)
        
        # O ensure_ascii=False garante que o pacote não quebre por causa dos acentos
        json_seguro = json.dumps(payload, ensure_ascii=False)
        post_data = Encoding.UTF8.GetBytes(json_seguro)
        
        req.ContentLength = post_data.Length
        
        with req.GetRequestStream() as stream:
            stream.Write(post_data, 0, post_data.Length)
            
        # Pega a imagem processada
        response = req.GetResponse()
        with response.GetResponseStream() as stream:
            reader = StreamReader(stream)
            resposta_texto = reader.ReadToEnd()
            
        resposta_json = json.loads(resposta_texto)
        img_render_base64 = resposta_json["artifacts"][0]["base64"]
        
        render_final_path = os.path.join(desktop_path, "KAIROS_RENDER_FINAL.png")
        with open(render_final_path, "wb") as fh:
            fh.write(base64.b64decode(img_render_base64))
            
        # Abre na tela
        os.startfile(render_final_path)
        forms.toast("Renderização concluída com sucesso!", title="Kairós AI")
        
except WebException as api_err:
    error_msg = str(api_err)
    if api_err.Response:
        with StreamReader(api_err.Response.GetResponseStream()) as reader:
            error_msg = reader.ReadToEnd()
    forms.alert("Erro no motor de renderização:\n{}".format(error_msg))

# Limpeza dos rastros
try:
    os.remove(imagem_exportada)
    os.remove(imagem_redimensionada)
except:
    pass