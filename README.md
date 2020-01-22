# hls-download
Very simple python script that allows to download hls stream locally in order to stream it from my computer. It goes over all streams (video/audio/i-frames) declared in the manifest and download all segments. Stream can be started using python stream server that allows range requests:

```python3
pip install rangehttpserver
python -m RangeHTTPServer 8000
```
