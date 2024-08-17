from .metadata import PLMetadata
import ffmpeg
import time
import sys
import os


class Converter:
  ACCPTD_CODECS = ['aac', 'h264']
  VENCODER = 'libx264'
  SEG_DURATION = 5.0
  TIMEOUT_MP = 2

  def __init__(self, logger, meta: PLMetadata) -> None:
    self.st = time.time()
    self.convertion_time = 0
    self.meta = meta
    self.logger = logger
    self.vcodec, self.acodec = self._codecs(meta.video.url)
    self.duration, self.timeout = self._file_info(meta.video.url)
    self.media_type = self._detect_type(meta.video.url)

  @staticmethod
  def _codecs(url) -> tuple[str, str]:
    probe = ffmpeg.probe(url)
    return probe['streams'][0]['codec_name'], probe['streams'][1]['codec_name']
  
  @staticmethod
  def _detect_type(url: str):
    return 'tv' if 'tvseries' in url.split('/') else 'movie'

  def _file_info(self, source) -> tuple[float, float]:
    try:
      probe = ffmpeg.probe(source)
      duration = round(float(probe['format']['duration']), 2)
      timeout = round(duration / self.SEG_DURATION) * self.TIMEOUT_MP
      return duration, timeout
    except ffmpeg._run.Error:
      self.logger.error('Video source isnt valid. Please, provide a valid one.')
      sys.exit(-1)

  def _collect_params(self):
    params = {
      'c:v': 'copy' if self.vcodec in self.ACCPTD_CODECS else self.VENCODER,
      'c:a': 'aac', 'format': 'mp4', 'metadata:s:a:0': f'language={self.meta.video.lang}', 'strict': -2,
      'metadata': f'title={self.meta.metatitle}'
    }
    args = ['-loglevel', 'error', '-metadata:s:a:0', f'title={self.meta.video.lang_title}']
    if self.meta.subtitles:
      params.update({'metadata:s:s:0': f'language={self.meta.subtitles.lang}', 'c:s': 'mov_text'})
      args.insert(2, '-i')
      args.insert(3, self.meta.subtitles.url)
      args.extend(('-metadata:s:s:0', f'title={self.meta.subtitles.lang_title}'))
    return args, params
  
  def _concat(self,):
    if self.meta.manifest: source = self.meta.manifest; fmt = {} # {'f': 'concat', 'safe': 0}
    args, params = self._collect_params()
    try:
      self.logger.info(f'Conversion for {self.meta.filename} started.')
      process = (
        ffmpeg
        .input(source, **fmt)
        .output(f'downloads/{self.media_type}/{self.meta.filename}.mp4', **params)
        .global_args(*args)
        .overwrite_output()
        .run_async(pipe_stdout=True)
      )
      process.wait()
      return True
    except Exception as ex:
      self.logger.error(f'Conversion for {self.meta.filename} failed. Traceback: {str(ex)}.')

  def _check_download(self):
    if not os.path.exists(f'downloads/{self.media_type}/{self.meta.filename}.mp4'):
      self.logger.error(f'File {self.meta.filename}.mp4 not found in downloads folder. Download failed!')
      sys.exit(-1)
    return True

  def _finish_conversion(self):
    self._check_download()
    consumed = round(time.time() - self.st)
    self.conversion_time = consumed
    self.logger.info(f'Conversion for {self.meta.filename} successfully ended. Consumed: {consumed}s')

  def start(self):
    try:
      state = self._concat()
      if state: self._finish_conversion()
    except Exception as _ex:
      self.logger.error(f'An error occured while converting. Traceback: {str(_ex)}')
      state = False
    return state, self.conversion_time
  
