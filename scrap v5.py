import re
import json
import csv
import os
import sys
import urllib.request
import customtkinter as ctk
from tkinter import filedialog, messagebox, PhotoImage
from datetime import datetime, timedelta, timezone
from googleapiclient.discovery import build

# ======================================================
# GANTI DENGAN API KEY LU SENDIRI
# ======================================================
API_KEY = ''

current_data = []
current_data_type = None
youtube = None


def init_youtube_client(api_key):
    global youtube
    try:
        youtube = build('youtube', 'v3', developerKey=api_key)
        return True, None
    except Exception as e:
        youtube = None
        return False, str(e)


init_youtube_client(API_KEY)

def ekstrak_id_video(url):
    pola = r"(?:youtu\.be\/|youtube\.com\/(?:embed\/|v\/|shorts\/|watch\?v=|watch\?.+&v=))([\w-]{11})"
    cocok = re.search(pola, url)
    return cocok.group(1) if cocok else None

def ekstrak_info_channel(teks):
    teks = teks.strip()
    if not teks:
        return None, None

    cocok_id = re.search(r"(?:youtube\.com\/channel\/|^)(UC[\w-]{22})", teks)
    if cocok_id:
        return "id", cocok_id.group(1)

    cocok_handle = re.search(r"(?:youtube\.com\/)?@([\w.\-]+)", teks)
    if cocok_handle:
        return "handle", cocok_handle.group(1)

    cocok_custom = re.search(r"youtube\.com\/(?:c|user)\/([\w.\-]+)", teks)
    if cocok_custom:
        return "query", cocok_custom.group(1)

    if re.match(r"^[\w.\- ]+$", teks):
        return "query", teks

    return None, None

def konversi_ke_wib(iso_date_str):
    if not iso_date_str:
        return "Tidak diketahui"
    try:
        if '.' in iso_date_str:
            iso_date_str = iso_date_str.split('.')[0] + 'Z'
        waktu_utc = datetime.strptime(iso_date_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        waktu_wib = waktu_utc.astimezone(timezone(timedelta(hours=7)))
        return waktu_wib.strftime("%d %B %Y | %H:%M:%S WIB")
    except Exception:
        return "Tidak diketahui"

def format_angka(angka):
    try:
        return f"{int(angka):,}".replace(',', '.')
    except Exception:
        return "0"

def get_thumbnail_terbaik(thumbs):
    for res in ['maxres', 'standard', 'high', 'medium', 'default']:
        if res in thumbs:
            return thumbs[res].get('url', '')
    return ""

def get_video_metadata(video_id):
    response_video = youtube.videos().list(part="snippet,statistics", id=video_id).execute()
    if not response_video.get('items'):
        return {"error": f"Video {video_id} tidak ditemukan atau di-private."}

    video_data = response_video['items'][0]
    snippet_v = video_data['snippet']
    stats_v = video_data['statistics']
    channel_id = snippet_v.get('channelId')
    teks_subs = "Disembunyikan"
    teks_total_video = "0 video"
    channel_dibuat = "Tidak diketahui"
    negara_channel = "Tidak diketahui"

    if channel_id:
        res_c = youtube.channels().list(part="snippet,statistics", id=channel_id).execute()
        if res_c.get('items'):
            c_item = res_c['items'][0]
            channel_dibuat = konversi_ke_wib(c_item['snippet'].get('publishedAt'))
            negara_channel = c_item['snippet'].get('country', 'Tidak diatur')
            subs = c_item['statistics'].get('subscriberCount')
            if subs:
                teks_subs = format_angka(subs)
            vids = c_item['statistics'].get('videoCount')
            if vids:
                teks_total_video = format_angka(vids)

    tags = snippet_v.get('tags', [])
    return {
        "Channel": snippet_v.get('channelTitle'),
        "Channel_ID": channel_id,
        "Channel_Dibuat": channel_dibuat,
        "Negara": negara_channel,
        "Subscribers": teks_subs,
        "Total_Video": teks_total_video,
        "Judul": snippet_v.get('title'),
        "Video_ID": video_id,
        "Waktu_Upload": konversi_ke_wib(snippet_v.get('publishedAt')),
        "Views": int(stats_v.get('viewCount', 0)),
        "Likes": int(stats_v.get('likeCount', 0)),
        "Komentar": int(stats_v.get('commentCount', 0)),
        "Thumbnail_URL": get_thumbnail_terbaik(snippet_v.get('thumbnails', {})),
        "Tags": ", ".join(tags) if tags else "Tidak ada tag",
        "Deskripsi": snippet_v.get('description', '')
    }

def resolve_channel_id(channel_input):
    jenis, nilai = ekstrak_info_channel(channel_input)
    if not jenis:
        return None, "Format link/nama channel tidak valid."
    if jenis == "id":
        return nilai, None
    if jenis == "handle":
        res = youtube.channels().list(part="id", forHandle=nilai).execute()
        if res.get('items'):
            return res['items'][0]['id'], None
        query = "@" + nilai
    else:
        query = nilai
    res_search = youtube.search().list(part="snippet", q=query, type="channel", maxResults=1).execute()
    if res_search.get('items'):
        return res_search['items'][0]['snippet']['channelId'], None
    return None, "Channel tidak ditemukan."

def get_channel_detail(channel_id, jumlah_video):
    res_channel = youtube.channels().list(part="snippet,statistics,contentDetails", id=channel_id).execute()
    if not res_channel.get('items'):
        return {"error": "Channel tidak ditemukan atau tidak bisa diakses."}

    item = res_channel['items'][0]
    snippet = item['snippet']
    stats = item['statistics']
    uploads_playlist = item.get('contentDetails', {}).get('relatedPlaylists', {}).get('uploads')
    channel_info = {
        "Channel": snippet.get('title', ''),
        "Channel_ID": channel_id,
        "Custom_URL": snippet.get('customUrl', ''),
        "Dibuat_Pada": konversi_ke_wib(snippet.get('publishedAt')),
        "Negara": snippet.get('country', 'Tidak diatur'),
        "Subscribers": format_angka(stats.get('subscriberCount', 0)) if stats.get('subscriberCount') else "Disembunyikan",
        "Total_View_Channel": format_angka(stats.get('viewCount', 0)),
        "Total_Video": format_angka(stats.get('videoCount', 0)),
        "Thumbnail_URL": get_thumbnail_terbaik(snippet.get('thumbnails', {})),
        "Deskripsi": snippet.get('description', '')
    }

    video_list = []
    jumlah_video = max(0, min(int(jumlah_video), 50))
    if uploads_playlist and jumlah_video > 0:
        res_playlist = youtube.playlistItems().list(part="snippet,contentDetails", playlistId=uploads_playlist, maxResults=jumlah_video).execute()
        video_ids = [v['contentDetails']['videoId'] for v in res_playlist.get('items', [])]
        if video_ids:
            res_videos = youtube.videos().list(part="snippet,statistics", id=",".join(video_ids)).execute()
            for video in res_videos.get('items', []):
                s = video['snippet']
                st = video['statistics']
                video_list.append({
                    "Judul": s.get('title', ''),
                    "Video_ID": video.get('id', ''),
                    "Waktu_Upload": konversi_ke_wib(s.get('publishedAt')),
                    "Views": int(st.get('viewCount', 0)),
                    "Likes": int(st.get('likeCount', 0)),
                    "Komentar": int(st.get('commentCount', 0)),
                    "URL": f"https://www.youtube.com/watch?v={video.get('id', '')}",
                    "Thumbnail_URL": get_thumbnail_terbaik(s.get('thumbnails', {}))
                })

    return {"Tipe_Data": "Channel_Detail", "Jumlah_Video_Diminta": jumlah_video, "Channel": channel_info, "Video_Terakhir": video_list}

# --- FUNGSI ACTION ---
def simpan_file():
    if not current_data:
        messagebox.showwarning("Kosong", "Belum ada data buat disimpan.")
        return
    file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON file", "*.json"), ("CSV file", "*.csv")], title="Simpan Data Metadata")
    if not file_path:
        return
    try:
        if file_path.endswith('.json'):
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(current_data, f, indent=4, ensure_ascii=False)
        else:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                if current_data_type == "channel":
                    data = current_data[0]
                    writer.writerow(["SECTION", "KEY", "VALUE"])
                    for k, v in data["Channel"].items():
                        writer.writerow(["CHANNEL", k, v])
                    writer.writerow([])
                    writer.writerow(["NO", "JUDUL", "VIDEO_ID", "WAKTU_UPLOAD", "VIEWS", "LIKES", "KOMENTAR", "URL", "THUMBNAIL_URL"])
                    for i, v in enumerate(data["Video_Terakhir"], start=1):
                        writer.writerow([i, v["Judul"], v["Video_ID"], v["Waktu_Upload"], v["Views"], v["Likes"], v["Komentar"], v["URL"], v["Thumbnail_URL"]])
                else:
                    writer.writerow(current_data[0].keys())
                    for baris in current_data:
                        writer.writerow(baris.values())
        messagebox.showinfo("Sukses", f"Berhasil menyimpan data ke:\n{file_path}")
    except Exception as e:
        messagebox.showerror("Error", f"Gagal simpan file:\n{e}")

def download_thumb():
    if len(current_data) != 1 or current_data_type != "video" or not current_data[0].get('Thumbnail_URL'):
        return
    file_path = filedialog.asksaveasfilename(defaultextension=".jpg", filetypes=[("Image file", "*.jpg")], title="Simpan Thumbnail")
    if not file_path:
        return
    try:
        urllib.request.urlretrieve(current_data[0]['Thumbnail_URL'], file_path)
        messagebox.showinfo("Sukses", f"Thumbnail berhasil didownload!\nLokasi: {file_path}")
    except Exception as e:
        messagebox.showerror("Error", f"Gagal download gambar:\n{e}")

def pakai_api_key_manual():
    api_key_input = entry_api_key.get().strip()
    if not api_key_input:
        tampilkan_pesan("API Key kosong. Isi dulu sebelum dipakai.", is_error=True)
        return

    ok, err = init_youtube_client(api_key_input)
    if ok:
        tampilkan_pesan("✅ API Key aktif. Siap dipakai scraping.")
    else:
        tampilkan_pesan(f"Gagal inisialisasi API Key: {err}", is_error=True)


def tampilkan_pesan(pesan, is_error=False):
    text_hasil.configure(state="normal")
    text_hasil.delete("0.0", "end")
    text_hasil.insert("end", f"{'⚠️ ERROR: ' if is_error else ''}{pesan}")
    text_hasil.configure(state="disabled")

def ubah_tampilan(pilihan_mode):
    if pilihan_mode == "Mode Single (1 Video)":
        frame_batch.pack_forget()
        frame_single.pack(fill="x")
    else:
        frame_single.pack_forget()
        frame_batch.pack(fill="x")

def ambil_data_single(event=None):
    link = entry_link.get().strip()
    if not link:
        tampilkan_pesan("Masukkan link YouTube dulu, bro!", is_error=True)
        return
    vid_id = ekstrak_id_video(link)
    if not vid_id:
        tampilkan_pesan("Format link video tidak valid!", is_error=True)
        return
    eksekusi_tarik_data([vid_id], is_batch=False)

def ambil_data_batch():
    teks_input = text_links.get("1.0", "end-1c").strip()
    if not teks_input:
        tampilkan_pesan("Kotak input masih kosong! Paste link lu dulu.", is_error=True)
        return
    valid_ids = []
    for baris in teks_input.split('\n'):
        vid = ekstrak_id_video(baris.strip())
        if vid and vid not in valid_ids:
            valid_ids.append(vid)
    if not valid_ids:
        tampilkan_pesan("Tidak ada satupun format link video yang valid di daftar lu!", is_error=True)
        return
    eksekusi_tarik_data(valid_ids, is_batch=True)

def eksekusi_tarik_data(daftar_id, is_batch):
    global current_data, current_data_type
    current_data.clear()
    current_data_type = "video"
    btn_export.configure(state="disabled")
    btn_dl_thumb.configure(state="disabled")
    try:
        if is_batch:
            total_video = len(daftar_id)
            for index, target_vid in enumerate(daftar_id):
                tampilkan_pesan(f"⏳ CUSTOM BATCH SCRAPING\n\nMenarik data video ke-{index + 1} dari total {total_video} link...\n[Jangan tutup aplikasi]\n\nMemproses ID: {target_vid}")
                app.update()
                data_mentah = get_video_metadata(target_vid)
                if "error" not in data_mentah:
                    current_data.append(data_mentah)
            tampilkan_pesan(format_tampilan_batch(current_data, total_video))
            btn_export.configure(state="normal" if current_data else "disabled")
        else:
            tampilkan_pesan("⏳ Mengambil data lengkap...")
            app.update()
            data = get_video_metadata(daftar_id[0])
            if "error" in data:
                tampilkan_pesan(data["error"], is_error=True)
            else:
                current_data.append(data)
                tampilkan_pesan(format_tampilan_video(data))
                btn_export.configure(state="normal")
                btn_dl_thumb.configure(state="normal")
    except Exception as e:
        tampilkan_pesan(f"Gagal: {e}", is_error=True)

def format_tampilan_video(data):
    tampilan = f"{'='*50}\n[ INFORMASI CHANNEL ]\n{'='*50}\n"
    tampilan += f"NAMA CHANNEL       : {data['Channel']}\nCHANNEL ID         : {data['Channel_ID']}\nDIBUAT PADA        : {data['Channel_Dibuat']}\nNEGARA             : {data['Negara']}\nSUBSCRIBERS        : {data['Subscribers']}\nTOTAL VIDEO        : {data['Total_Video']}\n\n"
    tampilan += f"{'='*50}\n[ INFORMASI VIDEO ]\n{'='*50}\n"
    tampilan += f"JUDUL VIDEO        : {data['Judul']}\nWAKTU UPLOAD       : {data['Waktu_Upload']}\nVIEWS              : {format_angka(data['Views'])} kali\nLIKES              : {format_angka(data['Likes'])} likes\nKOMENTAR           : {format_angka(data['Komentar'])} komentar\nTHUMBNAIL LINK     : {data['Thumbnail_URL']}\n\n"
    tampilan += f"{'='*50}\n[ TAGS ]\n{'='*50}\n{data['Tags']}\n\n"
    tampilan += f"{'='*50}\n[ DESKRIPSI VIDEO ]\n{'='*50}\n{data['Deskripsi']}\n"
    return tampilan

def format_tampilan_batch(daftar_data, total_input):
    tampilan = f"{'='*60}\n✅ BATCH SCRAPING SELESAI!\n{'='*60}\n"
    tampilan += f"TOTAL LINK INPUT    : {total_input}\n"
    tampilan += f"DATA BERHASIL       : {len(daftar_data)} video\n"
    tampilan += f"{'='*60}\n[ HASIL DATA VIDEO ]\n{'='*60}\n"
    if not daftar_data:
        tampilan += "Tidak ada data video berhasil diambil.\n"
        return tampilan

    for i, data in enumerate(daftar_data, start=1):
        tampilan += f"\n{i}. {data['Judul']}\n"
        tampilan += f"   CHANNEL      : {data['Channel']}\n"
        tampilan += f"   CHANNEL ID   : {data['Channel_ID']}\n"
        tampilan += f"   VIDEO ID     : {data['Video_ID']}\n"
        tampilan += f"   UPLOAD       : {data['Waktu_Upload']}\n"
        tampilan += f"   VIEWS        : {format_angka(data['Views'])} kali\n"
        tampilan += f"   LIKES        : {format_angka(data['Likes'])} likes\n"
        tampilan += f"   KOMENTAR     : {format_angka(data['Komentar'])} komentar\n"
        tampilan += f"   THUMBNAIL    : {data['Thumbnail_URL']}\n"
    tampilan += "\nKlik tombol '💾 EXPORT DATA' kalau mau simpan JSON/CSV.\n"
    return tampilan


def ambil_data_channel(event=None):
    global current_data, current_data_type
    link_channel = entry_channel.get().strip()
    if not link_channel:
        tampilkan_pesan("Masukkan link/nama channel dulu.", is_error=True)
        return
    try:
        jumlah_video = int(entry_jumlah_video.get().strip())
    except Exception:
        tampilkan_pesan("Jumlah video harus angka.", is_error=True)
        return
    if jumlah_video < 0 or jumlah_video > 50:
        tampilkan_pesan("Jumlah video minimal 0, maksimal 50.", is_error=True)
        return
    current_data.clear()
    current_data_type = "channel"
    btn_export.configure(state="disabled")
    btn_dl_thumb.configure(state="disabled")
    try:
        tampilkan_pesan("⏳ Mencari channel...")
        app.update()
        channel_id, err = resolve_channel_id(link_channel)
        if err:
            tampilkan_pesan(err, is_error=True)
            return
        tampilkan_pesan(f"⏳ Mengambil detail channel dan {jumlah_video} video terakhir...\nChannel ID: {channel_id}")
        app.update()
        data = get_channel_detail(channel_id, jumlah_video)
        if "error" in data:
            tampilkan_pesan(data["error"], is_error=True)
            return
        current_data.append(data)
        tampilkan_pesan(format_tampilan_channel(data))
        btn_export.configure(state="normal")
    except Exception as e:
        tampilkan_pesan(f"Gagal ambil detail channel: {e}", is_error=True)

def format_tampilan_channel(data):
    c = data["Channel"]
    tampilan = f"{'='*60}\n[ DETAIL CHANNEL ]\n{'='*60}\n"
    tampilan += f"NAMA CHANNEL        : {c['Channel']}\nCHANNEL ID          : {c['Channel_ID']}\nCUSTOM URL          : {c['Custom_URL']}\nDIBUAT PADA         : {c['Dibuat_Pada']}\nNEGARA              : {c['Negara']}\nSUBSCRIBERS         : {c['Subscribers']}\nTOTAL VIEW CHANNEL  : {c['Total_View_Channel']}\nTOTAL VIDEO         : {c['Total_Video']}\nTHUMBNAIL CHANNEL   : {c['Thumbnail_URL']}\n\n"
    tampilan += f"{'='*60}\n[ DESKRIPSI CHANNEL ]\n{'='*60}\n{c['Deskripsi']}\n\n"
    tampilan += f"{'='*60}\n[ {len(data['Video_Terakhir'])} VIDEO TERAKHIR ]\n{'='*60}\n"
    if not data["Video_Terakhir"]:
        tampilan += "Tidak ada video diambil.\n"
    else:
        for i, v in enumerate(data["Video_Terakhir"], start=1):
            tampilan += f"\n{i}. {v['Judul']}\n   VIDEO ID     : {v['Video_ID']}\n   UPLOAD       : {v['Waktu_Upload']}\n   VIEWS        : {format_angka(v['Views'])}\n   LIKES        : {format_angka(v['Likes'])}\n   KOMENTAR     : {format_angka(v['Komentar'])}\n   URL          : {v['URL']}\n"
    return tampilan

# --- GUI SETUP ---
ctk.set_appearance_mode("Dark")
app = ctk.CTk()
app.title("YME v5")
app.geometry("1000x850")
try:
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    app_icon_path = os.path.join(base_path, "yme_icon.png")
    app_icon = PhotoImage(file=app_icon_path)
    app.iconphoto(True, app_icon)
except Exception:
    pass

main_frame = ctk.CTkFrame(app, corner_radius=15)
main_frame.pack(pady=20, padx=20, fill="both", expand=True)
ctk.CTkLabel(main_frame, text="YOUTUBE METADATA EXTRACTOR", font=("Helvetica", 22, "bold")).pack(pady=15)

api_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
api_frame.pack(fill="x", padx=25, pady=(0, 10))
ctk.CTkLabel(api_frame, text="YouTube API Key:", font=("Arial", 12, "bold")).pack(anchor="w", pady=(0, 5))
api_input_row = ctk.CTkFrame(api_frame, fg_color="transparent")
api_input_row.pack(fill="x")
entry_api_key = ctk.CTkEntry(api_input_row, placeholder_text="Paste API key di sini...", height=38, show="*")
entry_api_key.pack(side="left", fill="x", expand=True, padx=(0, 8))
entry_api_key.insert(0, API_KEY)
ctk.CTkButton(api_input_row, text="PAKAI API KEY", width=140, height=38, command=pakai_api_key_manual, font=("Arial", 12, "bold"), fg_color="#1f6aa5").pack(side="right")

tab_view = ctk.CTkTabview(main_frame)
tab_view.pack(fill="both", expand=True, padx=20, pady=(0, 15))
tab_video = tab_view.add("Video Metadata")
tab_channel = tab_view.add("Channel Detail")

mode_var = ctk.StringVar(value="Mode Single (1 Video)")
mode_selector = ctk.CTkSegmentedButton(tab_video, values=["Mode Single (1 Video)", "Mode Batch (Multi-Link)"], variable=mode_var, command=ubah_tampilan, font=("Arial", 13, "bold"), height=35)
mode_selector.pack(pady=(10, 15))

container_input = ctk.CTkFrame(tab_video, fg_color="transparent")
container_input.pack(fill="x", padx=15)

frame_single = ctk.CTkFrame(container_input, fg_color="transparent")
entry_link = ctk.CTkEntry(frame_single, placeholder_text="Paste Link Video YouTube di sini...", height=45)
entry_link.pack(fill="x", pady=(0, 10))
entry_link.bind('<Return>', ambil_data_single)
ctk.CTkButton(frame_single, text="CARI", height=40, command=ambil_data_single, font=("Arial", 13, "bold")).pack(fill="x")

frame_batch = ctk.CTkFrame(container_input, fg_color="transparent")
ctk.CTkLabel(frame_batch, text="Paste daftar link video di bawah ini (1 link per baris):", font=("Arial", 12)).pack(anchor="w", pady=(0, 5))
text_links = ctk.CTkTextbox(frame_batch, height=120, font=("Consolas", 12))
text_links.pack(fill="x", pady=(0, 10))
ctk.CTkButton(frame_batch, text="MULAI BATCH SCRAPING", height=40, command=ambil_data_batch, font=("Arial", 13, "bold"), fg_color="#c0392b").pack(fill="x")
frame_single.pack(fill="x")

channel_frame = ctk.CTkFrame(tab_channel, fg_color="transparent")
channel_frame.pack(fill="x", padx=15, pady=15)
ctk.CTkLabel(channel_frame, text="Link channel / @handle / nama channel:", font=("Arial", 12)).pack(anchor="w", pady=(0, 5))
entry_channel = ctk.CTkEntry(channel_frame, placeholder_text="Contoh: https://www.youtube.com/@MrBeast atau https://www.youtube.com/channel/UC...", height=45)
entry_channel.pack(fill="x", pady=(0, 10))
entry_channel.bind('<Return>', ambil_data_channel)

count_frame = ctk.CTkFrame(channel_frame, fg_color="transparent")
count_frame.pack(fill="x", pady=(0, 10))
ctk.CTkLabel(count_frame, text="Jumlah video terakhir (0-50):", font=("Arial", 12)).pack(side="left", padx=(0, 10))
entry_jumlah_video = ctk.CTkEntry(count_frame, width=90, height=35)
entry_jumlah_video.insert(0, "10")
entry_jumlah_video.pack(side="left")
ctk.CTkButton(channel_frame, text="AMBIL DETAIL CHANNEL", height=42, command=ambil_data_channel, font=("Arial", 13, "bold"), fg_color="#8e44ad").pack(fill="x")

act_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
act_frame.pack(fill="x", padx=25, pady=(0, 15))
btn_export = ctk.CTkButton(act_frame, text="💾 EXPORT DATA (JSON/CSV)", state="disabled", command=simpan_file, fg_color="#2c3e50")
btn_export.pack(side="left", padx=(0, 10))
btn_dl_thumb = ctk.CTkButton(act_frame, text="🖼️ DOWNLOAD THUMBNAIL HD", state="disabled", command=download_thumb, fg_color="#27ae60")
btn_dl_thumb.pack(side="left")

text_hasil = ctk.CTkTextbox(main_frame, font=("Consolas", 13), corner_radius=10)
text_hasil.pack(fill="both", expand=True, padx=25, pady=(0, 15))
text_hasil.configure(state="disabled")

if __name__ == "__main__":
    app.mainloop()
