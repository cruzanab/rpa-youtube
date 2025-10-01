import os
import pandas as pd
from googleapiclient.discovery import build
from datetime import datetime
import google.auth

API_KEY = os.getenv("YOUTUBE_API_KEY")
CHANNEL_HANDLE = "cortes-leonenilceoficial4101"  # handle do canal (sem o "@")
OUTPUT_DIR = "dados"  # pasta onde o Excel será salvo
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "monitoramento_cortesleonnilce.xlsx")

# Cria a pasta se não existir
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# ⚠️ PROBLEMA AQUI: Remover qualquer autenticação padrão

try:
    credentials, project = google.auth.default()
    # Forçar o uso apenas da API Key
    youtube = build("youtube", "v3", developerKey=API_KEY)
except:
    # Se falhar, usar apenas API Key
    youtube = build("youtube", "v3", developerKey=API_KEY)

def get_channel_stats_by_handle(handle):
    """
    Busca estatísticas do canal a partir do handle usando search()
    """
    # Busca o canal pelo handle
    request = youtube.search().list(
        part="snippet",
        q=f"@{handle}",
        type="channel",
        maxResults=1
    )
    response = request.execute()

    if "items" not in response or not response["items"]:
        raise Exception("Canal não encontrado via search()")
    
    channel_id = response["items"][0]["snippet"]["channelId"]

    # Agora pega stats usando channelId
    request = youtube.channels().list(
        part="snippet,statistics",
        id=channel_id
    )
    response = request.execute()
    data = response["items"][0]

    return {
        "nome": data["snippet"]["title"],
        "inscritos": int(data["statistics"].get("subscriberCount", 0)),
        "visualizacoes": int(data["statistics"].get("viewCount", 0)),
        "videos": int(data["statistics"].get("videoCount", 0)),
        "canal_id": data["id"]
    }

def get_latest_videos(channel_id, max_results=5):
    """
    Pega os últimos vídeos do canal com estatísticas básicas
    """
    request = youtube.search().list(
        part="id",
        channelId=channel_id,
        order="date",
        maxResults=max_results
    )
    response = request.execute()
    
    video_ids = [item["id"]["videoId"] for item in response["items"] if item["id"]["kind"] == "youtube#video"]
    
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
                "compartilhamentos": stats.get("shareCount", "N/A")  # geralmente não disponível
            })
    return video_stats

def save_to_excel(data, filename):
    """
    Salva os dados em Excel, acumulando histórico
    """
    df = pd.DataFrame(data)
    if os.path.exists(filename):
        old_df = pd.read_excel(filename)
        df = pd.concat([old_df, df], ignore_index=True)
    df.to_excel(filename, index=False)

def coletar_dados():
    stats = get_channel_stats_by_handle(CHANNEL_HANDLE)
    videos = get_latest_videos(stats["canal_id"])

    coleta = {
        "data_coleta": datetime.today().strftime("%Y-%m-%d"),
        "inscritos": stats["inscritos"],
        "visualizacoes_totais": stats["visualizacoes"],
        "qtd_videos": stats["videos"]
    }

    for v in videos:
        coleta.update({
            f"{v['titulo']} - views": v["views"],
            f"{v['titulo']} - likes": v["likes"],
            f"{v['titulo']} - comentarios": v["comentarios"],
            f"{v['titulo']} - compartilhamentos": v["compartilhamentos"]
        })

    save_to_excel([coleta], OUTPUT_FILE)
    print(f"✅ Dados salvos em {OUTPUT_FILE}")

if __name__ == "__main__":
    coletar_dados()
