from downloader import CacheTree, Converter, Logger, SegmentDownloader, PLMetadata, ExMetadata
from datetime import timedelta
import sys

def main():
  outside_IDE = True if len(sys.argv) > 1 else False
  meta = PLMetadata('latest.yaml') if not outside_IDE else ExMetadata(*sys.argv[1:])
  cache = CacheTree('cache/files')
  logger = Logger('red', 'cyan', outside_IDE)
  conv = Converter(logger, meta)
  segmenter = SegmentDownloader(logger, meta.video, meta.filename, meta.subtitles, outside_IDE)
  cache.folders = meta.filename
  manifest, subtitles, seg_time = segmenter.run(conv.timeout)
  meta.subtitles.url = subtitles
  cache.files = subtitles
  meta.manifest = manifest
  state, conv_time = conv.start()
  if state:
    cache.clear()
    total_time = '{:02}'.format(str(timedelta(seconds=int(conv_time + seg_time))))
    logger.info(f'Total time consumed: {total_time}')


if __name__ == '__main__':
  main()
