import yaml

class Source:
  langs = {'eng': 'English', 'rus': 'Русский'}
  url: str = None
  lang: str = None
  
  def __init__(self, url: str, lang: str='eng') -> None:
    self.url = url
    self.lang = lang
  
  @property
  def lang_title(self):
    return self.langs[self.lang]
  
  def __repr__(self):
    source = 'Undefined'
    if self.url.endswith('.m3u8'): source = 'Video'
    if self.url.endswith('.vtt'): source = 'Subtitles'
    return f'{source} source'

  def __str__(self):
    return self.url

class PLMetadata:
  filename: str = None
  subtitles: Source = None
  video: Source = None
  metatitle: str = None
  manifest: str = None

  def __init__(self, fp) -> None:
    self._init_meta(fp)

  def _init_meta(self, fp) -> None:
    try:
      with open(fp, 'r', encoding='utf-8') as f:
        data: dict = yaml.safe_load(f)
      self.filename = data['filename']
      self.subtitles = Source(data['sub_source'], data.get('sub_lang'))
      self.video = Source(data['video_source'], data.get('video_lang'))
      self.metatitle = data['metatitle']
    except FileNotFoundError:
      import sys
      print('MetaData file not found!')
      sys.exit(-1)


class ExMetadata:
  filename: str = None
  subtitles: Source = None
  video: Source = None
  metatitle: str = None

  def __init__(self, filename, video, metatitle, subtitles=None, *args, **kwargs) -> None:
    self.filename = filename
    self.video = Source(video)
    self.metatitle = metatitle
    self.subtitles = Source(subtitles)
