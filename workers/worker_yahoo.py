"""
Implementation of a worker server that connects to Yahoo! Babel Fish.
"""
import re
import sys
import urllib
import urllib2

from worker import AbstractWorkerServer
from TranslationRequestMessage_pb2 import TranslationRequestMessage


class YahooWorker(AbstractWorkerServer):
    """
    Implementation of a worker server that connects to Yahoo! Babel Fish.
    """
    __name__ = 'YahooWorker'
    
    def handle_translation(self, request_id):
        """
        Translates text from German->English using Yahoo! Babel Fish.
        """
        handle = open('/tmp/{0}.message'.format(request_id), 'r+b')
        message = TranslationRequestMessage()
        message.ParseFromString(handle.read())
        
        opener = urllib2.build_opener(urllib2.HTTPHandler)
        
        the_data = urllib.urlencode({'text': message.source_text,
          'lp': 'de_en'})
        the_url = 'http://babelfish.yahoo.com/translate_txt?{0}'.format(
          the_data)
        the_header = {'User-agent': 'Mozilla/5.0'}
        
        http_request = urllib2.Request(the_url, None, the_header)
        http_handle = opener.open(http_request)
        content = http_handle.read()
        http_handle.close()
        
        result_exp = re.compile('<div id="result"><.*?>(.*?)</div></div>',
          re.I|re.U)
        
        result = result_exp.search(content)
        
        if result:
            message.target_text = result.group(1)
            handle.seek(0)
            handle.write(message.SerializeToString())

        handle.close()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print "\n\tusage {0} <host> <port>\n".format(sys.argv[0])
        sys.exit(-1)

    # Prepare XML-RPC server instance running on hostname:port.
    SERVER = YahooWorker(sys.argv[1], int(sys.argv[2]),
      '/tmp/workerserver-yahoo.log')

    # Start server and serve forever.
    SERVER.start_worker()