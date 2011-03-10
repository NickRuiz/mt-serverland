"""
Implementation of a worker server that connects to Microsoft Translator.
"""
import re
import sys
import urllib
import urllib2

from workers.worker import AbstractWorkerServer
from protobuf.TranslationRequestMessage_pb2 import TranslationRequestMessage


class BingWorker(AbstractWorkerServer):
    """
    Implementation of a worker server that connects to Microsoft Translator.
    """
    __name__ = 'BingWorker'
    __splitter__ = '[BING_SPLITTER_TOKEN]'

    def language_pairs(self):
        """
        Returns a tuple of all supported language pairs for this worker.
        """
        languages = ('ara', 'bul', 'chi', 'cze', 'dan', 'dut', 'eng', 'est',
          'fin', 'fre', 'ger', 'gre', 'hat', 'heb', 'hun', 'ita', 'jpn',
          'kor', 'lav', 'lit', 'nor', 'pol', 'por', 'rum', 'rus', 'slo',
          'slv', 'spa', 'swe', 'tha', 'tur')
        return tuple([(a,b) for a in languages for b in languages if a != b])

    def language_code(self, iso639_2_code):
        """
        Converts a given ISO-639-2 code into the worker representation.

        Returns None for unknown languages.
        """
        mapping = {
          'ara': 'ar', 'bul': 'bg', 'chi': 'zh-CHS', 'cze': 'cs', 'dan': 'da',
          'dut': 'nl', 'eng': 'en', 'est': 'et', 'fin': 'fi', 'fre': 'fr',
          'ger': 'de', 'gre': 'el', 'hat': 'ht', 'heb': 'he', 'hun': 'hu',
          'ita': 'it', 'jpn': 'ja', 'kor': 'ko', 'lav': 'lv', 'lit': 'lt',
          'nor': 'no', 'pol': 'pl', 'por': 'pt', 'rum': 'ro', 'rus': 'ru',
          'slo': 'sk', 'slv': 'sl', 'spa': 'es', 'swe': 'sv', 'tha': 'th',
          'tur': 'tr'
        }
        return mapping.get(iso639_2_code)


    def handle_translation(self, request_id):
        """
        Translates text from German->English using Microsoft Translator.

        Requires a Bing AppID as documented at MSDN:
        - http://msdn.microsoft.com/en-us/library/ff512421.aspx
        """
        handle = open('/tmp/{0}.message'.format(request_id), 'r+b')
        message = TranslationRequestMessage()
        message.ParseFromString(handle.read())

        source = self.language_code(message.source_language)
        target = self.language_code(message.target_language)

        # Insert splitter tokens to allow re-construction of original lines.
        _source_text = []
        for source_line in message.source_text.split('\n'):
            _source_text.append(source_line.strip().encode('utf-8'))
            _source_text.append(self.__splitter__)

        app_id = '9259D297CB9F67680C259FD62734B07C0D528312'
        the_data = urllib.urlencode({'appId': app_id, 'from': source,
          'to': target, 'text': u'\n'.join(_source_text)})
        the_url = 'http://api.microsofttranslator.com/v2/Http.svc/' \
          'Translate?{0}'.format(the_data)
        the_header = {'User-agent': 'Mozilla/5.0'}

        opener = urllib2.build_opener(urllib2.HTTPHandler)
        http_request = urllib2.Request(the_url, None, the_header)
        http_handle = opener.open(http_request)
        content = http_handle.read()
        http_handle.close()

        result_exp = re.compile('<string xmlns="http://schemas.microsoft.' \
          'com/2003/10/Serialization/">(.*?)</string>', re.I|re.U|re.S)

        result = result_exp.search(content)

        if result:
            target_text = result.group(1)

            # Re-construct original lines using the splitter tokens.
            _target_text = []
            _current_line = []
            for target_line in target_text.split('\n'):
                if target_line.strip() != self.__splitter__:
                    _current_line.append(unicode(target_line.strip(),
                      'utf-8'))
                else:
                    _target_text.append(u' '.join(_current_line))
                    _current_line = []

            message.target_text = u'\n'.join(_target_text)
            handle.seek(0)
            handle.write(message.SerializeToString())

        else:
            message.target_text = "ERROR: result_exp did not match.\n" \
              "CONTENT: {0}".format(content)
            handle.seek(0)
            handle.write(message.SerializeToString())

        handle.close()
