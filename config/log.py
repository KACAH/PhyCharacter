import logging


logger = None


def setupLogging(logfilename="demo.log", logidentifier="PythonOgre.Demo"):
    global logger
    # set up logging to file
    logging.basicConfig(level=logging.DEBUG,
                        format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
                        datefmt="%m-%d %H:%M",
                        filename=logfilename,
                        filemode="w")
    # define a Handler which writes INFO messages or higher to the sys.stderr
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    # set a format which is simpler for console use
    formatter = logging.Formatter("%(name)-12s: %(levelname)-8s %(message)s")
    # tell the handler to use this format
    console.setFormatter(formatter)
    # add the handler to the root logger
    logging.getLogger("").addHandler(console)

    logger = logging.getLogger(logidentifier)

def info(msg):
    if logger:
        logger.info(msg)

def error(msg):
    if logger:
        logger.error(msg)

def debug(msg):
    if logger:
        logger.debug(msg)

def warning(msg):
    if logger:
        logger.warning(msg)
