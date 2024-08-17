from urllib.parse import urlparse
from .metadata import Source
from .progress import Progress
from natsort import natsorted
import asyncio
import aiohttp
import time
import sys
import os
import re

class SegmentDownloader:
  DR_ATTEMPTS = 5
  MAX_ELEMENTS = 50

  def __init__(self, logger, video_source: Source, filename, subtitles: Source = None, outside_ide=False) -> None:
    self.st = time.time()
    self.logger = logger
    self.video_source = video_source
    self.subtitles = subtitles
    self.filename = filename
    self.downloaded = 0
    self.endpoint = self._extract_endpoint(video_source.url)
    self.progress = Progress(filename, outside_ide)

  def __exit__(self) -> None:
    asyncio.run(self._close_session())

  @staticmethod
  def _extract_endpoint(url):
    parsed_url = urlparse(url)
    return f"{parsed_url.scheme}://{parsed_url.netloc}/{'/'.join(parsed_url.path.split('/')[:-1])}/"

  def _init_session(self):
    self.loop = asyncio.get_event_loop()
    connector = aiohttp.TCPConnector(limit=self.MAX_ELEMENTS)
    timeout = aiohttp.ClientTimeout(total=self.timeout, sock_read=10)
    self.session = aiohttp.ClientSession(connector=connector, trust_env=True, timeout=timeout)

  async def _close_session(self):
    await self.session.close()
  
  async def _extract_segments(self):
    async with self.session.get(self.video_source.url) as resp:
      info = await resp.read()
    self.segments = [link.replace('/', '') for link in info.decode('utf-8').split('\n') if link.endswith('.ts')]
    self._segments_length = len(self.segments)
    self.progress.start(self._segments_length)

  async def _download_segment(self, segment):
    fp = f'cache/files/{self.filename}'
    if not os.path.exists(fp): os.makedirs(fp)
    seg_num = re.findall(r'-\d+-', segment)[0].replace('-', '')
    filename = f'{fp}/{self.filename}_{seg_num}.ts'
    segment = segment[1:]
    return await self._retrieve_segment(segment, filename, seg_num)

  async def _retrieve_segment(self, segment, filename, seg_num):
    attempt = 0
    while attempt <= self.DR_ATTEMPTS:
      try:
        async with self.session.get(f'{self.endpoint}{segment}') as resp:
          content = await resp.read()
        with open(filename, 'wb') as file:
          file.write(content)
        self.progress.increase()
        # if int(seg_num) % 50 == 0:
        #   time.sleep(1)
        return filename
      except (aiohttp.ClientPayloadError, aiohttp.ServerTimeoutError):
        attempt += 1
        if attempt > 1:
          self.logger.error(f'Some troubles downloading seg{seg_num}. Retrying x{attempt}')  
    else:
      raise IndexError(seg_num)
    
  async def _download_segments(self):
    try:
      self.logger.info(f'Starting download for {self.filename}:')
      tasks = [asyncio.create_task(self._download_segment(segment)) for segment in self.segments]
      self.dd_started = time.time()
      self.segments_list = await asyncio.gather(*tasks)
      self.segments_time = round(time.time() - self.st, 1)
      self.logger.info(f'Downloaded all segments in {round(time.time() - self.st, 1)}s')
      return True
    except asyncio.TimeoutError:
      print()
      self.logger.error(f'Not enough time ({self.timeout}) to download all fragments')
      sys.exit(-1)

  async def _download_subtitles(self, sub_source):
    path = None
    if sub_source:
      async with self.session.get(sub_source) as resp:
        content = await resp.read()
      path = f'cache/files/{self.filename}.vtt'
      with open(path, 'wb') as file:
        file.write(content)
    return path

  def _create_manifest(self):
    # fp = f'cache/files/{self.filename}_manifest.txt'
    # with open(fp, 'w') as file:
    #   file.writelines(
    #     [f"file '{os.path.join(self.filename, os.path.split(el)[-1])}'\n"
    #      for el in natsorted(os.listdir(f'cache/files/{self.filename}')) if el.endswith('.ts')]
    #   )
    fp = f'concat:{"|".join(natsorted(self.segments_list))}'
    return fp

  def _check_integrity(self):
    segments = [file for file in os.listdir(f'cache/files/{self.filename}') if file.endswith('.ts')]
    if len(segments) == self._segments_length:
      return True
    else:
      self.logger.error(f'Downloaded segments length mismatch manifest.')
      sys.exit(-1)

  async def main(self, timeout):
    self.timeout = timeout
    self._init_session()
    await self._extract_segments()
    await self._download_segments()
    subtitles = await self._download_subtitles(self.subtitles.url)
    await self._close_session()
    self._check_integrity()
    return self._create_manifest(), subtitles, self.segments_time

  def run(self, timeout): return asyncio.run(self.main(timeout))
