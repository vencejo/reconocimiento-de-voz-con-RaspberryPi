#!/usr/bin/env python3
# -*- coding: utf-8-*-
import os
import wave
import json
import tempfile
import logging
import urllib
import urlparse
import re
import subprocess
from abc import ABCMeta, abstractmethod
import requests
import yaml
import jasperpath
import diagnose
import vocabcompiler
import speech_recognition as sr



class AbstractSTTEngine(object):
    """
    Generic parent class for all STT engines
    """

    __metaclass__ = ABCMeta
    VOCABULARY_TYPE = None

    @classmethod
    def get_config(cls):
        # FIXME: Replace this as soon as we have a config module
        config = {}
        # HMM dir
        # Try to get hmm_dir from config
        profile_path = jasperpath.config('profile.yml')
     
        if os.path.exists(profile_path):
            with open(profile_path, 'r') as f:
                profile = yaml.safe_load(f)
                if 'keys' in profile :
                    config['userName'] = profile['keys']['USER']
                    config['password'] = profile['keys']['PASS']
        return config

    @classmethod
    def get_instance(cls, vocabulary_name, phrases):
        config = cls.get_config()
        if cls.VOCABULARY_TYPE:
            vocabulary = cls.VOCABULARY_TYPE(vocabulary_name,
                                             path=jasperpath.config(
                                                 'vocabularies'))
            if not vocabulary.matches_phrases(phrases):
                vocabulary.compile(phrases)
            config['vocabulary'] = vocabulary
        instance = cls(**config)
        return instance

    @classmethod
    def get_passive_instance(cls):
        phrases = vocabcompiler.get_keyword_phrases()
        return cls.get_instance('keyword', phrases)

    @classmethod
    def get_active_instance(cls):
        phrases = vocabcompiler.get_all_phrases()
        return cls.get_instance('default', phrases)

    @classmethod
    @abstractmethod
    def is_available(cls):
        return True

    @abstractmethod
    def transcribe(self, fp):
        pass


class Ibm(AbstractSTTEngine):

    SLUG = 'IBM'

    def __init__(self, userName=None,password =None, language='es-ES'):
        """
        Arguments:
        api_key - the public api key which allows access to Google APIs
        """
        self._logger = logging.getLogger(__name__)
        self.language = language
  
    def transcribe(self, audio):
		"""
		Performs STT via the IBM Speech API, transcribing an audio file and
		returning an Spanish string.
		"""
		r = sr.Recognizer()
	
		config = self.get_config()
		IBM_USERNAME = config['userName'] 
		IBM_PASSWORD = config['password'] 
		try:
			mensaje = r.recognize_ibm(audio, username=IBM_USERNAME, password=IBM_PASSWORD,
										language=self.language, show_all=False)
		except sr.UnknownValueError:
			mensaje = "IBM Speech to Text could not understand audio"
		except sr.RequestError as e:
			mensaje ="Could not request results from IBM Speech to Text service; {0}".format(e)
		
		finally:
			return mensaje



class AttSTT(AbstractSTTEngine):
    """
    Speech-To-Text implementation which relies on the AT&T Speech API.
    """

    SLUG = 'ATT'
    
    def __init__(self, userName=None,password =None, language='es-US'):
        """
        Arguments:
        api_key - the public api key which allows access to Google APIs
        """
        self._logger = logging.getLogger(__name__)
        self.language = language
      
    def transcribe(self, audio):
		"""
		Performs STT via the IBM Speech API, transcribing an audio file and
		returning an Spanish string.
		"""
		r = sr.Recognizer()
		
		config = self.get_config()
		ATT_APPKEY = config['userName'] 
		ATT_APPSECRET = config['password'] 
		try:
			mensaje = r.recognize_att(audio, app_key=ATT_APPKEY, app_secret=ATT_APPSECRET,
									language=self.language, show_all=False)
		except sr.UnknownValueError:
			mensaje = "AT&T Speech to Text could not understand audio"
		except sr.RequestError as e:
			mensaje ="Could not request results from IBM Speech to Text service; {0}".format(e)
		
		finally:
			return mensaje

    @classmethod
    def is_available(cls):
        return diagnose.check_network_connection()


def get_engine_by_slug(slug=None):
	"""
	Returns:
		An STT Engine implementation available on the current platform
	
	Raises:
		ValueError if no speaker implementation is supported on this platform
	"""
	
	for engine in get_engines():
		if engine.SLUG == slug:
			return engine
			
	raise ValueError("No  engine found for slug '%s'" % slug)
	

def get_engines():
    def get_subclasses(cls):
        subclasses = set()
        for subclass in cls.__subclasses__():
            subclasses.add(subclass)
            subclasses.update(get_subclasses(subclass))
        return subclasses
    return [tts_engine for tts_engine in
            list(get_subclasses(AbstractSTTEngine))
            if hasattr(tts_engine, 'SLUG') and tts_engine.SLUG]
            
if __name__ == "__main__":
	att = AttSTT()
	
	print(att.get_config())
