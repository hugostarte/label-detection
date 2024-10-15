sudo apt-get install python3-tk python3-pil python3-pil.imagetk


[ WARN:0@1.148] global ./modules/videoio/src/cap_gstreamer.cpp (1405) open OpenCV | GStreamer warning: Cannot query video position: status=0, value=-1, duration=-1
Traceback (most recent call last):
  File "/home/hugo/Desktop/label_reco/interface-label-relais.py", line 247, in <module>
    root = tk.Tk()
           ^^^^^^^
  File "/usr/lib/python3.11/tkinter/__init__.py", line 2326, in __init__
    self.tk = _tkinter.create(screenName, baseName, className, interactive, wantobjects, useTk, sync, use)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_tkinter.TclError: no display name and no $DISPLAY environment variable
