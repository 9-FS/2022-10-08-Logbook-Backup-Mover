import KFS.log      #setup logging
import logging      #standard logging
import traceback    #exception message full when program crashes as .exe
from main import main


logger=KFS.log.setup_logging(__name__, logging.INFO)    #named logger because dropbox injects global logger with own undesired logging messages
try:
    main(logger)
except:
    logger.critical(traceback.format_exc())
    
    print("\n\nPress enter to close program.", flush=True)
    input() #pause
else:
    print("\n", end="", flush=True)