import os
import sys
import md5
import os.path
import imp
import logging

log = logging.getLogger("proctor.plugins")


def load_module(code_path):
    """Load the module"""
    log.debug(u"Loading module {}".format(code_path))
    try:
        try:
            code_dir = os.path.dirname(code_path)
            code_file = os.path.basename(code_path)

            fin = open(code_path, 'rb')
            module_id = md5.new(code_path).hexdigest()
            module_id = "{}_{}".format(module_id, os.path.splitext(code_file)[0])
            log.debug("Importing {} as {}".format(code_file, module_id))
            sys.path.insert(0, code_dir)
            mod = imp.load_source(module_id, code_path, fin)
            sys.path.pop(sys.path.index(code_dir))
            log.debug(u"Loaded {}".format(mod))
            return mod
        finally:
            try:
                fin.close()
                sys.path.pop(sys.path.index(code_dir))
            except:
                pass

    except ImportError:
        log.exception("IMPORT ERROR")

    except:
        log.exception("OTHER ERROR")


def load(directory):
    """traverse a directory trying to import modules"""

    log.info("Loading modules in {}".format(directory))

    if not os.path.isdir(directory):
        log.warn("{} does not exist".format(directory))
        return False

    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if filename.endswith(".py"):
            log.debug("Loading py module: {}".format(filename))
            load_module(filepath)

        if os.path.isdir(filepath):
            load(filepath)
    return True
