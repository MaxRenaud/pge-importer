__author__ = 'Max Renaud'
from lib import XMLLoader
from lib import rrd
import argparse
import ConfigParser
import logging


def read_config(file_name):
    ret_dict = dict()
    Config = ConfigParser.ConfigParser()
    Config.read(file_name)
    for option in Config.options('config'):
        ret_dict[option] = Config.get('config', option)
    return ret_dict


def log_config():
    """Configure logging"""
    logging.basicConfig(format='%(asctime)s (%(levelname)s) %(message)s',
                        datefmt='%m/%d/%Y %H:%M:%S')
    logging.getLogger().setLevel(logging.INFO)


def get_parser():
    parser = argparse.ArgumentParser(description="PG&E usage/cost to cacti importer")
    parser.add_argument('-c', '--config', action='store', dest='config', help='config file to use.',
                        default='./config')
    parser.add_argument('-d', '--debug', action='store_true', default=False, dest='debug',
                        help="show debugging information")
    return parser.parse_args()


def main():
    log_config()
    opts = get_parser()
    if opts.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    print "PG&E RRD importer v0.1 - by Max Renaud"
    logging.debug("Parsing config file: {0}".format(opts.config))
    config = read_config(opts.config)
    last_update = rrd.find_next_ts(config['kwh_file'])
    logging.info("Last update: {0}".format(last_update))
    archive = XMLLoader.download_archive(last_update, config['login'] , config['password'])
    #archive = open('/home/max/tmp/test.zip', 'r').read()
    files = XMLLoader.extract_file(archive)
    if len(files) != 1:
        print "PG&E's zip file has more than one file. Unknown condition."
        quit()
    intervals = XMLLoader.parse_file(files.pop())
    updates=0
    for i in intervals:
        #ignore old data
        if i[0] > last_update:
            logging.debug( "{0} - {1} - {2}".format(i[0], i[1], i[2]))
            rrd.update_rrd(config['kwh_file'], i[0], i[1])
            rrd.update_rrd(config['cost_file'], i[0], i[2])
            updates += 1
    logging.info("Updated {0} records".format(updates))

if __name__ == '__main__':
    main()