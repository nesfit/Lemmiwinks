import os

class DwnldIntf():


    def safe_2_file(self, stream, path):
        dir = os.path.dirname(path)
        if not os.path.exists(dir):
            os.makedirs(dir)

        with open(path, 'wb') as fd:
            fd.write(stream)



