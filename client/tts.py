#!/usr/bin/env python3
# -*- coding: utf-8-*-
"""
A Speaker handles audio output from Jasper to the user

Speaker methods:
    say - output 'phrase' as speech
    play - play the audio in 'filename'
    is_available - returns True if the platform supports this implementation
"""
import os
import platform
import re
import tempfile
import subprocess
import pipes
import logging
import wave
import urllib
import urlparse
import requests
from abc import ABCMeta, abstractmethod

import argparse
import yaml
import codecs
import sys


#logging.basicConfig(level=logging.DEBUG)

try:
    import mad
except ImportError:
    pass

try:
    import gtts
except ImportError:
    pass

try:
    import pyvona
except ImportError:
    pass

import diagnose
import jasperpath


class AbstractTTSEngine(object):
    """
    Generic parent class for all speakers
    """
    __metaclass__ = ABCMeta

    @classmethod
    def get_config(cls):
        return {}

    @classmethod
    def get_instance(cls):
        config = cls.get_config()
        instance = cls(**config)
        return instance

    @classmethod
    @abstractmethod
    def is_available(cls):
        return diagnose.check_executable('aplay')

    def __init__(self, **kwargs):
        self._logger = logging.getLogger(__name__)

    @abstractmethod
    def say(self, phrase, *args):
        pass

    def play(self, filename):
        # FIXME: Use platform-independent audio-output here
        # See issue jasperproject/jasper-client#188
        cmd = ['aplay', '-D', 'plughw:1,0', str(filename)]
        self._logger.debug('Executing %s', ' '.join([pipes.quote(arg)
                                                     for arg in cmd]))
        with tempfile.TemporaryFile() as f:
            subprocess.call(cmd, stdout=f, stderr=f)
            f.seek(0)
            output = f.read()
            if output:
                self._logger.debug("Output was: '%s'", output)


class AbstractMp3TTSEngine(AbstractTTSEngine):
    """
    Generic class that implements the 'play' method for mp3 files
    """
    @classmethod
    def is_available(cls):
        return (super(AbstractMp3TTSEngine, cls).is_available() and
                diagnose.check_python_import('mad'))

    def play_mp3(self, filename):
        mf = mad.MadFile(filename)
        with tempfile.NamedTemporaryFile(suffix='.wav') as f:
            wav = wave.open(f, mode='wb')
            wav.setframerate(mf.samplerate())
            wav.setnchannels(1 if mf.mode() == mad.MODE_SINGLE_CHANNEL else 2)
            # 4L is the sample width of 32 bit audio
            wav.setsampwidth(4L)
            frame = mf.read()
            while frame is not None:
                wav.writeframes(frame)
                frame = mf.read()
            wav.close()
            self.play(f.name)


class FestivalTTS(AbstractTTSEngine):
    """
    Uses the festival speech synthesizer
    Requires festival (text2wave) to be available
    """

    SLUG = 'festival-tts'

    @classmethod
    def is_available(cls):
        if (super(cls, cls).is_available() and
           diagnose.check_executable('text2wave') and
           diagnose.check_executable('festival')):

            logger = logging.getLogger(__name__)
            cmd = ['festival', '--pipe']
            with tempfile.SpooledTemporaryFile() as out_f:
                with tempfile.SpooledTemporaryFile() as in_f:
                    logger.debug('Executing %s', ' '.join([pipes.quote(arg)
                                                           for arg in cmd]))
                    subprocess.call(cmd, stdin=in_f, stdout=out_f,
                                    stderr=out_f)
                    out_f.seek(0)
                    output = out_f.read().strip()
                    if output:
                        logger.debug("Output was: '%s'", output)
                    return ('No default voice found' not in output)
        return False
        
    def say2(self, phrase):
        self._logger.debug("Saying '%s' with '%s'", phrase, self.SLUG)
        cmd = ['text2wave']
        with tempfile.NamedTemporaryFile(suffix='.wav') as out_f:
            with tempfile.SpooledTemporaryFile() as in_f:
                in_f.write(phrase)
                in_f.seek(0)
                with tempfile.SpooledTemporaryFile() as err_f:
                    self._logger.debug('Executing %s',
                                       ' '.join([pipes.quote(arg)
                                                 for arg in cmd]))
                    subprocess.call(cmd, stdin=in_f, stdout=out_f,
                                    stderr=err_f)
                    err_f.seek(0)
                    output = err_f.read()
                    if output:
                        self._logger.debug("Output was: '%s'", output)
            self.play(out_f.name)
                          

    def say(self, phrase):
           
        orden = """ echo " {0} " | 
                    iconv -f utf-8 -t iso-8859-1 |  
                    text2wave  | 
                    aplay -D plughw:1,0 """.format(phrase)

        
        os.system(orden)
        
        
        
        
        
       
         





def get_default_engine_slug():
    return 'osx-tts' if platform.system().lower() == 'darwin' else 'espeak-tts'


def get_engine_by_slug(slug=None):
    """
    Returns:
        A speaker implementation available on the current platform

    Raises:
        ValueError if no speaker implementation is supported on this platform
    """

    if not slug or type(slug) is not str:
        raise TypeError("Invalid slug '%s'", slug)

    selected_engines = filter(lambda engine: hasattr(engine, "SLUG") and
                              engine.SLUG == slug, get_engines())
    if len(selected_engines) == 0:
        raise ValueError("No TTS engine found for slug '%s'" % slug)
    else:
        if len(selected_engines) > 1:
            print("WARNING: Multiple TTS engines found for slug '%s'. " +
                  "This is most certainly a bug." % slug)
        engine = selected_engines[0]
        if not engine.is_available():
            raise ValueError(("TTS engine '%s' is not available (due to " +
                              "missing dependencies, etc.)") % slug)
        return engine


def get_engines():
    def get_subclasses(cls):
        subclasses = set()
        for subclass in cls.__subclasses__():
            subclasses.add(subclass)
            subclasses.update(get_subclasses(subclass))
        return subclasses
    return [tts_engine for tts_engine in
            list(get_subclasses(AbstractTTSEngine))
            if hasattr(tts_engine, 'SLUG') and tts_engine.SLUG]

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Jasper TTS module')
    parser.add_argument('--debug', action='store_true',
                        help='Show debug messages')
    args = parser.parse_args()

    logging.basicConfig()
    if args.debug:
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)

    engines = get_engines()
    available_engines = []
    for engine in get_engines():
        if engine.is_available():
            available_engines.append(engine)
    disabled_engines = list(set(engines).difference(set(available_engines)))
    print("Available TTS engines:")
    for i, engine in enumerate(available_engines, start=1):
        print("%d. %s" % (i, engine.SLUG))

    print("")
    print("Disabled TTS engines:")

    for i, engine in enumerate(disabled_engines, start=1):
        print("%d. %s" % (i, engine.SLUG))

    print("")
    for i, engine in enumerate(available_engines, start=1):
        print("%d. Testing engine '%s'..." % (i, engine.SLUG))
        engine.get_instance().say("España")
    print("Done.")
