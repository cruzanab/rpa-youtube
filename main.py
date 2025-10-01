import os
import pandas as pd
from googleapiclient.discovery import build
from datetime import datetime

# 🔑 Desabilitar completamente as Application Default Credentials
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = ''

# API Key do YouTube
API_KEY = os.getenv("YOUTUBE_API_KEY")
CHANNEL_HANDLE = "cortes-leonenilceoficial4101"
OUTPUT_DIR = "dados"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "monitoramento_cortesleonnilce.xlsx")

# Verificar se a API Key está disponível
if not API_KEY:
    raise ValueError("❌ YOUTUBE_API_KEY não encontrada. Verifique as GitHub Secrets.")

print(f"✅ API Key carregada: {API_KEY[:10]}...")

# Cria a pasta se não existir
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# 🔧 SOLUÇÃO DEFINITIVA: Criar o cliente YouTube sem credenciais padrão
try:
    # Método alternativo para construir o cliente
    from googleapiclient.discovery import build
    
    # Forçar criação sem autenticação padrão
    youtube = build(
        "youtube", 
        "v3", 
        developerKey=API_KEY,
        static_discovery=False  # Importante: evitar discovery automático
    )
    print("✅ Cliente YouTube criado com sucesso usando API Key")
except Exception as e:
    print(f"❌ Erro ao criar cliente YouTube: {e}")
    raise

def get_channel_stats_by_handle(handle):
    """
    Busca estatísticas do canal a partir do handle usando search()
    """
    print("🔍 Buscando canal pelo handle...")
    
    try:
        # Busca o canal pelo handle
        request = youtube.search().list(
            part="snippet",
            q=f"@{handle}",
            type="channel",
            maxResults=1
        )
        response = request.execute()

        if "items" not in response or not response["items"]:
            raise Exception(f"❌ Canal @{handle} não encontrado")
        
        channel_id = response["items"][0]["snippet"]["channelId"]
        channel_title = response["items"][0]["snippet"]["title"]
        print(f"✅ Canal encontrado: {channel_title} (ID: {channel_id})")

        # Agora pega stats usando channelId
        request = youtube.channels().list(
            part="snippet,statistics",
            id=channel_id
        )
        response = request.execute()
        
        if not response["items"]:
            raise Exception("❌ Estatísticas do canal não encontradas")
        
        data = response["items"][0]

        return {
            "nome": data["snippet"]["title"],
            "inscritos": int(data["statistics"].get("subscriberCount", 0)),
            "visualizacoes": int(data["statistics"].get("viewCount", 0)),
            "videos": int(data["statistics"].get("videoCount", 0)),
            "canal_id": data["id"]
        }
    except Exception as e:
        print(f"❌ Erro ao buscar estatísticas do canal: {e}")
        raise

def get_latest_videos(channel_id, max_results=5):
    """
    Pega os últimos vídeos do canal com estatísticas básicas
    """
    print(f"🎥 Buscando últimos {max_results} vídeos...")
    
    try:
        request = youtube.search().list(
            part="id,snippet",
            channelId=channel_id,
            order="date",
            type="video",
            maxResults=max_results
        )
        response = request.execute()
        
        video_ids = [item["id"]["videoId"] for item in response["items"] if item["id"]["kind"] == "youtube#video"]
        
        print(f"📹 IDs dos vídeos encontrados: {video_ids}")
        
        video_stats = []
        for vid in video_ids:
            request = youtube.videos().list(
                part="snippet,statistics",
                id=vid
            )
            vid_response = request.execute()
            if "items" in vid_response and vid_response["items"]:
                info = vid_response["items"][0]
                stats = info["statistics"]
                video_stats.append({
                    "titulo": info["snippet"]["title"],
                    "views": int(stats.get("viewCount", 0)),
                    "likes": int(stats.get("likeCount", 0)),
                    "comentarios": int(stats.get("commentCount", 0)),
                    "compartilhamentos": stats.get("shareCount", "N/A")
                })
                print(f"   ✅ Vídeo: {info['snippet']['title'][:30]}... - {stats.get('viewCount', 0)} views")
        
        return video_stats
    except Exception as e:
        print(f"❌ Erro ao buscar vídeos: {e}")
        return []

def save_to_excel(data, filename):
    """
    Salva os dados em Excel, acumulando histórico
    """
    try:
        df = pd.DataFrame([data])
        if os.path.exists(filename):
            old_df = pd.read_excel(filename)
            df = pd.concat([old_df, df], ignore_index=True)
        
        df.to_excel(filename, index=False)
        print(f"💾 Dados salvos em {filename}")
    except Exception as e:
        print(f"❌ Erro ao salvar Excel: {e}")
        raise

def coletar_dados():
    print("🚀 Iniciando coleta de dados...")
    
    try:
        stats = get_channel_stats_by_handle(CHANNEL_HANDLE)
        videos = get_latest_videos(stats["canal_id"])

        coleta = {
            "data_coleta": datetime.today().strftime("%Y-%m-%d %H:%M:%S"),
            "inscritos": stats["inscritos"],
            "visualizacoes_totais": stats["visualizacoes"],
            "qtd_videos": stats["videos"]
        }

        # Adiciona estatísticas dos vídeos
        for i, v in enumerate(videos[:3], 1):
            coleta.update({
                f"video_{i}_titulo": v['titulo'][:50],
                f"video_{i}_views": v["views"],
                f"video_{i}_likes": v["likes"],
                f"video_{i}_comentarios": v["comentarios"]
            })

        save_to_excel(coleta, OUTPUT_FILE)
        print("✅ Coleta concluída com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro durante a coleta: {str(e)}")
        raise

if __name__ == "__main__":
    coletar_dados()