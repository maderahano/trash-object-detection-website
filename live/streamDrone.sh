# ffmpeg -i rtmp://localhost/src/$name -vcodec libx264 -vprofile baseline -g 10 -s 300x200 -acodec aac -ar 44100 -ac 1 -f flv rtmp://localhost/hls/$name 2>>/var/log/ffmpeg-$name.log;
# ffmpeg -re -i rtmp://10.252.131.91/src/str -c:v copy -c:a aac -ar 44100 -ac 1 -f flv rtmp://10.252.131.91/live/str
ffmpeg -i rtmp://192.168.119.87:1935/src/str -async 1 -vsync -1
						-c:v libx264 -c:a aac -b:v 256k  -b:a 64k  -vf "scale=480:trunc(ow/a/2)*2"  -tune zerolatency -preset superfast -crf 23 -f flv rtmp://192.168.119.87:1935/live/str_low
						-c:v libx264 -c:a aac -b:v 768k  -b:a 128k -vf "scale=720:trunc(ow/a/2)*2"  -tune zerolatency -preset superfast -crf 23 -f flv rtmp://192.168.119.87:1935/live/str_mid
						-c:v libx264 -c:a aac -b:v 1024k -b:a 128k -vf "scale=960:trunc(ow/a/2)*2"  -tune zerolatency -preset superfast -crf 23 -f flv rtmp://192.168.119.87:1935/live/str_high
						-c:v libx264 -c:a aac -b:v 1920k -b:a 128k -vf "scale=1280:trunc(ow/a/2)*2" -tune zerolatency -preset superfast -crf 23 -f flv rtmp://192.168.119.87:1935/live/str_hd720
						-c copy -f flv rtmp://192.168.119.87:1935/live/src;