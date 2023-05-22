# ffmpeg -re -i DJI_0784.MP4 -vcodec copy -loop -1 -c:a aac -b:a 160k -ar 44100 -strict -2 -f flv rtmp:0.0.0.0/live/bbb
# ffmpeg -re -i "Video EWaras.mp4" -c:v copy -c:a aac -ar 44100 -ac 1 -f flv rtmp://192.168.18.64/live/str
# ffmpeg -re -stream_loop -1 -i "SADAR DIRI KAMU!.mp4" -f flv rtmp://127.0.0.1/live/str
ffmpeg -re -stream_loop -1 -i "SADAR DIRI KAMU!.mp4" -f flv rtmp://0.tcp.ap.ngrok.io:16328/live/stream
