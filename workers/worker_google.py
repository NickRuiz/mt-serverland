"""
Implementation of a worker server that connects to Google Translate.
"""
import re
import sys
import urllib
import urllib2

from worker import AbstractWorkerServer
from TranslationRequestMessage_pb2 import TranslationRequestMessage


class GoogleWorker(AbstractWorkerServer):
    """
    Implementation of a worker server that connects to Google Translate.
    """
    __name__ = 'GoogleWorker'
    
    def handle_translation(self, request_id):
        """
        Translation handler that obtains a translation via the Google
        translation web front end.

        Currently hard-coded to the language pair DE -> EN.

        """
        message = open('/tmp/{0}.message'.format(request_id), 'r+b')
        request = TranslationRequestMessage()
        request.ParseFromString(message.read())
        
        opener = urllib2.build_opener(urllib2.HTTPHandler)
        
        the_url = 'http://translate.google.com/translate_t'
        the_data = urllib.urlencode({'js': 'n', 'text': request.source_text,
          'sl': 'de', 'tl': 'en'})
        the_header = {'User-agent': 'Mozilla/5.0'}
        
        http_request = urllib2.Request(the_url, the_data, the_header)
        handle = opener.open(http_request)
        content = handle.read()
        handle.close()
        
        result_exp = re.compile('<textarea name=utrans wrap=SOFT ' \
          'dir="ltr" id=suggestion.*>(.*?)</textarea>', re.I|re.U)
        
        result = result_exp.search(content)
        
        if result:
            request.target_text = result.group(1)
            message.seek(0)
            message.write(request.SerializeToString())

        message.close()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print "\n\tusage {0} <host> <port>\n".format(sys.argv[0])
        sys.exit(-1)

    # Prepare XML-RPC server instance running on hostname:port.
    SERVER = GoogleWorker(sys.argv[1], int(sys.argv[2]),
      '/tmp/workerserver-google.log')

    # Start server and serve forever.
    SERVER.start_worker()