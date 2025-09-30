import os
import pandas as pd
from googleapiclient.discovery import build
from datetime import datetime

# 🔑 API Key do YouTube (crie no Google Cloud e cole aqui como variável de ambiente no Render)
API_KEY = os.getenv("YOUTUBE_API_KEY")
CHANNEL_USERNAME = "cortes-leonenilceoficial4101"
OUTPUT_FILE = "monitoramento_cortesleonnilce.xlsx"

# Conectar na API do YouTube
youtube = build("youtube", "v3", developerKey=API_KEY)

def get_channel_stats(username):
    request = youtube.channels().list(
        part="snippet,statistics",
        forUsername=username
    )
    response = request.execute()
    
    if "items" not in response or not response["items"]:
        raise Exception("Canal não encontrado.")
    
    data = response["items"][0]
    return {
        "nome": data["snippet"]["title"],
        "inscritos": int(data["statistics"].get("subscriberCount", 0)),
        "visualizacoes": int(data["statistics"].get("viewCount", 0)),
        "videos": int(data["statistics"].get("videoCount", 0)),
        "canal_id": data["id"]
    }

def get_latest_videos(channel_id, max_results=5):
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
                "compartilhamentos": stats.get("shareCount", "N/A")  # API do YouTube nem sempre expõe isso
            })
    return video_stats

def save_to_excel(data, filename):
    df = pd.DataFrame(data)
    if os.path.exists(filename):
        old_df = pd.read_excel(filename)
        df = pd.concat([old_df, df], ignore_index=True)
    df.to_excel(filename, index=False)

def coletar_dados():
    stats = get_channel_stats(CHANNEL_USERNAME)
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
