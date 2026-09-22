#!/usr/bin/env python3
"""Render and probe synthetic video with subtitles. Never records the desktop."""
import json
from pathlib import Path
import subprocess
import tempfile


def main():
    with tempfile.TemporaryDirectory(prefix='factory-video-') as folder:
        root=Path(folder)
        (root/'labels.ass').write_text('''[Script Info]
ScriptType: v4.00+
PlayResX: 320
PlayResY: 180
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Helvetica,20,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,1,0,2,10,10,10,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,0:00:01.00,Default,,0,0,0,,Synthetic factory test
''')
        try:
            subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-f','lavfi','-i','color=c=blue:s=320x180:r=10','-t','1','-vf','ass=labels.ass','-c:v','libx264','-pix_fmt','yuv420p','out.mp4'],cwd=root,check=True,capture_output=True,timeout=30)
            p=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration:stream=codec_name,width,height','-of','json','out.mp4'],cwd=root,check=True,capture_output=True,text=True,timeout=15)
            info=json.loads(p.stdout)
            ok=float(info['format']['duration'])>0 and any(s.get('codec_name')=='h264' and s.get('width')==320 and s.get('height')==180 for s in info['streams'])
        except (OSError,subprocess.SubprocessError,ValueError,KeyError):
            ok=False
        print(json.dumps({'synthetic_video_passed':ok,'desktop_recorded':False,'remedy':None if ok else 'Check ffmpeg-full PATH, libx264, ass filter, and ffprobe with factory_doctor.py.'}))
        return 0 if ok else 2


if __name__=='__main__':
    raise SystemExit(main())
